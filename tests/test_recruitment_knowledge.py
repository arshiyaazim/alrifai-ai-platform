from alrifai.recruitment.knowledge import (
    RecruitmentFactStatus,
    RecruitmentSourceClass,
    build_current_recruitment_contract,
)


def test_approved_contract_contains_only_source_grounded_process_rules():
    contract = build_current_recruitment_contract()

    assert contract.answerable_value("recruitment.model") == "year_round_role_based"
    assert contract.answerable_value("recruitment.vacancy_requirement") == (
        "vacancy_optional_for_role_based_interest_or_application"
    )
    assert contract.answerable_value("recruitment.application_lifecycle") == (
        "new", "screening", "interviewing", "offered", "hired", "rejected", "withdrawn"
    )
    assert contract.get("recruitment.application_process").sources[0].source_class is RecruitmentSourceClass.CURRENT_APPROVED


def test_unresolved_protected_facts_never_expose_values():
    contract = build_current_recruitment_contract()
    protected = (
        "recruitment.brand",
        "recruitment.office_address",
        "recruitment.office_hours_and_friday",
        "recruitment.available_roles",
        "recruitment.current_vacancies",
        "recruitment.role_responsibilities",
        "recruitment.eligibility",
        "recruitment.required_documents",
        "recruitment.interview_or_immediate_joining",
        "recruitment.duty_hours_and_weekly_duty",
        "recruitment.overtime_and_leave",
        "recruitment.salary_by_role",
        "recruitment.joining_salary",
        "recruitment.accommodation_and_food",
        "recruitment.joining_charges_and_deposits",
        "recruitment.authorized_contact_details",
    )

    for key in protected:
        fact = contract.get(key)
        assert fact is not None
        assert not fact.answerable
        assert contract.answerable_value(key) is None
        assert contract.safe_action(key) in {
            "request_authorized_domain_read",
            "owner_confirmation_required",
        }


def test_address_and_fee_conflicts_remain_explicit_and_fail_closed():
    contract = build_current_recruitment_contract()
    address = contract.get("recruitment.office_address")
    fee = contract.get("recruitment.joining_charges_and_deposits")

    assert address.status is RecruitmentFactStatus.OWNER_CONFIRMATION_REQUIRED
    assert address.conflicts == (
        "AK Khan Mor, Pahartali, Chattogram",
        "AK Khan Mor, Victoria No. 1 Gate",
    )
    assert address.safe_action == "owner_confirmation_required"
    assert fee.status is RecruitmentFactStatus.CONFLICTING_FACT
    assert fee.safe_action == "owner_confirmation_required"


def test_legacy_evidence_is_traceable_but_never_current_answer_authority():
    contract = build_current_recruitment_contract()
    historical = contract.get("legacy.recruitment_values")

    assert historical.status is RecruitmentFactStatus.HISTORICAL_FACT
    assert all(source.source_class is RecruitmentSourceClass.HISTORICAL_REFERENCE for source in historical.sources)
    assert contract.answerable_value("legacy.recruitment_values") is None
