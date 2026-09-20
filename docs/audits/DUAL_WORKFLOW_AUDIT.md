# DUAL WORKFLOW AUDIT — Fazle-Core to AL-RIFAI

Scope: read-only audit of the live current Fazle-Core system (`/home/azim/core`) and the independent AL-RIFAI platform (`/home/azim/alrifai-ai-platform`). No schema changes, no migrations, no service restarts, no feature implementation.

## Evidence base
- `core/app/main.py`
- `core/modules/message_router/__init__.py`
- `core/modules/bridge_poller/__init__.py`
- `core/modules/identity_brain/__init__.py`
- `core/modules/attendance/routes.py`
- `core/modules/admin_employees/__init__.py`
- `core/modules/client_billing/routes.py`
- `core/modules/fazle_payroll_engine/routes.py`
- `core/modules/escort_roster/routes.py`
- live PostgreSQL schema via `docker exec ai-postgres psql -U postgres -d postgres ...`
- AL-RIFAI live schema via `docker compose exec alrifai-postgres psql -U alrifai -d alrifai ...`

## 1. Exact messaging workflow findings

### Workflow A — Messaging Conversation → Business Data

Status: implemented, with multiple partial layers and duplication risk.

| Stage | File / function | Evidence | Table(s) / target | Status |
|---|---|---|---|---|
| Entry point | `/home/azim/core/app/main.py` — webhook routes, `/webhook/meta` and `/send/meta` | Meta webhook and send handlers are registered here; routing delegates to `modules.message_router.process_message()` | `wbom_whatsapp_messages`, `fazle_messages` | Implemented |
| Bridge ingest | `/home/azim/core/modules/bridge_poller/__init__.py` — `init_tables()`, `_fetch_new_messages()`, `process_bridge_inbound()` | Polls bridge SQLite DBs and persists inbound rows before routing; dedup via `processed_bridge_messages` | `processed_bridge_messages`, `wbom_whatsapp_messages`, `fh` | Implemented |
| Identity resolution | `/home/azim/core/modules/identity_brain/__init__.py` — `detect_identity()` | Resolves admin / family / accountant / escort / employee / candidate / unknown using phone and DB context | `wbom_contacts`, `wbom_employees`, `wbom_escort_programs`, `fazle_contact_roles` | Implemented |
| Parser | `/home/azim/core/modules/message_router/__init__.py` — `process_message()` + `classify()` from `modules.intent` | Classifies intent and dispatches by role; calls parse handlers for attendance / escort / recruitment | `wbom_message_intents`, `wbom_whatsapp_messages` | Implemented |
| Validation | `/home/azim/core/modules/message_router/__init__.py` and `modules.employee_verification` | `is_admin_command`, `route_recruitment_message`, `check_identity_mismatch`, attendance validation | `wbom_candidates`, `wbom_unmatched_confirmations`, `ops_attendance` | Partial |
| Business service | `/home/azim/core/modules/recruitment_flow/__init__.py`, `/home/azim/core/modules/escort/__init__.py`, `/home/azim/core/modules/attendance/__init__.py`, `/home/azim/core/modules/payment_ingest/__init__.py` | Recruitment intake, escort ordering, attendance drafts, payment ingestion | `wbom_candidates`, `ops_attendance`, `fpe_cash_transactions`, `fazle_payment_drafts` | Implemented |
| DB write | direct SQL via `app/database.py` | `fetch_one`, `fetch_all`, `execute` use asyncpg and insert/update into canonical tables | `wbom_*`, `fpe_*`, `ops_*`, `fazle_*` | Implemented |
| Response / delivery | `/home/azim/core/app/main.py` — `send_whatsapp_message()`, queue-based outbound, `/api/outbound/status` | Sends reply via outbound queue and tracks delivery-state metadata | `fazle_outbound_queue`, `outbound_safety_incidents` | Implemented |

### Actual code path
1. `bridge_poller` reads a bridge SQLite table and persists inbound message to `wbom_whatsapp_messages`.
2. `process_message(sender, text, source, message_id=...)` normalizes the sender, calls `detect_identity()` and `classify()`.
3. Router branches by role: admin, escort_client, accountant, candidate, employee, unknown.
4. For escort: `handle_escort_client_message()` and `handle_admin_escort_completion()`.
5. For attendance: `parse_attendance()` then `create_attendance_draft()` + admin review.
6. For payment / payroll: `ingest_payment_sms()` and FPE review queue / ledger entries.
7. For recruitment: `route_recruitment_message()` seeds or updates `wbom_candidates`.
8. Reply/outbound is queued through `modules.outbound` and then sent via WhatsApp / Meta transport.

