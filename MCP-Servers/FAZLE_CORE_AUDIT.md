# Fazle-Core Fresh Read-Only Audit for MCP Boundaries

## Audit status

**FAZLE_CORE_FRESH_AUDIT: COMPLETE.** Fresh read-only SSH access succeeded through the preconfigured `iamazim` alias. The audit inspected the running service, source modules/routes, migrations, and the authoritative Fazle database in the `ai-postgres` container. No VPS file, service, container, environment, or database data was changed.

| Evidence item | Result |
|---|---|
| SSH method | Existing `iamazim` SSH alias (`azim@5.189.131.48`), existing configured identity only |
| VPS source | `/home/azim/core` |
| VPS branch/HEAD | `feat/bridge1-2-conversation-continuity-20260902` / `e76365ecfec1d49df3c32cad866db4f6958098f7` |
| VPS worktree | Clean (`git status --short` empty) |
| Running service | `fazle-core.service`, active since 2026-09-18, `/home/azim/.venv/bin/python run.py` |
| Running bridges | `whatsapp-bridge.service`, `whatsapp-bridge2.service`, `whatsapp-bridge3.service` active |
| Authoritative legacy DB | `ai-postgres`, database `postgres`; the separate `alrifai-postgres` is the newer AL-RIFAI database and was not treated as Fazle evidence |

Evidence labels: `VERIFIED_LIVE` means directly rechecked now; `VERIFIED_SOURCE` means source/schema inspected during this audit; `DOCUMENTED_ONLY` means carried from an older report and not relied on for current claims; `INFERRED` means an architecture conclusion; `UNKNOWN` means not established by available evidence.

## Evidence register and reconciliation

| Previous claim | Classification | Fresh evidence | Consequence |
|---|---|---|---|
| SSH/live state unavailable | **CHANGED** | Existing `iamazim` authentication succeeded; clean VPS source at the recorded HEAD | Replace the previous access blocker with current evidence |
| Six consolidated servers are appropriate | **CONFIRMED** | Live source and schema still show recruitment, workforce, finance, conversations/AI, operations/clients, and cross-domain administration | Retain six-server baseline |
| Bridge ingestion persists before routing and deduplicates | **CONFIRMED / VERIFIED_LIVE + VERIFIED_SOURCE** | `modules/bridge_poller`: cursors, `processed_bridge_messages`, raw `wbom_whatsapp_messages` insert, message-hash conflict handling, then `process_message()` | Conversations & AI owns channel normalization and evidence; domain services own mutations |
| Current schema/data was unknown | **CHANGED** | Live `ai-postgres` table inventory, counts, columns, and distributions were queried read-only | Replace unknowns with the mapping below |
| Hermes/admin relay was only historically evidenced | **CHANGED** | Live `hermes_tasks` (29), `hermes_action_approvals` (32), actor/workflow fields, and `modules/hermes_dispatch.py`/`hermes_tasks/routes.py` | Hermes remains a draft/interpretation/dispatch capability, not a business authority |
| Messenger/Facebook comments are current production channels | **PARTLY CONFIRMED / PARTLY UNKNOWN** | Source has social auto-reply routes/modules; live `wbom_whatsapp_messages.platform` directly verifies `bridge1`, `bridge2`, `bridge3`, `meta`, and `whatsapp`, but not a current Facebook/Messenger row | Keep adapters in Conversations & AI; mark individual social channel activity unknown until channel-specific evidence exists |
| Message/form paths diverge | **CONFIRMED** | Separate static HTML/API routes and message router/domain handlers coexist; some paths use drafts/approval while direct forms write domain tables | AL-RIFAI convergence must occur in canonical domain services |

## Live message and state evidence

The live `wbom_whatsapp_messages` table contains 32,436 rows: 22,467 inbound and 9,969 outbound. Platforms are `bridge1` 12,840, `bridge2` 11,827, `bridge3` 5,839, `meta` 1,512, and `whatsapp` 418. Actor attribution is present for automation (3,555), external user (7,095), Hermes (823), human device (364), and system (1,376), with 19,223 rows null. Workflow values include recruitment (3,675), payment due (193), salary query (83), escort duty (70), attendance (32), client order (11), join (42), admin instruction (364), Hermes admin send (165), and Hermes relay reply (420), among others.

