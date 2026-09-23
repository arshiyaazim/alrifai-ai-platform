"""C4 deterministic topic-state contracts and persistence adapters.

This module consumes typed topic proposals only. It does not classify language,
select Admin instructions, call Hermes, retrieve semantic history, or dispatch
domain actions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from .models import Channel, ConversationScope


class TopicState(StrEnum):
    OPENED = "opened"
    NEW = "opened"
    GATHERING = "gathering"
    ACTIVE = "gathering"
    AWAITING_USER = "awaiting_user"
    AWAITING_APPROVAL = "awaiting_approval"
    SUSPENDED = "suspended"
    PAUSED = "suspended"
    COMPLETED = "completed"
    CLOSED = "closed"
    REOPENED = "reopened"
    RESUMED = "reopened"
    UNRESOLVED = "unresolved"


class TopicTransitionKind(StrEnum):
    CREATE = "create"
    ACTIVATE = "activate"
    SUSPEND = "suspend"
    RESUME = "resume"
    COMPLETE = "complete"
    CLOSE = "close"
    REOPEN = "reopen"
    ASSOCIATE = "associate"


class TopicEvidence(StrEnum):
    CREATED = "created"
    TYPED_ASSOCIATION = "typed_association"
    AUTHORIZED_HUMAN_CLOSURE = "authorized_human_closure"
    EXPLICIT_USER_COMPLETION = "explicit_user_completion"
    WORKFLOW_COMPLETION = "workflow_completion"
    SEMANTIC_CLOSURE_PROPOSAL = "semantic_closure_proposal"
    EXPLICIT_REOPEN = "explicit_reopen"
    EXPLICIT_RESUME = "explicit_resume"
    TOPIC_SWITCH = "topic_switch"
    LATE_ARRIVAL_REEVALUATION = "late_arrival_reevaluation"
    RETRY = "retry"


class TopicTransitionError(ValueError):
    """A deterministic topic transition failed validation."""


class TopicConflictError(RuntimeError):
    """A topic transition encountered stale or conflicting state."""


@dataclass(frozen=True, slots=True)
class TopicTransitionRequest:
    target_state: TopicState
    transition_kind: TopicTransitionKind
    evidence: tuple[TopicEvidence, ...]
    conversation_id: UUID
    message_ids: tuple[UUID, ...] = ()
    turn_ids: tuple[UUID, ...] = ()
    actor: str = "system"
    source: str = "c4"
    correlation_id: str | None = None
    causation_id: str | None = None
    idempotency_key: str | None = None
    expected_state_version: int | None = None
    related_topic_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class TopicTransition:
    transition_id: UUID
    topic_id: UUID
    from_state: TopicState | None
    to_state: TopicState
    transition_kind: TopicTransitionKind
    evidence: tuple[TopicEvidence, ...]
    conversation_id: UUID
    message_ids: tuple[UUID, ...]
    turn_ids: tuple[UUID, ...]
    actor: str
    source: str
    occurred_at: datetime
    correlation_id: str | None
    causation_id: str | None
    idempotency_key: str | None
    state_version: int


@dataclass(frozen=True, slots=True)
class Topic:
    topic_id: UUID
    conversation_id: UUID
    conversation_scope: ConversationScope
    channel: Channel
    source_account: str
    state: TopicState
    domain: str | None = None
    semantic_label: str | None = None
    related_topic_id: UUID | None = None
    message_ids: tuple[UUID, ...] = ()
    turn_ids: tuple[UUID, ...] = ()
    last_activity_at: datetime | None = None
    state_version: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TopicStore(Protocol):
    def get(self, topic_id: UUID) -> Topic | None: ...

    def create(self, topic: Topic, transition: TopicTransition) -> Topic: ...

    def apply(
        self,
        topic: Topic,
        transition: TopicTransition,
        expected_state_version: int | None,
    ) -> Topic: ...

    def history(self, topic_id: UUID) -> tuple[TopicTransition, ...]: ...

    def find_idempotent(self, topic_id: UUID, key: str) -> TopicTransition | None: ...


class InMemoryTopicStore:
    """Deterministic C4 store used by unit tests and local orchestration."""

    def __init__(self) -> None:
        self.topics: dict[UUID, Topic] = {}
        self.transitions: dict[UUID, list[TopicTransition]] = {}
        self.idempotency: dict[tuple[UUID, str], TopicTransition] = {}

    def get(self, topic_id: UUID) -> Topic | None:
        return self.topics.get(topic_id)

    def create(self, topic: Topic, transition: TopicTransition) -> Topic:
        if topic.topic_id in self.topics:
            existing = self.topics[topic.topic_id]
            if transition.idempotency_key and self.find_idempotent(topic.topic_id, transition.idempotency_key):
                return existing
            raise TopicConflictError("topic already exists")
        self.topics[topic.topic_id] = topic
        self.transitions[topic.topic_id] = [transition]
        if transition.idempotency_key:
            self.idempotency[(topic.topic_id, transition.idempotency_key)] = transition
        return topic

    def apply(
        self,
        topic: Topic,
        transition: TopicTransition,
        expected_state_version: int | None,
    ) -> Topic:
        current = self.topics.get(topic.topic_id)
        if current is None:
            raise TopicConflictError("topic does not exist")
        if expected_state_version is not None and current.state_version != expected_state_version:
            raise TopicConflictError("stale topic state version")
        if transition.idempotency_key:
            existing = self.find_idempotent(topic.topic_id, transition.idempotency_key)
            if existing is not None:
                return current
        self.topics[topic.topic_id] = topic
        self.transitions.setdefault(topic.topic_id, []).append(transition)
        if transition.idempotency_key:
            self.idempotency[(topic.topic_id, transition.idempotency_key)] = transition
        return topic

    def history(self, topic_id: UUID) -> tuple[TopicTransition, ...]:
        return tuple(self.transitions.get(topic_id, ()))

    def find_idempotent(self, topic_id: UUID, key: str) -> TopicTransition | None:
        return self.idempotency.get((topic_id, key))


class PostgresTopicStore:
    """Minimal transactional adapter for the canonical V008 tables."""

    def __init__(self, connection) -> None:
        self.connection = connection

    def get(self, topic_id: UUID) -> Topic | None:
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """
                SELECT topic_id, conversation_id, conversation_scope, channel,
                       source_account, state, domain, semantic_label,
                       related_topic_id, evidence_message_ids, evidence_turn_ids,
                       last_activity_at, state_version, created_at, updated_at
                FROM conversation_topics WHERE topic_id = %s
                """,
                (topic_id,),
            )
            row = cursor.fetchone()
            return _topic_from_row(row) if row else None
        finally:
            cursor.close()

    def create(self, topic: Topic, transition: TopicTransition) -> Topic:
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO conversation_topics (
                    topic_id, conversation_id, conversation_scope, channel,
                    source_account, state, domain, semantic_label,
                    related_topic_id, evidence_message_ids, evidence_turn_ids,
                    last_activity_at, state_version, created_at, updated_at
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s)
                """,
                _topic_params(topic),
            )
            self._insert_transition(cursor, transition)
            self.connection.commit()
            return topic
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def apply(
        self,
        topic: Topic,
        transition: TopicTransition,
        expected_state_version: int | None,
    ) -> Topic:
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """
                UPDATE conversation_topics SET state=%s, related_topic_id=%s,
                    evidence_message_ids=%s::jsonb, evidence_turn_ids=%s::jsonb,
                    last_activity_at=%s, state_version=%s, updated_at=%s
                WHERE topic_id=%s AND (%s IS NULL OR state_version=%s)
                RETURNING topic_id
                """,
                (
                    topic.state.value,
                    topic.related_topic_id,
                    json.dumps([str(item) for item in topic.message_ids]),
                    json.dumps([str(item) for item in topic.turn_ids]),
                    topic.last_activity_at,
                    topic.state_version,
                    topic.updated_at,
                    topic.topic_id,
                    expected_state_version,
                    expected_state_version,
                ),
            )
            if cursor.fetchone() is None:
                raise TopicConflictError("stale topic state version or missing topic")
            self._insert_transition(cursor, transition)
            self.connection.commit()
            return topic
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

    def history(self, topic_id: UUID) -> tuple[TopicTransition, ...]:
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """
                SELECT transition_id, topic_id, from_state, to_state,
                       transition_kind, evidence, conversation_id,
                       message_ids, turn_ids, actor, source, occurred_at,
                       correlation_id, causation_id, idempotency_key, state_version
                FROM conversation_topic_transitions
                WHERE topic_id=%s ORDER BY state_version, occurred_at, transition_id
                """,
                (topic_id,),
            )
            return tuple(_transition_from_row(row) for row in cursor.fetchall())
        finally:
            cursor.close()

    def find_idempotent(self, topic_id: UUID, key: str) -> TopicTransition | None:
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """
                SELECT transition_id, topic_id, from_state, to_state,
                       transition_kind, evidence, conversation_id,
                       message_ids, turn_ids, actor, source, occurred_at,
                       correlation_id, causation_id, idempotency_key, state_version
                FROM conversation_topic_transitions
                WHERE topic_id=%s AND idempotency_key=%s
                """,
                (topic_id, key),
            )
            row = cursor.fetchone()
            return _transition_from_row(row) if row else None
        finally:
            cursor.close()

    @staticmethod
    def _insert_transition(cursor, transition: TopicTransition) -> None:
        cursor.execute(
            """
            INSERT INTO conversation_topic_transitions (
                transition_id, topic_id, from_state, to_state, transition_kind,
                evidence, conversation_id, message_ids, turn_ids, actor, source,
                occurred_at, correlation_id, causation_id, idempotency_key,
                state_version
            ) VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (topic_id, idempotency_key) DO NOTHING
            """,
            (
                transition.transition_id,
                transition.topic_id,
                transition.from_state.value if transition.from_state else None,
                transition.to_state.value,
                transition.transition_kind.value,
                json.dumps([item.value for item in transition.evidence]),
                transition.conversation_id,
                json.dumps([str(item) for item in transition.message_ids]),
                json.dumps([str(item) for item in transition.turn_ids]),
                transition.actor,
                transition.source,
                transition.occurred_at,
                transition.correlation_id,
                transition.causation_id,
                transition.idempotency_key,
                transition.state_version,
            ),
        )