### Messaging status by domain
- WhatsApp bridge ingestion: implemented.
- Meta WhatsApp: implemented, via `/webhook/meta` and Meta API flows.
- Bridge1 / Bridge2 / Bridge3: implemented via configuration and bridge poller.
- Messenger / Facebook comments: implemented as social auto-reply and integration points, but not equivalent to canonical admin form CRUD.
- Admin relay: implemented via admin command handling and direct admin message routes.
- Hermes integration: partially implemented as dedicated admin/Hermes relay paths.
- Duplicate prevention: implemented via `processed_bridge_messages` and idempotency-ish review; not on all business tables.
- Delivery confirmation: implemented at outbound queue and Meta delivery-state hooks, but not consistently uniform across all channels.

## 2. Exact frontend form workflow findings

### Visible and functional frontend surfaces
The current Fazle-Core app exposes HTML UI pages in `/home/azim/core/app/static` and route handlers in `/home/azim/core/app/main.py`.

| Frontend surface | Source file | Backend API(s) | Notes |
|---|---|---|---|
| Dashboard / admin overview | `app/static/dashboard.html` | `/admin/overview`, `/admin/users`, `/admin/audit`, `/admin/drafts` | Visible and functional |
| Payroll | `app/static/payroll.html` | `/api/fpe/*`, `/admin/payroll/*`, `/api/admin/income/*` | Functional, finance-heavy |
| Attendance | `app/static/payroll.html` and `modules/attendance/routes.py` | `/admin/attendance`, `/admin/attendance/draft`, `/admin/payroll/...` | Functional |
| Escort roster | `app/static/escort-roster.html` | `/api/escort-roster/*` | Functional |
| Dispatch / operations | `app/static/dispatch.html` | `/api/dispatch/*` | Functional |
| Client billing | `app/static/payroll.html` (billing views) | `/admin/client-billing-profiles`, `/admin/bills/*` | Functional |
| Employee management | `app/static/payroll.html` + `admin_employees` | `/api/admin/employees`, `/api/admin/employees/*` | Functional |
| Admin / user management | `app/static/dashboard.html` | `/admin/users`, `/admin/users/{phone}/apikey`, `/admin/users/{phone}/disable` | Functional |
| WhatsApp / conversation UI | `app/static/wa_chat.html`, `open-chat.html` | `/api/whatsapp/messages/*` | Functional |

### Form-level workflow examples

| Form / operation | Frontend handler | API endpoint | Validation | Domain service | DB write | Status |
|---|---|---|---|---|---|---|
| Employee create | `modules/admin_employees/__init__.py` `create_employee` | `POST /api/admin/employees` | phone normalization, duplicate check | `match_or_create_employee()` from FPE | `wbom_employees`, then `fpe_employees` | Implemented |
| Attendance create | `modules/attendance/routes.py` `api_create_attendance` | `POST /admin/attendance` | Pydantic `AttendanceCreateIn` + RBAC | `create_manual_attendance()` | `wbom_attendance` / `ops_attendance` | Implemented |
| Attendance draft | `modules/attendance/routes.py` `api_create_attendance_draft` | `POST /admin/attendance/draft` | office assistant or above | attendance draft helper | draft tables + final approval path | Implemented |
| Client billing profile | `modules/client_billing/routes.py` | `/admin/client-billing-profiles` | role-based admin gate | `create_client_billing_profile()` | client billing profiles table | Implemented |
| Bill generation | `/admin/bills/generate` | `POST /admin/bills/generate` | admin gate | `generate_bill()` | `wbom_billing_records` or related billing tables | Implemented |
| Payroll / manual cash transaction | `app/static/payroll.html` + `/api/fpe` | `/api/fpe/transactions/manual` | normalization, role checks | FPE accounting engine | `fpe_cash_transactions` | Implemented |

### Visible vs functional vs tested
- Visible: the HTML pages are present under `app/static`.
- Functional: the corresponding FastAPI routers and DB writes exist and the route registration is in `app/main.py`.
- Tested: unit/coverage exists in `/home/azim/core/tests`, but not every page has explicit E2E coverage; some modules are only partially covered.
- Verified live: some routes are clearly live in the running server, but the audit did not execute an end-to-end form submission against production data.

## 3. Shared versus duplicated business logic

### Comparison table

