"""Applicant and employee service tests against the isolated local database."""

from __future__ import annotations

import os
from uuid import UUID, uuid4

import pytest

psycopg = pytest.importorskip("psycopg")

from src.alrifai.applicant.applicant_service import (  # noqa: E402
    ApplicantService,
    ApplicantServiceError,
    ApplicationSubmission,
)
from src.alrifai.employee.employee_service import (  # noqa: E402
    EmployeeInput,
    EmployeeService,
)
from src.alrifai.identity.identity_resolver import IdentityObservation  # noqa: E402
from src.alrifai.identity.phone_normalizer import normalize_phone  # noqa: E402


pytestmark = pytest.mark.skipif(
    os.getenv("ALRIFAI_TEST_DATABASE_URL") is None
    or os.getenv("ALRIFAI_TEST_DATABASE_ISOLATED") != "1",
    reason="isolated local PostgreSQL test database is not configured",
)


def _phone() -> str:
    return f"+88017{uuid4().int % 100000000:08d}"


def _code(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}"


def _one(connection, sql: str, parameters: tuple[object, ...] = ()):
    with connection.cursor() as cursor:
        cursor.execute(sql, parameters)
        return cursor.fetchone()


def _person_with_phone(connection, phone: str) -> UUID:
    person_id = _one(
        connection,
        """
        INSERT INTO persons (person_type, phone_normalized)
        VALUES ('APPLICANT', %s)
        RETURNING person_id
        """,
        (normalize_phone(phone),),
    )[0]
    _one(
        connection,
        """
        INSERT INTO person_phones (person_id, raw_value, normalized_value, source_system)
        VALUES (%s, %s, %s, 'service-integration-test')
        RETURNING phone_id
        """,
        (person_id, phone, normalize_phone(phone)),
    )
    return person_id


@pytest.fixture
def database_url() -> str:
    return os.environ["ALRIFAI_TEST_DATABASE_URL"]


def test_applicant_submission_reuses_person_and_is_idempotent(database_url: str):
    phone = _phone()
    with psycopg.connect(database_url) as connection:
        person_id = _person_with_phone(connection, phone)
        connection.commit()
        service = ApplicantService(connection)
        key = _code("submit")
        submission = ApplicationSubmission(
            application_code=_code("APP"),
            position="Operations",
            observation=IdentityObservation(phone=phone, name="Existing Person"),
            idempotency_key=key,
        )

        first = service.submit(submission)
        second = service.submit(submission)

        assert first.created is True
        assert first.person_id == person_id
        assert second.created is False
        assert second.applicant_id == first.applicant_id
        assert _one(
            connection,
            "SELECT count(*) FROM applicants WHERE applicant_id = %s",
            (first.applicant_id,),
        )[0] == 1


def test_duplicate_application_code_is_rejected(database_url: str):
    with psycopg.connect(database_url) as connection:
        service = ApplicantService(connection)
        code = _code("APP")
        first = ApplicationSubmission(
            application_code=code,
            position="Support",
            observation=IdentityObservation(name="First Applicant"),
        )
        service.submit(first)

        with pytest.raises(ApplicantServiceError, match="application_code already exists"):
            service.submit(
                ApplicationSubmission(
                    application_code=code,
                    position="Support",
                    observation=IdentityObservation(name="Second Applicant"),
                )
            )


def test_employee_service_reactivates_existing_inactive_employee(database_url: str):
    phone = _phone()
    with psycopg.connect(database_url) as connection:
        person_id = _person_with_phone(connection, phone)
        employee_id = _one(
            connection,
            """
            INSERT INTO employees (person_id, employee_code, display_name, status)
            VALUES (%s, %s, 'Existing Employee', 'inactive')
            RETURNING employee_id
            """,
            (person_id, _code("EMP")),
        )[0]
        connection.commit()
        result = EmployeeService(connection).create_or_reuse(
            EmployeeInput(
                employee_code=_code("NEW-CODE"),
                display_name="Existing Employee",
                observation=IdentityObservation(phone=phone),
            )
        )

        assert result.employee_id == employee_id
        assert result.person_id == person_id
        assert result.created is False
        assert result.activated is True
        assert _one(
            connection,
            "SELECT status FROM employees WHERE employee_id = %s",
            (employee_id,),
        )[0] == "active"


def test_employee_service_rolls_back_reactivation_when_audit_fails(
    database_url: str,
    monkeypatch: pytest.MonkeyPatch,
):
    phone = _phone()
    with psycopg.connect(database_url) as connection:
        person_id = _person_with_phone(connection, phone)
        employee_id = _one(
            connection,
            """
            INSERT INTO employees (person_id, employee_code, display_name, status)
            VALUES (%s, %s, 'Rollback Employee', 'inactive')
            RETURNING employee_id
            """,
            (person_id, _code("EMP")),
        )[0]
        connection.commit()

        def fail_audit(*args, **kwargs):
            raise RuntimeError("forced service audit failure")

        monkeypatch.setattr(
            "src.alrifai.employee.employee_service.write_audit",
            fail_audit,
        )
        with pytest.raises(RuntimeError, match="forced service audit failure"):
            EmployeeService(connection).create_or_reuse(
                EmployeeInput(
                    employee_code=_code("NEW-CODE"),
                    display_name="Rollback Employee",
                    observation=IdentityObservation(phone=phone),
                )
            )

        assert _one(
            connection,
            "SELECT status FROM employees WHERE employee_id = %s",
            (employee_id,),
        )[0] == "inactive"
        assert connection.info.transaction_status == psycopg.pq.TransactionStatus.INTRANS
        connection.rollback()
