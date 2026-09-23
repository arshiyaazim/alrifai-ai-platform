# Recruitment MCP

Primary implementation handoff: [`FINAL_IMPLEMENTATION_SPEC.md`](FINAL_IMPLEMENTATION_SPEC.md).

Purpose: expose applicant and recruitment domain capabilities over canonical AL-RIFAI services. Business owner: Recruitment/HR. It excludes employee master ownership after joining, authentication, generic conversations, and payroll.

Dependencies: shared identity, audit/events, Conversations & AI for extracted evidence, Workforce for approved conversion. Permissions are READ/DRAFT/VALIDATE/WRITE; hiring/approval is ADMIN and fail-closed until trusted authorization exists. The internal AL-RIFAI frontend calls the canonical Recruitment API/domain service directly; MCP is an additional adapter for agents and Conversations & AI.

Recruitment is year-round: a valid canonical Role supports interest and application without an open Vacancy. Vacancy/Opening is optional campaign, location, client/program, priority, or headcount context. The final lifecycle is `Person → Applicant profile → Application for Role → new → screening → interviewing → offered → joining_pending → hired`, with `rejected` and `withdrawn` terminal states per Application. A later attempt reuses the Person/Applicant and creates a new Application. Applicant document intake records candidate-provided references without formal verification; Workforce owns formal employee-document verification after handoff.
Business Employee ID rule: the authoritative Employee ID is the designated normalized Bangladeshi mobile number (final 11 digits beginning with `0`). Person UUIDs and physical employee-record UUIDs are internal technical keys only. Contact/messaging numbers may differ and never change Employee ID automatically; only an authorized `Edit Employee ID` workflow may do so.
