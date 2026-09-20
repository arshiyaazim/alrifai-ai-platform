# NEW AL-RIFAI SCHEMA AUDIT

## Scope
- Database: `alrifai-postgres`
- Port: `127.0.0.1:5434`
- Live status: healthy
- Schema source: actual live DB + `database/init-sql/001_identity_foundation.sql`

## Verified live schema
The database is live and currently contains exactly 13 tables:
- persons
- person_identifiers
- person_phones
- person_aliases
- contact_methods
- payout_accounts
- external_platform_ids
- employees
- applicants
- clients
- business_events
- audit_log
- provenance_records

The live schema matches the init SQL file `database/init-sql/001_identity_foundation.sql`.

## Migration status
There are no actual SQL migration files under `database/migrations`; only `database/migrations/VERSIONS.md` documents the intended naming scheme. The live schema is created by the init script and is therefore the current source of truth for this audit.

## Table-by-table inventory

### 1) persons
Purpose: top-level canonical person entity and shared identity root.
Columns:
- `person_id` UUID PK DEFAULT uuid_generate_v4()
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
- `person_type` TEXT NOT NULL CHECK IN ('EMPLOYEE','APPLICANT','CLIENT','CONTACT','VENDOR','UNKNOWN')
- `status` TEXT NOT NULL DEFAULT 'active' CHECK IN ('active','inactive','suspended','pending','deleted')
- `national_id` TEXT NULL
- `phone_normalized` TEXT NULL
- `email_normalized` TEXT NULL
Related tables: `person_identifiers`, `person_phones`, `person_aliases`, `contact_methods`, `external_platform_ids`, `employees`, `applicants`, `clients`
Expected domain owner: Identity & Access

### 2) person_identifiers
Purpose: government and external identifiers for a person.
Columns:
- `identifier_id` UUID PK DEFAULT uuid_generate_v4()
- `person_id` UUID NOT NULL FK -> persons(person_id)
- `identifier_type` TEXT NOT NULL CHECK IN ('NATIONAL_ID','PASSPORT','DRIVER_LICENSE','EMPLOYEE_CODE','EXTERNAL_PLATFORM','BIRTH_REGISTRATION','OTHER')
- `identifier_value` TEXT NOT NULL
- `source_system` TEXT NOT NULL
- `source_record_id` TEXT NULL
- `verified` BOOLEAN NOT NULL DEFAULT false
- `verified_at` TIMESTAMPTZ NULL
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
Unique: `(person_id, identifier_type, identifier_value)`
Related tables: `persons`
Expected domain owner: Identity & Access

### 3) person_phones
Purpose: phone numbers tied to a person with raw and normalized values.
Columns:
- `phone_id` UUID PK DEFAULT uuid_generate_v4()
- `person_id` UUID NOT NULL FK -> persons(person_id)
- `raw_value` TEXT NOT NULL
- `normalized_value` TEXT NULL
- `country_code` TEXT NULL
- `phone_type` TEXT CHECK IN ('MOBILE','LANDLINE','WHATSAPP','TELEGRAM','OTHER')
- `is_primary` BOOLEAN NOT NULL DEFAULT false
- `source_system` TEXT NOT NULL
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
Unique: `(person_id, raw_value)`
Indexes: `idx_person_phones_normalized`, `idx_person_phones_raw`
Related tables: `persons`
Expected domain owner: Identity & Access

### 4) person_aliases
Purpose: alternative names and display names for a person.
Columns:
- `alias_id` UUID PK DEFAULT uuid_generate_v4()
- `person_id` UUID NOT NULL FK -> persons(person_id)
- `alias_value` TEXT NOT NULL
- `alias_type` TEXT CHECK IN ('NAME','NICKNAME','INITIALS','DISPLAY_NAME','SPOUSE_NAME')
- `source_system` TEXT NOT NULL
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
Related tables: `persons`
Expected domain owner: Identity & Access

### 5) contact_methods
Purpose: general-purpose communication channels.
Columns:
- `contact_id` UUID PK DEFAULT uuid_generate_v4()
- `person_id` UUID NOT NULL FK -> persons(person_id)
- `method_type` TEXT NOT NULL CHECK IN ('EMAIL','PHONE','WHATSAPP','TELEGRAM','SIGNAL','LINKEDIN','OTHER')
- `value` TEXT NOT NULL
- `is_verified` BOOLEAN NOT NULL DEFAULT false
- `verified_at` TIMESTAMPTZ NULL
- `source_system` TEXT NOT NULL
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
Related tables: `persons`
Expected domain owner: Identity & Access

### 6) payout_accounts
Purpose: financial routing destination options for a person.
Columns:
- `payout_id` UUID PK DEFAULT uuid_generate_v4()
- `person_id` UUID NOT NULL FK -> persons(person_id)
- `account_type` TEXT NOT NULL CHECK IN ('BANK','BKASH','NAGAD','ROCKET','COD','PAYPAL','STRIPE','OTHER')
- `account_number` TEXT NOT NULL
- `account_holder` TEXT NULL
- `bank_name` TEXT NULL
- `is_default` BOOLEAN NOT NULL DEFAULT false
- `source_system` TEXT NOT NULL
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
Related tables: `persons`
Expected domain owner: Business & Operations