class TopicStateService:
    """Validate and apply typed C4 topic transitions."""

    _allowed: dict[TopicState, frozenset[TopicState]] = {
        TopicState.OPENED: frozenset({TopicState.GATHERING, TopicState.UNRESOLVED, TopicState.SUSPENDED}),
        TopicState.GATHERING: frozenset({TopicState.AWAITING_USER, TopicState.AWAITING_APPROVAL, TopicState.COMPLETED, TopicState.SUSPENDED, TopicState.CLOSED}),
        TopicState.AWAITING_USER: frozenset({TopicState.GATHERING, TopicState.COMPLETED, TopicState.SUSPENDED}),
        TopicState.AWAITING_APPROVAL: frozenset({TopicState.GATHERING, TopicState.COMPLETED, TopicState.SUSPENDED}),
        TopicState.SUSPENDED: frozenset({TopicState.GATHERING, TopicState.REOPENED, TopicState.CLOSED}),
        TopicState.COMPLETED: frozenset({TopicState.CLOSED, TopicState.REOPENED}),
        TopicState.CLOSED: frozenset({TopicState.REOPENED}),
        TopicState.REOPENED: frozenset({TopicState.GATHERING, TopicState.SUSPENDED, TopicState.COMPLETED}),
        TopicState.UNRESOLVED: frozenset({TopicState.OPENED, TopicState.GATHERING, TopicState.SUSPENDED}),
    }

    def __init__(self, store: TopicStore) -> None:
        self.store = store

    def create_topic(
        self,
        *,
        conversation_id: UUID,
        conversation_scope: ConversationScope,
        channel: Channel,
        source_account: str,
        state: TopicState = TopicState.OPENED,
        domain: str | None = None,
        semantic_label: str | None = None,
        message_ids: tuple[UUID, ...] = (),
        turn_ids: tuple[UUID, ...] = (),
        related_topic_id: UUID | None = None,
        topic_id: UUID | None = None,
        idempotency_key: str | None = None,
        actor: str = "system",
        source: str = "c4",
    ) -> Topic:
        if state not in (TopicState.OPENED, TopicState.UNRESOLVED):
            raise TopicTransitionError("new topics must start opened or unresolved")
        _validate_scope(conversation_scope, None)
        now = datetime.now(timezone.utc)
        topic = Topic(
            topic_id=topic_id or uuid4(),
            conversation_id=conversation_id,
            conversation_scope=conversation_scope,
            channel=channel,
            source_account=source_account,
            state=state,
            domain=domain,
            semantic_label=semantic_label,
            related_topic_id=related_topic_id,
            message_ids=message_ids,
            turn_ids=turn_ids,
            last_activity_at=now,
            created_at=now,
            updated_at=now,
        )
        transition = _transition(
            topic,
            None,
            TopicTransitionKind.CREATE,
            (TopicEvidence.CREATED,),
            conversation_id,
            actor,
            source,
            idempotency_key,
            0,
        )
        return self.store.create(topic, transition)

    def transition(self, topic_id: UUID, request: TopicTransitionRequest) -> Topic:
        topic = self.store.get(topic_id)
        if topic is None:
            raise TopicConflictError("topic does not exist")
        if request.conversation_id != topic.conversation_id:
            raise TopicTransitionError("topic transition crosses conversation scope")
        if request.expected_state_version is not None and request.expected_state_version != topic.state_version:
            raise TopicConflictError("stale topic state version")
        if request.idempotency_key:
            existing = self.store.find_idempotent(topic_id, request.idempotency_key)
            if existing is not None:
                return topic
        _validate_transition(topic, request)
        now = datetime.now(timezone.utc)
        next_topic = replace(
            topic,
            state=request.target_state,
            related_topic_id=request.related_topic_id or topic.related_topic_id,
            message_ids=_merge_ids(topic.message_ids, request.message_ids),
            turn_ids=_merge_ids(topic.turn_ids, request.turn_ids),
            last_activity_at=now,
            updated_at=now,
            state_version=topic.state_version + 1,
        )
        transition = _transition(
            next_topic,
            topic.state,
            request.transition_kind,
            request.evidence,
            request.conversation_id,
            request.actor,
            request.source,
            request.idempotency_key,
            next_topic.state_version,
            request.message_ids,
            request.turn_ids,
            request.correlation_id,
            request.causation_id,
        )
        return self.store.apply(next_topic, transition, request.expected_state_version)

    def history(self, topic_id: UUID) -> tuple[TopicTransition, ...]:
        return self.store.history(topic_id)


