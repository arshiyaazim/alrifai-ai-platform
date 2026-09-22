"""Deterministic identity lookup and employee reactivation orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal, Protocol, Sequence
from uuid import UUID

from .phone_normalizer import normalize_phone

ResolutionStatus = Literal["matched", "ambiguous", "unmatched", "invalid"]
ReactivationStatus = Literal["activated", "already_active", "not_reactivated"]


@dataclass(frozen=True)
class StableIdentifier:
    """A typed identifier stored in ``person_identifiers``."""

    identifier_type: str
    value: str


@dataclass(frozen=True)
class IdentityObservation:
    """Identifiers observed at an inbound workflow boundary."""

    phone: str | None = None
    name: str | None = None
    employee_code: str | None = None
    stable_identifiers: tuple[StableIdentifier, ...] = ()
    platform: str | None = None
    platform_account: str | None = None
    platform_user_id: str | None = None


@dataclass(frozen=True)
class IdentityCandidate:
    """A person and optional employee returned by deterministic lookup."""

    person_id: UUID
    employee_id: UUID | None
    employee_status: str | None


@dataclass(frozen=True)
class IdentityResolution:
    """The result of identity lookup without changing database state."""

    status: ResolutionStatus
    person_id: UUID | None = None
    employee_id: UUID | None = None
    normalized_phone: str | None = None
    evidence: tuple[str, ...] = ()
    candidates: tuple[IdentityCandidate, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class ReactivationResult:
    """The outcome of an atomic resolve-and-reactivate operation."""

    resolution: IdentityResolution
    status: ReactivationStatus


class IdentityRepository(Protocol):
    """Read-only repository operations required by the resolver."""

    def find_by_normalized_phone(self, normalized_phone: str) -> Sequence[IdentityCandidate]: ...

    def find_by_identifier(self, identifier_type: str, value: str) -> Sequence[IdentityCandidate]: ...

    def find_by_platform_id(self, platform: str, platform_user_id: str, source_account: str | None = None) -> Sequence[IdentityCandidate]: ...


class ReactivationRepository(IdentityRepository, Protocol):
    """Repository operations required by the mutation orchestration."""

    connection: "DbConnection"

    def lock_employee(self, employee_id: UUID) -> IdentityCandidate | None: ...

    def activate_employee(self, employee_id: UUID) -> bool: ...

    def record_activation_audit(
        self,
        employee_id: UUID,
        actor_id: UUID | None,
        correlation_id: str | None,
    ) -> None: ...


class DbCursor(Protocol):
    def execute(self, operation: str, parameters: Sequence[object] = ()) -> object: ...

    def fetchall(self) -> Sequence[Sequence[object]]: ...

    def fetchone(self) -> Sequence[object] | None: ...

    def close(self) -> object: ...


class DbConnection(Protocol):
    def cursor(self) -> DbCursor: ...

    def commit(self) -> object: ...

    def rollback(self) -> object: ...


def resolve_identity(
    repository: IdentityRepository,
    observation: IdentityObservation,
) -> IdentityResolution:
    """Resolve an observation without creating or updating any records."""
    normalized_phone: str | None = None
    if observation.phone is not None:
        if not isinstance(observation.phone, str):
            return IdentityResolution(status="invalid", reason="phone must be a string")
        normalized_phone = normalize_phone(observation.phone)
        if not _is_supported_normalized_phone(normalized_phone):
            return IdentityResolution(
                status="invalid",
                normalized_phone=normalized_phone,
                reason="unsupported phone format",
            )

    if (observation.platform is None) != (observation.platform_user_id is None):
        return IdentityResolution(status="invalid", reason="platform identifier is incomplete")
    if observation.platform_account is not None and observation.platform is None:
        return IdentityResolution(status="invalid", reason="platform account is incomplete")

    evidence_sets: list[tuple[str, tuple[IdentityCandidate, ...]]] = []
    if normalized_phone is not None:
        evidence_sets.append(
            ("phone", tuple(repository.find_by_normalized_phone(normalized_phone)))
        )
    if observation.employee_code is not None:
        evidence_sets.append(
            (
                "employee_code",
                tuple(repository.find_by_identifier("EMPLOYEE_CODE", observation.employee_code)),
            )
        )
    for identifier in observation.stable_identifiers:
        evidence_sets.append(
            (
                f"identifier:{identifier.identifier_type}",
                tuple(repository.find_by_identifier(identifier.identifier_type, identifier.value)),
            )
        )
    if observation.platform is not None and observation.platform_user_id is not None:
        evidence_sets.append(
            (
                "platform_id",
                tuple(
                    repository.find_by_platform_id(
                        observation.platform,
                        observation.platform_user_id,
                        observation.platform_account or "default",
                    )
                ),
            )
        )

    if not evidence_sets:
        return IdentityResolution(
            status="unmatched",
            normalized_phone=normalized_phone,
            evidence=("name_ignored_for_deterministic_matching",) if observation.name else (),
            reason="no deterministic identifier supplied",
        )

    all_candidates = _unique_candidates(
        candidate for _, candidates in evidence_sets for candidate in candidates
    )
    if any(len(candidates) > 1 for _, candidates in evidence_sets):
        return _ambiguous(normalized_phone, evidence_sets, all_candidates, "multiple candidates")

    non_empty_sets = [
        frozenset(candidates) for _, candidates in evidence_sets if candidates
    ]
    if not non_empty_sets:
        return IdentityResolution(
            status="unmatched",
            normalized_phone=normalized_phone,
            evidence=tuple(name for name, _ in evidence_sets),
            reason="no deterministic identifier matched",
        )
    if len(non_empty_sets) != len(evidence_sets) or len(set(non_empty_sets)) != 1:
        return _ambiguous(
            normalized_phone,
            evidence_sets,
            all_candidates,
            "identifier evidence conflicts",
        )

    candidate = next(iter(non_empty_sets[0]))
    return IdentityResolution(
        status="matched",
        person_id=candidate.person_id,
        employee_id=candidate.employee_id,
        normalized_phone=normalized_phone,
        evidence=tuple(name for name, _ in evidence_sets),
        candidates=(candidate,),
        reason="one deterministic identity matched",
    )


def resolve_and_reactivate(
    repository: ReactivationRepository,
    observation: IdentityObservation,
    *,
    actor_id: UUID | None = None,
    correlation_id: str | None = None,
) -> ReactivationResult:
    """Resolve and atomically activate one existing inactive employee.

    The repository owns the same database connection for lookup, row locking,
    update, audit insertion, and commit/rollback. No person or employee is
    created, and no external call is made while the employee row is locked.
    """
    try:
        resolution = resolve_identity(repository, observation)
        if resolution.status != "matched" or resolution.employee_id is None:
            repository.connection.commit()
            return ReactivationResult(resolution, "not_reactivated")

        locked_employee = repository.lock_employee(resolution.employee_id)
        if locked_employee is None or locked_employee.person_id != resolution.person_id:
            repository.connection.commit()
            return ReactivationResult(
                IdentityResolution(
                    status="unmatched",
                    normalized_phone=resolution.normalized_phone,
                    evidence=resolution.evidence,
                    reason="matched employee disappeared or changed identity",
                ),
                "not_reactivated",
            )

        if locked_employee.employee_status == "active":
            repository.connection.commit()
            return ReactivationResult(resolution, "already_active")
        if locked_employee.employee_status != "inactive":
            repository.connection.commit()
            return ReactivationResult(resolution, "not_reactivated")

        if not repository.activate_employee(locked_employee.employee_id or resolution.employee_id):
            raise RuntimeError("inactive employee activation did not update a row")
        repository.record_activation_audit(
            locked_employee.employee_id or resolution.employee_id,
            actor_id,
            correlation_id,
        )
        repository.connection.commit()
        return ReactivationResult(resolution, "activated")
    except Exception:
        repository.connection.rollback()
        raise


class PostgresIdentityRepository:
    """DB-API-compatible PostgreSQL adapter for the existing schema."""

    _candidate_select = """
        SELECT p.person_id, e.employee_id, e.status
        FROM persons AS p
        LEFT JOIN employees AS e ON e.person_id = p.person_id
    """

    def __init__(self, connection: DbConnection):
        self.connection = connection

    def find_by_normalized_phone(self, normalized_phone: str) -> Sequence[IdentityCandidate]:
        return self._fetch(
            self._candidate_select
            + """
        LEFT JOIN person_phones AS pp ON pp.person_id = p.person_id
        WHERE p.phone_normalized = %s OR pp.normalized_value = %s
        """,
            (normalized_phone, normalized_phone),
        )

    def find_by_identifier(self, identifier_type: str, value: str) -> Sequence[IdentityCandidate]:
        if identifier_type == "EMPLOYEE_CODE":
            return self._fetch(
                self._candidate_select
                + """
        LEFT JOIN person_identifiers AS pi ON pi.person_id = p.person_id
        WHERE e.employee_code = %s
           OR (pi.identifier_type = %s AND pi.identifier_value = %s)
        """,
                (value, identifier_type, value),
            )
        return self._fetch(
            self._candidate_select
            + """
        JOIN person_identifiers AS pi ON pi.person_id = p.person_id
        WHERE pi.identifier_type = %s AND pi.identifier_value = %s
        """,
            (identifier_type, value),
        )

    def find_by_platform_id(
        self,
        platform: str,
        platform_user_id: str,
        source_account: str | None = None,
    ) -> Sequence[IdentityCandidate]:
        return self._fetch(
            self._candidate_select
                + """
        JOIN external_platform_ids AS epi ON epi.person_id = p.person_id
        WHERE epi.platform = %s
          AND epi.platform_user_id = %s
          AND epi.source_account = %s
        """,
            (platform, platform_user_id, source_account or "default"),
        )

    def lock_employee(self, employee_id: UUID) -> IdentityCandidate | None:
        rows = self._fetch(
            """
        SELECT p.person_id, e.employee_id, e.status
        FROM employees AS e
        JOIN persons AS p ON p.person_id = e.person_id
        WHERE e.employee_id = %s
        FOR UPDATE OF e
        """,
            (employee_id,),
        )
        return rows[0] if rows else None

    def activate_employee(self, employee_id: UUID) -> bool:
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """
                UPDATE employees
                SET status = 'active', updated_at = NOW()
                WHERE employee_id = %s AND status = 'inactive'
                RETURNING employee_id
                """,
                (employee_id,),
            )
            return cursor.fetchone() is not None
        finally:
            cursor.close()

    def record_activation_audit(
        self,
        employee_id: UUID,
        actor_id: UUID | None,
        correlation_id: str | None,
    ) -> None:
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO audit_log (
                    entity_type, entity_id, action, actor_id,
                    before_state, after_state, correlation_id
                )
                VALUES ('employee', %s, 'UPDATE', %s, %s::jsonb, %s::jsonb, %s)
                """,
                (
                    employee_id,
                    actor_id,
                    json.dumps({"status": "inactive"}),
                    json.dumps({"status": "active"}),
                    correlation_id,
                ),
            )
        finally:
            cursor.close()

    def _fetch(
        self,
        operation: str,
        parameters: Sequence[object],
    ) -> tuple[IdentityCandidate, ...]:
        cursor = self.connection.cursor()
        try:
            cursor.execute(operation, parameters)
            return tuple(_candidate_from_row(row) for row in cursor.fetchall())
        finally:
            cursor.close()


