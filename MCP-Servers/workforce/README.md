# Workforce MCP

Workforce owns the authoritative business Employee ID: the designated normalized Bangladeshi mobile (final 11 digits beginning with `0`). Internal Person/employee-record UUIDs remain technical keys. Contact numbers may support identity resolution but do not mutate Employee ID; only an authorized `Edit Employee ID` operation may change it.

Purpose: own employee lifecycle, operational workforce history, attendance, and assignments. Business owner: Workforce/Operations. It excludes applicant intake before joining, financial ledger/payout decisions, authentication, and generic message storage.

Dependencies: shared identity, Recruitment handoff, Finance employee reference, Operations assignment context, audit/events. WRITE requires trusted actor and idempotency.