def _validate_transition(topic: Topic, request: TopicTransitionRequest) -> None:
    target = request.target_state
    if target not in TopicState:
        raise TopicTransitionError("unknown topic state")
    same_state_association = (
        target is topic.state and request.transition_kind is TopicTransitionKind.ASSOCIATE
    )
    if not same_state_association and target not in TopicStateService._allowed[topic.state]:
        raise TopicTransitionError(f"invalid transition {topic.state.value} -> {target.value}")
    if TopicEvidence.LATE_ARRIVAL_REEVALUATION in request.evidence and topic.state is TopicState.CLOSED:
        raise TopicConflictError("late arrival cannot silently reopen a closed topic")
    if topic.state is TopicState.CLOSED and target is TopicState.REOPENED:
        if not ({TopicEvidence.EXPLICIT_REOPEN, TopicEvidence.EXPLICIT_RESUME} & set(request.evidence)):
            raise TopicTransitionError("closed topics require explicit reopening evidence")
    if request.target_state is TopicState.CLOSED:
        closure_evidence = {
            TopicEvidence.AUTHORIZED_HUMAN_CLOSURE,
            TopicEvidence.EXPLICIT_USER_COMPLETION,
            TopicEvidence.WORKFLOW_COMPLETION,
            TopicEvidence.SEMANTIC_CLOSURE_PROPOSAL,
        }
        if not closure_evidence.intersection(request.evidence):
            raise TopicTransitionError("closure requires typed completion evidence")
    _validate_scope(topic.conversation_scope, None)


