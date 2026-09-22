"""C2 deterministic identity and conversation/thread resolution.

This module establishes boundaries only. It does not infer topics, aggregate
turns, retrieve semantic context, call Hermes, or dispatch domain actions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from ..identity.identity_resolver import (
    DbConnection,
    IdentityObservation,
    IdentityRepository,
    IdentityResolution,
    resolve_identity,
)
from .models import Channel, Conversation, ConversationScope, Message, ProcessingState


class IdentityResultStatus(StrEnum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"
    INVALID_IDENTITY_EVIDENCE = "invalid_identity_evidence"
    CONFLICT = "conflict"


class ConversationResultStatus(StrEnum):
    EXISTING = "existing"
    NEW = "new"
    UNRESOLVED = "unresolved"
    AMBIGUOUS = "ambiguous"
    INVALID_IDENTITY_EVIDENCE = "invalid_identity_evidence"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True)
class ConversationKey:
    """Transport/thread scope used for deterministic lookup."""

    channel: Channel
    source_account: str
    external_thread_id: str
    scope: ConversationScope


@dataclass(frozen=True, slots=True)
class IdentityResolutionResult:
    status: IdentityResultStatus
    resolution: IdentityResolution
    reason: str


@dataclass(frozen=True, slots=True)
class ConversationResolutionResult:
    status: ConversationResultStatus
    conversation: Conversation | None
    identity: IdentityResolutionResult
    key: ConversationKey | None = None
    reason: str = ""


class ConversationStore(Protocol):
    def find(self, key: ConversationKey) -> Conversation | None: ...

    def create(self, conversation: Conversation) -> Conversation: ...


class InMemoryConversationStore:
    """Small deterministic C2 store for contract tests and local adapters."""

    def __init__(self) -> None:
        self._conversations: dict[ConversationKey, Conversation] = {}

    def find(self, key: ConversationKey) -> Conversation | None:
        return self._conversations.get(key)

    def create(self, conversation: Conversation) -> Conversation:
        key = _key_for_conversation(conversation)
        existing = self._conversations.get(key)
        if existing is not None:
            return existing
        self._conversations[key] = conversation
        return conversation


class PostgresConversationStore:
    """Minimal C2 adapter for the canonical local conversation tables."""

    def __init__(self, connection: DbConnection) -> None:
        self.connection = connection

    def find(self, key: ConversationKey) -> Conversation | None:
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """
                SELECT conversation_id, channel, source_account,
                       external_thread_id, conversation_scope, person_id,
                       platform_identity, processing_state,
                       created_at, updated_at
                FROM conversation_threads
                WHERE channel = %s
                  AND source_account = %s
                  AND external_thread_id = %s
                  AND conversation_scope = %s
                """,
                (key.channel.value, key.source_account, key.external_thread_id, key.scope.value),
            )
            row = cursor.fetchone()
            return _conversation_from_row(row) if row else None
        finally:
            cursor.close()

    def create(self, conversation: Conversation) -> Conversation:
        key = _key_for_conversation(conversation)
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO conversation_threads (
                    conversation_id, channel, source_account,
                    external_thread_id, conversation_scope, person_id,
                    platform_identity, processing_state, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, COALESCE(%s, NOW()), COALESCE(%s, NOW()))
                ON CONFLICT (channel, source_account, external_thread_id, conversation_scope)
                DO UPDATE SET updated_at = conversation_threads.updated_at
                RETURNING conversation_id, channel, source_account,
                          external_thread_id, conversation_scope, person_id,
                          platform_identity, processing_state,
                          created_at, updated_at
                """,
                (
                    conversation.conversation_id,
                    key.channel.value,
                    key.source_account,
                    key.external_thread_id,
                    key.scope.value,
                    conversation.person_id,
                    json.dumps(conversation.platform_identity),
                    conversation.processing_state.value,
                    conversation.created_at,
                    conversation.updated_at,
                ),
            )
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError("conversation insert returned no row")
            result = _conversation_from_row(row)
            self.connection.commit()
            return result
        except Exception:
            self.connection.rollback()
            raise
        finally:
            cursor.close()