The source path is: bridge-local message read and cursor → duplicate/system/pairing/media gates → raw/canonical `wbom_whatsapp_messages` persistence and queue state → identity enrichment (`identity_brain`/resolver) → `modules.message_router.process_message()` → deterministic domain handler or Hermes/LLM interpretation → draft/approval or domain persistence → outbound queue/bridge delivery and audit. `wbom_whatsapp_messages` has platform, direction, conversation key, canonical phone, source references, actor type/id, identity role/confidence, intent, workflow, extracted text, and message hash fields. `requires_action` is derived by `app/main.py` conversation-attention queries from domain state; it is not evidence that an AI model has authority.

## Recruitment / interested persons

**VERIFIED_LIVE:** `wbom_candidates` has 741 rows: 600 `collecting`, 141 `scored`; post-intake states include `awaiting_agreement` 93, `agreed` 6, `joining_ready` 6, `future_contact` 2, `not_ready_now` 3, `declined` 4, and 625 null. `fazle_recruitment_sessions` has 759 rows and links `phone`, source bridge/message, collection step, funnel stage, score, and `candidate_id`. `wbom_candidates` has `linked_employee_id`, proving an applicant-to-employee linkage path. `wbom_job_applications` exists but currently has 0 rows.

**VERIFIED_SOURCE:** `modules/recruitment_flow` creates/reuses candidates by phone, appends candidate conversation audit rows with source/message deduplication, persists staged intake fields, finalizes post-intake state, and contains readiness/joining-related rules. `modules/message_router` and `modules/bridge_poller` route recruitment messages. Recruitment/admin API and static paths exist in `app/main.py` (`/api/recruitment/interested-candidates`, `/admin/recruitment`); no equivalent populated application-table workflow is demonstrated by live data.

Boundary: Recruitment owns interested → applicant → screening/interview/readiness/joining decision and emits a reviewed Workforce handoff. Workforce owns the employee record after approved conversion. AI may extract or draft; Recruitment policy decides.

## Workforce / employees / attendance

**VERIFIED_LIVE:** `wbom_employees` has 250 rows (226 Active, 24 Inactive); `fpe_employees` has 593 rows. The stores overlap employee name/phone/status and link fields. `wbom_attendance` has 2 rows and includes approval/source fields. Live routes expose employee CRUD/reactivation/linking (`modules/admin_employees`), attendance (`modules/attendance/routes.py`), and FPE employee search/edit workflows.

**VERIFIED_SOURCE:** identity resolution uses phone/name evidence and FPE/WBOM links; attendance is handled separately from the financial ledger. Operational assignment history is distributed across escort/dispatch modules. Financial employee fields, payout destinations, cash, and ledger rows must not be owned by Workforce in AL-RIFAI.

Boundary: Workforce owns employee lifecycle, identity references, attendance, assignment context, and non-financial history. Finance owns salary, payout accounts, financial ledger, and payment effects.

## Finance / payroll / accountant / cash

**VERIFIED_LIVE:** `fpe_cash_transactions` has 4,901 rows: 4,865 `final`, 35 `pending`, 1 `reversed`; approval status has 7 `approved`, 35 `pending_review`, and 4,859 null. `fpe_employee_ledger` has 747 rows. `wbom_cash_transactions` has 1,428 rows. `wbom_payroll_runs` has 705 rows, all currently `draft`; `wbom_salary_records` and `wbom_billing_records` exist but are empty. FPE employees include salary/designation/joining fields and payout/identity links. This is direct evidence of overlapping financial stores and incomplete/parallel lifecycle state.

**VERIFIED_SOURCE:** `modules/fazle_payroll_engine`, `payment_workflow`, `payment_ingest`, `payment_relay`, `payment_relay_accounting`, `draft_approval`, and admin transaction routes implement payroll calculation, payment drafts, accountant review, cash/ledger recording, reversals, reconciliation, and outbound handling. Routes distinguish viewer/operator/accountant/admin capabilities. The source uses transaction references, idempotency keys, approval/review status, reversal links, and legacy WBOM transaction references, but universal exactly-once behavior across every message/form callback is **UNKNOWN**.