### 7) external_platform_ids
Purpose: platform accounts and external identifiers.
Columns:
- `ext_id` UUID PK DEFAULT uuid_generate_v4()
- `person_id` UUID NOT NULL FK -> persons(person_id)
- `platform` TEXT NOT NULL CHECK IN ('WHATSAPP','FACEBOOK','TELEGRAM','SIGNAL','LINKEDIN','GITHUB','GOOGLE','MICROSOFT','OTHER')
- `platform_user_id` TEXT NOT NULL
- `platform_user_name` TEXT NULL
- `is_verified` BOOLEAN NOT NULL DEFAULT false
- `source_system` TEXT NOT NULL
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
Unique: `(person_id, platform, platform_user_id)`
Indexes: `idx_external_platform_ids_platform`
Related tables: `persons`
Expected domain owner: Communications & Data Extraction

### 8) employees
Purpose: employee roster with canonical identity linkage.
Columns:
- `employee_id` UUID PK DEFAULT uuid_generate_v4()
- `person_id` UUID NOT NULL FK -> persons(person_id)
- `employee_code` TEXT UNIQUE NOT NULL
- `display_name` TEXT NOT NULL
- `designation` TEXT NULL
- `department` TEXT NULL
- `status` TEXT NOT NULL DEFAULT 'active' CHECK IN ('active','inactive','suspended','probation','terminated')
- `hire_date` DATE NULL
- `termination_date` DATE NULL
- `payout_number` TEXT NULL
- `manager_id` UUID NULL FK -> employees(employee_id)
- `source_system` TEXT NOT NULL DEFAULT 'manual'
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
- `updated_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
Related tables: `persons`, `employees` (self-FK)
Expected domain owner: Business & Operations

### 9) applicants
Purpose: recruitment applicants and application intake.
Columns:
- `applicant_id` UUID PK DEFAULT uuid_generate_v4()
- `person_id` UUID NULL FK -> persons(person_id)
- `application_code` TEXT UNIQUE NOT NULL
- `position` TEXT NOT NULL
- `source` TEXT NULL
- `status` TEXT NOT NULL DEFAULT 'new' CHECK IN ('new','screening','interviewing','offered','hired','rejected','withdrawn')
- `applied_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
- `source_system` TEXT NOT NULL DEFAULT 'manual'
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
Related tables: `persons`
Expected domain owner: Business & Operations

### 10) clients
Purpose: client-facing business entity.
Columns:
- `client_id` UUID PK DEFAULT uuid_generate_v4()
- `person_id` UUID NULL FK -> persons(person_id)
- `client_code` TEXT UNIQUE NOT NULL
- `company_name` TEXT NULL
- `billing_email` TEXT NULL
- `status` TEXT NOT NULL DEFAULT 'active' CHECK IN ('active','inactive','suspended')
- `source_system` TEXT NOT NULL DEFAULT 'manual'
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
Related tables: `persons`
Expected domain owner: Business & Operations

### 11) business_events
Purpose: event log for business actions and state changes.
Columns:
- `event_id` UUID PK DEFAULT uuid_generate_v4()
- `event_type` TEXT NOT NULL
- `aggregate_type` TEXT NOT NULL
- `aggregate_id` UUID NOT NULL
- `actor_id` UUID NULL FK -> persons(person_id)
- `payload` JSONB NOT NULL
- `idempotency_key` TEXT NULL
- `occurred_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
- `source_system` TEXT NOT NULL
Indexes: `idx_business_events_aggregate`, `idx_business_events_type`, `idx_business_events_idempotency`, `idx_business_events_occurred`
Related tables: `persons`
Expected domain owner: Data & Integrations

### 12) audit_log
Purpose: explicit audit trail for entity changes and actions.
Columns:
- `audit_id` UUID PK DEFAULT uuid_generate_v4()
- `entity_type` TEXT NOT NULL
- `entity_id` UUID NOT NULL
- `action` TEXT NOT NULL CHECK IN ('CREATE','UPDATE','DELETE','LOGIN','EXPORT','APPROVE','REJECT')
- `actor_id` UUID NULL FK -> persons(person_id)
- `before_state` JSONB NULL
- `after_state` JSONB NULL
- `ip_address` INET NULL
- `user_agent` TEXT NULL
- `correlation_id` TEXT NULL
- `occurred_at` TIMESTAMPTZ NOT NULL DEFAULT NOW()
Indexes: `idx_audit_log_entity`, `idx_audit_log_actor`, `idx_audit_log_time`
Related tables: `persons`
Expected domain owner: Platform & Observability

### 13) provenance_records
Purpose: source provenance and transformation tracking for imported data.
Columns:
- `provenance_id` UUID PK DEFAULT uuid_generate_v4()
- `source_system` TEXT NOT NULL
- `source_record_id` TEXT NOT NULL
- `source_timestamp` TIMESTAMPTZ NULL
- `ingestion_timestamp` TIMESTAMPTZ NOT NULL DEFAULT NOW()
- `transformation_version` TEXT NULL
- `business_rule_version` TEXT NULL
- `entity_type` TEXT NOT NULL
- `entity_id` UUID NOT NULL
- `conflict_strategy` TEXT CHECK IN ('skip','overwrite','merge','queue_review')
- `status` TEXT NOT NULL DEFAULT 'pending' CHECK IN ('pending','applied','conflict','rejected')
Related tables: none (source-of-truth provenance table)
Expected domain owner: Data & Integrations

## Schema validation summary
- Live DB: verified.
- Schema matches init SQL: verified.
- Migration ownership: documented but not fully materialized as SQL files in repo; therefore live schema is the authoritative source for this audit.