def _validate_scope(scope: ConversationScope, person_id) -> None:
    if scope in (ConversationScope.GROUP, ConversationScope.PUBLIC) and person_id is not None:
        raise TopicTransitionError("group/public topic cannot be owned by one Person")


def _merge_ids(existing: tuple[UUID, ...], incoming: tuple[UUID, ...]) -> tuple[UUID, ...]:
    return tuple(dict.fromkeys((*existing, *incoming)))


def _transition(
    topic: Topic,
    from_state: TopicState | None,
    kind: TopicTransitionKind,
    evidence: tuple[TopicEvidence, ...],
    conversation_id: UUID,
    actor: str,
    source: str,
    idempotency_key: str | None,
    state_version: int,
    message_ids: tuple[UUID, ...] = (),
    turn_ids: tuple[UUID, ...] = (),
    correlation_id: str | None = None,
    causation_id: str | None = None,
) -> TopicTransition:
    return TopicTransition(
        transition_id=uuid4(),
        topic_id=topic.topic_id,
        from_state=from_state,
        to_state=topic.state,
        transition_kind=kind,
        evidence=evidence,
        conversation_id=conversation_id,
        message_ids=message_ids,
        turn_ids=turn_ids,
        actor=actor,
        source=source,
        occurred_at=topic.updated_at or datetime.now(timezone.utc),
        correlation_id=correlation_id,
        causation_id=causation_id,
        idempotency_key=idempotency_key,
        state_version=state_version,
    )