Verified current ownership interpretation: OWNER/ADMIN instruction → message/router interpretation → payment draft or accountant queue → recipient/amount validation and approval → outbound delivery evidence → FPE cash transaction/ledger effects → audit/reconciliation. Interpretation is AI/conversation work; authorization, accounting, idempotency, delivery completion, and persistence are deterministic Finance work. Finance owns client settlement; Operations owns the operational program that generated the billable event.

## Conversations / AI / Hermes

**VERIFIED_LIVE + VERIFIED_SOURCE:** all three bridge services are active. `modules/bridge_poller` has per-bridge cursors, deduplication, pairing/system-message quarantine, media/OCR branches, raw message persistence, queue state, heartbeat writes, and outbound completion handling. `modules.message_router` resolves identity/role and routes recruitment, attendance, escort, payment, salary, client, admin, and other intents. `modules.conversation_canonical`, `conversation_memory`, `message_archive`, `outbound`, `social_auto_reply`, and `hermes_dispatch` are distinct layers.

`fazle_conversations` has 2 rows and `fazle_messages` 8 rows, while the much larger canonical operational message evidence is in `wbom_whatsapp_messages`; these are not interchangeable authorities. `hermes_tasks` and `hermes_action_approvals` persist task/action state, requested/reviewed actors, domain/reference/evidence/idempotency fields. `hermes_tasks/routes.py` describes pass-through task/approval routes; `hermes_dispatch.py` calls Hermes for interpretation/semantic gating and explicitly falls through to deterministic routing on failure.

Boundary: Conversations & AI owns channel adapters, canonical message/thread evidence, extraction/classification, Hermes/assistant calls, drafts, dispatch requests, outbound orchestration, and delivery state. It does not own business authorization or direct HR/finance/operations persistence. Facebook/Messenger current data activity is **UNKNOWN** beyond source-level social integration evidence.

## Operations / clients / escort

**VERIFIED_LIVE:** `wbom_escort_programs` has 347 rows: 327 completed, 13 confirmed, 5 cancelled, 2 draft. `escort_roster_entries` has 360 rows: 331 completed, 13 confirmed, 8 active, 5 cancelled, 3 draft. Roster columns include mother/lighter vessel, escort, destination, dates/shifts, release point, salary, conveyance, net payable, employee link, and status. `wbom_clients`, `ops_programs`, billing profiles, slip extraction, release match, and change-request tables exist; the older `fazle_clients` name was not found in the live table inventory.

**VERIFIED_SOURCE:** client/admin/escort messages are classified and extracted by message/Hermes layers, while `escort_lifecycle`, `escort_roster`, `dispatch`, `escort_slip_extractor`, and client routes validate or mutate structured operational records. Roster sync is atomic with `ON CONFLICT (program_id) DO UPDATE`; roster audit logs and change requests preserve review. Assignment, replacement, completion, release, and billing are distinct operations. A vessel mention does not itself prove an assignment or completion.

Boundary: Operations & Clients owns clients in operational context, vessels, escort programs, roster, assignments, replacements, lifecycle, release/completion, and service history. Finance owns billing settlement and financial effects.

## Platform / administration

**VERIFIED_SOURCE + VERIFIED_LIVE:** admin/API-key/RBAC routes, authority lanes, draft approvals, user/role administration, `fazle_audit_log`, `fazle_admin_audit`, Hermes task/action approvals, and cross-domain reporting exist. Platform/Admin is a cross-domain control plane. Ordinary domain logic remains in Recruitment, Workforce, Finance, Conversations, or Operations even when an administrator triggers it. Legacy API keys, internal relay gates, and role claims are not AL-RIFAI authorization proof.

## Two current entry workflows

### Messaging

`Bridge/local channel or social adapter → source/cursor/dedup gates → raw wbom_whatsapp_messages and queue → identity enrichment → router/intent → deterministic domain handler or Hermes extraction/draft → domain validation/approval → persistence/audit → outbound queue/bridge delivery.`

