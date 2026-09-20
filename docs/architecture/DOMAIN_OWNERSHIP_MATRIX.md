# DOMAIN OWNERSHIP MATRIX

## Proposed top-level domains
1. Identity & Access
2. Business & Operations
3. Communications & Data Extraction
4. AI & Automation
5. Data & Integrations
6. Platform & Observability

## Ownership matrix

| MODULE | PRIMARY DOMAIN | SUBMODULE | DATABASE OWNER | SHARED DEPENDENCIES | MCP TOOL GROUP |
|---|---|---|---|---|---|
| Person / identity core | Identity & Access | persons, aliases, identifiers, phone matching | `alrifai-postgres` / `persons` family | shared across all workflows | `identity` |
| Employee lifecycle | Business & Operations | employees, payroll, leave, approvals | `employees`, `payout_accounts` | identity core, audit, payroll | `operations` |
| Recruitment / screening | Business & Operations | applicants, interview flow, offer/approval | `applicants`, `business_events` | identity core + audit | `recruitment` |
| Client operations | Business & Operations | client registry, billing account | `clients`, `payout_accounts` | identity core + audit + billing | `clients` |
| Messaging ingestion | Communications & Data Extraction | bridge ingestion, WhatsApp, Messenger, admin relay | current Fazle-Core `wbom_*` + `fazle_*` stores | identity resolution, audit, enrichment | `communications` |
| Message parsing / OCR / extraction | Communications & Data Extraction | text extraction, media OCR, entity extraction | current Fazle-Core extraction tables | identity core, AI automation, business events | `extraction` |
| AI classification / intent routing | AI & Automation | message intent classification, auto-triage | `business_events` or service state | communications, identity, domain services | `ai-automation` |
| Data ingestion / sync | Data & Integrations | ETL, API connectors, external source provenance | `provenance_records`, `business_events` | identity, communications, operations | `integration` |
| Payment / cash / ledger | Business & Operations | payroll, reimbursement, payout flows | `payout_accounts`, future financial tables | identity + audit + events | `finance` |
| Audit / traceability | Platform & Observability | audit log, correlation, health, service metrics | `audit_log` | all modules | `observability` |
| Platform runtime / deployment | Platform & Observability | service health, retries, operational boundaries | runtime state, logs | all modules | `platform` |

## Domain ownership assessment
This six-domain model covers the real current architecture better than ad hoc folder-level ownership. The key is to keep identity and audit as cross-cutting domains rather than embedding them in every business table.

## Recommended architecture
Use a modular monolith or bounded-domain service layout with a shared canonical identity layer and a single shared business engine. Avoid:
- one MCP tool per database table
- multiple identity stores
- separate business logic duplicated across message and form handlers

## Recommended implementation boundaries
- Identity & Access: `persons`, `person_*`, `employees`, `clients`, `applicants` as canonical references
- Business & Operations: business actions and approvals; must call shared domain services
- Communications & Data Extraction: message bridges and parser/validator pipeline only
- AI & Automation: intent/classification orchestration, enrichment, optional summarization
- Data & Integrations: ingest, provenance, ETL, sync adapters
- Platform & Observability: audits, correlation IDs, health checks, retry policies

## Final recommendation
A modular monolith with explicit domain boundaries is the best fit for the current state. It preserves clear ownership without forcing every table into a separate process.
