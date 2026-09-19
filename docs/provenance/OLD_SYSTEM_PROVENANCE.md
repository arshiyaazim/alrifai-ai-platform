# Old System Provenance Report

**Status:** DESIGN PHASE  
**Created:** 2026-09-19  
**Source:** READ-ONLY inspection of `/home/azim/core` (Fazle-Core)

This document records all business/domain knowledge extracted from the existing Fazle-Core system.

---

## Source System Profile

| Attribute | Value |
|---|---|
| System Name | Fazle-Core |
| Location | `/home/azim/core` |
| Type | Python/FastAPI application |
| Database | PostgreSQL (`ai-postgres`) |
| Web Server | Uvicorn |
| Entry Point | `/home/azim/core/run.py` |
| Migration Format | SQL (`/home/azim/core/migrations/`) |
| Service Name | `fazle-core.service` |

---

## Domain Modules Found (READ-ONLY)

| Module | Domain | Source Path |
|---|---|---|
| recruitment_flow | Recruitment | `modules/recruitment_flow/` |
| recruitment_ai | Recruitment AI | `modules/recruitment_ai/` |
| employee_verification | Identity | `modules/employee_verification/` |
| attendance | Attendance | `modules/attendance/` |
| fazle_payroll_engine | Payroll | `modules/fazle_payroll_engine/` |
| payment | Billing/Accounting | `modules/payment/` |
| client_billing | Billing | `modules/client_billing/` |
| billing | Billing | `modules/billing/` |
| escort_lifecycle | Operations | `modules/escort_lifecycle/` |
| escort_roster | Operations | `modules/escort_roster/` |
| contact_roles | Contact/Client | `modules/contact_roles/` |
| social_auto_reply | Messaging | `modules/social_auto_reply/` |
| wa_chat_frontend | WhatsApp | `modules/wa_chat_frontend/` |
| hermes_dispatch | AI Dispatch | `modules/hermes_dispatch.py` |
| conversation_canonical | AI Memory | `modules/conversation_canonical/` |
| message_archive | Messaging | `modules/message_archive/` |
| message_router | Messaging | `modules/message_router/` |
| outbound | Messaging | `modules/outbound/` |
| scheduler | Operations | `modules/scheduler/` |
| health_monitor | Observability | `modules/health_monitor/` |
| operations_health | Observability | `modules/operations_health/` |
| phone_normalizer | Identity | `modules/phone_normalizer/` |
| identity_brain | Identity | `modules/identity_brain/` |
| identity_resolver | Identity | `modules/identity_resolver.py` |
| group_identity | Identity | `modules/group_identity.py` |
| number_identity | Identity | `modules/number_identity/` |
| kb_upload | Documents | `modules/kb_upload/` |
| knowledge_base | Documents | `modules/knowledge_base/` |
| rag | AI RAG | `modules/rag/` |
| admin_employees | Admin | `modules/admin_employees/` |
| admin_transactions | Admin | `modules/admin_transactions/` |
| ai_console | AI | `modules/ai_console/` |
| draft_approval | Approval | `modules/draft_approval/` |
| draft_quality | Quality | `modules/draft_quality/` |
| authority_lanes | Permissions | `modules/authority_lanes.py` |
| business_action_execution | Business Logic | `modules/business_action_execution.py` |
| user_role | Permissions | `modules/user_role/` |
| rbac | Permissions | `modules/rbac/` |

---

## Database Schema Insights (READ-ONLY)

### Tables Identified
- `fazle_admins` — Admin users with `phone`, `name`, `status`, `api_key_hash`
- `fazle_admin_roles` — Role assignments (`admin_id`, `role_name`, `granted_by`)
- `fpe_employees` — Full payroll engine employees (`employee_code`, `primary_phone`, indexes)
- `wbom_employees` — Shared operational employee roster
- `fpe_income_transactions` — Income transactions (`txn_date`)
- `fpe_cash_transactions` — Cash transactions (`txn_date`)

### Migrations Found
- `002_add_hr_officers.sql` — Creates HR Officer accounts (OfficeAssistant01/02)
- `003_add_fpe_indexes.sql` — Indexes on `employee_code`, `primary_phone`, `txn_date`
- `004_add_accounting_period_constraint.sql` — Accounting period constraint
- `005_add_admin_login_auth.sql` — Admin login auth
- `escort_history_schema.sql` — Escort assignment history
- `escort_roster_schema.sql` — Escort roster schema

### Known Issues (Historical)
- `thread-store conflict` in Codex app-server (stale writer locks)
- Duplicate message/dispatch on retry (idempotency gaps)
- Identity ambiguity (name vs phone vs payout number confusion)
- Missing column meaning documentation
- Inconsistent employee matching across modules

---

## Provenance Tracking Schema

The new platform stores provenance for every imported record:

```sql
CREATE TABLE provenance_records (
    provenance_id     UUID PRIMARY KEY,
    source_system     TEXT NOT NULL,     -- 'fazle-core'
    source_record_id  TEXT NOT NULL,     -- old row identifier
    source_timestamp  TIMESTAMPTZ,        -- when in old system
    ingestion_timestamp TIMESTAMPTZ,      -- when imported
    transformation_version TEXT,          -- mapping version
    business_rule_version TEXT,          -- rule version applied
    entity_type       TEXT NOT NULL,
    entity_id         UUID NOT NULL,
    conflict_strategy TEXT,              -- skip/overwrite/merge/queue_review
    status            TEXT                 -- pending/applied/conflict/rejected
);
```

---

## Import Boundary

```
OLD FAZLE-CORE (READ-ONLY)
       │
       ▼
Read-only Connector    ← NEVER writes to old DB
       │
       ▼
Validation / Normalization
       │
       ▼
Identity Resolution    ← New platform canonical identity
       │
       ▼
AL-RIFAI Canonical Database  ← New platform owns all data
```

**Rule:** Random agents must NOT query old production tables directly. Connector behavior must be documented and testable.

---

## Ownership Matrix (from Fazle-Core ARCHITECTURE.md)

| Domain | Owner | Boundary |
|---|---|---|
| WhatsApp, payroll, attendance, escort, recruitment, AI replies | Fazle-Core | Primary source of truth |
| SMS onboarding, employee app identity, GPS, Firebase | LocationWhere | Outbound sync only |
| Shared `wbom_employees` | Fazle-Core | Write via documented sync contract |
| Infrastructure (Postgres, Redis, Ollama, Qdrant, monitoring) | Shared | Both apps use shared containers |
