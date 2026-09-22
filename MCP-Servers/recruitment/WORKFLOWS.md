# Recruitment Workflows

The final workflow and contract specification is [`FINAL_IMPLEMENTATION_SPEC.md`](FINAL_IMPLEMENTATION_SPEC.md).

Message: recruitment conversation → canonical message → identity resolution → extract role/application fields → draft applicant/application → Recruitment validation → approved persistence → status reply.

Form: authenticated application form → validation → same Recruitment service → event/audit → response.

Statuses belong to an Application and preserve the canonical `new → screening → interviewing → offered → hired` lifecycle, with `rejected` and `withdrawn` terminal outcomes. `joining_pending` is a reviewed Workforce handoff substate. Recruitment is year-round: Role-based interest/application does not require an open Vacancy; an explicitly selected closed campaign/opening is the only narrow `VACANCY_CLOSED` case. A later attempt reuses the canonical Person/Applicant and creates a new Application; terminal history is never reopened. Ambiguity creates review, never an automatic person merge. Applicant conversion reuses the canonical person and calls Workforce/EmployeeService; it does not create payroll records directly.

The frontend calls the same canonical Recruitment service directly rather than routing internal traffic through MCP. Conversations & AI passes trusted identity context, source/message IDs, extracted fields, confidence, evidence, correlation, and idempotency; Recruitment validates all of it. Candidate CV/NID/photo/PDF intake is accepted as metadata/reference and provenance without asserting formal verification; Workforce owns formal employee-document verification after handoff.
Employee handoff: the designated normalized Bangladesh mobile becomes the authoritative Employee ID only after Workforce uniqueness validation. A contact number discovered in conversation is not an Employee-ID edit; changes require the separate authorized `Edit Employee ID` workflow.
