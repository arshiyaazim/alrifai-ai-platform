-- =============================================================================
-- AL-RIFAI AI OPERATIONS PLATFORM - Phase 4: Identity Foundation
-- This file is loaded by PostgreSQL on first startup via /docker-entrypoint-initdb.d/
-- =============================================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE persons (
    person_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    person_type TEXT NOT NULL CHECK (person_type IN ('EMPLOYEE','APPLICANT','CLIENT','CONTACT','VENDOR','UNKNOWN')),
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','suspended','pending','deleted')),
    national_id TEXT,
    phone_normalized TEXT,
    email_normalized TEXT
);

CREATE TABLE person_identifiers (
    identifier_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID NOT NULL REFERENCES persons(person_id) ON DELETE CASCADE,
    identifier_type TEXT NOT NULL CHECK (identifier_type IN ('NATIONAL_ID','PASSPORT','DRIVER_LICENSE','EMPLOYEE_CODE','EXTERNAL_PLATFORM','BIRTH_REGISTRATION','OTHER')),
    identifier_value TEXT NOT NULL,
    source_system TEXT NOT NULL,
    source_record_id TEXT,
    verified BOOLEAN NOT NULL DEFAULT false,
    verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(person_id, identifier_type, identifier_value)
);

CREATE TABLE person_phones (
    phone_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID NOT NULL REFERENCES persons(person_id) ON DELETE CASCADE,
    raw_value TEXT NOT NULL,
    normalized_value TEXT,
    country_code TEXT,
    phone_type TEXT CHECK (phone_type IN ('MOBILE','LANDLINE','WHATSAPP','TELEGRAM','OTHER')),
    is_primary BOOLEAN NOT NULL DEFAULT false,
    source_system TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(person_id, raw_value)
);

CREATE TABLE person_aliases (
    alias_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID NOT NULL REFERENCES persons(person_id) ON DELETE CASCADE,
    alias_value TEXT NOT NULL,
    alias_type TEXT CHECK (alias_type IN ('NAME','NICKNAME','INITIALS','DISPLAY_NAME','SPOUSE_NAME')),
    source_system TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE contact_methods (
    contact_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID NOT NULL REFERENCES persons(person_id) ON DELETE CASCADE,
    method_type TEXT NOT NULL CHECK (method_type IN ('EMAIL','PHONE','WHATSAPP','TELEGRAM','SIGNAL','LINKEDIN','OTHER')),
    value TEXT NOT NULL,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    verified_at TIMESTAMPTZ,
    source_system TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE payout_accounts (
    payout_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID NOT NULL REFERENCES persons(person_id) ON DELETE CASCADE,
    account_type TEXT NOT NULL CHECK (account_type IN ('BANK','BKASH','NAGAD','ROCKET','COD','PAYPAL','STRIPE','OTHER')),
    account_number TEXT NOT NULL,
    account_holder TEXT,
    bank_name TEXT,
    is_default BOOLEAN NOT NULL DEFAULT false,
    source_system TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE external_platform_ids (
    ext_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID NOT NULL REFERENCES persons(person_id) ON DELETE CASCADE,
    platform TEXT NOT NULL CHECK (platform IN ('WHATSAPP','FACEBOOK','TELEGRAM','SIGNAL','LINKEDIN','GITHUB','GOOGLE','MICROSOFT','OTHER')),
    platform_user_id TEXT NOT NULL,
    platform_user_name TEXT,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    source_system TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(person_id, platform, platform_user_id)
);

CREATE INDEX idx_persons_phone ON persons(phone_normalized);
CREATE INDEX idx_person_phones_normalized ON person_phones(normalized_value);
CREATE INDEX idx_person_phones_raw ON person_phones(raw_value);
CREATE INDEX idx_person_identifiers_value ON person_identifiers(identifier_value);
CREATE INDEX idx_external_platform_ids_platform ON external_platform_ids(platform, platform_user_id);

-- === EMPLOYEE ===
CREATE TABLE employees (
    employee_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID NOT NULL REFERENCES persons(person_id) ON DELETE CASCADE,
    employee_code TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    designation TEXT,
    department TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','suspended','probation','terminated')),
    hire_date DATE,
    termination_date DATE,
    payout_number TEXT,
    manager_id UUID REFERENCES employees(employee_id),
    source_system TEXT NOT NULL DEFAULT 'manual',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- === APPLICANT ===
CREATE TABLE applicants (
    applicant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID REFERENCES persons(person_id) ON DELETE SET NULL,
    application_code TEXT UNIQUE NOT NULL,
    position TEXT NOT NULL,
    source TEXT,
    status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new','screening','interviewing','offered','hired','rejected','withdrawn')),
    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_system TEXT NOT NULL DEFAULT 'manual',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- === CLIENT ===
CREATE TABLE clients (
    client_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id UUID REFERENCES persons(person_id) ON DELETE SET NULL,
    client_code TEXT UNIQUE NOT NULL,
    company_name TEXT,
    billing_email TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive','suspended')),
    source_system TEXT NOT NULL DEFAULT 'manual',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- === BUSINESS EVENTS ===
CREATE TABLE business_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type TEXT NOT NULL,
    aggregate_type TEXT NOT NULL,
    aggregate_id UUID NOT NULL,
    actor_id UUID REFERENCES persons(person_id),
    payload JSONB NOT NULL,
    idempotency_key TEXT,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source_system TEXT NOT NULL
);
CREATE INDEX idx_business_events_aggregate ON business_events(aggregate_type, aggregate_id);
CREATE INDEX idx_business_events_type ON business_events(event_type);
CREATE INDEX idx_business_events_idempotency ON business_events(idempotency_key);
CREATE INDEX idx_business_events_occurred ON business_events(occurred_at DESC);

-- === AUDIT LOG ===
CREATE TABLE audit_log (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('CREATE','UPDATE','DELETE','LOGIN','EXPORT','APPROVE','REJECT')),
    actor_id UUID REFERENCES persons(person_id),
    before_state JSONB,
    after_state JSONB,
    ip_address INET,
    user_agent TEXT,
    correlation_id TEXT,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_actor ON audit_log(actor_id);
CREATE INDEX idx_audit_log_time ON audit_log(occurred_at DESC);

-- === PROVENANCE RECORDS ===
CREATE TABLE provenance_records (
    provenance_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_system TEXT NOT NULL,
    source_record_id TEXT NOT NULL,
    source_timestamp TIMESTAMPTZ,
    ingestion_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    transformation_version TEXT,
    business_rule_version TEXT,
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    conflict_strategy TEXT CHECK (conflict_strategy IN ('skip','overwrite','merge','queue_review')),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','applied','conflict','rejected'))
);
