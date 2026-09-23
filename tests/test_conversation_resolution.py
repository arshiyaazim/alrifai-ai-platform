"""Focused C2 identity and conversation-resolution tests."""

from uuid import uuid4

import pytest

from src.alrifai.conversations import (
    Channel,
    ConversationScope,
    ConversationResultStatus,
    IdentityResultStatus,
    InMemoryConversationStore,
    Message,
    resolve_conversation,
)
from src.alrifai.identity.identity_resolver import IdentityCandidate, IdentityObservation


PERSON = uuid4()
EMPLOYEE = uuid4()


class FakeIdentityRepository:
    def __init__(self):
        self.phones = {}
        self.platforms = {}

    def find_by_normalized_phone(self, normalized_phone):
        return self.phones.get(normalized_phone, ())

    def find_by_identifier(self, identifier_type, value):
        return ()

    def find_by_platform_id(self, platform, platform_user_id, source_account=None):
        return self.platforms.get((platform, source_account or "default", platform_user_id), ())


def message(*, external_thread_id=None, scope=ConversationScope.PRIVATE, platform=None):
    return Message(
        channel=Channel.BRIDGE1,
        source_account="account-a",
        external_thread_id=external_thread_id,
        conversation_scope=scope,
        platform_identity=platform,
        body="hello",
    )


def test_known_phone_creates_then_reuses_private_conversation():
    repository = FakeIdentityRepository()
    repository.phones["01712345678"] = (IdentityCandidate(PERSON, EMPLOYEE, "active"),)
    store = InMemoryConversationStore()

    first = resolve_conversation(
        message(),
        IdentityObservation(phone="+8801712345678"),
        repository,
        store,
    )
    second = resolve_conversation(
        message(),
        IdentityObservation(phone="008801712345678"),
        repository,
        store,
    )

    assert first.status is ConversationResultStatus.NEW
    assert first.identity.status is IdentityResultStatus.RESOLVED
    assert first.conversation.person_id == PERSON
    assert second.status is ConversationResultStatus.EXISTING
    assert second.conversation.conversation_id == first.conversation.conversation_id


def test_unknown_phone_creates_unresolved_thread_without_person_creation():
    result = resolve_conversation(
        message(),
        IdentityObservation(phone="01799999999"),
        FakeIdentityRepository(),
        InMemoryConversationStore(),
    )

    assert result.status is ConversationResultStatus.UNRESOLVED
    assert result.identity.status is IdentityResultStatus.UNRESOLVED
    assert result.conversation.person_id is None


def test_ambiguous_phone_fails_closed_without_thread_creation():
    repository = FakeIdentityRepository()
    repository.phones["01712345678"] = (
        IdentityCandidate(PERSON, EMPLOYEE, "active"),
        IdentityCandidate(uuid4(), None, None),
    )
    store = InMemoryConversationStore()

    result = resolve_conversation(
        message(),
        IdentityObservation(phone="01712345678"),
        repository,
        store,
    )

    assert result.status is ConversationResultStatus.AMBIGUOUS
    assert result.conversation is None


def test_group_thread_never_gets_single_person_link():
    repository = FakeIdentityRepository()
    repository.phones["01712345678"] = (IdentityCandidate(PERSON, EMPLOYEE, "active"),)

    result = resolve_conversation(
        message(external_thread_id="group-1", scope=ConversationScope.GROUP),
        IdentityObservation(phone="01712345678"),
        repository,
        InMemoryConversationStore(),
    )

    assert result.status is ConversationResultStatus.NEW
    assert result.conversation.scope is ConversationScope.GROUP
    assert result.conversation.person_id is None
    assert result.identity.resolution.person_id == PERSON


def test_same_opaque_platform_id_is_scoped_by_platform_and_account():
    repository = FakeIdentityRepository()
    repository.platforms[("WHATSAPP", "account-a", "opaque-1")] = (
        IdentityCandidate(PERSON, EMPLOYEE, "active"),
    )
    first = resolve_conversation(
        message(platform={"platform": "WHATSAPP", "external_id": "opaque-1"}),
        IdentityObservation(
            platform="WHATSAPP",
            platform_account="account-a",
            platform_user_id="opaque-1",
        ),
        repository,
        InMemoryConversationStore(),
    )
    second = resolve_conversation(
        Message(
            channel=Channel.META_WHATSAPP,
            source_account="account-b",
            external_thread_id="thread-b",
            platform_identity={"platform": "WHATSAPP", "external_id": "opaque-1"},
            body="hello",
        ),
        IdentityObservation(
            platform="WHATSAPP",
            platform_account="account-b",
            platform_user_id="opaque-1",
        ),
        repository,
        InMemoryConversationStore(),
    )

    assert first.identity.status is IdentityResultStatus.RESOLVED
    assert second.identity.status is IdentityResultStatus.UNRESOLVED
    assert first.conversation.conversation_id != second.conversation.conversation_id


def test_private_thread_without_scoped_identity_is_unresolved():
    result = resolve_conversation(
        message(external_thread_id=None),
        IdentityObservation(),
        FakeIdentityRepository(),
        InMemoryConversationStore(),
    )

    assert result.status is ConversationResultStatus.UNRESOLVED
    assert result.conversation is None


def test_identity_result_does_not_authorize_employee_mutation():
    repository = FakeIdentityRepository()
    repository.phones["01712345678"] = (IdentityCandidate(PERSON, EMPLOYEE, "active"),)
    result = resolve_conversation(
        message(),
        IdentityObservation(phone="01712345678"),
        repository,
        InMemoryConversationStore(),
    )

    assert result.identity.resolution.employee_id == EMPLOYEE
    assert not hasattr(result, "employee_id_edit")
