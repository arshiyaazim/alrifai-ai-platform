"""Small DB-API helpers shared by core services."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from typing import TypeVar
from uuid import UUID

from ..identity.identity_resolver import DbConnection, IdentityObservation

T = TypeVar("T")


def in_transaction(connection: DbConnection, operation: Callable[[], T]) -> T:
    try:
        result = operation()
        connection.commit()
        return result
    except Exception:
        connection.rollback()
        raise


def one(connection: DbConnection, sql: str, parameters: Sequence[object] = ()):
    cursor = connection.cursor()
    try:
        cursor.execute(sql, parameters)
        return cursor.fetchone()
    finally:
        cursor.close()


def all_rows(connection: DbConnection, sql: str, parameters: Sequence[object] = ()):
    cursor = connection.cursor()
    try:
        cursor.execute(sql, parameters)
        return tuple(cursor.fetchall())
    finally:
        cursor.close()


def idempotent_aggregate(connection: DbConnection, key: str | None) -> UUID | None:
    if key is None:
        return None
    one(connection, "SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (key,))
    row = one(
        connection,
        """
        SELECT aggregate_id
        FROM business_events
        WHERE idempotency_key = %s
        ORDER BY occurred_at
        LIMIT 1
        """,
        (key,),
    )
    return UUID(str(row[0])) if row else None


def write_audit(
    connection: DbConnection,
    *,
    entity_type: str,
    entity_id: UUID,
    action: str,
    actor_id: UUID | None,
    before: dict | None,
    after: dict | None,
    correlation_id: str | None,
) -> None:
    one(
        connection,
        """
        INSERT INTO audit_log (
            entity_type, entity_id, action, actor_id,
            before_state, after_state, correlation_id
        )
        VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s)
        RETURNING audit_id
        """,
        (
            entity_type,
            entity_id,
            action,
            actor_id,
            json.dumps(before) if before is not None else None,
            json.dumps(after) if after is not None else None,
            correlation_id,
        ),
    )


def write_event(
    connection: DbConnection,
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: UUID,
    actor_id: UUID | None,
    payload: dict,
    source_system: str,
    idempotency_key: str | None,
) -> None:
    one(
        connection,
        """
        INSERT INTO business_events (
            event_type, aggregate_type, aggregate_id, actor_id,
            payload, idempotency_key, source_system
        )
        VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s)
        RETURNING event_id
        """,
        (
            event_type,
            aggregate_type,
            aggregate_id,
            actor_id,
            json.dumps(payload),
            idempotency_key,
            source_system,
        ),
    )


def create_person(
    connection: DbConnection,
    *,
    person_type: str,
    observation: IdentityObservation,
    normalized_phone: str | None,
    source_system: str,
) -> UUID:
    row = one(
        connection,
        """
        INSERT INTO persons (person_type, phone_normalized)
        VALUES (%s, %s)
        RETURNING person_id
        """,
        (person_type, normalized_phone),
    )
    person_id = UUID(str(row[0]))
    if observation.name:
        one(
            connection,
            """
            INSERT INTO person_aliases (person_id, alias_value, alias_type, source_system)
            VALUES (%s, %s, 'NAME', %s)
            RETURNING alias_id
            """,
            (person_id, observation.name, source_system),
        )
    if observation.phone is not None and normalized_phone is not None:
        one(
            connection,
            """
            INSERT INTO person_phones (
                person_id, raw_value, normalized_value, source_system
            )
            VALUES (%s, %s, %s, %s)
            RETURNING phone_id
            """,
            (person_id, observation.phone, normalized_phone, source_system),
        )
    if observation.platform and observation.platform_user_id:
        one(
            connection,
            """
            INSERT INTO external_platform_ids (
                person_id, platform, platform_user_id, source_system
            )
            VALUES (%s, %s, %s, %s)
            RETURNING ext_id
            """,
            (person_id, observation.platform, observation.platform_user_id, source_system),
        )
    return person_id