| Business operation | Message path | Form path | Shared service | Database | Difference | Risk |
|---|---|---|---|---|---|---|
| Employee creation | `detect_identity()` + `match_or_create_employee()` + admin route | `POST /api/admin/employees` | `modules.fazle_payroll_engine.employee.match_or_create_employee` | `wbom_employees`, `fpe_employees` | message path is identity-driven; form path is direct admin create | duplicate employee resolution risk |
| Recruitment intake | `route_recruitment_message()` | recruitment UI/flow | `route_recruitment_message()` | `wbom_candidates`, `wbom_job_applications` | message path is conversational and may create draft; form path is direct | inconsistent candidate stage logic |
| Attendance entry | `parse_attendance()` + `create_attendance_draft()` | `POST /admin/attendance` | attendance CRUD + review queue | `ops_attendance`, `wbom_attendance` | messages are draft-first; forms can be final/manual | divergent approval rules |
| Escort assignment | `handle_escort_client_message()` | `/api/escort-roster` + dispatch UI | escort roster + validation | `escort_roster_entries`, `wbom_escort_programs` | message path is conversational and stricter; form path is manual adjustment | reconciliation drift |
| Cash transaction | payment ingest and FPE rules | manual cash transaction routes | FPE accounting | `fpe_cash_transactions`, `wbom_cash_transactions` | message path may parse by text; form path is explicit numeric input | duplicate payment writes |
| Client creation | social/contact identity + sales pipeline | client billing profile and client registry | client profile / contact logic | `wbom_clients`, `fazle_clients` | message source identity is weak; admin UI is explicit | identity normalization mismatch |
| Payroll adjustment | salary/payment keyword routing | payroll admin API | FPE ledger engine | `fpe_employee_ledger`, `fpe_cash_transactions` | message path may be untidy or AI-driven; form path is explicit | approval drift |

### Confirmed duplication and conflict patterns
- Duplicate identity matching: `wbom_contacts`, `wbom_employees`, `fpe_employees`, `fazle_contact_roles`, `identity_brain.detect_identity()`, and direct `match_or_create_employee()` all resolve identity differently.
- Inconsistent phone normalization: multiple normalizer helpers exist (`modules.phone_normalizer`, `modules.fazle_payroll_engine.normalizer`, legacy conversions); the system has a documented risk of 01 vs +880 vs 880 normalization mismatch.
- Payout numbers can be treated as identity in some flows (`employee_id_phone`, `payout_phone`, `payment_number`). This is a known risk.
- Missing validation: some message-triggered flows fall back to admin review instead of strict validation.
- Duplicate writes: message-ingest and form-based flows can both create candidate / employee / cash rows.

## 4. Current Fazle-Core schema findings

### Live schema status
The live current schema is on the `ai-postgres` container and is accessible with `docker exec ai-postgres psql -U postgres -d postgres ...`.

Key live tables in use by the workflows:
- `wbom_whatsapp_messages` — raw inbound/outbound message stream and conversation metadata
- `wbom_contacts` — contact identity and sender metadata
- `wbom_employees` — canonical employee records
- `wbom_candidates` — recruitment funnel data
- `wbom_clients` — direct client table
- `wbom_cash_transactions` — cash transaction ledger
- `fpe_employees` — payroll engine employee canonicalization
- `fpe_cash_transactions` — payroll-cash engine ledger
- `ops_attendance` — attendance table used by office/admin actions
- `escort_roster_entries` — escort roster and assignments
- `fazle_messages` / `fazle_conversations` — conversation memory
- `fazle_admins` / `fazle_users` — admin/user access
- `fazle_audit_log` — traceability

### Important schema findings
- The current system is not a single canonical model; it is a hybrid of old WBOM tables and newer FPE / escort / operations tables.
- Tables like `wbom_contacts`, `wbom_employees`, `fpe_employees`, `fazle_clients`, `wbom_clients`, and `fazle_contact_roles` represent overlapping identity or client concepts.
- There is a real `message` table (`wbom_whatsapp_messages`) and a separate conversation memory table (`fazle_conversations` / `fazle_messages`), which are not the same thing.
- The database is live and includes legacy and shadow tables (for example `_legacy_*` tables), confirming multi-source ownership and migration history.

## 5. AL-RIFAI live schema inventory

The live AL-RIFAI database is `alrifai-postgres`, running at port 5434, and the current schema exactly matches the init SQL in `database/init-sql/001_identity_foundation.sql`.

The 13 tables are:
1. persons
2. person_identifiers
3. person_phones
4. person_aliases
5. contact_methods
6. payout_accounts
7. external_platform_ids
8. employees
9. applicants
10. clients
11. business_events
12. audit_log
13. provenance_records