def resolve_conversation(
    message: Message,
    observation: IdentityObservation,
    identity_repository: IdentityRepository,
    conversation_store: ConversationStore,
) -> ConversationResolutionResult:
    """Resolve identity and thread scope without creating a Person or domain record."""
    if observation.platform and observation.platform_account is None and message.source_account:
        observation = replace(observation, platform_account=message.source_account)
    identity = _resolve_identity(observation, identity_repository)
    if identity.status is IdentityResultStatus.INVALID_IDENTITY_EVIDENCE:
        return ConversationResolutionResult(
            ConversationResultStatus.INVALID_IDENTITY_EVIDENCE,
            None,
            identity,
            reason=identity.reason,
        )
    if identity.status is IdentityResultStatus.AMBIGUOUS:
        return ConversationResolutionResult(
            ConversationResultStatus.AMBIGUOUS,
            None,
            identity,
            reason=identity.reason,
        )

    key = _conversation_key(message, identity.resolution.normalized_phone)
    if key is None:
        return ConversationResolutionResult(
            ConversationResultStatus.UNRESOLVED,
            None,
            identity,
            reason="conversation requires a scoped external thread or deterministic sender identity",
        )

    existing = conversation_store.find(key)
    resolved_person_id = identity.resolution.person_id
    if existing is not None:
        if (
            key.scope is ConversationScope.PRIVATE
            and existing.person_id is not None
            and resolved_person_id is not None
            and existing.person_id != resolved_person_id
        ):
            return ConversationResolutionResult(
                ConversationResultStatus.CONFLICT,
                None,
                identity,
                key,
                "private conversation is linked to a different Person",
            )
        return ConversationResolutionResult(
            ConversationResultStatus.EXISTING,
            existing,
            identity,
            key,
        )

    conversation = Conversation(
        channel=key.channel,
        source_account=key.source_account,
        external_thread_id=key.external_thread_id,
        scope=key.scope,
        # Group/public threads remain unlinked to a single Person. The
        # message-level identity remains available to later authorized stages.
        person_id=resolved_person_id if key.scope is ConversationScope.PRIVATE else None,
        platform_identity=message.platform_identity,
    )
    created = conversation_store.create(conversation)
    status = (
        ConversationResultStatus.NEW
        if identity.status is IdentityResultStatus.RESOLVED
        else ConversationResultStatus.UNRESOLVED
    )
    return ConversationResolutionResult(status, created, identity, key)


def _resolve_identity(
    observation: IdentityObservation,
    repository: IdentityRepository,
) -> IdentityResolutionResult:
    resolution = resolve_identity(repository, observation)
    if resolution.status == "invalid":
        status = IdentityResultStatus.INVALID_IDENTITY_EVIDENCE
    elif resolution.status == "ambiguous":
        status = IdentityResultStatus.AMBIGUOUS
    elif resolution.status == "matched":
        status = IdentityResultStatus.RESOLVED
    else:
        status = IdentityResultStatus.UNRESOLVED
    return IdentityResolutionResult(status, resolution, resolution.reason)


def _conversation_key(
    message: Message,
    normalized_phone: str | None,
) -> ConversationKey | None:
    source_account = message.source_account or "default"
    external_thread_id = message.external_thread_id
    if external_thread_id is None and message.conversation_scope is ConversationScope.PRIVATE:
        platform_id = (message.platform_identity or {}).get("external_id")
        external_thread_id = platform_id or normalized_phone
    if not external_thread_id:
        return None
    return ConversationKey(
        channel=message.channel,
        source_account=source_account,
        external_thread_id=external_thread_id,
        scope=message.conversation_scope,
    )


def _key_for_conversation(conversation: Conversation) -> ConversationKey:
    if not conversation.external_thread_id:
        raise ValueError("conversation requires external_thread_id")
    return ConversationKey(
        channel=conversation.channel,
        source_account=conversation.source_account or "default",
        external_thread_id=conversation.external_thread_id,
        scope=conversation.scope,
    )


def _conversation_from_row(row) -> Conversation:
    (
        conversation_id,
        channel,
        source_account,
        external_thread_id,
        scope,
        person_id,
        platform_identity,
        processing_state,
        created_at,
        updated_at,
    ) = row
    return Conversation(
        conversation_id=UUID(str(conversation_id)),
        channel=Channel(channel),
        source_account=source_account,
        external_thread_id=external_thread_id,
        scope=ConversationScope(scope),
        person_id=UUID(str(person_id)) if person_id is not None else None,
        platform_identity=platform_identity,
        processing_state=ProcessingState(processing_state),
        created_at=created_at,
        updated_at=updated_at,
    )
