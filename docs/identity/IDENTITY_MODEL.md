# AL-RIFAI Identity Model

**Status:** DESIGN PHASE  
**Created:** 2026-09-19  
**Provenance:** Fazle-Core `phone_normalizer`, `number_identity`, `identity_brain`, `group_identity`, `identity_resolver` modules (READ-ONLY discovery)

---

## Problem Statement

The previous system experienced recurring identity problems:
- Duplicate people with different spellings
- Phone numbers treated as identity
- Payout numbers confused with employee IDs
- Missing canonical internal IDs
- Inconsistent matching across modules
- Inactive employees matched by stable identifier

**Core Rule:** `name ≠ identity`, `phone ≠ person`, `payout number ≠ employee ID`

---

## Canonical Identity Tables

### `persons` (Core entity)
Immutable internal primary key via UUID (`person_id`). Human-readable attributes are stored but never used as identity.

| Field | Type | Nullable | Description |
|---|---|---|---|
| `person_id` | UUID | NO (PK) | Immutable canonical identity |
| `person_type` | TEXT | NO | EMPLOYEE, APPLICANT, CLIENT, CONTACT, VENDOR |
| `status` | TEXT | NO | active, inactive, suspended, pending, deleted |
| `phone_normalized` | TEXT | YES | Canonical normalized phone |
| `email_normalized` | TEXT | YES | Canonical normalized email |
| `national_id` | TEXT | YES | Government ID (if applicable) |
| `created_at` | TIMESTAMPTZ | NO | |
| `updated_at` | TIMESTAMPTZ | NO | |

### `person_identifiers` (Stable external identifiers)
| Field | Type | Description |
|---|---|---|
| `identifier_id` | UUID | PK |
| `person_id` | UUID | FK to persons |
| `identifier_type` | TEXT | NATIONAL_ID, PASSPORT, EMPLOYEE_CODE, EXTERNAL_PLATFORM |
| `identifier_value` | TEXT | The actual identifier value |
| `source_system` | TEXT | Which system provided this |
| `verified` | BOOLEAN | Verification status |
| `created_at` | TIMESTAMPTZ | |

### `person_phones` (Contact methods, NOT identity)
| Field | Type | Description |
|---|---|---|
| `phone_id` | UUID | PK |
| `person_id` | UUID | FK |
| `raw_value` | TEXT | Original observed value |
| `normalized_value` | TEXT | Canonical normalized format |
| `phone_type` | TEXT | MOBILE, WHATSAPP, LANDLINE, TELEGRAM |
| `is_primary` | BOOLEAN | Primary contact flag |
| `source_system` | TEXT | |

### `person_aliases` (Name variations)
| Field | Type | Description |
|---|---|---|
| `alias_id` | UUID | PK |
| `person_id` | UUID | FK |
| `alias_value` | TEXT | Name variant |
| `alias_type` | TEXT | NAME, NICKNAME, DISPLAY_NAME |
| `source_system` | TEXT | |

### `contact_methods` (Generic contact channels)
| Field | Type | Description |
|---|---|---|
| `contact_id` | UUID | PK |
| `person_id` | UUID | FK |
| `method_type` | TEXT | EMAIL, PHONE, WHATSAPP, TELEGRAM, LINKEDIN |
| `value` | TEXT | The contact value |
| `is_verified` | BOOLEAN | |
| `source_system` | TEXT | |

### `payout_accounts` (Financial routing — NOT identity)
| Field | Type | Description |
|---|---|---|
| `payout_id` | UUID | PK |
| `person_id` | UUID | FK |
| `account_type` | TEXT | BANK, BKASH, NAGAD, ROCKET, COD |
| `account_number` | TEXT | |
| `account_holder` | TEXT | |
| `is_default` | BOOLEAN | |

### `external_platform_ids` (Typed external IDs)
| Field | Type | Description |
|---|---|---|
| `ext_id` | UUID | PK |
| `person_id` | UUID | FK |
| `platform` | TEXT | WHATSAPP, FACEBOOK, TELEGRAM, etc. |
| `platform_user_id` | TEXT | The external ID |
| `is_verified` | BOOLEAN | |

---

## Identity Resolution Algorithm

```
incoming observation
       │
       ▼
normalize identifiers (phone, email, national_id)
       │
       ▼
exact stable identifier match?
       │              │
      YES             NO
       │              │
       ▼              ▼
  resolve          candidate matching
  existing         (by normalized phone,
  person           alias, identifier)
       │              │
       ▼              ▼
  confidence/evidence   │
       │              │
  ┌────┴────┐    ┌────┴────┐
  ▼         ▼    ▼         ▼
safe     ambiguous  safe    ambiguous
match    match      match   match
  │         │        │        │
  ▼         ▼        ▼        ▼
existing  review   existing  review
person    queue    person    queue
```

**Rules:**
- LLM must NEVER silently merge people
- Ambiguous identity = reviewable event
- Every merge/link is auditable
- Reversible where practical
- Deterministic resolution only (no LLM-based merging)

---

## Phone Number Normalization

One canonical library/service for all modules. Bangladeshi format (`+880XXXXXXXXX`) normalized consistently. Raw observed values preserved alongside normalized values.

**Provenance:** Fazle-Core `phone_normalizer` module  
**Implementation Location:** `domain/identity/phone_normalizer.py`  
**Test Coverage:** Required (see `tests/`)

---

## Identity Resolution Rules

| Rule ID | Rule | Source |
|---|---|---|
| `IDENTITY-001` | A person is identified by immutable UUID, never by name or phone | Fazle-Core identity_brain |
| `IDENTITY-002` | Phone numbers are contact methods, never the primary key | Fazle-Core number_identity |
| `IDENTITY-003` | Payout numbers are financial routing, never person identity | Fazle-Core payroll |
| `IDENTITY-004` | External platform IDs (WhatsApp/Facebook) must be explicitly typed | Fazle-Core contact_roles |
| `IDENTITY-005` | Name variations are aliases, never the identity | Fazle-Core group_identity |
