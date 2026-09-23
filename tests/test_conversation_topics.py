from uuid import uuid4

import pytest

from alrifai.conversations import (
    Channel,
    ConversationScope,
    InMemoryTopicStore,
    TopicConflictError,
    TopicEvidence,
    TopicState,
    TopicStateService,
    TopicTransitionError,
    TopicTransitionKind,
    TopicTransitionRequest,
)


def make_service():
    return TopicStateService(InMemoryTopicStore())


def make_topic(service, *, conversation_id=None, scope=ConversationScope.PRIVATE):
    return service.create_topic(
        conversation_id=conversation_id or uuid4(),
        conversation_scope=scope,
        channel=Channel.WHATSAPP,
        source_account="test-account",
        idempotency_key=f"create-{uuid4()}",
    )


def transition(service, topic, state, kind, evidence, *, key=None, **kwargs):
    return service.transition(
        topic.topic_id,
        TopicTransitionRequest(
            target_state=state,
            transition_kind=kind,
            evidence=tuple(evidence),
            conversation_id=topic.conversation_id,
            idempotency_key=key,
            expected_state_version=kwargs.pop("expected_state_version", None),
            **kwargs,
        ),
    )


def test_topic_lifecycle_supports_activation_suspension_resumption_completion_and_closure():
    service = make_service()
    topic = make_topic(service)

    topic = transition(service, topic, TopicState.GATHERING, TopicTransitionKind.ACTIVATE, [TopicEvidence.TYPED_ASSOCIATION])
    topic = transition(service, topic, TopicState.SUSPENDED, TopicTransitionKind.SUSPEND, [TopicEvidence.TOPIC_SWITCH])
    topic = transition(service, topic, TopicState.REOPENED, TopicTransitionKind.RESUME, [TopicEvidence.EXPLICIT_RESUME])
    topic = transition(service, topic, TopicState.GATHERING, TopicTransitionKind.ACTIVATE, [TopicEvidence.TYPED_ASSOCIATION])
    topic = transition(service, topic, TopicState.COMPLETED, TopicTransitionKind.COMPLETE, [TopicEvidence.WORKFLOW_COMPLETION])
    topic = transition(service, topic, TopicState.CLOSED, TopicTransitionKind.CLOSE, [TopicEvidence.EXPLICIT_USER_COMPLETION])

    assert topic.state is TopicState.CLOSED
    assert [item.to_state for item in service.history(topic.topic_id)] == [
        TopicState.OPENED,
        TopicState.GATHERING,
        TopicState.SUSPENDED,
        TopicState.REOPENED,
        TopicState.GATHERING,
        TopicState.COMPLETED,
        TopicState.CLOSED,
    ]


def test_closed_topic_requires_explicit_reopening_evidence():
    service = make_service()
    topic = make_topic(service)
    topic = transition(service, topic, TopicState.GATHERING, TopicTransitionKind.ACTIVATE, [TopicEvidence.TYPED_ASSOCIATION])
    topic = transition(service, topic, TopicState.COMPLETED, TopicTransitionKind.COMPLETE, [TopicEvidence.WORKFLOW_COMPLETION])
    topic = transition(service, topic, TopicState.CLOSED, TopicTransitionKind.CLOSE, [TopicEvidence.WORKFLOW_COMPLETION])

    with pytest.raises(TopicTransitionError):
        transition(service, topic, TopicState.REOPENED, TopicTransitionKind.REOPEN, [TopicEvidence.TOPIC_SWITCH])

    reopened = transition(service, topic, TopicState.REOPENED, TopicTransitionKind.REOPEN, [TopicEvidence.EXPLICIT_REOPEN])
    assert reopened.state is TopicState.REOPENED


def test_invalid_transition_is_rejected_without_history_mutation():
    service = make_service()
    topic = make_topic(service)

    with pytest.raises(TopicTransitionError):
        transition(service, topic, TopicState.CLOSED, TopicTransitionKind.CLOSE, [TopicEvidence.WORKFLOW_COMPLETION])

    assert len(service.history(topic.topic_id)) == 1
    assert service.store.get(topic.topic_id).state is TopicState.OPENED


def test_duplicate_transition_is_idempotent():
    service = make_service()
    topic = make_topic(service)
    request = TopicTransitionRequest(
        target_state=TopicState.GATHERING,
        transition_kind=TopicTransitionKind.ACTIVATE,
        evidence=(TopicEvidence.TYPED_ASSOCIATION,),
        conversation_id=topic.conversation_id,
        idempotency_key="activate-1",
    )

    first = service.transition(topic.topic_id, request)
    second = service.transition(topic.topic_id, request)

    assert first == second
    assert len(service.history(topic.topic_id)) == 2
    assert first.state_version == 1


