"""Contract tests for the canonical Conversations & AI message model."""

from datetime import datetime, timezone
import pytest

from src.alrifai.conversations import (
    ActorType,
    Channel,
    Conversation,
    DeliveryEvidence,
    DeliveryState,
    Direction,
    Message,
    MessageContentType,
    MediaReference,
    OrderingEvidence,
    ProcessingState,
    Provenance,
)


def test_message_preserves_canonical_identity_order_and_provenance():
    conversation = Conversation(channel=Channel.WHATSAPP)
    occurred_at = datetime.now(timezone.utc)
    message = Message(
        conversation_id=conversation.conversation_id,
        channel=conversation.channel,
        direction=Direction.INBOUND,
        actor_type=ActorType.EXTERNAL_USER,
        normalized_sender_mobile="01712345678",
        occurred_at=occurred_at,
        received_at=occurred_at,
        ordering=OrderingEvidence(provider_sequence="7", ordering_confidence=1.0),
        content_type=MessageContentType.TEXT,
        body="চাকরি করতে চাই",
        provenance=(Provenance(source="bridge1", external_id="external-7"),),
        idempotency_scope="whatsapp:bridge1",
        idempotency_key="external-7",
    )

    assert message.conversation_id == conversation.conversation_id
    assert message.occurred_at == occurred_at
    assert message.delivery_state is DeliveryState.RECEIVED
    assert message.ordering.provider_sequence == "7"
    assert message.provenance[0].external_id == "external-7"
    assert message.to_dict()["message_id"] == str(message.message_id)


def test_text_message_requires_body():
    with pytest.raises(ValueError, match="text messages require body"):
        Message(content_type=MessageContentType.TEXT, body=None)


def test_media_message_can_reference_media_without_text():
    message = Message(
        content_type=MessageContentType.DOCUMENT,
        body=None,
        media_refs=(
            MediaReference(
                reference="media://document-1",
                content_type=MessageContentType.DOCUMENT,
                source="bridge1",
            ),
        ),
    )

    assert message.media_refs[0].reference == "media://document-1"
    assert message.message_id


def test_outbound_delivery_and_processing_contracts_preserve_evidence():
    message = Message(
        direction=Direction.OUTBOUND,
        actor_type=ActorType.HERMES_AI,
        body="Your application is under review.",
        delivery_state=DeliveryState.PROVIDER_ACKNOWLEDGED,
        delivery_evidence=(
            DeliveryEvidence(
                state=DeliveryState.PROVIDER_ACKNOWLEDGED,
                provider_message_id="provider-1",
                attempt=1,
            ),
        ),
        processing_state=ProcessingState.PENDING,
    )

    assert message.delivery_evidence[0].provider_message_id == "provider-1"
    assert message.processing_state is ProcessingState.PENDING


@pytest.mark.parametrize("value", ["+8801712345678", "008801712345678", "8801712345678", "01712345678"])
def test_message_accepts_canonical_phone_representations(value):
    # C1 carries the normalized contract value; C2 owns conversion of raw input.
    normalized = "01712345678"
    message = Message(normalized_sender_mobile=normalized, body=value)
    assert message.normalized_sender_mobile == normalized


def test_invalid_contract_values_are_rejected():
    with pytest.raises(ValueError, match="canonical 11-digit"):
        Message(normalized_sender_mobile="+8801712345678", body="text")
    with pytest.raises(ValueError, match="idempotency_scope"):
        Message(idempotency_key="event-1", body="text")