def _topic_params(topic: Topic) -> tuple:
    return (
        topic.topic_id,
        topic.conversation_id,
        topic.conversation_scope.value,
        topic.channel.value,
        topic.source_account,
        topic.state.value,
        topic.domain,
        topic.semantic_label,
        topic.related_topic_id,
        json.dumps([str(item) for item in topic.message_ids]),
        json.dumps([str(item) for item in topic.turn_ids]),
        topic.last_activity_at,
        topic.state_version,
        topic.created_at,
        topic.updated_at,
    )


def _topic_from_row(row) -> Topic:
    (
        topic_id, conversation_id, scope, channel, source_account, state,
        domain, semantic_label, related_topic_id, message_ids, turn_ids,
        last_activity_at, state_version, created_at, updated_at,
    ) = row
    return Topic(
        topic_id=UUID(str(topic_id)),
        conversation_id=UUID(str(conversation_id)),
        conversation_scope=ConversationScope(scope),
        channel=Channel(channel),
        source_account=source_account,
        state=TopicState(state),
        domain=domain,
        semantic_label=semantic_label,
        related_topic_id=UUID(str(related_topic_id)) if related_topic_id else None,
        message_ids=tuple(UUID(item) for item in (message_ids or [])),
        turn_ids=tuple(UUID(item) for item in (turn_ids or [])),
        last_activity_at=last_activity_at,
        state_version=state_version,
        created_at=created_at,
        updated_at=updated_at,
    )


def _transition_from_row(row) -> TopicTransition:
    (
        transition_id, topic_id, from_state, to_state, kind, evidence,
        conversation_id, message_ids, turn_ids, actor, source, occurred_at,
        correlation_id, causation_id, idempotency_key, state_version,
    ) = row
    return TopicTransition(
        transition_id=UUID(str(transition_id)),
        topic_id=UUID(str(topic_id)),
        from_state=TopicState(from_state) if from_state else None,
        to_state=TopicState(to_state),
        transition_kind=TopicTransitionKind(kind),
        evidence=tuple(TopicEvidence(item) for item in (evidence or [])),
        conversation_id=UUID(str(conversation_id)),
        message_ids=tuple(UUID(item) for item in (message_ids or [])),
        turn_ids=tuple(UUID(item) for item in (turn_ids or [])),
        actor=actor,
        source=source,
        occurred_at=occurred_at,
        correlation_id=correlation_id,
        causation_id=causation_id,
        idempotency_key=idempotency_key,
        state_version=state_version,
    )
