# Recruitment Legacy Mapping

Evidence: `modules/recruitment_flow`, `modules/recruitment_ai`, `modules/message_router`; live `wbom_candidates` (741 rows), `fazle_recruitment_sessions` (759), `wbom_candidate_conversations`, and `wbom_job_applications` (0 rows) (`VERIFIED_LIVE`/`VERIFIED_SOURCE`). Candidate fields include phone, name, preference, experience, availability, funnel stage, collection step, score, recruiter, follow-up, source, post-intake state, and linked employee.

Gap: message and form paths diverge in candidate stage/application persistence; the populated candidate/session path is not the empty application table. Import requires provenance, identity review, and explicit handling of the `linked_employee_id` conversion handoff.

Canonical target: shared `persons` + `applicants` with ApplicantService-owned writes, shared identity resolution, audit/business events, and Workforce-owned employee handoff. Recruitment MCP exposes the service; it does not write legacy tables or create a duplicate recruitment database.

Owner policy reconciliation: recruitment is year-round and Role-based; an absent Vacancy does not block a new Application. Rejected/withdrawn legacy applications remain terminal history, while repeat attempts reuse the Person/Applicant and create a new Application. Candidate-provided document references remain provenance/intake records and are not formal identity verification; Workforce owns employee-document verification after handoff.
The legacy `linked_employee_id` value must not be assumed to define the business Employee identity. Future mapping resolves the designated normalized Bangladesh mobile as authoritative Employee ID, preserves any physical UUID as an internal technical reference, validates uniqueness, and records provenance during Recruitment → Workforce handoff.
