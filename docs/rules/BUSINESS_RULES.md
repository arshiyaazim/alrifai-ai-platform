# AL-RIFAI Business Rules Registry

**Status:** DESIGN PHASE  
**Created:** 2026-09-19  
**Provenance:** Fazle-Core modules (READ-ONLY discovery)

Each rule has a stable identifier. Code, MCP tools, documentation, and agents reference the SAME rule.

---

## Business Policy

| Rule ID | Rule | Source | Current Behavior | Known Historical Problem | Normalized Rule | New Implementation |
|---|---|---|---|---|---|---|
| PAYMENT-COMPLETE-001 | Payment completion requires transaction validation | Fazle-Core payment module | Validates before write | Double-payment on retry | Idempotent payment completion via stable idempotency key | domain/payment/ |
| EMPLOYEE-ACTIVATE-001 | Employee activation requires identity verification | Fazle-Core employee_verification | Identity verified before activation | Missing ID → duplicate employee | Canonical identity resolution first | domain/employee/ |
| RECRUITMENT-JOIN-001 | Applicant joins via verified identity resolution | Fazle-Core recruitment_flow | Applicants linked to existing or new person | Duplicate people on join | Identity resolution with review queue for ambiguous cases | domain/recruitment/ |
| ATTENDANCE-RECORD-001 | Attendance must be recorded once per person per day | Fazle-Core attendance | Recorded via mobile | Duplicate entries | Idempotent attendance recording | domain/attendance/ |

---

## Identity Rules

| Rule ID | Rule | Source | Normalized Rule | New Implementation |
|---|---|---|---|---|
| IDENTITY-001 | A person is identified by immutable UUID | Fazle-Core identity_brain | Never use name or phone as PK | domain/identity/persons table |
| IDENTITY-002 | Phone is a contact method, not identity | Fazle-Core number_identity | Normalize via canonical library | domain/identity/phone_normalizer |
| IDENTITY-003 | Payout number is financial routing, not identity | Fazle-Core payroll | Never equate to person | domain/identity/payout_accounts |
| IDENTITY-004 | External platform IDs must be typed | Fazle-Core contact_roles | WhatsApp/Facebook/other typed | domain/identity/external_platform_ids |
| IDENTITY-005 | Name is an attribute, not identity | Fazle-Core group_identity | Aliases table | domain/identity/person_aliases |

---

## Workflow Rules

| Rule ID | Rule | Source | Normalized Rule | New Implementation |
|---|---|---|---|---|
| WORKFLOW-APPLICATION-001 | Application has discrete states | Fazle-Core recruitment_flow | new → screening → interviewing → offered → hired/rejected | domain/workflow/applicant_states |
| WORKFLOW-JOINING-001 | Joining flows through identity resolution | Fazle-Core recruitment_flow | Verify identity → create employee | domain/workflow/joining |
| WORKFLOW-PAYMENT-001 | Payroll follows approved attendance | Fazle-Core payroll_logic | Attendance → payroll calculation → validation → payment | domain/workflow/payroll |
| WORKFLOW-PAYROLL-001 | Payroll must be calculated once per period | Fazle-Core fazle_payroll_engine | Period-based idempotent calculation | domain/payroll/ |
| WORKFLOW-RELEASE-001 | Release (escort) has lifecycle | Fazle-Core escort_lifecycle | assignment → in-progress → completed | domain/workflow/release |

---

## AI Conversation Policy

| Rule ID | Rule | Normalized Rule |
|---|---|---|
| AI-001 | LLM never writes directly to database | AI calls domain services |
| AI-002 | AI identifies intent, code enforces policy | Intent → Domain Service → Validation → Write |
| AI-003 | AI explains ambiguity before merge | Ambiguous identity → reviewable event |
| AI-004 | AI prepares drafts, user approves | Draft → Validate → Approve → Execute |
| AI-005 | AI does not invent SQL for financial ops | Domain service handles all mutations |

---

## Security Policy

| Rule ID | Rule | Normalized Rule |
|---|---|---|
| SEC-001 | MCP tools declare permission class | READ, DRAFT, VALIDATE, WRITE, ADMIN |
| SEC-002 | Minimum permission principle | Agents receive only required classes |
| SEC-003 | No secrets in Git | .env excluded, secrets via Docker secrets |
| SEC-004 | Old system read-only | Connector queries never write to old DB |
| SEC-005 | Audit trail for all mutations | All writes → audit_log |

---

## Operational Policy

| Rule ID | Rule | Normalized Rule |
|---|---|---|
| OPS-001 | Scheduled tasks must be registered | Scheduler subsystem only |
| OPS-002 | No AI-generated root cron jobs | Tasks registered, documented, observable |
| OPS-003 | Idempotency for all mutations | Stable idempotency keys |
| OPS-004 | Observability without mutation rights | Monitoring ≠ admin |

---

## Duplicate Processing Rules

| Rule ID | Rule | Source | Normalized Rule |
|---|---|---|---|
| DUP-001 | Duplicate messages detected | Fazle-Core message_router | Dedup by idempotency key |
| DUP-002 | Duplicate transactions rejected | Fazle-Core payment | UNIQUE constraint on idempotency_key |
| DUP-003 | Duplicate employee creation prevented | Fazle-Core identity_brain | Identity resolution first |
| DUP-004 | Duplicate webhook handled | Fazle-Core bridge_poller | Idempotent processing |
