# Legacy-to-AL-RIFAI Data Ownership Matrix

The legacy table names below are fresh live/source evidence from `/home/azim/core` and `ai-postgres`. They are migration/import inputs, not future AL-RIFAI runtime dependencies. Counts and live-state qualifications are detailed in [`FAZLE_CORE_AUDIT.md`](FAZLE_CORE_AUDIT.md).

| Fazle-Core table/group | Current purpose | Current writers/readers | Future canonical domain | Proposed MCP owner | Migration relevance |
|---|---|---|---|---|---|
| `wbom_contacts`, `fazle_unified_contacts`, `fazle_contact_roles`, aliases | Contact/identity and roles | Identity brain, routers, admin flows | `persons`, identifiers, phones, aliases | Shared identity + Platform/Admin | Merge, deduplicate, review ambiguity |
| `wbom_candidates` (741), `wbom_job_applications` (0), employee requests | Recruitment funnel | Recruitment flow, message router, forms | `applicants`, applications, recruitment events | Recruitment | Preserve history and source provenance; do not assume the empty application table is authoritative |
| `wbom_employees` (250), `fpe_employees` (593), aliases/links | Operational and payroll employee variants | Admin employee, FPE, identity resolution | `employees` linked to canonical persons, with designated normalized-mobile Employee ID and historical IDs | Workforce | Reconcile duplicate employees and Employee IDs before import; preserve technical keys and phone provenance |
| `ops_attendance`, `wbom_attendance` | Attendance and drafts | Attendance routes/router | Workforce attendance records | Workforce | Preserve approval and source metadata |
| `fpe_employee_ledger` (747), `fpe_cash_transactions` (4,901), `wbom_cash_transactions` (1,428) | Payroll, ledger, cash | FPE/payment/admin routes | Finance/payroll ledger and transactions | Finance & Payroll | Reconcile overlapping transaction identities, approval/reversal state, and idempotency |
| `wbom_payroll_runs`, salary records, approval log | Payroll periods and approvals | FPE/payroll routes | Payroll runs, approvals | Finance & Payroll | Import period/status/audit history |
| `wbom_escort_programs` (347), `escort_roster_entries` (360), change requests, slip extractions, `ops_programs` | Escort programs and roster | Escort modules, message router, forms | Operations programs, assignments, release | Operations & Clients | Preserve lifecycle evidence; do not infer completion |
| `wbom_clients`, `fazle_clients`, billing profiles/records | Client and billing context | Client/billing routes, social/contact flows | Clients, vessels, operational relationships; financial billing | Operations & Clients + Finance | Split operational vs financial ownership |
| `wbom_whatsapp_messages` (32,436), bridge/processed tables | Raw channel messages | Bridge poller, Meta/social handlers, router | Canonical messages/media/delivery | Conversations & AI | Import external IDs, direction, actor/provenance, hashes, raw evidence |
| `fazle_conversations`, `fazle_messages`, draft replies | Conversation memory and drafts | Hermes/admin/AI paths | Conversation threads, drafts, approvals | Conversations & AI | Treat as memory/draft evidence, not raw message authority |
| `fazle_admins`, `fazle_users`, roles | Legacy access | RBAC/admin routes | AL-RIFAI auth (already separately designed) | Platform/Admin dependency only | Do not migrate as runtime authority |
| `fazle_audit_log`, FPE review logs | Audit and review evidence | Domain/admin modules | AL-RIFAI audit/events/provenance | Platform/Admin shared service | Import as immutable historical provenance |

Individual absent/uncertain schema details remain `UNKNOWN`; the current live schema and counts are recorded in `FAZLE_CORE_AUDIT.md`.
