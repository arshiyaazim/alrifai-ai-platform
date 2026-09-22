from __future__ import annotations

import os
from uuid import uuid4

import pytest

psycopg = pytest.importorskip("psycopg")

from src.alrifai.conversations import (  # noqa: E402
    Channel,
    ConversationScope,
    PostgresTopicStore,
    TopicEvidence,
    TopicState,
    TopicStateService,
    TopicTransitionKind,
    TopicTransitionRequest,
)


pytestmark = pytest.mark.skipif(
    os.getenv("ALRIFAI_TEST_DATABASE_URL") is None
    or os.getenv("ALRIFAI_TEST_DATABASE_ISOLATED") != "1",
    reason="isolated local PostgreSQL test database is not configured",
)


def test_postgres_topic_state_and_history_survive_store_reconstruction():
    database_url = os.environ["ALRIFAI_TEST_DATABASE_URL"]
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('conversation_topics')")
            if cursor.fetchone()[0] is None:
                pytest.skip("V008 topic foundation is not applied")
            conversation_id = uuid4()
            cursor.execute(
                """
                INSERT INTO conversation_threads (
                    conversation_id, channel, source_account,
                    external_thread_id, conversation_scope
                ) VALUES (%s, 'whatsapp', 'c4-test', %s, 'private')
                """,
                (conversation_id, f"c4-{conversation_id}"),
            )
            connection.commit()

        service = TopicStateService(PostgresTopicStore(connection))
        topic = service.create_topic(
            conversation_id=conversation_id,
            conversation_scope=ConversationScope.PRIVATE,
            channel=Channel.WHATSAPP,
            source_account="c4-test",
            idempotency_key=f"create-{conversation_id}",
        )
        updated = service.transition(
            topic.topic_id,
            TopicTransitionRequest(
                target_state=TopicState.GATHERING,
                transition_kind=TopicTransitionKind.ACTIVATE,
                evidence=(TopicEvidence.TYPED_ASSOCIATION,),
                conversation_id=conversation_id,
                idempotency_key=f"activate-{conversation_id}",
                expected_state_version=0,
            ),
        )
        retry = service.transition(
            topic.topic_id,
            TopicTransitionRequest(
                target_state=TopicState.GATHERING,
                transition_kind=TopicTransitionKind.ACTIVATE,
                evidence=(TopicEvidence.TYPED_ASSOCIATION,),
                conversation_id=conversation_id,
                idempotency_key=f"activate-{conversation_id}",
            ),
        )

        reconstructed_store = PostgresTopicStore(connection)
        reconstructed = reconstructed_store.get(topic.topic_id)
        history = reconstructed_store.history(topic.topic_id)

        assert updated.state is TopicState.GATHERING
        assert retry.state_version == updated.state_version
        assert reconstructed == updated
        assert [item.to_state for item in history] == [TopicState.OPENED, TopicState.GATHERING]

        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM conversation_topics WHERE topic_id = %s", (topic.topic_id,))
            cursor.execute("DELETE FROM conversation_threads WHERE conversation_id = %s", (conversation_id,))
            connection.commit()
