"""Integration tests for the identity resolver against an isolated PostgreSQL database."""

from __future__ import annotations

import os
import threading
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import pytest

psycopg = pytest.importorskip("psycopg")

from src.alrifai.identity.identity_resolver import (  # noqa: E402
    IdentityObservation,
    PostgresIdentityRepository,
    resolve_and_reactivate,
    resolve_identity,
)
from src.alrifai.identity.phone_normalizer import normalize_phone  # noqa: E402


pytestmark = pytest.mark.skipif(
    os.getenv("ALRIFAI_TEST_DATABASE_URL") is None
    or os.getenv("ALRIFAI_TEST_DATABASE_ISOLATED") != "1",
    reason="isolated local PostgreSQL test database is not configured",
)


def _scalar(connection, operation: str, parameters: tuple[object, ...] = ()):
    with connection.cursor() as cursor:
        cursor.execute(operation, parameters)
        return cursor.fetchone()[0]


def _create_person(connection, phone: str | None = None) -> UUID:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO persons (person_type, phone_normalized)
            VALUES ('EMPLOYEE', %s)
            RETURNING person_id
            """,
            (normalize_phone(phone),),
        )
        return cursor.fetchone()[0]


def _create_employee(
    connection,
    person_id: UUID,
    employee_code: str,
    status: str = "inactive",
) -> UUID:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO employees (person_id, employee_code, display_name, status)
            VALUES (%s, %s, %s, %s)
            RETURNING employee_id
            """,
            (person_id, employee_code, employee_code, status),
        )
        return cursor.fetchone()[0]


def _add_phone(connection, person_id: UUID, normalized_phone: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO person_phones (
                person_id, raw_value, normalized_value, phone_type, source_system
            )
            VALUES (%s, %s, %s, 'MOBILE', 'integration-test')
            """,
            (person_id, normalized_phone, normalize_phone(normalized_phone)),
        )


def _add_employee_identifier(connection, person_id: UUID, value: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO person_identifiers (
                person_id, identifier_type, identifier_value, source_system
            )
            VALUES (%s, 'EMPLOYEE_CODE', %s, 'integration-test')
            """,
            (person_id, value),
        )


