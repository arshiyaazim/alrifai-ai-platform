"""C3 deterministic multi-message turn aggregation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import NAMESPACE_URL, UUID, uuid5

from .models import ActorType, Direction, MediaReference, Message, MessageContentType
from .ordering import OrderedMessage, OrderingConfidence, OrderingResult, resolve_message_order


class AggregationEvidence(StrEnum):
    SAME_SENDER = "same_sender"
    SAME_THREAD = "same_thread"
    WITHIN_CONFIGURED_WINDOW = "within_configured_window"
    CONTINUATION_FRAGMENT = "continuation_fragment"
    MEDIA_ASSOCIATION = "media_association"
    OUTBOUND_BOUNDARY = "outbound_boundary"
    SENDER_CHANGED = "sender_changed"
    THREAD_CHANGED = "thread_changed"
    TEMPORAL_BOUNDARY = "temporal_boundary"
    EXPLICIT_REPLY_BOUNDARY = "explicit_reply_boundary"
    DIRECTION_BOUNDARY = "direction_boundary"
    SYSTEM_EVENT_IGNORED = "system_event_ignored"
    LATE_ARRIVAL_REEVALUATION = "late_arrival_reevaluation"


class TurnStatus(StrEnum):
    OPEN = "open"
    STABILIZED = "stabilized"
    RE_EVALUATED = "re_evaluated"


@dataclass(frozen=True, slots=True)
class TurnAggregationConfig:
    max_gap: timedelta = timedelta(seconds=60)
    fragment_max_chars: int = 40

    def __post_init__(self) -> None:
        if self.max_gap <= timedelta(0):
            raise ValueError("max_gap must be positive")
        if self.fragment_max_chars < 1:
            raise ValueError("fragment_max_chars must be positive")


@dataclass(frozen=True, slots=True)
class ConversationalTurn:
    turn_id: UUID
    conversation_id: UUID
    sender_key: str
    direction: Direction
    message_ids: tuple[UUID, ...]
    first_source_timestamp: datetime | None
    last_source_timestamp: datetime | None
    ordering_confidence: OrderingConfidence
    aggregation_evidence: tuple[AggregationEvidence, ...]
    boundary_reason: AggregationEvidence | None
    media_refs: tuple[MediaReference, ...]
    correlation_ids: tuple[str, ...]
    status: TurnStatus = TurnStatus.OPEN


@dataclass(frozen=True, slots=True)
class TurnBuildResult:
    ordering: OrderingResult
    turns: tuple[ConversationalTurn, ...]
    replaced_turn_ids: tuple[UUID, ...] = ()


def build_turns(
    messages: tuple[Message, ...] | list[Message],
    *,
    config: TurnAggregationConfig = TurnAggregationConfig(),
    previous_turns: tuple[ConversationalTurn, ...] = (),
) -> TurnBuildResult:
    """Order and group structural evidence; never infer business meaning."""
    ordering = resolve_message_order(messages)
    turns: list[ConversationalTurn] = []
    pending: list[OrderedMessage] = []
    pending_boundary: AggregationEvidence | None = None
    for item in ordering.ordered:
        message = item.message
        if message.direction is Direction.OUTBOUND and message.actor_type is ActorType.SYSTEM:
            # Technical events do not create conversational boundaries.
            continue
        if not pending or _can_join(pending[-1], item, config):
            pending.append(item)
            continue
        turns.append(
            _make_turn(
                pending,
                ordering.confidence,
                config,
                pending_boundary,
            )
        )
        pending_boundary = _boundary_reason(pending[-1].message, item.message, config)
        pending = [item]
    if pending:
        turns.append(_make_turn(pending, ordering.confidence, config, pending_boundary))

    replaced: list[UUID] = []
    if previous_turns:
        previous_sets = {turn.message_ids: turn.turn_id for turn in previous_turns}
        for turn in turns:
            if turn.message_ids not in previous_sets and any(
                set(turn.message_ids).intersection(previous.message_ids)
                for previous in previous_turns
            ):
                replaced.extend(
                    previous.turn_id
                    for previous in previous_turns
                    if set(turn.message_ids).intersection(previous.message_ids)
                )
                turns[turns.index(turn)] = replace(
                    turn,
                    status=TurnStatus.RE_EVALUATED,
                    aggregation_evidence=turn.aggregation_evidence
                    + (AggregationEvidence.LATE_ARRIVAL_REEVALUATION,),
                )
    return TurnBuildResult(ordering, tuple(turns), tuple(dict.fromkeys(replaced)))


def stabilize_turns(
    result: TurnBuildResult,
    *,
    as_of: datetime,
    config: TurnAggregationConfig = TurnAggregationConfig(),
) -> TurnBuildResult:
    """Mark turns stable only after the configured structural window closes."""
    turns = []
    for turn in result.turns:
        last = turn.last_source_timestamp
        if last is not None and as_of - last >= config.max_gap:
            turns.append(replace(turn, status=TurnStatus.STABILIZED))
        else:
            turns.append(turn)
    return replace(result, turns=tuple(turns))


def _can_join(previous: OrderedMessage, current: OrderedMessage, config: TurnAggregationConfig) -> bool:
    left = previous.message
    right = current.message
    if left.conversation_id != right.conversation_id:
        return False
    if left.direction is not Direction.INBOUND or right.direction is not Direction.INBOUND:
        return False
    if _sender_key(left) != _sender_key(right):
        return False
    if right.reply_to_message_id is not None:
        return False
    gap = _message_gap(left, right)
    if gap is not None and gap > config.max_gap:
        return False
    return _has_continuation_evidence(left, right, config)


def _has_continuation_evidence(left: Message, right: Message, config: TurnAggregationConfig) -> bool:
    if left.media_refs or right.media_refs:
        return True
    for message in (left, right):
        if message.content_type is not MessageContentType.TEXT:
            return True
        body = (message.body or "").strip()
        if body and (len(body) <= config.fragment_max_chars or body[-1:] not in ".!?。！？"):
            return True
    return False


def _message_gap(left: Message, right: Message) -> timedelta | None:
    if left.occurred_at is not None and right.occurred_at is not None:
        return right.occurred_at - left.occurred_at
    if left.received_at is not None and right.received_at is not None:
        return right.received_at - left.received_at
    return None


def _sender_key(message: Message) -> str:
    if message.platform_identity:
        platform = ":".join(f"{key}={value}" for key, value in sorted(message.platform_identity.items()))
        return f"platform:{platform}"
    if message.person_id is not None:
        return f"person:{message.person_id}"
    if message.normalized_sender_mobile:
        return f"phone:{message.normalized_sender_mobile}"
    if message.sender:
        return f"sender:{message.sender}"
    return f"message:{message.message_id}"


def _make_turn(
    items: list[OrderedMessage],
    ordering_confidence: OrderingConfidence,
    config: TurnAggregationConfig,
    boundary_reason: AggregationEvidence | None,
) -> ConversationalTurn:
    messages = [item.message for item in items]
    conversation_id = messages[0].conversation_id
    if conversation_id is None:
        raise ValueError("turn requires a canonical conversation")
    ids = tuple(message.message_id for message in messages)
    turn_id = uuid5(NAMESPACE_URL, f"alrifai:c3:{conversation_id}:{','.join(map(str, ids))}")
    evidence = [
        AggregationEvidence.SAME_SENDER,
        AggregationEvidence.SAME_THREAD,
    ]
    if len(messages) > 1:
        evidence.append(AggregationEvidence.WITHIN_CONFIGURED_WINDOW)
        if any(message.media_refs for message in messages):
            evidence.append(AggregationEvidence.MEDIA_ASSOCIATION)
        if any(
            message.body and len(message.body.strip()) <= config.fragment_max_chars
            for message in messages
        ):
            evidence.append(AggregationEvidence.CONTINUATION_FRAGMENT)
    media_refs = tuple(ref for message in messages for ref in message.media_refs)
    correlations = tuple(
        correlation for message in messages if (correlation := message.correlation_id)
    )
    return ConversationalTurn(
        turn_id=turn_id,
        conversation_id=conversation_id,
        sender_key=_sender_key(messages[0]),
        direction=messages[0].direction,
        message_ids=ids,
        first_source_timestamp=messages[0].occurred_at,
        last_source_timestamp=messages[-1].occurred_at,
        ordering_confidence=ordering_confidence,
        aggregation_evidence=tuple(evidence),
        boundary_reason=boundary_reason,
        media_refs=media_refs,
        correlation_ids=correlations,
    )


def _boundary_reason(
    previous: Message | ConversationalTurn,
    current: Message,
    config: TurnAggregationConfig,
) -> AggregationEvidence:
    previous_sender = (
        previous.sender_key
        if isinstance(previous, ConversationalTurn)
        else _sender_key(previous)
    )
    previous_direction = previous.direction
    previous_timestamp = (
        previous.last_source_timestamp
        if isinstance(previous, ConversationalTurn)
        else previous.occurred_at
    )
    message = current
    if previous_sender != _sender_key(message):
        return AggregationEvidence.SENDER_CHANGED
    if message.direction is Direction.OUTBOUND:
        return AggregationEvidence.OUTBOUND_BOUNDARY
    if previous_direction is not message.direction:
        return AggregationEvidence.DIRECTION_BOUNDARY
    if message.reply_to_message_id is not None:
        return AggregationEvidence.EXPLICIT_REPLY_BOUNDARY
    if previous_timestamp is not None and message.occurred_at is not None:
        if message.occurred_at - previous_timestamp > config.max_gap:
            return AggregationEvidence.TEMPORAL_BOUNDARY
    return AggregationEvidence.CONTINUATION_FRAGMENT
