# AL-RIFAI Data Dictionary

**Status:** DESIGN PHASE  
**Created:** 2026-09-19

Each field has a single, unambiguous meaning across the entire platform.

---

## Naming Convention Rules

Owner Employee-ID correction: `person_id` is the internal Person UUID. The authoritative business Employee ID is `employee_business_id`, the designated normalized Bangladeshi mobile (final 11 digits beginning with `0`). A physical UUID employee-record key, if retained, is technical only.

- `person_id` means exactly one thing everywhere (immutable UUID)
- `employee_id` physical UUID columns, where present, are internal employee-record keys only; they are not the business Employee ID
- `applicant_id` means exactly one thing everywhere
- Do not reuse the same name for different concepts
- Do not use different names for the same concept without explicit mapping

---

## Core Fields

### person_id
- **Display:** Person ID
- **Domain:** Identity
- **Type:** UUID
- **Nullable:** NO (PK)
- **Unique:** YES
- **Canonical Format:** `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- **Meaning:** Immutable canonical person identity
- **Source:** System-generated (uuid_generate_v4)
- **Privacy:** PII — restricted access
- **Mutable:** IMMUTABLE
- **Authoritative:** AL-RIFAI Platform

### employee_code
- **Display:** Employee Code
- **Domain:** Employee
- **Type:** TEXT
- **Nullable:** NO (UNIQUE)
- **Meaning:** Human-readable employee identifier (distinct from person_id)
- **Source:** Assigned on hire
- **Privacy:** Internal
- **Mutable:** NO (once assigned)

### employee_business_id
- **Display:** Employee ID
- **Domain:** Workforce / Employee
- **Type:** TEXT
- **Nullable:** NO for an active Employee
- **Unique:** YES after Bangladesh normalization
- **Canonical Format:** final 11 digits beginning with `0` (`01XXXXXXXXX`)
- **Meaning:** Authoritative business Employee identifier; designated normalized mobile number
- **Source:** Explicit authorized hire/handoff or `Edit Employee ID` workflow
- **Mutable:** Only through explicit authorized edit; prior values remain historical aliases
- **Note:** Contact/messaging numbers do not automatically change this value.

### phone_normalized
- **Display:** Phone (Normalized)
- **Domain:** Identity
- **Type:** TEXT
- **Nullable:** YES
- **Canonical Format:** final 11 digits beginning with `0` (`01XXXXXXXXX`)
- **Meaning:** Canonical normalized Bangladesh mobile comparison value for contact and identity evidence
- **Source:** phone_normalizer library
- **Privacy:** PII — restricted access
- **Mutable:** YES (via update process)
- **Authoritative:** phone_normalizer normalization

### payout_number
- **Display:** Payout Number
- **Domain:** Employee Financial
- **Type:** TEXT
- **Nullable:** YES
- **Meaning:** Financial routing attribute — NOT identity
- **Source:** Assigned during onboarding
- **Privacy:** Financial — restricted access
- **Mutable:** YES
- **Authoritative:** Payroll system

### status
- **Display:** Status
- **Domain:** All entities
- **Type:** TEXT
- **Meaning:** Current lifecycle state
- **Values:** active, inactive, suspended, pending, deleted, terminated, probation
- **Authoritative:** The owning domain service

---

## Business Tables

### employees
| Field | Type | Nullable | Unique | Meaning |
|---|---|---|---|---|
| employee_id | UUID | NO | YES | Physical internal employee-record key; not the business Employee ID |
| person_id | UUID | NO | — | FK to persons |
| employee_code | TEXT | NO | YES | Human-readable code |
| employee_business_id | TEXT | NO | YES | Authoritative normalized Bangladesh mobile Employee ID |
| display_name | TEXT | NO | — | Preferred display name |
| designation | TEXT | YES | — | Job title |
| department | TEXT | YES | — | Department |
| status | TEXT | NO | — | Lifecycle state |
| hire_date | DATE | YES | — | Employment start |
| termination_date | DATE | YES | — | End date |
| payout_number | TEXT | YES | — | Financial routing |
| manager_id | UUID | YES | — | FK to employees |
| source_system | TEXT | NO | — | Origin system |

### applicants
| Field | Type | Nullable | Meaning |
|---|---|---|---|
| applicant_id | UUID | NO | PK |
| person_id | UUID | YES | FK to persons |
| application_code | TEXT | NO | Unique application reference |
| position | TEXT | NO | Applied position |
| source | TEXT | YES | Where applied |
| status | TEXT | NO | Application state |
| applied_at | TIMESTAMPTZ | NO | Timestamp |

### clients
| Field | Type | Nullable | Meaning |
|---|---|---|---|
| client_id | UUID | NO | PK |
| person_id | UUID | YES | FK to persons |
| client_code | TEXT | NO | Unique client code |
| company_name | TEXT | YES | Company name |
| billing_email | TEXT | YES | |
| status | TEXT | NO | Lifecycle state |

---

## Audit & Events

### business_events
| Field | Type | Meaning |
|---|---|---|
| event_id | UUID | PK |
| event_type | TEXT | EMPLOYEE_CREATED, PAYMENT_CONFIRMED, etc. |
| aggregate_type | TEXT | Entity type (employee, applicant, client) |
| aggregate_id | UUID | The affected entity |
| actor_id | UUID | Who performed the action |
| payload | JSONB | Event data |
| idempotency_key | TEXT | Idempotency control |
| occurred_at | TIMESTAMPTZ | When |
| source_system | TEXT | Origin system |

### audit_log
| Field | Type | Meaning |
|---|---|---|
| audit_id | UUID | PK |
| entity_type | TEXT | Table name |
| entity_id | UUID | Row ID |
| action | TEXT | CREATE, UPDATE, DELETE, LOGIN, APPROVE |
| actor_id | UUID | Who |
| before_state | JSONB | Pre-state |
| after_state | JSONB | Post-state |
| ip_address | INET | Source IP |
| correlation_id | TEXT | Request trace |
| occurred_at | TIMESTAMPTZ | When |
