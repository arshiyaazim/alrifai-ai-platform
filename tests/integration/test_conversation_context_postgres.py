"""C6 read-only context composition against the isolated canonical schema."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

psycopg = pytest.importorskip("psycopg")

from alrifai.authorization.policy import (  # noqa: E402
    AssuranceLevel,
    AuthenticationMethod,
    Capability,
    PrincipalType,
    _from_verified_authentication,
)
from alrifai.conversations import (  # noqa: E402
    Channel,
    ContextPurpose,
    ContextRequest,
    ContextRetrievalService,
    ConversationScope,
    Direction,
    IdentityResolutionResult,
    IdentityResultStatus,
    InMemoryInstructionStore,
    InstructionService,
    PostgresContextSource,
    ProcessingState,
    build_turns,
)
from alrifai.identity.identity_resolver import (  # noqa: E402
    IdentityObservation,
    IdentityResolution,
    PostgresIdentityRepository,
    resolve_identity,
)
from alrifai.identity.phone_normalizer import normalize_phone  # noqa: E402


pytestmark = pytest.mark.skipif(
    os.getenv("ALRIFAI_TEST_DATABASE_URL") is None
    or os.getenv("ALRIFAI_TEST_DATABASE_ISOLATED") != "1",
    reason="isolated local PostgreSQL test database is not configured",
)


def test_postgres_context_adapter_keeps_closed_topic_history_out_of_current_package():
    at = datetime.now(timezone.utc).replace(microsecond=0)
    conversation_id = uuid4()
    old_message_id, current_message_id, topic_id = uuid4(), uuid4(), uuid4()
    person_id, employee_id = uuid4(), uuid4()
    source_account = "c6-isolated-test"
    phone = f"+88017{uuid4().int % 100000000:08d}"
    normalized_phone = normalize_phone(phone)
    with psycopg.connect(os.environ["ALRIFAI_TEST_DATABASE_URL"]) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO persons(person_id,person_type,phone_normalized) VALUES (%s,'EMPLOYEE',%s)",
                (person_id, normalized_phone),
            )
            cursor.execute(
                "INSERT INTO employees(employee_id,person_id,employee_code,display_name,status) VALUES (%s,%s,%s,%s,'active')",
                (employee_id, person_id, f"C6-{employee_id.hex}", "C6 integration employee"),
            )
            cursor.execute(
                "INSERT INTO person_phones(person_id,raw_value,normalized_value,phone_type,source_system) VALUES (%s,%s,%s,'MOBILE','c6-test')",
                (person_id, phone, normalized_phone),
            )
            cursor.execute(
                """INSERT INTO conversation_threads(
                    conversation_id,channel,source_account,external_thread_id,conversation_scope
                ) VALUES (%s,'whatsapp',%s,%s,'group')""",
                (conversation_id, source_account, str(conversation_id)),
            )
            for message_id, body, occurred_at, message_person_id in (
                (old_message_id, "closed historical text", at - timedelta(minutes=5), None),
                (current_message_id, "current turn", at, person_id),
            ):
                cursor.execute(
                    """INSERT INTO conversation_messages(
                        message_id,conversation_id,channel,source_account,direction,sender,person_id,
                        actor_type,occurred_at,received_at,content_type,body,topic
                    ) VALUES (%s,%s,'whatsapp',%s,'inbound','member-a',%s,'external_user',%s,%s,'text',%s,NULL)""",
                    (message_id, conversation_id, source_account, message_person_id,
                     occurred_at, occurred_at + timedelta(seconds=1), body),
                )
            cursor.execute(
                """INSERT INTO conversation_topics(
                    topic_id,conversation_id,conversation_scope,channel,source_account,state,
                    evidence_message_ids,last_activity_at
                ) VALUES (%s,%s,'group','whatsapp',%s,'closed',%s::jsonb,%s)""",
                (topic_id, conversation_id, source_account,
                 json.dumps([str(old_message_id)]), at - timedelta(minutes=5)),
            )
            connection.commit()

        source = PostgresContextSource(connection)
        current = source.get_messages(conversation_id, (current_message_id,))
        turn = build_turns(current).turns[0]
        principal = _from_verified_authentication(
            principal_id=uuid4(), principal_type=PrincipalType.ADMIN, person_id=None,
            authentication_method=AuthenticationMethod.SERVICE_IDENTITY,
            source="c6-isolated-integration", assurance=AssuranceLevel.STANDARD,
            capabilities=frozenset({Capability.MANAGE_CONVERSATIONS}),
        )
        resolution = IdentityResolution(status="unmatched", person_id=None)
        result = ContextRetrievalService(
            source, InstructionService(InMemoryInstructionStore()),
        ).retrieve(ContextRequest(
            principal=principal, conversation_id=conversation_id, current_turn=turn,
            channel=Channel.WHATSAPP, source_account=source_account,
            identity=IdentityResolutionResult(
                IdentityResultStatus.UNRESOLVED, resolution, "isolated test evidence",
            ),
            purpose=ContextPurpose.CURRENT_TURN, at=at,
        ))
        assert [message.message_id for message in result.messages] == [current_message_id]
        assert result.topics == ()
        assert result.relationship_status.value == "unknown"

        resolved = resolve_identity(
            PostgresIdentityRepository(connection), IdentityObservation(phone=phone),
        )
        assert resolved.status == "matched"
        assert resolved.employee_id == employee_id
        assert len(resolved.candidates) == 1
        assert resolved.candidates[0].employee_status == "active"
        employee_identity = IdentityResolutionResult(
            IdentityResultStatus.RESOLVED, resolved, "canonical PostgreSQL identity evidence",
        )
        employee_result = ContextRetrievalService(
            source, InstructionService(InMemoryInstructionStore()),
        ).retrieve(ContextRequest(
            principal=principal, conversation_id=conversation_id, current_turn=turn,
            channel=Channel.WHATSAPP, source_account=source_account,
            identity=employee_identity, purpose=ContextPurpose.CURRENT_TURN, at=at,
        ))
        assert employee_result.relationship_status.value == "confirmed_current_employee"

        with connection.cursor() as cursor:
            duplicate_person_id, duplicate_employee_id = uuid4(), uuid4()
            cursor.execute(
                "INSERT INTO persons(person_id,person_type,phone_normalized) VALUES (%s,'EMPLOYEE',%s)",
                (duplicate_person_id, normalized_phone),
            )
            cursor.execute(
                "INSERT INTO employees(employee_id,person_id,employee_code,display_name,status) VALUES (%s,%s,%s,%s,'active')",
                (duplicate_employee_id, duplicate_person_id, f"C6-{duplicate_employee_id.hex}", "C6 duplicate"),
            )
            cursor.execute(
                "INSERT INTO person_phones(person_id,raw_value,normalized_value,phone_type,source_system) VALUES (%s,%s,%s,'MOBILE','c6-test')",
                (duplicate_person_id, phone, normalized_phone),
            )
            connection.commit()
        ambiguous = resolve_identity(
            PostgresIdentityRepository(connection), IdentityObservation(phone=phone),
        )
        assert ambiguous.status == "ambiguous"
        ambiguous_result = ContextRetrievalService(
            source, InstructionService(InMemoryInstructionStore()),
        ).retrieve(ContextRequest(
            principal=principal, conversation_id=conversation_id, current_turn=turn,
            channel=Channel.WHATSAPP, source_account=source_account,
            identity=IdentityResolutionResult(
                IdentityResultStatus.AMBIGUOUS, ambiguous, "ambiguous PostgreSQL identity evidence",
            ), purpose=ContextPurpose.CURRENT_TURN, at=at,
        ))
        assert ambiguous_result.relationship_status.value == "unknown"

        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM conversation_threads WHERE conversation_id=%s", (conversation_id,))
            cursor.execute("DELETE FROM persons WHERE person_id IN (%s,%s)", (person_id, duplicate_person_id))
            connection.commit()
