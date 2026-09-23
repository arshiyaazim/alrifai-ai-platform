# Recruitment knowledge contract

Status: bounded pre-C8 contract; no domain dispatch, persistence, or outbound behavior.

The current repository contains an immutable, source-grounded register in
`src/alrifai/recruitment/knowledge.py`. It is deliberately language-neutral:
Bangla, Banglish, English, and mixed-language conversation remain input and
response-layer concerns. The contract returns a value only for a
`VERIFIED_FACT` or `APPROVED_CONDITIONAL_POLICY`. Missing, conflicting,
historical, and owner-confirmation-required facts return no value and require
an authorized domain read or human confirmation.

## Source inventory

| Source | Classification | Scope of use |
| --- | --- | --- |
| `MCP-Servers/recruitment/FINAL_IMPLEMENTATION_SPEC.md` | `CURRENT_APPROVED` for lifecycle/grounding rules; unimplemented service portions remain draft | Year-round role-based intake, optional Vacancy, lifecycle, document-intake distinction, fail-closed knowledge policy |
| `MCP-Servers/recruitment/README.md` | `CURRENT_APPROVED` for domain boundaries | Recruitment ownership, permissions, lifecycle and no-duplicate-domain rules |
| `docs/rules/BUSINESS_RULES.md` | `CURRENT_APPROVED` for cross-domain invariants | Identity resolution before joining and application lifecycle |
| `MCP-Servers/recruitment/WORKFLOWS.md`, `TOOLS_AND_RESOURCES.md`, `LEGACY_MAPPING.md` | `DRAFT`/`HISTORICAL_REFERENCE` design and migration evidence | Proposed service boundaries and legacy provenance only; not operational policy values |
| Concrete current role/policy records and a live approved knowledge service | `UNVERIFIED` | No such source was found in the current repository; absence is not permission to infer values |
| `/home/azim/core/resources/ops/recruitment_source_of_truth.txt` | `HISTORICAL_REFERENCE` | Legacy candidate-facing values; not current authority and conflicts with other legacy artifacts |
| `/home/azim/core/resources/ops/salary_structure.txt` | `HISTORICAL_REFERENCE` | Legacy salary/package values; no current AL-RIFA'I approval in this repository |
| `/home/azim/core/resources/ops/joining_fee_policy.txt` | `HISTORICAL_REFERENCE` | Legacy fee values; conflicts with legacy no-fee seed replies |
| `/home/azim/core/scripts/seed_recruitment_kb.sql` | `CONFLICTING` historical seed | Legacy canned replies conflict with other legacy policy files; never a current source |
| `/home/azim/core/resources/ops/food_expense_policy.txt` | `HISTORICAL_REFERENCE` | Employee/escort operational material, explicitly not candidate-reply authority |
| `/home/azim/core/RECRUITMENT_CONVERSATION_AUDIT_VERIFIED_2026-08-22_TO_2026-08-23.md` | `HISTORICAL_REFERENCE` | Audit observations, not a policy source |

Legacy files were read only. They were not copied into the current contract as
candidate-facing facts and `/home/azim/core` was not modified.

## Protected fact register

Approved now: recruitment is year-round and role-based; a Vacancy is optional
for ordinary role interest/application; the documented application lifecycle
is `new → screening → interviewing → offered → hired` with `rejected` and
`withdrawn` terminal paths; candidate document intake is metadata/provenance,
not formal verification; candidate claims do not establish selection or
joining; and joining requires authorized identity resolution and lifecycle
control.

Unresolved and therefore not answerable: brand, office hours/Friday policy,
available roles, current vacancies, role responsibilities, eligibility,
role-specific document requirements, interview/immediate-joining policy, duty
hours/weekly duty, overtime/leave, all salary/joining salary, accommodation or
food, and authorized contact details.

The office address is `OWNER_CONFIRMATION_REQUIRED`. The evidence contains
both “AK Khan Mor, Pahartali, Chattogram” and “AK Khan Mor, Victoria No. 1
Gate”; the contract does not select either string. Joining charges/deposits are
`CONFLICTING_FACT` because legacy fee policy and legacy no-fee seed replies
disagree. Neither may be turned into a response without current approved
policy or owner confirmation.

No C7 interpreter result may invent these values. A later C8 domain read may
replace an unresolved register entry only with current approved, versioned,
provenanced policy evidence.
