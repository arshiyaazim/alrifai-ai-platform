from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest

from src.alrifai.identity.identity_resolver import (
    IdentityCandidate,
    IdentityObservation,
    IdentityResolution,
    ReactivationResult,
    StableIdentifier,
    resolve_and_reactivate,
    resolve_identity,
)


PERSON_A = uuid4()
PERSON_B = uuid4()
EMPLOYEE_A = uuid4()
ACTOR = uuid4()


def candidate(
    person_id: UUID = PERSON_A,
    employee_id: UUID | None = EMPLOYEE_A,
    status: str | None = "inactive",
) -> IdentityCandidate:
    return IdentityCandidate(person_id, employee_id, status)


@dataclass
class FakeConnection:
    commits: int = 0
    rollbacks: int = 0

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1


class FakeRepository:
    def __init__(self):
        self.connection = FakeConnection()
        self.phones: dict[str, tuple[IdentityCandidate, ...]] = {}
        self.identifiers: dict[tuple[str, str], tuple[IdentityCandidate, ...]] = {}
        self.platforms: dict[tuple[str, str], tuple[IdentityCandidate, ...]] = {}
        self.locked: IdentityCandidate | None = None
        self.activated = 0
        self.audits = 0
        self.fail_audit = False

    def find_by_normalized_phone(self, normalized_phone: str):
        return self.phones.get(normalized_phone, ())

    def find_by_identifier(self, identifier_type: str, value: str):
        return self.identifiers.get((identifier_type, value), ())

    def find_by_platform_id(self, platform: str, platform_user_id: str, source_account=None):
        return self.platforms.get((platform, platform_user_id), ())

    def lock_employee(self, employee_id: UUID):
        return self.locked

    def activate_employee(self, employee_id: UUID) -> bool:
        self.activated += 1
        return True

    def record_activation_audit(self, employee_id: UUID, actor_id, correlation_id):
        if self.fail_audit:
            raise RuntimeError("audit failure")
        self.audits += 1


def test_unique_employee_code_match():
    repo = FakeRepository()
    repo.identifiers["EMPLOYEE_CODE", "E-001"] = (candidate(),)

    result = resolve_identity(
        repo,
        IdentityObservation(stable_identifiers=(StableIdentifier("EMPLOYEE_CODE", "E-001"),)),
    )

    assert result.status == "matched"
    assert result.employee_id == EMPLOYEE_A


def test_unique_typed_platform_id_match():
    repo = FakeRepository()
    repo.platforms["WHATSAPP", "wa-1"] = (candidate(),)

    result = resolve_identity(repo, IdentityObservation(platform="WHATSAPP", platform_user_id="wa-1"))

    assert result.status == "matched"
    assert result.person_id == PERSON_A


def test_unique_normalized_phone_match():
    repo = FakeRepository()
    repo.phones["01712345678"] = (candidate(),)

    result = resolve_identity(repo, IdentityObservation(phone="017-1234-5678"))

    assert result.status == "matched"
    assert result.normalized_phone == "01712345678"


def test_shared_phone_is_ambiguous():
    repo = FakeRepository()
    repo.phones["01712345678"] = (candidate(), candidate(PERSON_B, None, None))

    result = resolve_identity(repo, IdentityObservation(phone="01712345678"))

    assert result.status == "ambiguous"
    assert result.person_id is None


def test_unsupported_phone_is_invalid():
    result = resolve_identity(FakeRepository(), IdentityObservation(phone="not-a-phone"))

    assert result.status == "invalid"


def test_name_only_does_not_auto_match():
    result = resolve_identity(FakeRepository(), IdentityObservation(name="Rahim"))

    assert result.status == "unmatched"
    assert "name_ignored_for_deterministic_matching" in result.evidence


def test_conflicting_stable_identifiers_are_ambiguous():
    repo = FakeRepository()
    repo.identifiers["EMPLOYEE_CODE", "E-001"] = (candidate(),)
    repo.platforms["WHATSAPP", "wa-2"] = (candidate(PERSON_B, None, None),)

    result = resolve_identity(
        repo,
        IdentityObservation(
            employee_code="E-001",
            platform="WHATSAPP",
            platform_user_id="wa-2",
        ),
    )

    assert result.status == "ambiguous"


def test_missing_phone_does_not_invalidate_stable_identifier():
    repo = FakeRepository()
    repo.identifiers["EMPLOYEE_CODE", "E-001"] = (candidate(),)

    result = resolve_identity(
        repo,
        IdentityObservation(employee_code="E-001"),
    )

    assert result.status == "matched"


def test_inactive_employee_is_activated_and_audited():
    repo = FakeRepository()
    repo.phones["01712345678"] = (candidate(),)
    repo.locked = candidate()

    result = resolve_and_reactivate(
        repo,
        IdentityObservation(phone="01712345678"),
        actor_id=ACTOR,
        correlation_id="corr-1",
    )

    assert result == ReactivationResult(result.resolution, "activated")
    assert repo.activated == 1
    assert repo.audits == 1
    assert repo.connection.commits == 1


def test_already_active_employee_is_not_updated_or_audited():
    repo = FakeRepository()
    repo.phones["01712345678"] = (candidate(status="active"),)
    repo.locked = candidate(status="active")

    result = resolve_and_reactivate(repo, IdentityObservation(phone="01712345678"))

    assert result.status == "already_active"
    assert repo.activated == 0
    assert repo.audits == 0


@pytest.mark.parametrize(
    "observation, status",
    [
        (IdentityObservation(phone="not-a-phone"), "invalid"),
        (IdentityObservation(name="Unknown"), "unmatched"),
    ],
)
def test_non_match_does_not_activate(observation, status):
    repo = FakeRepository()

    result = resolve_and_reactivate(repo, observation)

    assert result.resolution.status == status
    assert result.status == "not_reactivated"
    assert repo.activated == 0
    assert repo.audits == 0


def test_ambiguous_match_does_not_activate():
    repo = FakeRepository()
    repo.phones["01712345678"] = (candidate(), candidate(PERSON_B, None, None))

    result = resolve_and_reactivate(repo, IdentityObservation(phone="01712345678"))

    assert result.resolution.status == "ambiguous"
    assert result.status == "not_reactivated"
    assert repo.activated == 0


def test_reactivation_is_idempotent_after_employee_becomes_active():
    repo = FakeRepository()
    repo.phones["01712345678"] = (candidate(),)
    repo.locked = candidate()
    first = resolve_and_reactivate(repo, IdentityObservation(phone="01712345678"))

    repo.locked = candidate(status="active")
    second = resolve_and_reactivate(repo, IdentityObservation(phone="01712345678"))

    assert first.status == "activated"
    assert second.status == "already_active"
    assert repo.activated == 1
    assert repo.audits == 1


def test_audit_failure_rolls_back_activation():
    repo = FakeRepository()
    repo.phones["01712345678"] = (candidate(),)
    repo.locked = candidate()
    repo.fail_audit = True

    with pytest.raises(RuntimeError, match="audit failure"):
        resolve_and_reactivate(repo, IdentityObservation(phone="01712345678"))

    assert repo.connection.commits == 0
    assert repo.connection.rollbacks == 1
