"""Transport-neutral canonical conversation and message contracts.

This module is the C1 contract foundation only. It deliberately does not
resolve identity, aggregate turns, infer topics, dispatch domain actions, or
send messages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Mapping
from uuid import UUID, uuid4


class Channel(StrEnum):
    BRIDGE1 = "bridge1"
    BRIDGE2 = "bridge2"
    BRIDGE3 = "bridge3"
    WHATSAPP = "whatsapp"
    META_WHATSAPP = "meta_whatsapp"
    MESSENGER = "messenger"
    FACEBOOK_COMMENT = "facebook_comment"
    INTERNAL = "internal"


class ConversationScope(StrEnum):
    PRIVATE = "private"
    GROUP = "group"
    PUBLIC = "public"
    INTERNAL = "internal"


class Direction(StrEnum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class ActorType(StrEnum):
    EXTERNAL_USER = "external_user"
    HUMAN_DEVICE = "human_device"
    HUMAN_OPERATOR = "human_operator"
    HERMES_AI = "hermes_ai"
    AUTOMATION = "automation"
    SYSTEM = "system"
    UNKNOWN = "unknown"
    HUMAN = "human_operator"
    AI = "hermes_ai"
    DEVICE = "human_device"


class DeliveryState(StrEnum):
    PREPARED = "prepared"
    APPROVED = "approved"
    QUEUED = "queued"
    ATTEMPTED = "attempted"
    PROVIDER_ACKNOWLEDGED = "provider_acknowledged"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"
    HUMAN_REVIEW = "human_review"
    RECEIVED = "received"


class MessageContentType(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    LOCATION = "location"
    OTHER = "other"


class ProcessingState(StrEnum):
    RECEIVED = "received"
    PERSISTED = "persisted"
    PENDING = "pending"
    FAILED = "failed"
    RETRYABLE_FAILURE = "retryable_failure"


@dataclass(frozen=True, slots=True)
class OrderingEvidence:
    """Raw ordering evidence stored for later-stage interpretation."""

    provider_sequence: str | None = None
    previous_external_id: str | None = None
    next_external_id: str | None = None
    ordering_confidence: float | None = None

    def __post_init__(self) -> None:
        if self.ordering_confidence is not None and not 0 <= self.ordering_confidence <= 1:
            raise ValueError("ordering_confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class MediaReference:
    """Reference to approved media storage; never the binary payload."""

    reference: str
    content_type: MessageContentType
    source: str | None = None
    external_id: str | None = None
    provenance_ref: str | None = None


@dataclass(frozen=True, slots=True)
class DeliveryEvidence:
    """Provider evidence for an outbound delivery attempt."""

    state: DeliveryState
    provider_message_id: str | None = None
    attempted_at: datetime | None = None
    acknowledged_at: datetime | None = None
    delivered_at: datetime | None = None
    failure_code: str | None = None
    attempt: int = 0

    def __post_init__(self) -> None:
        if self.attempt < 0:
            raise ValueError("delivery attempt cannot be negative")


@dataclass(frozen=True, slots=True)
class Provenance:
    """Structured source evidence without hidden model reasoning."""

    source: str
    external_id: str | None = None
    actor: ActorType = ActorType.UNKNOWN
    source_timestamp: datetime | None = None
    ingestion_timestamp: datetime | None = None
    processing_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Conversation:
    """Canonical thread identity shared by all channel adapters."""

    conversation_id: UUID = field(default_factory=uuid4)
    channel: Channel = Channel.INTERNAL
    source_account: str | None = None
    external_thread_id: str | None = None
    scope: ConversationScope = ConversationScope.PRIVATE
    person_id: UUID | None = None
    platform_identity: dict[str, str] | None = None
    processing_state: ProcessingState = ProcessingState.PERSISTED
    message_ids: tuple[UUID, ...] = ()
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Message:
    """Canonical message envelope; transport-specific metadata stays in provenance."""

    message_id: UUID = field(default_factory=uuid4)
    conversation_id: UUID | None = None
    external_message_id: str | None = None
    external_thread_id: str | None = None
    channel: Channel = Channel.INTERNAL
    source_account: str | None = None
    conversation_scope: ConversationScope = ConversationScope.PRIVATE
    direction: Direction = Direction.INBOUND
    sender: str | None = None
    recipient: str | None = None
    person_id: UUID | None = None
    normalized_sender_mobile: str | None = None
    platform_identity: dict[str, str] | None = None
    actor_type: ActorType = ActorType.UNKNOWN
    occurred_at: datetime | None = None
    received_at: datetime | None = None
    ordering: OrderingEvidence = field(default_factory=OrderingEvidence)
    reply_to_message_id: UUID | None = None
    content_type: MessageContentType = MessageContentType.TEXT
    body: str | None = None
    media_refs: tuple[MediaReference, ...] = ()
    delivery_state: DeliveryState | None = None
    delivery_evidence: tuple[DeliveryEvidence, ...] = ()
    processing_state: ProcessingState = ProcessingState.PERSISTED
    idempotency_scope: str | None = None
    idempotency_key: str | None = None
    causation_id: str | None = None
    correlation_id: str | None = None
    provenance: tuple[Provenance, ...] = ()
    extraction_refs: tuple[str, ...] = ()
    domain: str | None = None
    topic: str | None = None

    def __post_init__(self) -> None:
        if self.body is None and self.content_type is MessageContentType.TEXT:
            raise ValueError("text messages require body")
        if self.direction is Direction.INBOUND and self.delivery_state is None:
            object.__setattr__(self, "delivery_state", DeliveryState.RECEIVED)
        if self.idempotency_key is not None and not self.idempotency_scope:
            raise ValueError("idempotency_scope is required with idempotency_key")
        if self.normalized_sender_mobile is not None:
            digits = "".join(character for character in self.normalized_sender_mobile if character.isdigit())
            if len(digits) != 11 or not digits.startswith("0"):
                raise ValueError("normalized_sender_mobile must be the canonical 11-digit form")

    def to_dict(self) -> dict[str, Any]:
        """Serialize contract data without introducing persistence behavior."""
        return _serialize(self)


def _serialize(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (UUID, datetime)):
        return str(value)
    if isinstance(value, tuple):
        return [_serialize(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _serialize(item) for key, item in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return {
            name: _serialize(getattr(value, name))
            for name in value.__dataclass_fields__
        }
    raise TypeError(f"unsupported contract value: {type(value).__name__}")
