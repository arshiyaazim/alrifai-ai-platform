from datetime import datetime, timedelta, timezone
from uuid import uuid4

from alrifai.conversations.models import (
    ActorType,
    Channel,
    Direction,
    MediaReference,
    Message,
    MessageContentType,
    OrderingEvidence,
)
from alrifai.conversations.ordering import OrderingConfidence, resolve_message_order
from alrifai.conversations.turns import (
    AggregationEvidence,
    TurnAggregationConfig,
    TurnStatus,
    build_turns,
    stabilize_turns,
)


BASE = datetime(2026, 9, 22, 10, 0, tzinfo=timezone.utc)


def message(
    conversation_id,
    *,
    seconds=0,
    body="fragment",
    sender="person-1",
    direction=Direction.INBOUND,
    actor=ActorType.EXTERNAL_USER,
    content_type=MessageContentType.TEXT,
    media_refs=(),
    reply_to=None,
    provider_sequence=None,
    received_seconds=None,
    message_id=None,
):
    occurred = BASE + timedelta(seconds=seconds)
    received = BASE + timedelta(seconds=seconds if received_seconds is None else received_seconds)
    return Message(
        message_id=message_id or uuid4(),
        conversation_id=conversation_id,
        channel=Channel.WHATSAPP,
        direction=direction,
        sender=sender,
        actor_type=actor,
        occurred_at=occurred,
        received_at=received,
        body=body if content_type is MessageContentType.TEXT else None,
        content_type=content_type,
        media_refs=media_refs,
        reply_to_message_id=reply_to,
        ordering=OrderingEvidence(provider_sequence=provider_sequence),
    )


def test_ordering_reconstructs_source_order_and_marks_late_arrival():
    conversation_id = uuid4()
    first = message(conversation_id, seconds=1, body="A")
    late = message(conversation_id, seconds=2, body="B")
    last = message(conversation_id, seconds=3, body="C")

    result = resolve_message_order((first, last, late))

    assert tuple(item.message.body for item in result.ordered) == ("A", "B", "C")
    assert result.ordered[1].late_arrival is True
    assert result.confidence is OrderingConfidence.HIGH


def test_provider_sequence_is_preferred_and_reply_evidence_is_preserved():
    conversation_id = uuid4()
    older = message(conversation_id, seconds=10, body="older", provider_sequence="1")
    reply = message(
        conversation_id,
        seconds=2,
        body="reply",
        provider_sequence="2",
        reply_to=older.message_id,
    )

    result = resolve_message_order((reply, older))

    assert tuple(item.message.body for item in result.ordered) == ("older", "reply")
    assert result.confidence is OrderingConfidence.EXACT_PROVIDER
    assert AggregationEvidence is not None
    assert "reply_relationship_preserved" in {
        evidence.value for evidence in result.ordered[1].evidence
    }


def test_conflicting_provider_sequence_is_explicitly_ambiguous():
    conversation_id = uuid4()
    left = message(conversation_id, seconds=1, body="left", provider_sequence="1")
    right = message(conversation_id, seconds=2, body="right", provider_sequence="1")

    result = resolve_message_order((left, right))

    assert result.confidence is OrderingConfidence.AMBIGUOUS
    assert any(
        evidence.value == "conflicting_provider_evidence"
        for evidence in result.ordered[0].evidence
    )


def test_identical_source_timestamps_preserve_deterministic_tie_evidence():
    conversation_id = uuid4()
    left = message(conversation_id, seconds=1, body="left")
    right = message(conversation_id, seconds=1, body="right")

    result = resolve_message_order((left, right))

    assert result.confidence is OrderingConfidence.AMBIGUOUS
    assert all(
        "arrival_order" in {evidence.value for evidence in item.evidence}
        for item in result.ordered
    )


def test_fragments_form_one_turn_and_rebuild_is_idempotent():
    conversation_id = uuid4()
    messages = (
        message(conversation_id, seconds=1, body="আমি"),
        message(conversation_id, seconds=5, body="জাহাজে"),
        message(conversation_id, seconds=10, body="কাজ করতে চাই"),
    )

    first = build_turns(messages)
    second = build_turns(messages)

    assert len(first.turns) == 1
    assert first.turns[0].message_ids == tuple(item.message_id for item in messages)
    assert first.turns[0].turn_id == second.turns[0].turn_id
    assert AggregationEvidence.CONTINUATION_FRAGMENT in first.turns[0].aggregation_evidence


def test_outbound_response_is_a_turn_boundary():
    conversation_id = uuid4()
    inbound_one = message(conversation_id, seconds=1, body="চাকরি করতে চাই")
    response = message(
        conversation_id,
        seconds=2,
        body="কোন পদে?",
        direction=Direction.OUTBOUND,
        actor=ActorType.HUMAN_OPERATOR,
    )
    inbound_two = message(conversation_id, seconds=3, body="জাহাজে")

    result = build_turns((inbound_one, response, inbound_two))

    assert [turn.message_ids for turn in result.turns] == [
        (inbound_one.message_id,),
        (response.message_id,),
        (inbound_two.message_id,),
    ]
    assert result.turns[1].boundary_reason is AggregationEvidence.OUTBOUND_BOUNDARY


def test_group_sender_change_and_media_are_structurally_safe():
    conversation_id = uuid4()
    text = message(conversation_id, seconds=1, body="এইটা আমার NID", sender="a")
    image = message(
        conversation_id,
        seconds=2,
        body=None,
        sender="a",
        content_type=MessageContentType.IMAGE,
        media_refs=(MediaReference("media:1", MessageContentType.IMAGE),),
    )
    other = message(conversation_id, seconds=3, body="আমি যাব", sender="b")

    result = build_turns((text, image, other))

    assert result.turns[0].message_ids == (text.message_id, image.message_id)
    assert AggregationEvidence.MEDIA_ASSOCIATION in result.turns[0].aggregation_evidence
    assert result.turns[1].boundary_reason is AggregationEvidence.SENDER_CHANGED


def test_temporal_boundary_and_stabilization_are_configurable():
    conversation_id = uuid4()
    config = TurnAggregationConfig(max_gap=timedelta(seconds=5))
    first = message(conversation_id, seconds=1, body="প্রথম")
    second = message(conversation_id, seconds=10, body="দ্বিতীয়")

    result = build_turns((first, second), config=config)
    stable = stabilize_turns(result, as_of=BASE + timedelta(seconds=20), config=config)

    assert len(result.turns) == 2
    assert result.turns[1].boundary_reason is AggregationEvidence.TEMPORAL_BOUNDARY
    assert all(turn.status is TurnStatus.STABILIZED for turn in stable.turns)


def test_late_arrival_re_evaluates_previous_candidate_without_duplicate_effects():
    conversation_id = uuid4()
    first = message(conversation_id, seconds=1, body="আমি")
    last = message(conversation_id, seconds=3, body="জাহাজে")
    late = message(conversation_id, seconds=2, body="কাজ চাই")

    previous = build_turns((first, last))
    rebuilt = build_turns((first, last, late), previous_turns=previous.turns)

    assert len(rebuilt.turns) == 1
    assert rebuilt.turns[0].status is TurnStatus.RE_EVALUATED
    assert previous.turns[0].turn_id in rebuilt.replaced_turn_ids
    assert len({turn.turn_id for turn in rebuilt.turns}) == 1
