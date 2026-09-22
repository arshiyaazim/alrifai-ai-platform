"""C6 bounded, authorized conversation context retrieval.

Retrieval composes canonical C1 messages, C3 turns, C4 topics, and C5
instruction selections. It does not persist copies, infer meaning, or mutate
conversation/domain state.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from ..authorization import Capability, TrustedPrincipal, require_capability
from .instructions import (
    InstructionConflictError, InstructionContext, InstructionService, SelectionEvidence,
)
from .models import (
    ActorType, Channel, Conversation, ConversationScope, DeliveryEvidence,
    DeliveryState, Direction, MediaReference, Message, MessageContentType,
    OrderingEvidence, ProcessingState, Provenance,
)
from .ordering import (
    OrderingConfidence as ResolvedOrderingConfidence,
    OrderingEvidence as ResolvedOrderingEvidence,
)
from .resolution import IdentityResolutionResult, IdentityResultStatus
from .topics import Topic, TopicState
from .turns import ConversationalTurn, TurnAggregationConfig, build_turns


class ContextPurpose(StrEnum):
    CURRENT_TURN = "current_turn"
    FOLLOW_UP = "follow_up"
    HISTORICAL_REFERENCE = "historical_reference"
    REPEATED_QUESTION = "repeated_question"


class ContextStatus(StrEnum):
    COMPLETE = "complete"
    INSUFFICIENT = "insufficient_context"
    IDENTITY_RESTRICTED = "identity_restricted"


class ContextContentTrust(StrEnum):
    UNTRUSTED_CONVERSATION_DATA = "untrusted_conversation_data"


class RelationshipStatus(StrEnum):
    UNKNOWN = "unknown"
    CONFIRMED_CURRENT_EMPLOYEE = "confirmed_current_employee"


class ContextReason(StrEnum):
    CURRENT_TURN = "current_turn"
    DIRECT_REPLY = "direct_reply"
    SAME_TOPIC = "same_topic"
    RECENT_TURN = "recent_turn"
    PREVIOUS_ANSWER = "previous_answer_candidate"


class ContextOmissionReason(StrEnum):
    MESSAGE_BUDGET = "message_budget"
    TURN_BUDGET = "turn_budget"
    CONTENT_BUDGET = "content_budget"
    AGE_LIMIT = "age_limit"
    IDENTITY_UNRESOLVED = "identity_unresolved"
    IDENTITY_AMBIGUOUS = "identity_ambiguous"
    INSTRUCTION_CONFLICT = "instruction_conflict"
    TOPIC_SCOPE = "topic_scope_mismatch"
    CLOSED_TOPIC = "closed_topic_not_active"
    NO_RELEVANT_HISTORY = "no_relevant_history"
    TOPIC_EVIDENCE_BUDGET = "topic_evidence_budget"


class ContextAccessError(ValueError):
    """The request or evidence crosses an authorization/privacy boundary."""


@dataclass(frozen=True, slots=True)
class ContextLimits:
    """Server-enforced defaults; callers cannot raise these per request."""

    max_messages: int = 32
    max_turns: int = 12
    max_topics: int = 5
    max_content_chars: int = 12_000
    candidate_pool_size: int = 200
    max_age: timedelta = timedelta(days=90)
    max_reply_depth: int = 5
    max_media_refs_per_message: int = 8

    def __post_init__(self) -> None:
        if min(self.max_messages, self.max_turns, self.max_topics,
               self.max_content_chars, self.candidate_pool_size,
               self.max_reply_depth, self.max_media_refs_per_message) < 1:
            raise ValueError("context limits must be positive")
        if self.candidate_pool_size < self.max_messages or self.max_age <= timedelta(0):
            raise ValueError("candidate pool and age limit are invalid")


@dataclass(frozen=True, slots=True)
class ContextRequest:
    principal: TrustedPrincipal
    conversation_id: UUID
    current_turn: ConversationalTurn
    channel: Channel
    source_account: str
    identity: IdentityResolutionResult
    purpose: ContextPurpose = ContextPurpose.CURRENT_TURN
    topic_id: UUID | None = None
    domain: str | None = None
    at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class ContextMessage:
    message_id: UUID
    turn_id: UUID | None
    direction: Direction
    actor_type: ActorType
    content_type: MessageContentType
    content: str | None
    source_timestamp: datetime | None
    reply_to_message_id: UUID | None
    media_refs: tuple[MediaReference, ...]
    ordering_confidence: ResolvedOrderingConfidence
    resolved_ordering_evidence: tuple[ResolvedOrderingEvidence, ...]
    candidate_arrival_index: int | None
    resolved_index: int | None
    late_arrival: bool | None
    correlation_id: str | None
    provenance_refs: tuple[str, ...]
    content_trust: ContextContentTrust
    reasons: tuple[ContextReason, ...]
    truncated: bool = False


@dataclass(frozen=True, slots=True)
class ContextTurn:
    turn_id: UUID
    message_ids: tuple[UUID, ...]
    first_source_timestamp: datetime | None
    last_source_timestamp: datetime | None
    is_current: bool


@dataclass(frozen=True, slots=True)
class ContextTopic:
    topic_id: UUID
    state: TopicState
    domain: str | None
    semantic_label: str | None
    related_topic_id: UUID | None
    evidence_message_ids: tuple[UUID, ...]
    evidence_turn_ids: tuple[UUID, ...]
    last_activity_at: datetime | None


@dataclass(frozen=True, slots=True)
class ContextInstruction:
    version_id: UUID
    instruction_id: UUID
    version: int
    subject_key: str
    content: str
    issuer_type: str
    effective_from: datetime
    expires_at: datetime | None


@dataclass(frozen=True, slots=True)
class ContextOmission:
    reference_id: UUID | None
    reason: ContextOmissionReason


@dataclass(frozen=True, slots=True)
class ContextPackage:
    status: ContextStatus
    conversation_id: UUID
    current_turn_id: UUID
    scope: ConversationScope
    channel: Channel
    source_account: str
    person_id: UUID | None
    relationship_status: RelationshipStatus
    relationship_evidence: tuple[str, ...]
    messages: tuple[ContextMessage, ...]
    turns: tuple[ContextTurn, ...]
    topics: tuple[ContextTopic, ...]
    instructions: tuple[ContextInstruction, ...]
    instruction_selection_evidence: tuple[SelectionEvidence, ...]
    previous_answer_ids: tuple[UUID, ...]
    ordering_confidence: str
    retrieval_evidence: tuple[str, ...]
    omissions: tuple[ContextOmission, ...]
    content_chars: int
    at: datetime


class ContextSource(Protocol):
    """Read-only access to existing canonical records; no C6 persistence."""

    def get_conversation(self, conversation_id: UUID) -> Conversation | None: ...

    def get_recent_messages(self, conversation_id: UUID, limit: int) -> tuple[Message, ...]: ...

    def get_messages(self, conversation_id: UUID, message_ids: tuple[UUID, ...]) -> tuple[Message, ...]: ...

    def get_topics(self, conversation_id: UUID, limit: int) -> tuple[Topic, ...]: ...


class PostgresContextSource:
    """Read-only adapter over V007/V008 canonical conversation tables."""

    def __init__(self, connection) -> None:
        self.connection = connection

    def get_conversation(self, conversation_id: UUID) -> Conversation | None:
        row = self._one("""SELECT conversation_id, channel, source_account,
            external_thread_id, conversation_scope, person_id, platform_identity,
            processing_state, created_at, updated_at
            FROM conversation_threads WHERE conversation_id=%s""", (conversation_id,))
        if row is None:
            return None
        return Conversation(
            conversation_id=UUID(str(row[0])), channel=Channel(row[1]), source_account=row[2],
            external_thread_id=row[3], scope=ConversationScope(row[4]),
            person_id=UUID(str(row[5])) if row[5] else None,
            platform_identity=_json(row[6]), processing_state=ProcessingState(row[7]),
            created_at=row[8], updated_at=row[9],
        )

    def get_recent_messages(self, conversation_id: UUID, limit: int) -> tuple[Message, ...]:
        rows = self._all(f"""SELECT {_MESSAGE_COLUMNS}, t.conversation_scope
            FROM conversation_messages m JOIN conversation_threads t USING (conversation_id)
            WHERE m.conversation_id=%s ORDER BY m.received_at DESC NULLS LAST,
            m.occurred_at DESC NULLS LAST, m.message_id DESC LIMIT %s""",
            (conversation_id, limit))
        return tuple(_message_from_row(row) for row in rows)

    def get_messages(self, conversation_id: UUID, message_ids: tuple[UUID, ...]) -> tuple[Message, ...]:
        if not message_ids:
            return ()
        rows = self._all(f"""SELECT {_MESSAGE_COLUMNS}, t.conversation_scope
            FROM conversation_messages m JOIN conversation_threads t USING (conversation_id)
            WHERE m.conversation_id=%s AND m.message_id = ANY(%s)""",
            (conversation_id, list(message_ids)))
        return tuple(_message_from_row(row) for row in rows)

    def get_topics(self, conversation_id: UUID, limit: int) -> tuple[Topic, ...]:
        rows = self._all("""SELECT topic_id, conversation_id, conversation_scope, channel,
            source_account, state, domain, semantic_label, related_topic_id,
            evidence_message_ids, evidence_turn_ids, last_activity_at, state_version,
            created_at, updated_at FROM conversation_topics
            WHERE conversation_id=%s ORDER BY last_activity_at DESC NULLS LAST, topic_id LIMIT %s""",
            (conversation_id, limit))
        return tuple(_topic_from_row(row) for row in rows)

    def _one(self, query, params):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            return cursor.fetchone()
        finally:
            cursor.close()

    def _all(self, query, params):
        cursor = self.connection.cursor()
        try:
            cursor.execute(query, params)
            return tuple(cursor.fetchall())
        finally:
            cursor.close()


class ContextRetrievalService:
    def __init__(self, source: ContextSource, instruction_service: InstructionService,
                 *, limits: ContextLimits = ContextLimits(),
                 turn_config: TurnAggregationConfig = TurnAggregationConfig()) -> None:
        self.source = source
        self.instruction_service = instruction_service
        self.limits = limits
        self.turn_config = turn_config

    def retrieve(self, request: ContextRequest) -> ContextPackage:
        require_capability(request.principal, Capability.MANAGE_CONVERSATIONS)
        if request.at.tzinfo is None or request.at.utcoffset() is None:
            raise ContextAccessError("context timestamp must be timezone-aware")
        if request.current_turn.conversation_id != request.conversation_id:
            raise ContextAccessError("turn belongs to another conversation")
        conversation = self.source.get_conversation(request.conversation_id)
        if conversation is None:
            raise ContextAccessError("conversation not found")
        if (conversation.channel != request.channel or
                conversation.source_account != request.source_account):
            raise ContextAccessError("channel/account scope mismatch")
        identity_ok = (
            request.identity.status is IdentityResultStatus.RESOLVED
            and request.identity.resolution.person_id is not None
            and request.identity.resolution.person_id == conversation.person_id
        )
        if conversation.scope is ConversationScope.PRIVATE and (not conversation.person_id or not identity_ok):
            raise ContextAccessError("private history requires matching resolved Person identity")
        if (not request.current_turn.message_ids
                or len(request.current_turn.message_ids) > self.limits.max_messages
                or len(set(request.current_turn.message_ids)) != len(request.current_turn.message_ids)):
            raise ContextAccessError("current turn exceeds the message budget or contains duplicate references")

        # Resolve and validate the requested topic before touching any message evidence.
        topics = self.source.get_topics(request.conversation_id, self.limits.candidate_pool_size + 1)
        if len(topics) > self.limits.candidate_pool_size:
            topics = topics[:self.limits.candidate_pool_size]
            topic_pool_truncated = True
        else:
            topic_pool_truncated = False
        if any(item.conversation_id != conversation.conversation_id
               or item.channel != conversation.channel
               or item.source_account != conversation.source_account
               or item.conversation_scope != conversation.scope for item in topics):
            raise ContextAccessError("topic privacy scope mismatch")
        topic = next((item for item in topics if item.topic_id == request.topic_id), None)
        if request.topic_id is not None and topic is None:
            raise ContextAccessError("topic is not in the authorized conversation scope")

        current_ids = request.current_turn.message_ids
        current = self.source.get_messages(request.conversation_id, current_ids)
        if {m.message_id for m in current} != set(current_ids):
            raise ContextAccessError("current turn references missing or cross-conversation messages")
        current = tuple(sorted(current, key=_arrival_order_key))
        rebuilt_current = build_turns(current, config=self.turn_config).turns
        if (len(rebuilt_current) != 1 or rebuilt_current[0].turn_id != request.current_turn.turn_id
                or rebuilt_current[0].message_ids != request.current_turn.message_ids):
            raise ContextAccessError("current turn is not a canonical C3 turn")
        for message in current:
            _validate_message_scope(message, conversation)
        relationship_status = _relationship_status(request, conversation, current)
        relationship_evidence = (
            ("C2_RESOLVED_PERSON_AND_ACTIVE_EMPLOYEE_RECORD",)
            if relationship_status is RelationshipStatus.CONFIRMED_CURRENT_EMPLOYEE else ()
        )

        omissions: list[ContextOmission] = []
        status = ContextStatus.COMPLETE
        if topic_pool_truncated:
            omissions.append(ContextOmission(None, ContextOmissionReason.TOPIC_EVIDENCE_BUDGET))
            status = ContextStatus.INSUFFICIENT
        pool = self.source.get_recent_messages(request.conversation_id, self.limits.candidate_pool_size)
        if len(pool) > self.limits.candidate_pool_size:
            pool = pool[:self.limits.candidate_pool_size]
        for message in pool:
            _validate_message_scope(message, conversation)
        if not pool or all(m.message_id in current_ids for m in pool):
            omissions.append(ContextOmission(None, ContextOmissionReason.NO_RELEVANT_HISTORY))
            status = ContextStatus.INSUFFICIENT

        historical = request.purpose is ContextPurpose.HISTORICAL_REFERENCE and topic is not None
        active_topics = tuple(t for t in topics if t.state not in (TopicState.CLOSED, TopicState.COMPLETED))
        if historical:
            topic_candidates = (topic,)
        elif topic is not None and topic.state not in (TopicState.CLOSED, TopicState.COMPLETED):
            topic_candidates = (topic,) + tuple(
                item for item in active_topics if item.topic_id != topic.topic_id
            )[:self.limits.max_topics - 1]
        else:
            topic_candidates = active_topics[:self.limits.max_topics]
        for item in topics:
            if (item.state in (TopicState.CLOSED, TopicState.COMPLETED)
                    and not (historical and item is topic)):
                omissions.append(ContextOmission(item.topic_id, ContextOmissionReason.CLOSED_TOPIC))
        candidate_by_id = {m.message_id: m for m in (*pool, *current)}
        direct_ids: set[UUID] = set()
        frontier = {m.reply_to_message_id for m in current if m.reply_to_message_id}
        for _ in range(self.limits.max_reply_depth):
            if not frontier:
                break
            requested = set(frontier)
            missing = requested - candidate_by_id.keys()
            found = (self.source.get_messages(request.conversation_id, tuple(sorted(missing, key=str)))
                     if missing else ())
            direct_ids.update(message.message_id for message in found)
            direct_ids.update(message_id for message_id in requested
                              if message_id in candidate_by_id)
            if not found:
                frontier = set()
                continue
            for message in found:
                candidate_by_id[message.message_id] = message
            frontier = {m.reply_to_message_id for m in found if m.reply_to_message_id}

        topic_message_ids = {mid for item in topic_candidates for mid in item.message_ids}
        topic_turn_ids = {tid for item in topic_candidates for tid in item.turn_ids}
        if topic_message_ids:
            bounded_topic_ids = tuple(sorted(topic_message_ids, key=str))[:self.limits.candidate_pool_size]
            if len(topic_message_ids) > len(bounded_topic_ids):
                omissions.append(ContextOmission(topic.topic_id if topic else None,
                                                 ContextOmissionReason.TOPIC_EVIDENCE_BUDGET))
                status = ContextStatus.INSUFFICIENT
            for message in self.source.get_messages(request.conversation_id, bounded_topic_ids):
                _validate_message_scope(message, conversation)
                candidate_by_id[message.message_id] = message

        active_topic_message_ids = {mid for item in active_topics for mid in item.message_ids}
        closed_only_ids = {mid for item in topics if item.state in (TopicState.CLOSED, TopicState.COMPLETED)
                           for mid in item.message_ids} - active_topic_message_ids
        historical_ids = set(topic.message_ids) if historical and topic else set()
        for message_id in closed_only_ids:
            if message_id not in current_ids and message_id not in historical_ids:
                candidate_by_id.pop(message_id, None)

        age_cutoff = request.at - self.limits.max_age
        aged_recent = {m.message_id for m in pool
                       if _source_time(m) is not None and _source_time(m) < age_cutoff}
        current_set = set(current_ids)
        for mid in aged_recent - current_set - direct_ids - topic_message_ids:
            omissions.append(ContextOmission(mid, ContextOmissionReason.AGE_LIMIT))
            candidate_by_id.pop(mid, None)

        messages = tuple(sorted(candidate_by_id.values(), key=_arrival_order_key))
        prior_messages = tuple(m for m in messages if m.message_id not in current_set)
        prior_built = build_turns(prior_messages, config=self.turn_config) if prior_messages else None
        all_turns = (*(prior_built.turns if prior_built else ()), request.current_turn)
        turn_by_message = {mid: turn for turn in all_turns for mid in turn.message_ids}
        reasons: dict[UUID, set[ContextReason]] = {mid: {ContextReason.CURRENT_TURN} for mid in current_ids}
        for mid in direct_ids:
            reasons.setdefault(mid, set()).add(ContextReason.DIRECT_REPLY)
        for mid in topic_message_ids:
            if mid in candidate_by_id:
                reasons.setdefault(mid, set()).add(ContextReason.SAME_TOPIC)
        for turn in all_turns:
            if set(turn.message_ids) & current_set:
                continue
            if turn.turn_id in topic_turn_ids:
                for mid in turn.message_ids:
                    reasons.setdefault(mid, set()).add(ContextReason.SAME_TOPIC)
            elif any(_source_time(candidate_by_id[mid]) is not None for mid in turn.message_ids):
                for mid in turn.message_ids:
                    reasons.setdefault(mid, set()).add(ContextReason.RECENT_TURN)

        selected_turns: list[ConversationalTurn] = []
        selected_turns.append(request.current_turn)
        priority = {ContextReason.DIRECT_REPLY: 0, ContextReason.SAME_TOPIC: 1, ContextReason.RECENT_TURN: 2}
        other_turns = [t for t in all_turns if t.turn_id != request.current_turn.turn_id]
        other_turns.sort(key=lambda t: (
            min((priority.get(r, 3) for mid in t.message_ids for r in reasons.get(mid, ())), default=3),
            -_timestamp_rank(t.last_source_timestamp), str(t.turn_id)))
        for turn in other_turns:
            if len(selected_turns) >= self.limits.max_turns:
                omissions.append(ContextOmission(turn.turn_id, ContextOmissionReason.TURN_BUDGET))
                status = ContextStatus.INSUFFICIENT
                continue
            selected_turns.append(turn)

        chosen_ids: list[UUID] = []
        selected_turn_ids: set[UUID] = set()
        for turn in selected_turns:
            room = self.limits.max_messages - len(chosen_ids)
            if room <= 0:
                omissions.append(ContextOmission(turn.turn_id, ContextOmissionReason.MESSAGE_BUDGET))
                status = ContextStatus.INSUFFICIENT
                continue
            chosen = turn.message_ids[:room]
            chosen_ids.extend(chosen)
            selected_turn_ids.add(turn.turn_id)
            if len(chosen) < len(turn.message_ids):
                omissions.append(ContextOmission(turn.turn_id, ContextOmissionReason.MESSAGE_BUDGET))
                status = ContextStatus.INSUFFICIENT
        ordered_messages = build_turns(messages, config=self.turn_config).ordering.ordered if messages else ()
        ordered_by_id = {item.message.message_id: item for item in ordered_messages}
        ordered_ids = [item.message.message_id for item in ordered_messages if item.message.message_id in chosen_ids]
        if request.current_turn.ordering_confidence.value == "ambiguous":
            ordering_confidence = "ambiguous"
        else:
            ordering_confidence = (prior_built.ordering.confidence.value
                                   if prior_built else request.current_turn.ordering_confidence.value)
        chosen_set = set(chosen_ids)
        ordered_ids = [mid for mid in ordered_ids if mid in chosen_set]

        previous_answers = tuple(
            mid for mid in ordered_ids
            if candidate_by_id[mid].direction is Direction.OUTBOUND
            and candidate_by_id[mid].actor_type is not ActorType.SYSTEM
            and mid not in current_set
            and (topic is None or mid in topic_message_ids
                 or (turn_by_message.get(mid) and turn_by_message[mid].turn_id in topic_turn_ids))
        )
        for answer_id in previous_answers:
            reasons.setdefault(answer_id, set()).add(ContextReason.PREVIOUS_ANSWER)

        instruction_selection = None
        instruction_selection_evidence: tuple[SelectionEvidence, ...] = ()
        # A closed topic is historical evidence only; do not make its instructions
        # appear current in an ordinary turn context.
        applicable_topic = topic if topic and topic.state not in (TopicState.CLOSED, TopicState.COMPLETED) else None
        try:
            instruction_selection = self.instruction_service.select(InstructionContext(
                at=request.at, domain=request.domain, topic_id=applicable_topic.topic_id if applicable_topic else None,
                topic_state=applicable_topic.state.value if applicable_topic else None,
                conversation_id=conversation.conversation_id,
                channel=conversation.channel.value, source_account=conversation.source_account,
            ))
            instruction_selection_evidence = instruction_selection.evidence
        except InstructionConflictError as exc:
            status = ContextStatus.INSUFFICIENT
            instruction_selection_evidence = exc.evidence
            omissions.extend(ContextOmission(e.version_id, ContextOmissionReason.INSTRUCTION_CONFLICT)
                             for e in exc.evidence if e.included is False)

        selected_instructions = tuple(instruction_selection.selected) if instruction_selection else ()
        instruction_chars = sum(len(v.content) for v in selected_instructions)
        if instruction_chars > self.limits.max_content_chars:
            status = ContextStatus.INSUFFICIENT
            omissions.extend(ContextOmission(v.version_id, ContextOmissionReason.CONTENT_BUDGET)
                             for v in selected_instructions)
            selected_instructions = ()
            instruction_chars = 0
        char_room = max(0, self.limits.max_content_chars - instruction_chars)
        context_messages = []
        # Give current-turn content first claim on the bounded text budget.
        ordered_priority = sorted(ordered_ids, key=lambda mid: (0 if mid in current_set else 1, ordered_ids.index(mid)))
        content_by_id: dict[UUID, tuple[str | None, bool]] = {}
        for mid in ordered_priority:
            source_message = candidate_by_id[mid]
            text = source_message.body
            refs = source_message.media_refs[:self.limits.max_media_refs_per_message]
            if len(source_message.media_refs) > len(refs):
                omissions.append(ContextOmission(mid, ContextOmissionReason.MESSAGE_BUDGET))
            if text is None:
                content_by_id[mid] = (None, False)
                continue
            kept = text[:char_room]
            truncated = len(kept) < len(text)
            char_room -= len(kept)
            content_by_id[mid] = (kept, truncated)
            if truncated:
                status = ContextStatus.INSUFFICIENT
                omissions.append(ContextOmission(mid, ContextOmissionReason.CONTENT_BUDGET))
        for mid in ordered_ids:
            message = candidate_by_id[mid]
            order = ordered_by_id[mid]
            content, truncated = content_by_id[mid]
            turn = turn_by_message.get(mid)
            context_messages.append(ContextMessage(
                message_id=mid, turn_id=turn.turn_id if turn else None,
                direction=message.direction, actor_type=message.actor_type,
                content_type=message.content_type, content=content,
                source_timestamp=message.occurred_at or message.received_at,
                reply_to_message_id=message.reply_to_message_id,
                media_refs=message.media_refs[:self.limits.max_media_refs_per_message],
                ordering_confidence=order.confidence,
                resolved_ordering_evidence=order.evidence,
                candidate_arrival_index=order.arrival_index,
                resolved_index=order.resolved_index,
                late_arrival=order.late_arrival,
                correlation_id=message.correlation_id,
                provenance_refs=tuple(dict.fromkeys(
                    ref for item in message.provenance
                    for ref in ((item.processing_ref,) if item.processing_ref else ()) + item.evidence_refs
                )),
                content_trust=ContextContentTrust.UNTRUSTED_CONVERSATION_DATA,
                reasons=tuple(sorted(reasons.get(mid, ()), key=lambda r: r.value)),
                truncated=truncated,
            ))

        context_topics = tuple(_context_topic(t, chosen_set, selected_turn_ids,
                                              self.limits.max_messages, self.limits.max_turns)
                               for t in topic_candidates)
        context_turns = tuple(sorted((ContextTurn(t.turn_id,
            tuple(mid for mid in t.message_ids if mid in chosen_set),
            t.first_source_timestamp, t.last_source_timestamp,
            bool(set(t.message_ids) & current_set))
            for t in selected_turns if set(t.message_ids) & chosen_set),
            key=lambda item: (_timestamp_rank(item.first_source_timestamp), str(item.turn_id))))
        selected_inst_dtos = tuple(ContextInstruction(
            v.version_id, v.instruction_id, v.version, v.subject_key, v.content,
            v.issuer_type.value, v.effective_from, v.expires_at,
        ) for v in selected_instructions)
        if any(item.confidence.value == "ambiguous" for item in
               ([prior_built.ordering] if prior_built else [])):
            ordering_confidence = "ambiguous"
        evidence = ["CURRENT_TURN", "C3_ORDERING", "C3_TURN_STRUCTURE"]
        if direct_ids:
            evidence.append("DIRECT_REPLY_CHAIN")
        if topic_candidates:
            evidence.append("C4_TOPIC_ASSOCIATION")
        if instruction_selection:
            evidence.append("C5_APPLICABLE_INSTRUCTIONS")
        content_chars = sum(len(item.content or "") for item in context_messages) + sum(
            len(item.content) for item in selected_inst_dtos)
        return ContextPackage(
            status=status, conversation_id=conversation.conversation_id,
            current_turn_id=request.current_turn.turn_id, scope=conversation.scope,
            channel=conversation.channel, source_account=conversation.source_account or "",
            person_id=conversation.person_id, relationship_status=relationship_status,
            relationship_evidence=relationship_evidence, messages=tuple(context_messages),
            turns=context_turns, topics=context_topics, instructions=selected_inst_dtos,
            instruction_selection_evidence=instruction_selection_evidence,
            previous_answer_ids=previous_answers, ordering_confidence=ordering_confidence,
            retrieval_evidence=tuple(evidence), omissions=tuple(omissions),
            content_chars=content_chars, at=request.at,
        )


_MESSAGE_COLUMNS = """m.message_id, m.conversation_id, m.external_message_id, m.channel,
m.source_account, m.direction, m.sender, m.recipient, m.person_id, m.normalized_sender_mobile,
m.platform_identity, m.actor_type, m.occurred_at, m.received_at, m.provider_sequence,
m.previous_external_id, m.next_external_id, m.ordering_confidence, m.reply_to_message_id,
m.content_type, m.body, m.media_refs, m.delivery_state, m.delivery_evidence, m.processing_state,
m.idempotency_scope, m.idempotency_key, m.causation_id, m.correlation_id, m.provenance,
m.extraction_refs, m.domain, m.topic"""


def _json(value):
    return json.loads(value) if isinstance(value, str) else value


def _message_from_row(row) -> Message:
    (message_id, conversation_id, external_id, channel, account, direction, sender,
     recipient, person_id, phone, platform_identity, actor, occurred_at, received_at,
     sequence, previous_id, next_id, confidence, reply_id, content_type, body,
     media, delivery_state, delivery, processing, idempotency_scope, idempotency_key,
     causation_id, correlation_id, provenance, extraction_refs, domain, topic,
     conversation_scope) = row
    media = _json(media) or []
    delivery = _json(delivery) or []
    provenance = _json(provenance) or []
    return Message(
        message_id=UUID(str(message_id)), conversation_id=UUID(str(conversation_id)),
        external_message_id=external_id, channel=Channel(channel), source_account=account,
        conversation_scope=ConversationScope(conversation_scope),
        direction=Direction(direction), sender=sender, recipient=recipient,
        person_id=UUID(str(person_id)) if person_id else None, normalized_sender_mobile=phone,
        platform_identity=_json(platform_identity), actor_type=ActorType(actor),
        occurred_at=occurred_at, received_at=received_at,
        ordering=OrderingEvidence(sequence, previous_id, next_id, float(confidence) if confidence is not None else None),
        reply_to_message_id=UUID(str(reply_id)) if reply_id else None,
        content_type=MessageContentType(content_type), body=body,
        media_refs=tuple(MediaReference(item["reference"], MessageContentType(item["content_type"]),
            item.get("source"), item.get("external_id"), item.get("provenance_ref")) for item in media),
        delivery_state=DeliveryState(delivery_state) if delivery_state else None,
        delivery_evidence=tuple(DeliveryEvidence(DeliveryState(item["state"]),
            item.get("provider_message_id"), item.get("attempted_at"), item.get("acknowledged_at"),
            item.get("delivered_at"), item.get("failure_code"), item.get("attempt", 0)) for item in delivery),
        processing_state=ProcessingState(processing), idempotency_scope=idempotency_scope,
        idempotency_key=idempotency_key, causation_id=causation_id, correlation_id=correlation_id,
        provenance=tuple(Provenance(item["source"], item.get("external_id"),
            ActorType(item.get("actor", "unknown")), item.get("source_timestamp"),
            item.get("ingestion_timestamp"), item.get("processing_ref"),
            tuple(item.get("evidence_refs", ()))) for item in provenance),
        extraction_refs=tuple(_json(extraction_refs) or ()), domain=domain, topic=topic,
    )


def _topic_from_row(row) -> Topic:
    (topic_id, conversation_id, scope, channel, source_account, state, domain,
     label, related, message_ids, turn_ids, activity, version, created, updated) = row
    return Topic(UUID(str(topic_id)), UUID(str(conversation_id)), ConversationScope(scope),
        Channel(channel), source_account, TopicState(state), domain, label,
        UUID(str(related)) if related else None,
        tuple(UUID(str(item)) for item in (_json(message_ids) or ())),
        tuple(UUID(str(item)) for item in (_json(turn_ids) or ())),
        activity, version, created, updated)


def _context_topic(topic: Topic, selected_message_ids: set[UUID], selected_turn_ids: set[UUID],
                   max_messages: int, max_turns: int) -> ContextTopic:
    return ContextTopic(topic.topic_id, topic.state, topic.domain, topic.semantic_label,
        topic.related_topic_id,
        tuple(mid for mid in topic.message_ids if mid in selected_message_ids)[:max_messages],
        tuple(tid for tid in topic.turn_ids if tid in selected_turn_ids)[:max_turns],
        topic.last_activity_at)


def _relationship_status(request: ContextRequest, conversation: Conversation,
                         current_messages: tuple[Message, ...]) -> RelationshipStatus:
    resolution = request.identity.resolution
    person_id = resolution.person_id
    if (request.identity.status is not IdentityResultStatus.RESOLVED
            or person_id is None or resolution.employee_id is None):
        return RelationshipStatus.UNKNOWN

    if conversation.scope is ConversationScope.PRIVATE:
        if conversation.person_id != person_id:
            return RelationshipStatus.UNKNOWN
    elif not any(message.direction is Direction.INBOUND and message.person_id == person_id
                 for message in current_messages):
        return RelationshipStatus.UNKNOWN

    matches = [candidate for candidate in resolution.candidates
               if candidate.person_id == person_id
               and candidate.employee_id == resolution.employee_id
               and candidate.employee_status == "active"]
    return (RelationshipStatus.CONFIRMED_CURRENT_EMPLOYEE
            if len(matches) == 1 else RelationshipStatus.UNKNOWN)


def _arrival_order_key(message: Message) -> tuple[tuple[int, str], tuple[int, str], str]:
    def sort_time(value: datetime | None) -> tuple[int, str]:
        if value is None:
            return (2, "")
        if value.tzinfo is None or value.utcoffset() is None:
            return (1, value.isoformat())
        return (0, value.astimezone(timezone.utc).isoformat())

    return sort_time(message.received_at), sort_time(message.occurred_at), str(message.message_id)


def _source_time(message: Message) -> datetime | None:
    return message.occurred_at or message.received_at


def _validate_message_scope(message: Message, conversation: Conversation) -> None:
    if (message.conversation_id != conversation.conversation_id
            or message.channel != conversation.channel
            or message.source_account != conversation.source_account
            or message.conversation_scope != conversation.scope):
        raise ContextAccessError("message privacy scope mismatch")
    if (conversation.scope is ConversationScope.PRIVATE and conversation.person_id
            and message.person_id not in (None, conversation.person_id)):
        raise ContextAccessError("message Person conflicts with private conversation")


def _timestamp_rank(value: datetime | None) -> float:
    return value.timestamp() if value else float("-inf")
