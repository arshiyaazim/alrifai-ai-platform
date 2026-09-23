-- AL-RIFAI authentication foundation.
-- Apply only to an isolated local AL-RIFAI database after owner approval.

CREATE TABLE auth_principals (
    principal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID REFERENCES persons(person_id) ON DELETE SET NULL,
    principal_type TEXT NOT NULL CHECK (principal_type IN (
        'OWNER','SUPER_ADMIN','ADMIN','OFFICE_STAFF','OPERATIONS',
        'ACCOUNTANT','EMPLOYEE','APPLICANT','CLIENT','AI_SERVICE'
    )),
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('active','pending','disabled','revoked')),
    must_change_password BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX auth_one_owner ON auth_principals (principal_type)
WHERE principal_type = 'OWNER';
CREATE INDEX auth_principals_person ON auth_principals(person_id);

CREATE TABLE auth_password_credentials (
    credential_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id UUID NOT NULL UNIQUE REFERENCES auth_principals(principal_id) ON DELETE CASCADE,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    failed_attempts INTEGER NOT NULL DEFAULT 0 CHECK (failed_attempts >= 0),
    locked_until TIMESTAMPTZ,
    password_changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE auth_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id UUID NOT NULL REFERENCES auth_principals(principal_id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    csrf_token_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at TIMESTAMPTZ,
    source TEXT NOT NULL DEFAULT 'frontend'
);
CREATE INDEX auth_sessions_principal ON auth_sessions(principal_id);
CREATE INDEX auth_sessions_active ON auth_sessions(expires_at) WHERE revoked_at IS NULL;

CREATE TABLE auth_roles (
    role_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE auth_permissions (
    permission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    permission_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE auth_role_permissions (
    role_id UUID NOT NULL REFERENCES auth_roles(role_id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES auth_permissions(permission_id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE auth_principal_roles (
    principal_id UUID NOT NULL REFERENCES auth_principals(principal_id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES auth_roles(role_id) ON DELETE CASCADE,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (principal_id, role_id)
);

CREATE TABLE auth_password_resets (
    reset_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    principal_id UUID NOT NULL REFERENCES auth_principals(principal_id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    consumed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE audit_log
    DROP CONSTRAINT IF EXISTS audit_log_action_check;
ALTER TABLE audit_log
    ADD CONSTRAINT audit_log_action_check CHECK (
        action IN ('CREATE','UPDATE','DELETE','LOGIN','LOGOUT','EXPORT',
                   'APPROVE','REJECT','RESET','BOOTSTRAP','DENY')
    );
ALTER TABLE audit_log
    ADD COLUMN IF NOT EXISTS actor_principal_id UUID REFERENCES auth_principals(principal_id) ON DELETE SET NULL;
CREATE INDEX audit_log_principal ON audit_log(actor_principal_id);

INSERT INTO auth_permissions (permission_name)
VALUES
    ('manage_users'), ('manage_roles'), ('manage_permissions'),
    ('manage_configuration'), ('view_all_business_data'),
    ('view_unmasked_contacts'), ('manage_applicants'), ('manage_employees'),
    ('manage_payroll'), ('manage_cash'), ('manage_conversations'),
    ('manage_escorts'), ('view_reports'), ('approve_business_operations'),
    ('hire_applicant'), ('mcp_admin')
ON CONFLICT (permission_name) DO NOTHING;

INSERT INTO auth_roles (role_name, description)
VALUES
    ('ADMIN', 'Administrative platform access'),
    ('OFFICE_STAFF', 'Office operations access'),
    ('OPERATIONS', 'Operations access'),
    ('ACCOUNTANT', 'Accounting access'),
    ('EMPLOYEE', 'Employee self-service access'),
    ('APPLICANT', 'Applicant access'),
    ('CLIENT', 'Client access')
ON CONFLICT (role_name) DO NOTHING;

-- Rollback: revoke sessions, remove auth tables, and restore the original
-- audit action constraint only after confirming no auth data is needed.
