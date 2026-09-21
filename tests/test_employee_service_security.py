"""Security regression tests for privileged employee operations."""

from uuid import uuid4

import pytest

from src.alrifai.employee.employee_service import (
    AdminAuthorizationUnavailable,
    EmployeeService,
)


class NeverUsedConnection:
    """Fail the test if a fail-closed operation touches the database."""

    def commit(self):
        raise AssertionError("hiring must fail before commit")

    def rollback(self):
        raise AssertionError("hiring must fail before rollback")

    def cursor(self):
        raise AssertionError("hiring must fail before database access")


def test_hiring_fails_closed_even_for_an_existing_person_id():
    service = EmployeeService(NeverUsedConnection())

    with pytest.raises(
        AdminAuthorizationUnavailable,
        match="trusted Admin authorization is unavailable",
    ):
        service.hire_applicant(
            application_code="APP-SECURITY",
            employee_code="EMP-SECURITY",
            display_name="Applicant",
            admin_actor_id=uuid4(),
        )
