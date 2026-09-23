"""C3 deterministic message ordering over preserved C1 evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Sequence
from uuid import UUID

from .models import Message


class OrderingConfidence(StrEnum):
    EXACT_PROVIDER = "exact_provider"
    HIGH = "high"
    INFERRED = "inferred"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"


class OrderingEvidence(StrEnum):
    PROVIDER_SEQUENCE = "provider_sequence"
    SOURCE_TIMESTAMP = "source_timestamp"
    INGESTION_TIMESTAMP = "ingestion_timestamp"
    ARRIVAL_ORDER = "arrival_order"
    MESSAGE_ID_FALLBACK = "message_id_fallback"
    REPLY_RELATIONSHIP_PRESERVED = "reply_relationship_preserved"
    CONFLICTING_PROVIDER_EVIDENCE = "conflicting_provider_evidence"


@dataclass(frozen=True, slots=True)
class OrderedMessage:
    message: Message
    arrival_index: int
    resolved_index: int
    late_arrival: bool
    confidence: OrderingConfidence
    evidence: tuple[OrderingEvidence, ...]


@dataclass(frozen=True, slots=True)
class OrderingResult:
    ordered: tuple[OrderedMessage, ...]
    conversation_id: UUID | None
    confidence: OrderingConfidence


def resolve_message_order(messages: Sequence[Message]) -> OrderingResult:
    """Resolve order without changing source timestamps or message objects.

    Provider sequence is preferred only when complete and unique. Otherwise
    source time, ingestion time, and original arrival order are used in that
    order. The original input position is retained as late-arrival evidence.
    """
    if not messages:
        return OrderingResult((), None, OrderingConfidence.UNKNOWN)
    conversation_ids = {message.conversation_id for message in messages}
    if len(conversation_ids) != 1 or None in conversation_ids:
        raise ValueError("ordering requires messages from one canonical conversation")

    provider_values = [message.ordering.provider_sequence for message in messages]
    complete_provider = all(value is not None for value in provider_values)
    unique_provider = len(set(provider_values)) == len(provider_values)
    if complete_provider and unique_provider:
        ordered_indices = sorted(
            range(len(messages)),
            key=lambda index: _provider_key(provider_values[index], index),
        )
        confidence = (
            OrderingConfidence.EXACT_PROVIDER
            if all(
                message.ordering.ordering_confidence in (None, 1, 1.0)
                for message in messages
            )
            else OrderingConfidence.HIGH
        )
        base_evidence = (OrderingEvidence.PROVIDER_SEQUENCE,)
    else:
        source_complete = all(message.occurred_at is not None for message in messages)
        received_complete = all(message.received_at is not None for message in messages)
        if source_complete:
            source_values = [message.occurred_at for message in messages]
            source_unique = len(set(source_values)) == len(source_values)
            ordered_indices = sorted(
                range(len(messages)),
                key=lambda index: (
                    messages[index].occurred_at,
                    index,
                    str(messages[index].message_id),
                ),
            )
            provider_conflict = any(value is not None for value in provider_values) and not unique_provider
            confidence = (
                OrderingConfidence.AMBIGUOUS
                if provider_conflict or not source_unique
                else OrderingConfidence.HIGH
            )
            base_evidence = (OrderingEvidence.SOURCE_TIMESTAMP,)
            if not source_unique:
                base_evidence += (OrderingEvidence.ARRIVAL_ORDER,)
        elif received_complete:
            ordered_indices = sorted(
                range(len(messages)),
                key=lambda index: (
                    messages[index].received_at,
                    index,
                    str(messages[index].message_id),
                ),
            )
            confidence = OrderingConfidence.INFERRED
            base_evidence = (OrderingEvidence.INGESTION_TIMESTAMP,)
        else:
            ordered_indices = sorted(
                range(len(messages)),
                key=lambda index: (index, str(messages[index].message_id)),
            )
            confidence = OrderingConfidence.UNKNOWN
            base_evidence = (
                OrderingEvidence.ARRIVAL_ORDER,
                OrderingEvidence.MESSAGE_ID_FALLBACK,
            )
        if complete_provider and not unique_provider:
            base_evidence += (OrderingEvidence.CONFLICTING_PROVIDER_EVIDENCE,)

    ordered: list[OrderedMessage] = []
    for resolved_index, arrival_index in enumerate(ordered_indices):
        message = messages[arrival_index]
        evidence = list(base_evidence)
        if message.reply_to_message_id is not None:
            evidence.append(OrderingEvidence.REPLY_RELATIONSHIP_PRESERVED)
        ordered.append(
            OrderedMessage(
                message=message,
                arrival_index=arrival_index,
                resolved_index=resolved_index,
                late_arrival=arrival_index != resolved_index,
                confidence=confidence,
                evidence=tuple(evidence),
            )
        )
    return OrderingResult(tuple(ordered), next(iter(conversation_ids)), confidence)


def _provider_key(value: str | None, arrival_index: int) -> tuple[int, object, int]:
    if value is None:
        return (1, "", arrival_index)
    try:
        return (0, int(value), arrival_index)
    except ValueError:
        return (0, value, arrival_index)