### Frontend/form

`Static HTML or authenticated API route → API-key/role validation and request validation → module-specific handler → direct domain-table transaction or draft/approval path → audit/result.`

Current divergence is verified: message paths often preserve raw evidence and create drafts or approvals, while form/API paths include direct employee, attendance, roster, billing, payroll, and transaction mutations; table ownership and idempotency are not uniform. AL-RIFAI must converge both entries on one canonical domain service beneath the MCP adapter.

## Database mapping

| Current live table/group | Purpose / current reader-writer evidence | Future AL-RIFAI domain | MCP owner | Migration/provenance relevance |
|---|---|---|---|---|
| `wbom_candidates`, `fazle_recruitment_sessions`, `wbom_candidate_conversations` | Candidate intake, staged conversation, source bridge/message; recruitment flow/router | Applicants, applications, recruitment events | Recruitment | Preserve conversation/source/status history; review `linked_employee_id` |
| `wbom_job_applications` | Application schema; 0 live rows | Applications | Recruitment | Empty current store; do not assume it is authoritative |
| `wbom_employees`, `fpe_employees`, aliases/links | Overlapping employee master/payroll identity | Persons, employees, identity links | Workforce + shared identity | Reconcile 250 vs 593 records and provenance |
| `wbom_attendance`, `ops_attendance` | Attendance and approval/source evidence | Attendance | Workforce | Preserve approval and entry source |
| `fpe_employee_ledger`, `fpe_cash_transactions`, `wbom_cash_transactions` | Financial ledger, cash, reversals, approval and legacy references | Finance ledger/transactions | Finance & Payroll | Reconcile 747/4,901/1,428 rows, transaction refs, reversals, and idempotency |
| `wbom_payroll_runs`, `wbom_salary_records` | Payroll periods/salary; 705 drafts and 0 salary rows | Payroll runs and salary policy | Finance & Payroll | Preserve period/status/approval history; clarify draft authority |
| `wbom_escort_programs`, `escort_roster_entries`, change/slip/history tables | Program, roster, release, extraction, lifecycle | Operations programs/assignments/releases | Operations & Clients | Preserve state transitions and evidence; never infer completion |
| `wbom_clients`, `ops_programs`, billing profiles/records | Client and operational/billing context; billing records currently empty | Operational clients plus financial settlement | Operations & Clients + Finance | Split operational relationship from monetary settlement; retain older `fazle_clients` references only as source/documentation claims |
| `wbom_whatsapp_messages`, queue, processed bridge tables | Raw/canonical channel messages and delivery workflow | Canonical messages, threads, media, outbox | Conversations & AI | Import external IDs, source, direction, actor/provenance, hashes |
| `fazle_conversations`, `fazle_messages`, drafts | Small chat-memory/draft model | Conversation threads/drafts | Conversations & AI | Treat as supplemental memory/draft evidence, not raw-message authority |
| `hermes_tasks`, `hermes_action_approvals`, Hermes logs | Task, action approval, model/decision/event evidence | AI/task/provenance records | Conversations & AI + Platform/Admin | Preserve requested/reviewed actors, evidence, domain, idempotency |
| `fazle_admins`, roles, `fazle_audit_log` and review logs | Legacy access and audit | AL-RIFAI auth plus audit/provenance | Platform/Admin dependency/shared audit | Import history as provenance only; do not reuse runtime auth |

## Final boundary decision

Fresh live evidence **validates six consolidated backend MCP servers**: Recruitment; Workforce; Finance & Payroll; Conversations & AI; Operations & Clients; Platform / Admin. No separate Accountant, Escort, Client, Hermes, channel, table, or screen server is justified. MCP remains an adapter over canonical AL-RIFAI domain services; Hermes remains interpretation/extraction/draft/dispatch capability; deterministic authorization, validation, accounting, state transitions, persistence, idempotency, and audit remain below MCP.

The evidence also requires explicit migration gates: reconcile WBOM/FPE employee and financial stores, preserve message provenance and duplicate keys, separate operational client/escort state from Finance settlement, and resolve the currently empty/parallel application, salary, and billing stores before cutover.