def _add_platform_identity(
    connection,
    person_id: UUID,
    platform: str,
    platform_user_id: str,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO external_platform_ids (
                person_id, platform, platform_user_id, source_system
            )
            VALUES (%s, %s, %s, 'integration-test')
            """,
            (person_id, platform, platform_user_id),
        )


def _new_code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


def _new_phone() -> str:
    return f"+88017{uuid4().int % 100000000:08d}"


@pytest.fixture
def database_url() -> str:
    return os.environ["ALRIFAI_TEST_DATABASE_URL"]


def test_identity_resolution_matches_phone_and_rejects_ambiguous_or_invalid_phone(
    database_url: str,
):
    phone = _new_phone()
    shared_phone = _new_phone()
    with psycopg.connect(database_url) as connection:
        unique_person = _create_person(connection, phone)
        unique_employee = _create_employee(connection, unique_person, _new_code("PHONE"))
        _add_phone(connection, unique_person, phone)

        shared_person_a = _create_person(connection)
        shared_person_b = _create_person(connection)
        _add_phone(connection, shared_person_a, shared_phone)
        _add_phone(connection, shared_person_b, shared_phone)
        connection.commit()

        repository = PostgresIdentityRepository(connection)
        unique = resolve_identity(repository, IdentityObservation(phone=phone))
        ambiguous = resolve_identity(repository, IdentityObservation(phone=shared_phone))
        invalid = resolve_identity(repository, IdentityObservation(phone="not-a-phone"))

        assert unique.status == "matched"
        assert unique.person_id == unique_person
        assert unique.employee_id == unique_employee
        assert ambiguous.status == "ambiguous"
        assert invalid.status == "invalid"


def test_identity_resolution_matches_employee_code_and_platform_id(database_url: str):
    employee_code = _new_code("EMPLOYEE")
    platform_user_id = _new_code("WHATSAPP")
    with psycopg.connect(database_url) as connection:
        person = _create_person(connection)
        employee = _create_employee(connection, person, employee_code)
        _add_employee_identifier(connection, person, employee_code)
        _add_platform_identity(connection, person, "WHATSAPP", platform_user_id)
        connection.commit()

        repository = PostgresIdentityRepository(connection)
        by_code = resolve_identity(
            repository,
            IdentityObservation(employee_code=employee_code),
        )
        by_platform = resolve_identity(
            repository,
            IdentityObservation(
                platform="WHATSAPP",
                platform_user_id=platform_user_id,
            ),
        )

        assert by_code.status == "matched"
        assert by_code.employee_id == employee
        assert by_platform.status == "matched"
        assert by_platform.employee_id == employee


def test_inactive_employee_activation_inserts_audit_without_creating_records(
    database_url: str,
):
    employee_code = _new_code("ACTIVATE")
    with psycopg.connect(database_url) as connection:
        person_count_before = _scalar(connection, "SELECT count(*) FROM persons")
        employee_count_before = _scalar(connection, "SELECT count(*) FROM employees")
        person = _create_person(connection)
        employee = _create_employee(connection, person, employee_code)
        connection.commit()

        result = resolve_and_reactivate(
            PostgresIdentityRepository(connection),
            IdentityObservation(employee_code=employee_code),
            correlation_id=_new_code("CORRELATION"),
        )

        assert result.status == "activated"
        assert _scalar(
            connection,
            "SELECT status FROM employees WHERE employee_id = %s",
            (employee,),
        ) == "active"
        assert _scalar(
            connection,
            "SELECT count(*) FROM audit_log WHERE entity_id = %s",
            (employee,),
        ) == 1
        assert _scalar(connection, "SELECT count(*) FROM persons") == person_count_before + 1
        assert _scalar(connection, "SELECT count(*) FROM employees") == employee_count_before + 1


def test_already_active_employee_is_idempotent_without_duplicate_audit(database_url: str):
    employee_code = _new_code("ACTIVE")
    with psycopg.connect(database_url) as connection:
        person = _create_person(connection)
        employee = _create_employee(connection, person, employee_code, status="active")
        connection.commit()

        result = resolve_and_reactivate(
            PostgresIdentityRepository(connection),
            IdentityObservation(employee_code=employee_code),
        )

        assert result.status == "already_active"
        assert _scalar(
            connection,
            "SELECT count(*) FROM audit_log WHERE entity_id = %s",
            (employee,),
        ) == 0


def test_audit_failure_rolls_back_activation(database_url: str):
    employee_code = _new_code("ROLLBACK")
    with psycopg.connect(database_url) as connection:
        person = _create_person(connection)
        employee = _create_employee(connection, person, employee_code)
        connection.commit()

        class FailingAuditRepository(PostgresIdentityRepository):
            def record_activation_audit(self, employee_id, actor_id, correlation_id):
                super().record_activation_audit(employee_id, actor_id, correlation_id)
                raise RuntimeError("forced integration audit failure")

        with pytest.raises(RuntimeError, match="forced integration audit failure"):
            resolve_and_reactivate(
                FailingAuditRepository(connection),
                IdentityObservation(employee_code=employee_code),
            )

        assert _scalar(
            connection,
            "SELECT status FROM employees WHERE employee_id = %s",
            (employee,),
        ) == "inactive"
        assert _scalar(
            connection,
            "SELECT count(*) FROM audit_log WHERE entity_id = %s",
            (employee,),
        ) == 0
        assert connection.info.transaction_status == psycopg.pq.TransactionStatus.INTRANS
        connection.rollback()
        assert connection.info.transaction_status == psycopg.pq.TransactionStatus.IDLE


def test_two_concurrent_activation_requests_are_safe(database_url: str):
    employee_code = _new_code("CONCURRENT")
    with psycopg.connect(database_url) as setup_connection:
        person = _create_person(setup_connection)
        employee = _create_employee(setup_connection, person, employee_code)
        setup_connection.commit()

    barrier = threading.Barrier(2)

    class SynchronizedRepository(PostgresIdentityRepository):
        def lock_employee(self, employee_id):
            barrier.wait(timeout=10)
            return super().lock_employee(employee_id)

    def activate():
        with psycopg.connect(database_url) as connection:
            result = resolve_and_reactivate(
                SynchronizedRepository(connection),
                IdentityObservation(employee_code=employee_code),
            )
            return result.status, connection.info.transaction_status

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: activate(), range(2)))

    assert sorted(status for status, _ in results) == ["activated", "already_active"]
    assert all(
        transaction_status == psycopg.pq.TransactionStatus.IDLE
        for _, transaction_status in results
    )
    with psycopg.connect(database_url) as verify_connection:
        assert _scalar(
            verify_connection,
            "SELECT status FROM employees WHERE employee_id = %s",
            (employee,),
        ) == "active"
        assert _scalar(
            verify_connection,
            "SELECT count(*) FROM employees WHERE employee_code = %s",
            (employee_code,),
        ) == 1
        assert _scalar(
            verify_connection,
            "SELECT count(*) FROM audit_log WHERE entity_id = %s",
            (employee,),
        ) == 1
