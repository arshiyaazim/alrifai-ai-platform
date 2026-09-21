-- Manual rollback for V006. Do not execute against production or business data.
-- Confirm the target is the isolated local database before running.

DROP TABLE IF EXISTS auth_password_resets;
DROP TABLE IF EXISTS auth_principal_roles;
DROP TABLE IF EXISTS auth_role_permissions;
DROP TABLE IF EXISTS auth_permissions;
DROP TABLE IF EXISTS auth_roles;
DROP TABLE IF EXISTS auth_sessions;
DROP TABLE IF EXISTS auth_password_credentials;
DROP TABLE IF EXISTS auth_principals;

ALTER TABLE audit_log DROP CONSTRAINT IF EXISTS audit_log_actor_principal_id_fkey;
ALTER TABLE audit_log DROP COLUMN IF EXISTS actor_principal_id;
ALTER TABLE audit_log DROP CONSTRAINT IF EXISTS audit_log_action_check;
ALTER TABLE audit_log ADD CONSTRAINT audit_log_action_check CHECK (
    action IN ('CREATE','UPDATE','DELETE','LOGIN','EXPORT','APPROVE','REJECT')
);