This is the live state; no additional domain tables appear in the schema. Migration files under `database/migrations` are not actual SQL files; the repo currently documents the naming scheme in `database/migrations/VERSIONS.md`, while the actual live schema is created by `database/init-sql/001_identity_foundation.sql`.

## 6. Six-domain ownership recommendation

The proposed domains are valid as a high-level architecture, but ownership must be explicitly one-to-one:

| Domain | Covers current modules | Recommendation |
|---|---|---|
| Identity & Access | `identity_brain`, RBAC, admin API keys, contact roles | Single canonical identity service and access layer |
| Business & Operations | attendance, payroll, escort roster, client billing, employee CRUD, recruitment flow | Canonical business services, not message-specific handlers |
| Communications & Data Extraction | bridge pollers, Meta webhook, WhatsApp messages, OCR/media extraction, admin relay | Message intake, normalization, extraction, and outbound transport |
| AI & Automation | intent classification, LLM reply generation, admin AI commands, recruitment semantics | AI orchestration isolated behind service interfaces |
| Data & Integrations | FPE sync, outbound queue, data imports, social integrations, bridge polling | Integration and persistence layer only |
| Platform & Observability | health checks, logging, runtime settings, monitoring | cross-cutting platform concerns |

### Recommendation
Use a modular monolith with bounded service interfaces and a single canonical business layer. Do not create one MCP process per table; instead group by domain, not by SQL table.

## 7. Canonical business engine design

The desired convergence point is:

Message path:
`Message → Normalization → Validation → Canonical Domain Service → Transaction → Database → Audit/Event`

Form path:
`Form → API → Normalization → Validation → Canonical Domain Service → Transaction → Database → Audit/Event`

Interpretation:
- `Identity` must be resolved once via a canonical identity service.
- `Phone normalization` must be centralized.
- `Recruitment`, `attendance`, `escort`, `cash`, and `billing` must map to canonical domain services, not duplicate ad hoc logic.
- Event sourcing and audit must use the same classification and idempotency strategy in all flows.

## 8. Error isolation design

Recommended domain codes:
- `COMM-MSG-001` — communications / bridge ingest failure
- `IDENTITY-MATCH-002` — identity resolution failure
- `BUSINESS-PAYROLL-003` — payroll workflow failure
- `DATA-IMPORT-004` — ingestion / import failure
- `OPS-ATTENDANCE-005` — attendance failure

Recommended fields:
- `domain`
- `error_code`
- `correlation_id`
- `source`
- `sender_phone`
- `message_id`
- `request_id`
- `db_table`
- `status`

The underlying principle is fail-closed per bounded domain without broad restarts or redeploys.

## 9. Findings summary

1. Exact messaging workflow findings: the live system implements a routed message intake pipeline from bridge/meta intake to `process_message()` and canonical DB writes, but it contains multiple partial identity and validation layers.
2. Exact frontend form workflow findings: the app exposes real form workflows via static web pages and FastAPI routes; they are functional in the codebase but not uniformly tested end-to-end.
3. Shared versus duplicated business logic: identity resolution, phone normalization, and payment/employee logic are duplicated or split across `identity_brain`, `fpe_employee`, `wbom_*`, and admin routes.
4. Current Fazle-Core schema findings: the live schema is hybrid and contains both legacy and canonical tables, with `wbom_*`, `fpe_*`, `ops_*`, `escort_*`, and `fazle_*` tables representing overlapping domains.
5. Exact AL-RIFAI table/column inventory: the live schema contains the 13 identity tables defined in `database/init-sql/001_identity_foundation.sql` and matches live DB state.
6. Six-domain ownership recommendation: use a modular monolith with clear ownership boundaries rather than table-per-MCP or one tool per DB table.
7. Missing business modules: canonical recruitment lifecycle, canonical attendance approval service, canonical client identity service, canonical payment ledger service, canonical event-audit layer.
8. Risks to resolve before MCP implementation: phone normalization drift, duplicate writes, unshared validation, weak identity resolution, inconsistent DB ownership.
9. Git commit and working-tree status: the audit artifacts are committed in the AL-RIFAI repo after documentation is finalized.
10. Next safe implementation phase: after audit, implement canonical domain service contracts and a read-only connector layer, not business feature growth.

## 10. Outcome

The current Fazle-Core application does not have a single canonical business engine across messaging and forms. The new AL-RIFAI platform should treat identity resolution, validation, and the business transaction layer as shared services instead of splitting them by entry channel.
