"""C2 PostgreSQL tests for the isolated canonical conversation foundation."""

from __future__ import annotations

import os

import pytest

psycopg = pytest.importorskip("psycopg")

from src.alrifai.conversations import (  # noqa: E402
    Channel,
    ConversationResultStatus,
    Message,
    PostgresConversationStore,
    resolve_conversation,
)
from src.alrifai.identity.identity_resolver import (  # noqa: E402
    IdentityObservation,
    PostgresIdentityRepository,
)


pytestmark = pytest.mark.skipif(
    os.getenv("ALRIFAI_TEST_DATABASE_URL") is None
    or os.getenv("ALRIFAI_TEST_DATABASE_ISOLATED") != "1",
    reason="isolated local PostgreSQL test database is not configured",
)


@pytest.fixture
def database_url() -> str:
    return os.environ["ALRIFAI_TEST_DATABASE_URL"]


def test_postgres_conversation_thread_is_idempotently_reused(database_url: str):
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('conversation_threads')")
            if cursor.fetchone()[0] is None:
                pytest.skip("V007 conversation foundation is not applied")
            cursor.execute(
                """
                INSERT INTO persons (person_type, phone_normalized)
                VALUES ('APPLICANT', '01712345678')
                RETURNING person_id
                """
            )
            person_id = cursor.fetchone()[0]
            cursor.execute(
                """
                INSERT INTO person_phones (person_id, raw_value, normalized_value, source_system)
                VALUES (%s, '+8801712345678', '01712345678', 'c2-integration')
                """,
                (person_id,),
            )
            connection.commit()

        store = PostgresConversationStore(connection)
        repository = PostgresIdentityRepository(connection)
        inbound = Message(
            channel=Channel.BRIDGE1,
            source_account="c2-account",
            body="hello",
        )
        first = resolve_conversation(
            inbound,
            IdentityObservation(phone="+8801712345678"),
            repository,
            store,
        )
        second = resolve_conversation(
            inbound,
            IdentityObservation(phone="008801712345678"),
            repository,
            store,
        )

        assert first.status is ConversationResultStatus.NEW
        assert second.status is ConversationResultStatus.EXISTING
        assert second.conversation.conversation_id == first.conversation.conversation_id

        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM conversation_threads WHERE person_id = %s", (person_id,))
            cursor.execute("DELETE FROM persons WHERE person_id = %s", (person_id,))
            connection.commit()
