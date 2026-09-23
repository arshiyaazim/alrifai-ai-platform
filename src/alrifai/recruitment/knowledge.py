"""Fail-closed recruitment knowledge contract.

This module is a read-only knowledge boundary for C7/C8 integration.  It is
not a dispatcher, an applicant store, or a reply template engine.  A caller
must supply the current approved policy through a later domain read before an
unresolved fact can become an answer.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Iterable, Mapping


class RecruitmentSourceClass(StrEnum):
    CURRENT_APPROVED = "current_approved"
    HISTORICAL_REFERENCE = "historical_reference"
    DRAFT = "draft"
    CONFLICTING = "conflicting"
    UNVERIFIED = "unverified"


class RecruitmentFactStatus(StrEnum):
    VERIFIED_FACT = "verified_fact"
    APPROVED_CONDITIONAL_POLICY = "approved_conditional_policy"
    MISSING_FACT = "missing_fact"
    CONFLICTING_FACT = "conflicting_fact"
    HISTORICAL_FACT = "historical_fact"
    OWNER_CONFIRMATION_REQUIRED = "owner_confirmation_required"


@dataclass(frozen=True, slots=True)
class SourceReference:
    """Traceable evidence for a fact; never a claim of runtime authority."""

    path: str
    location: str
    source_class: RecruitmentSourceClass

    def __post_init__(self) -> None:
        if not self.path.strip() or not self.location.strip():
            raise ValueError("source path and location are required")


@dataclass(frozen=True, slots=True)
class RecruitmentFact:
    """One protected fact or an explicit unresolved knowledge state.

    ``value`` is intentionally absent for unresolved states.  The contract
    stores a semantic safe action rather than natural-language scripts so
    Bangla, Banglish, English, and mixed-language replies remain a later
    conversation-layer concern.
    """

    key: str
    status: RecruitmentFactStatus
    value: Any = None
    sources: tuple[SourceReference, ...] = ()
    effective_date: str | None = None
    conflicts: tuple[str, ...] = ()
    safe_action: str = "request_authorized_domain_read"

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("fact key is required")
        if not self.sources:
            raise ValueError("at least one source reference is required")
        if any(not isinstance(source, SourceReference) for source in self.sources):
            raise TypeError("sources must contain SourceReference values")
        if self.status in {
            RecruitmentFactStatus.MISSING_FACT,
            RecruitmentFactStatus.CONFLICTING_FACT,
            RecruitmentFactStatus.HISTORICAL_FACT,
            RecruitmentFactStatus.OWNER_CONFIRMATION_REQUIRED,
        } and self.value is not None:
            raise ValueError("unresolved facts must not carry an answer value")
        if self.status is RecruitmentFactStatus.CONFLICTING_FACT and not self.conflicts:
            raise ValueError("conflicting facts require conflict evidence")
        if self.status is RecruitmentFactStatus.OWNER_CONFIRMATION_REQUIRED and self.safe_action != "owner_confirmation_required":
            raise ValueError("owner-confirmation facts must fail closed to owner confirmation")

    @property
    def answerable(self) -> bool:
        return self.status in {
            RecruitmentFactStatus.VERIFIED_FACT,
            RecruitmentFactStatus.APPROVED_CONDITIONAL_POLICY,
        } and self.value is not None


class RecruitmentKnowledgeContract:
    """Immutable lookup boundary that never promotes unresolved evidence."""

    def __init__(self, facts: Iterable[RecruitmentFact]):
        indexed = tuple(facts)
        keys = [fact.key for fact in indexed]
        if len(keys) != len(set(keys)):
            raise ValueError("recruitment fact keys must be unique")
        self._facts = indexed
        self._by_key = {fact.key: fact for fact in indexed}

    @property
    def facts(self) -> tuple[RecruitmentFact, ...]:
        return self._facts

    def get(self, key: str) -> RecruitmentFact | None:
        return self._by_key.get(key)

    def answerable_value(self, key: str) -> Any | None:
        """Return only a current approved value; unresolved means ``None``."""

        fact = self.get(key)
        return fact.value if fact is not None and fact.answerable else None

    def safe_action(self, key: str) -> str:
        fact = self.get(key)
        return fact.safe_action if fact is not None else "request_authorized_domain_read"

    def as_mapping(self) -> Mapping[str, RecruitmentFact]:
        return self._by_key.copy()


_CURRENT_SPEC = SourceReference(
    "MCP-Servers/recruitment/FINAL_IMPLEMENTATION_SPEC.md",
    "§§ 2, 3, 4, 12.3, 12.5, 14, 16",
    RecruitmentSourceClass.CURRENT_APPROVED,
)
_CURRENT_README = SourceReference(
    "MCP-Servers/recruitment/README.md",
    "Purpose, permissions, lifecycle, and recruitment invariants",
    RecruitmentSourceClass.CURRENT_APPROVED,
)
_CURRENT_RULES = SourceReference(
    "docs/rules/BUSINESS_RULES.md",
    "RECRUITMENT-JOIN-001; WORKFLOW-APPLICATION-001; WORKFLOW-JOINING-001",
    RecruitmentSourceClass.CURRENT_APPROVED,
)
_LEGACY_SOURCE = SourceReference(
    "/home/azim/core/resources/ops/recruitment_source_of_truth.txt",
    "§§ অফিস তথ্য, বর্তমানে নিয়োগ চলমান পদ, সাধারণ যোগ্যতা, বেতন, ফি",
    RecruitmentSourceClass.HISTORICAL_REFERENCE,
)
_LEGACY_SALARY = SourceReference(
    "/home/azim/core/resources/ops/salary_structure.txt",
    "last-verified 2026-05-29; §§ 17-67",
    RecruitmentSourceClass.HISTORICAL_REFERENCE,
)
_LEGACY_FEE = SourceReference(
    "/home/azim/core/resources/ops/joining_fee_policy.txt",
    "last-verified 2026-05-29; §§ 9-65",
    RecruitmentSourceClass.HISTORICAL_REFERENCE,
)
_CURRENT_SPEC_CONFLICT = SourceReference(
    "MCP-Servers/recruitment/FINAL_IMPLEMENTATION_SPEC.md",
    "§ 12.5 and § 16; no approved concrete policy records found",
    RecruitmentSourceClass.CURRENT_APPROVED,
)


def _fact(
    key: str,
    status: RecruitmentFactStatus,
    *,
    value: Any = None,
    sources: tuple[SourceReference, ...] = (_CURRENT_SPEC,),
    conflicts: tuple[str, ...] = (),
    safe_action: str = "request_authorized_domain_read",
) -> RecruitmentFact:
    return RecruitmentFact(
        key=key,
        status=status,
        value=value,
        sources=sources,
        conflicts=conflicts,
        safe_action=safe_action,
    )


def build_current_recruitment_contract() -> RecruitmentKnowledgeContract:
    """Build the bounded register available before the C8 domain read service.

    The approved entries are semantic lifecycle/grounding rules, not
    operational job facts.  Concrete candidate-facing values stay unresolved
    until a current approved policy source is provided.
    """

    approved = RecruitmentFactStatus.APPROVED_CONDITIONAL_POLICY
    missing = RecruitmentFactStatus.MISSING_FACT
    owner = RecruitmentFactStatus.OWNER_CONFIRMATION_REQUIRED
    historical = RecruitmentFactStatus.HISTORICAL_FACT
    conflicting = RecruitmentFactStatus.CONFLICTING_FACT
    return RecruitmentKnowledgeContract(
        (
            _fact(
                "recruitment.model",
                approved,
                value="year_round_role_based",
                sources=(_CURRENT_SPEC, _CURRENT_README),
            ),
            _fact(
                "recruitment.vacancy_requirement",
                approved,
                value="vacancy_optional_for_role_based_interest_or_application",
                sources=(_CURRENT_SPEC, _CURRENT_README),
            ),
            _fact(
                "recruitment.application_lifecycle",
                approved,
                value=("new", "screening", "interviewing", "offered", "hired", "rejected", "withdrawn"),
                sources=(_CURRENT_SPEC, _CURRENT_RULES),
            ),
            _fact(
                "recruitment.document_intake",
                approved,
                value="received_or_linked_metadata_is_not_formal_verification",
                sources=(_CURRENT_SPEC, _CURRENT_README),
            ),
            _fact(
                "recruitment.application_process",
                approved,
                value="identity_resolution_then_role_validation_then_reviewed_application",
                sources=(_CURRENT_SPEC, _CURRENT_RULES),
            ),
            _fact(
                "recruitment.selection_authority",
                approved,
                value="staff_controlled;_candidate_claims_do_not_establish_selection_or_joining",
                sources=(_CURRENT_SPEC, _CURRENT_RULES),
            ),
            _fact(
                "recruitment.brand",
                owner,
                sources=(_CURRENT_SPEC_CONFLICT,),
                safe_action="owner_confirmation_required",
            ),
            _fact(
                "recruitment.office_address",
                owner,
                sources=(
                    _CURRENT_SPEC_CONFLICT,
                    SourceReference(
                        "MCP-Servers/recruitment/FINAL_IMPLEMENTATION_SPEC.md",
                        "§ 12.5; AK Khan Mor, Pahartali, Chattogram vs AK Khan Mor, Victoria No. 1 Gate",
                        RecruitmentSourceClass.CONFLICTING,
                    ),
                    _LEGACY_SOURCE,
                ),
                conflicts=("AK Khan Mor, Pahartali, Chattogram", "AK Khan Mor, Victoria No. 1 Gate"),
                safe_action="owner_confirmation_required",
            ),
            _fact(
                "recruitment.office_hours_and_friday",
                missing,
                sources=(_CURRENT_SPEC_CONFLICT, _LEGACY_SOURCE),
            ),
            _fact(
                "recruitment.available_roles",
                missing,
                sources=(_CURRENT_SPEC_CONFLICT, _LEGACY_SOURCE),
            ),
            _fact(
                "recruitment.current_vacancies",
                missing,
                sources=(_CURRENT_SPEC_CONFLICT, _LEGACY_SOURCE),
            ),
            _fact(
                "recruitment.role_responsibilities",
                missing,
                sources=(_CURRENT_SPEC_CONFLICT, _LEGACY_SOURCE),
            ),
            _fact(
                "recruitment.eligibility",
                missing,
                sources=(_CURRENT_SPEC_CONFLICT, _LEGACY_SOURCE),
            ),
            _fact(
                "recruitment.required_documents",
                missing,
                sources=(_CURRENT_SPEC_CONFLICT, _CURRENT_SPEC),
            ),
            _fact(
                "recruitment.interview_or_immediate_joining",
                missing,
                sources=(_CURRENT_SPEC_CONFLICT, _CURRENT_SPEC),
            ),
            _fact(
                "recruitment.duty_hours_and_weekly_duty",
                missing,
                sources=(_CURRENT_SPEC_CONFLICT, _LEGACY_SOURCE),
            ),
            _fact(
                "recruitment.overtime_and_leave",
                missing,
                sources=(_CURRENT_SPEC_CONFLICT,),
            ),
            _fact(
                "recruitment.salary_by_role",
                missing,
                sources=(_CURRENT_SPEC_CONFLICT, _LEGACY_SOURCE, _LEGACY_SALARY),
            ),
            _fact(
                "recruitment.joining_salary",
                missing,
                sources=(_CURRENT_SPEC_CONFLICT, _LEGACY_SOURCE, _LEGACY_SALARY),
            ),
            _fact(
                "recruitment.accommodation_and_food",
                missing,
                sources=(_CURRENT_SPEC_CONFLICT, _LEGACY_SALARY),
            ),
            _fact(
                "recruitment.joining_charges_and_deposits",
                conflicting,
                sources=(_CURRENT_SPEC_CONFLICT, _LEGACY_SOURCE, _LEGACY_FEE),
                conflicts=("legacy says a conditional fee exists", "legacy seed replies say no fee or deposit"),
                safe_action="owner_confirmation_required",
            ),
            _fact(
                "recruitment.authorized_contact_details",
                missing,
                sources=(_CURRENT_SPEC_CONFLICT, _LEGACY_SOURCE),
            ),
            _fact(
                "legacy.recruitment_values",
                historical,
                sources=(_LEGACY_SOURCE, _LEGACY_SALARY, _LEGACY_FEE),
                safe_action="historical_only_do_not_answer",
            ),
        )
    )