def _is_supported_normalized_phone(value: str) -> bool:
    return len(value) == 11 and value.startswith("0") and value.isdigit()


def _candidate_from_row(row: Sequence[object]) -> IdentityCandidate:
    person_id, employee_id, employee_status = row
    return IdentityCandidate(
        person_id=UUID(str(person_id)),
        employee_id=UUID(str(employee_id)) if employee_id is not None else None,
        employee_status=str(employee_status) if employee_status is not None else None,
    )


def _unique_candidates(candidates: Sequence[IdentityCandidate]) -> tuple[IdentityCandidate, ...]:
    unique: dict[tuple[UUID, UUID | None, str | None], IdentityCandidate] = {}
    for candidate in candidates:
        key = (candidate.person_id, candidate.employee_id, candidate.employee_status)
        unique[key] = candidate
    return tuple(unique.values())


def _ambiguous(
    normalized_phone: str | None,
    evidence_sets: Sequence[tuple[str, Sequence[IdentityCandidate]]],
    candidates: Sequence[IdentityCandidate],
    reason: str,
) -> IdentityResolution:
    return IdentityResolution(
        status="ambiguous",
        normalized_phone=normalized_phone,
        evidence=tuple(name for name, _ in evidence_sets),
        candidates=tuple(candidates),
        reason=reason,
    )
