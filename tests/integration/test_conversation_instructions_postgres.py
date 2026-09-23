from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

psycopg = pytest.importorskip("psycopg")

from src.alrifai.authorization.policy import (  # noqa: E402
    AuthenticationMethod,
    AssuranceLevel,
    Capability,
    PrincipalType,
    _from_verified_authentication,
)
from src.alrifai.conversations.instructions import (  # noqa: E402
    InstructionContext,
    InstructionDraft,
    InstructionScope,
    InstructionService,
    PostgresInstructionStore,
)


pytestmark = pytest.mark.skipif(
    os.getenv("ALRIFAI_TEST_DATABASE_URL") is None
    or os.getenv("ALRIFAI_TEST_DATABASE_ISOLATED") != "1",
    reason="isolated local PostgreSQL test database is not configured",
)


def test_instruction_versions_selection_and_history_survive_reconstruction():
    now = datetime.now(timezone.utc)
    admin_id = uuid4()
    run_key = str(uuid4())
    with psycopg.connect(os.environ["ALRIFAI_TEST_DATABASE_URL"]) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT to_regclass('conversation_ai_instruction_versions')")
            if cursor.fetchone()[0] is None:
                pytest.skip("V009 instruction foundation is not applied")
            cursor.execute("SELECT principal_id FROM auth_principals WHERE principal_type='OWNER'")
            owner_row = cursor.fetchone()
            owner_id = owner_row[0] if owner_row else uuid4()
            if owner_row is None:
                cursor.execute(
                    "INSERT INTO auth_principals(principal_id,principal_type,status) VALUES (%s,'OWNER','active')",
                    (owner_id,),
                )
            cursor.execute(
                "INSERT INTO auth_principals(principal_id,principal_type,status) VALUES (%s,'ADMIN','active')",
                (admin_id,),
            )
            conversation_id = uuid4()
            cursor.execute(
                """INSERT INTO conversation_threads(
                    conversation_id,channel,source_account,external_thread_id,conversation_scope
                ) VALUES (%s,'whatsapp','c5-test',%s,'private')""",
                (conversation_id, str(conversation_id)),
            )
            connection.commit()

        owner = _from_verified_authentication(
            principal_id=owner_id, principal_type=PrincipalType.OWNER, person_id=None,
            authentication_method=AuthenticationMethod.FRONTEND_PASSWORD,
            source="test.owner", assurance=AssuranceLevel.HIGH, capabilities=frozenset(),
        )
        admin = _from_verified_authentication(
            principal_id=admin_id, principal_type=PrincipalType.ADMIN, person_id=None,
            authentication_method=AuthenticationMethod.FRONTEND_PASSWORD,
            source="test.admin", assurance=AssuranceLevel.STANDARD,
            capabilities=frozenset({Capability.MANAGE_CONVERSATIONS}),
        )

        service = InstructionService(PostgresInstructionStore(connection))
        admin_version = service.create_version(admin, InstructionDraft(
            "recruitment.greeting", "Admin greeting", effective_from=now-timedelta(minutes=1),
            idempotency_key=f"admin-create:{run_key}", provenance=("admin console",),
        ))
        service.activate(admin, admin_version.version_id, idempotency_key=f"admin-activate:{run_key}")
        owner_version = service.create_version(owner, InstructionDraft(
            "recruitment.greeting", "Owner greeting", effective_from=now-timedelta(minutes=1),
            idempotency_key=f"owner-create:{run_key}", provenance=("owner console",),
        ))
        service.activate(owner, owner_version.version_id, idempotency_key=f"owner-activate:{run_key}")

        revised_owner = service.create_version(owner, InstructionDraft(
            "recruitment.greeting", "Revised Owner greeting", effective_from=now+timedelta(hours=1),
            supersedes_version_id=owner_version.version_id, idempotency_key=f"owner-revision:{run_key}",
            provenance=("owner console",),
        ))
        service.activate(owner, revised_owner.version_id, idempotency_key=f"owner-revision-activate:{run_key}")

        restarted = InstructionService(PostgresInstructionStore(connection))
        current = restarted.select(InstructionContext(at=now+timedelta(minutes=1), conversation_id=conversation_id))
        future = restarted.select(InstructionContext(at=now+timedelta(hours=2), conversation_id=conversation_id))
        assert [v.content for v in current.selected] == ["Owner greeting"]
        assert [v.content for v in future.selected] == ["Revised Owner greeting"]
        assert restarted.status(owner_version.version_id).value == "active"
        assert restarted.store.events(owner_version.version_id)[-1].event_type.value == "superseded"
        assert {event.event_type.value for event in restarted.store.events(revised_owner.version_id)} == {"created", "activated"}

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*) FROM audit_log WHERE entity_type='conversation_ai_instruction' AND actor_principal_id IN (%s,%s)",
                (owner_id, admin_id),
            )
            assert cursor.fetchone()[0] >= 5
            cursor.execute(
                """SELECT count(*) FROM conversation_ai_instruction_versions
                WHERE instruction_id=%s""", (owner_version.instruction_id,),
            )
            assert cursor.fetchone()[0] == 2
            # Keep append-only evidence; this test is intended for a disposable DB.


def test_postgres_enforces_topic_conversation_scope_and_immutable_versions():
    principal_id, conversation_id, other_conversation_id = uuid4(), uuid4(), uuid4()
    topic_id = uuid4()
    with psycopg.connect(os.environ["ALRIFAI_TEST_DATABASE_URL"]) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO auth_principals(principal_id,principal_type,status) VALUES (%s,'ADMIN','active')",
                (principal_id,),
            )
            for item in (conversation_id, other_conversation_id):
                cursor.execute(
                    """INSERT INTO conversation_threads(
                        conversation_id,channel,source_account,external_thread_id,conversation_scope
                    ) VALUES (%s,'whatsapp','scope-test',%s,'private')""",
                    (item, str(item)),
                )
            cursor.execute(
                """INSERT INTO conversation_topics(
                    topic_id,conversation_id,conversation_scope,channel,source_account,state
                ) VALUES (%s,%s,'private','whatsapp','scope-test','opened')""",
                (topic_id, other_conversation_id),
            )
            connection.commit()

        admin = _from_verified_authentication(
            principal_id=principal_id, principal_type=PrincipalType.ADMIN, person_id=None,
            authentication_method=AuthenticationMethod.FRONTEND_PASSWORD,
            source="test.admin", assurance=AssuranceLevel.STANDARD,
            capabilities=frozenset({Capability.MANAGE_CONVERSATIONS}),
        )
        service = InstructionService(PostgresInstructionStore(connection))
        with pytest.raises(psycopg.errors.RaiseException, match="topic must belong"):
            service.create_version(admin, InstructionDraft(
                "scope-check", "must reject", scope=InstructionScope(
                    conversation_id=conversation_id, topic_id=topic_id,
                ), idempotency_key=f"bad-scope:{uuid4()}",
            ))

        version = service.create_version(admin, InstructionDraft(
            "immutable-check", "original", idempotency_key=f"immutable:{uuid4()}",
        ))
        with pytest.raises(psycopg.errors.RaiseException, match="append-only"):
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE conversation_ai_instruction_versions SET content='changed' WHERE version_id=%s",
                    (version.version_id,),
                )
        connection.rollback()
        assert service.store.get(version.version_id).content == "original"
