# Domain Ownership

| Future MCP server | Owns | Explicitly does not own | Primary legacy evidence |
|---|---|---|---|
| Recruitment | Interested persons, applicants, roles, applications, screening, joining transition | Employee master after conversion; authentication; generic messaging storage | `modules/recruitment_flow`, `modules/recruitment_ai`, `wbom_candidates`, `wbom_job_applications` (`VERIFIED_SOURCE`) |
| Workforce | Employee lifecycle, operational assignments, attendance, non-financial workforce history | Applicant lifecycle before joining; payout/ledger accounting; authentication | `modules/admin_employees`, `modules/attendance`, `wbom_employees`, `fpe_employees`, `ops_attendance` (`VERIFIED_SOURCE`) |
| Finance & Payroll | Payroll calculation, approval, cash/payment workflow, financial employee ledger, billing settlement | Identity authority; operational roster state; AI interpretation | `modules/fazle_payroll_engine`, `modules/payment`, `modules/client_billing`, `fpe_*`, `wbom_cash_transactions` (`VERIFIED_SOURCE`) |
| Conversations & AI | Canonical messages, threads, channel adapters, extraction, classification, Hermes dispatch, outbound delivery | Domain mutation policy; direct financial/HR/operations writes | `bridge_poller`, `message_router`, `hermes_dispatch`, `conversation_canonical`, `wbom_whatsapp_messages`, `fazle_messages` (`VERIFIED_SOURCE`) |
| Operations & Clients | Clients, contacts in operational context, vessels, escort programs, rosters, assignments, release/completion, service history | Financial settlement; canonical authentication; generic AI reasoning | `escort_lifecycle`, `escort_roster`, `client_billing`, `escort_roster_entries`, `ops_programs`, `wbom_clients` (`VERIFIED_SOURCE`) |
| Platform / Admin | Approved cross-domain reports, workflow orchestration, approvals, audit/provenance views, administrative aggregation | Owning domain records, unrestricted SQL, authentication redesign, direct legacy writes | `rbac`, `authority_lanes`, `business_action_execution`, `draft_approval`, `fazle_audit_log` (`VERIFIED_SOURCE`) |

Identity and audit are shared AL-RIFAI capabilities. They are dependencies of every server rather than a seventh business server.

The immutable `person_id` is the internal Person identity. Workforce owns the authoritative business Employee ID: the designated normalized Bangladeshi mobile. Contact numbers and platform identities support resolution but cannot mutate Employee ID; only the authorized Employee-ID edit workflow can do so.