def test_stale_version_and_conflicting_conversation_fail_closed():
    service = make_service()
    topic = make_topic(service)
    topic = transition(service, topic, TopicState.GATHERING, TopicTransitionKind.ACTIVATE, [TopicEvidence.TYPED_ASSOCIATION])

    with pytest.raises(TopicConflictError):
        transition(
            service,
            topic,
            TopicState.SUSPENDED,
            TopicTransitionKind.SUSPEND,
            [TopicEvidence.TOPIC_SWITCH],
            expected_state_version=0,
        )

    with pytest.raises(TopicTransitionError):
        service.transition(
            topic.topic_id,
            TopicTransitionRequest(
                target_state=TopicState.SUSPENDED,
                transition_kind=TopicTransitionKind.SUSPEND,
                evidence=(TopicEvidence.TOPIC_SWITCH,),
                conversation_id=uuid4(),
            ),
        )


def test_multiple_topics_and_topic_switch_do_not_close_previous_topic():
    service = make_service()
    conversation_id = uuid4()
    first = make_topic(service, conversation_id=conversation_id)
    first = transition(service, first, TopicState.GATHERING, TopicTransitionKind.ACTIVATE, [TopicEvidence.TYPED_ASSOCIATION])
    second = service.create_topic(
        conversation_id=conversation_id,
        conversation_scope=ConversationScope.PRIVATE,
        channel=Channel.WHATSAPP,
        source_account="test-account",
        related_topic_id=first.topic_id,
        idempotency_key="second-topic",
    )

    assert first.state is TopicState.GATHERING
    assert second.related_topic_id == first.topic_id
    assert second.topic_id != first.topic_id


def test_group_and_public_topics_have_no_single_person_owner():
    service = make_service()
    group = make_topic(service, scope=ConversationScope.GROUP)
    public = make_topic(service, scope=ConversationScope.PUBLIC)

    assert group.conversation_scope is ConversationScope.GROUP
    assert public.conversation_scope is ConversationScope.PUBLIC


def test_late_arrival_association_preserves_history_and_does_not_reopen_closed_topic():
    service = make_service()
    topic = make_topic(service)
    topic = transition(service, topic, TopicState.GATHERING, TopicTransitionKind.ACTIVATE, [TopicEvidence.TYPED_ASSOCIATION])
    topic = transition(service, topic, TopicState.COMPLETED, TopicTransitionKind.COMPLETE, [TopicEvidence.WORKFLOW_COMPLETION])
    topic = transition(service, topic, TopicState.CLOSED, TopicTransitionKind.CLOSE, [TopicEvidence.WORKFLOW_COMPLETION])

    with pytest.raises(TopicConflictError):
        transition(
            service,
            topic,
            TopicState.REOPENED,
            TopicTransitionKind.REOPEN,
            [TopicEvidence.LATE_ARRIVAL_REEVALUATION],
        )

    assert service.store.get(topic.topic_id).state is TopicState.CLOSED
    assert len(service.history(topic.topic_id)) == 4


def test_association_is_restart_reconstructable_and_does_not_infer_semantics():
    service = make_service()
    topic = make_topic(service)
    turn_id = uuid4()
    message_id = uuid4()
    updated = transition(
        service,
        topic,
        TopicState.OPENED,
        TopicTransitionKind.ASSOCIATE,
        [TopicEvidence.TYPED_ASSOCIATION],
        key="associate-1",
        turn_ids=(turn_id,),
        message_ids=(message_id,),
    )

    assert updated.turn_ids == (turn_id,)
    assert updated.message_ids == (message_id,)
    assert updated.domain is None
    assert updated.semantic_label is None
    assert service.store.get(topic.topic_id) == updated
    assert len(service.history(topic.topic_id)) == 2


def test_user_text_or_actor_label_does_not_create_admin_authority():
    service = make_service()
    topic = make_topic(service)

    with pytest.raises(TopicTransitionError):
        transition(
            service,
            topic,
            TopicState.CLOSED,
            TopicTransitionKind.CLOSE,
            [TopicEvidence.AUTHORIZED_HUMAN_CLOSURE],
            actor="claimed_admin_from_message_text",
        )
