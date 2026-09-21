"""Identity-aware applicant application service."""

from __future__ import annotations

from dataclasses import dataclass
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


class ApplicantServiceError(ValueError):
    """A submission cannot be safely accepted."""


@dataclass(frozen=True)
class ApplicationSubmission:
    application_code: str
    position: str
    observation: IdentityObservation
    source: str | None = None
    actor_id: UUID | None = None
    idempotency_key: str | None = None
    correlation_id: str | None = None


@dataclass(frozen=True)
class ApplicantResult:
    applicant_id: UUID
    person_id: UUID
    created: bool


class ApplicantService:
    """Own applicant writes while delegating identity decisions to the resolver."""

    def __init__(self, connection: DbConnection):
        self.connection = connection
        self.repository = PostgresIdentityRepository(connection)

    def submit(self, submission: ApplicationSubmission) -> ApplicantResult:
        return in_transaction(self.connection, lambda: self._submit(submission))

    def _submit(self, submission: ApplicationSubmission) -> ApplicantResult:
        if not submission.application_code.strip() or not submission.position.strip():
            raise ApplicantServiceError("application_code and position are required")
        existing = idempotent_aggregate(self.connection, submission.idempotency_key)
        if existing:
            row = one(
                self.connection,
                "SELECT person_id FROM applicants WHERE applicant_id = %s",
                (existing,),
            )
            if row:
                return ApplicantResult(existing, UUID(str(row[0])), False)
        if one(
            self.connection,
            "SELECT applicant_id FROM applicants WHERE application_code = %s",
            (submission.application_code,),
        ):
            raise ApplicantServiceError("application_code already exists")

        resolution = resolve_identity(self.repository, submission.observation)
        if resolution.status in {"invalid", "ambiguous"}:
            raise ApplicantServiceError(f"identity resolution is {resolution.status}")
        person_id = resolution.person_id
        if person_id is None:
            if not submission.observation.name and not submission.observation.phone:
                raise ApplicantServiceError("new applicants require a name or phone")
            person_id = create_person(
                self.connection,
                person_type="APPLICANT",
                observation=submission.observation,
                normalized_phone=resolution.normalized_phone,
                source_system="alrifai.applicant_service",
            )

        row = one(
            self.connection,
            """
            INSERT INTO applicants (person_id, application_code, position, source)
            VALUES (%s, %s, %s, %s)
            RETURNING applicant_id
            """,
            (person_id, submission.application_code, submission.position, submission.source),
        )
        applicant_id = UUID(str(row[0]))
        write_audit(
            self.connection,
            entity_type="applicant",
            entity_id=applicant_id,
            action="CREATE",
            actor_id=submission.actor_id,
            before=None,
            after={"status": "new", "person_id": str(person_id)},
            correlation_id=submission.correlation_id,
        )
        write_event(
            self.connection,
            event_type="APPLICATION_SUBMITTED",
            aggregate_type="applicant",
            aggregate_id=applicant_id,
            actor_id=submission.actor_id,
            payload={"application_code": submission.application_code},
            source_system="alrifai.applicant_service",
            idempotency_key=submission.idempotency_key,
        )
        return ApplicantResult(applicant_id, person_id, True)
