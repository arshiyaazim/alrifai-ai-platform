"""Identity-aware employee creation, reuse, and hiring approval."""

from __future__ import annotations

from dataclasses import dataclass, replace
from uuid import UUID

from ..identity.identity_resolver import (
    DbConnection,
    IdentityObservation,
    PostgresIdentityRepository,
    resolve_identity,
)
from ..services._common import (
    create_person,
    idempotent_aggregate,
    in_transaction,
    one,
    write_audit,
    write_event,
)


class EmployeeServiceError(ValueError):
    """An employee operation cannot be safely completed."""


class AdminAuthorizationUnavailable(EmployeeServiceError):
    """Hiring is unavailable until a trusted Admin authorization is supplied."""


@dataclass(frozen=True)
class EmployeeInput:
    employee_code: str
    display_name: str
    observation: IdentityObservation
    designation: str | None = None
    department: str | None = None
    actor_id: UUID | None = None
    idempotency_key: str | None = None
    correlation_id: str | None = None


@dataclass(frozen=True)
class EmployeeResult:
    employee_id: UUID
    person_id: UUID
    created: bool
    activated: bool = False


class EmployeeService:
    """Own employee lifecycle writes after deterministic identity resolution."""

    def __init__(self, connection: DbConnection):
        self.connection = connection
        self.repository = PostgresIdentityRepository(connection)

    def create_or_reuse(self, employee: EmployeeInput) -> EmployeeResult:
        return in_transaction(self.connection, lambda: self._create_or_reuse(employee))

    def _create_or_reuse(self, employee: EmployeeInput) -> EmployeeResult:
        if not employee.employee_code.strip() or not employee.display_name.strip():
            raise EmployeeServiceError("employee_code and display_name are required")
        existing = idempotent_aggregate(self.connection, employee.idempotency_key)
        if existing:
            row = one(
                self.connection,
                "SELECT person_id FROM employees WHERE employee_id = %s",
                (existing,),
            )
            if row:
                return EmployeeResult(existing, UUID(str(row[0])), False)
        observation = employee.observation
        resolution = resolve_identity(self.repository, observation)
        if resolution.status in {"invalid", "ambiguous"}:
            raise EmployeeServiceError(f"identity resolution is {resolution.status}")

        if resolution.employee_id:
            locked = self.repository.lock_employee(resolution.employee_id)
            if locked is None:
                raise EmployeeServiceError("matched employee disappeared")
            if locked.employee_status == "inactive":
                if not self.repository.activate_employee(locked.employee_id):
                    raise EmployeeServiceError("employee activation did not update a row")
                write_audit(
                    self.connection,
                    entity_type="employee",
                    entity_id=locked.employee_id,
                    action="UPDATE",
                    actor_id=employee.actor_id,
                    before={"status": "inactive"},
                    after={"status": "active"},
                    correlation_id=employee.correlation_id,
                )
                activated = True
            elif locked.employee_status != "active":
                raise EmployeeServiceError(
                    f"existing employee status {locked.employee_status} cannot be reused"
                )
            else:
                activated = False
            write_event(
                self.connection,
                event_type="EMPLOYEE_REUSED",
                aggregate_type="employee",
                aggregate_id=locked.employee_id,
                actor_id=employee.actor_id,
                payload={"activated": activated},
                source_system="alrifai.employee_service",
                idempotency_key=employee.idempotency_key,
            )
            return EmployeeResult(locked.employee_id, locked.person_id, False, activated)

        person_id = resolution.person_id
        if person_id is None:
            if not observation.name and not observation.phone:
                observation = replace(observation, name=employee.display_name)
            person_id = create_person(
                self.connection,
                person_type="EMPLOYEE",
                observation=observation,
                normalized_phone=resolution.normalized_phone,
                source_system="alrifai.employee_service",
            )
        row = one(
            self.connection,
            """
            INSERT INTO employees (
                person_id, employee_code, display_name, designation, department
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING employee_id
            """,
            (
                person_id,
                employee.employee_code,
                employee.display_name,
                employee.designation,
                employee.department,
            ),
        )
        employee_id = UUID(str(row[0]))
        write_audit(
            self.connection,
            entity_type="employee",
            entity_id=employee_id,
            action="CREATE",
            actor_id=employee.actor_id,
            before=None,
            after={"person_id": str(person_id), "status": "active"},
            correlation_id=employee.correlation_id,
        )
        write_event(
            self.connection,
            event_type="EMPLOYEE_CREATED",
            aggregate_type="employee",
            aggregate_id=employee_id,
            actor_id=employee.actor_id,
            payload={"employee_code": employee.employee_code},
            source_system="alrifai.employee_service",
            idempotency_key=employee.idempotency_key,
        )
        return EmployeeResult(employee_id, person_id, True)

    def hire_applicant(
        self,
        *,
        application_code: str,
        employee_code: str,
        display_name: str,
        admin_actor_id: UUID,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
    ) -> EmployeeResult:
        # A person ID is an audit reference, not proof of Admin authority.
        # AL-RIFAI currently has no trusted authentication/authorization
        # context, so fail closed before any transaction or database access.
        raise AdminAuthorizationUnavailable(
            "trusted Admin authorization is unavailable; hiring is disabled"
        )
        return in_transaction(
            self.connection,
            lambda: self._hire_applicant(
                application_code,
                employee_code,
                display_name,
                admin_actor_id,
                idempotency_key,
                correlation_id,
            ),
        )

    def _hire_applicant(
        self,
        application_code: str,
        employee_code: str,
        display_name: str,
        admin_actor_id: UUID,
        idempotency_key: str | None,
        correlation_id: str | None,
    ) -> EmployeeResult:
        raise AdminAuthorizationUnavailable(
            "trusted Admin authorization is unavailable; hiring is disabled"
        )
        if not admin_actor_id:
            raise EmployeeServiceError("admin_actor_id is required")
        existing = idempotent_aggregate(self.connection, idempotency_key)
        if existing:
            row = one(
                self.connection,
                """
                SELECT e.employee_id, e.person_id
                FROM business_events AS be
                JOIN employees AS e
                  ON e.employee_id = (be.payload->>'employee_id')::uuid
                WHERE be.event_type = 'APPLICANT_HIRED'
                  AND be.aggregate_id = %s
                  AND be.idempotency_key = %s
                LIMIT 1
                """,
                (existing, idempotency_key),
            )
            if row:
                return EmployeeResult(UUID(str(row[0])), UUID(str(row[1])), False)
        applicant = one(
            self.connection,
            """
            SELECT applicant_id, person_id, status
            FROM applicants
            WHERE application_code = %s
            FOR UPDATE
            """,
            (application_code,),
        )
        if applicant is None:
            raise EmployeeServiceError("application not found")
        applicant_id, person_id, status = applicant
        if status != "offered":
            raise EmployeeServiceError("only offered applicants can be hired")
        person_id = UUID(str(person_id)) if person_id else None
        if person_id is None:
            raise EmployeeServiceError("applicant has no canonical person")
        if not one(
            self.connection,
            "SELECT person_id FROM persons WHERE person_id = %s",
            (admin_actor_id,),
        ):
            raise EmployeeServiceError("admin actor does not exist")

        employee_row = one(
            self.connection,
            """
            SELECT employee_id, status
            FROM employees
            WHERE person_id = %s
            FOR UPDATE
            """,
            (person_id,),
        )
        if employee_row:
            employee_id, employee_status = employee_row
            employee_id = UUID(str(employee_id))
            if employee_status == "inactive":
                one(
                    self.connection,
                    """
                    UPDATE employees
                    SET status = 'active', updated_at = NOW()
                    WHERE employee_id = %s
                    RETURNING employee_id
                    """,
                    (employee_id,),
                )
                write_audit(
                    self.connection,
                    entity_type="employee",
                    entity_id=employee_id,
                    action="UPDATE",
                    actor_id=admin_actor_id,
                    before={"status": "inactive"},
                    after={"status": "active"},
                    correlation_id=correlation_id,
                )
                activated = True
            elif employee_status == "active":
                activated = False
            else:
                raise EmployeeServiceError(
                    f"existing employee status {employee_status} cannot be hired"
                )
            created = False
        else:
            row = one(
                self.connection,
                """
                INSERT INTO employees (person_id, employee_code, display_name)
                VALUES (%s, %s, %s)
                RETURNING employee_id
                """,
                (person_id, employee_code, display_name),
            )
            employee_id = UUID(str(row[0]))
            write_audit(
                self.connection,
                entity_type="employee",
                entity_id=employee_id,
                action="CREATE",
                actor_id=admin_actor_id,
                before=None,
                after={"person_id": str(person_id), "status": "active"},
                correlation_id=correlation_id,
            )
            created = True
            activated = False

        one(
            self.connection,
            """
            UPDATE applicants
            SET status = 'hired'
            WHERE applicant_id = %s
            RETURNING applicant_id
            """,
            (applicant_id,),
        )
        write_audit(
            self.connection,
            entity_type="applicant",
            entity_id=UUID(str(applicant_id)),
            action="UPDATE",
            actor_id=admin_actor_id,
            before={"status": "offered"},
            after={"status": "hired"},
            correlation_id=correlation_id,
        )
        write_event(
            self.connection,
            event_type="APPLICANT_HIRED",
            aggregate_type="applicant",
            aggregate_id=UUID(str(applicant_id)),
            actor_id=admin_actor_id,
            payload={"employee_id": str(employee_id)},
            source_system="alrifai.employee_service",
            idempotency_key=idempotency_key,
        )
        return EmployeeResult(employee_id, person_id, created, activated)
