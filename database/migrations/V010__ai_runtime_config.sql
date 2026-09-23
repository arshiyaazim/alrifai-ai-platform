-- V010: canonical AI runtime gateway configuration (C7 live-route prerequisite).
-- Stores approved gateways plus the single active gateway reference.
-- Secrets are never stored here; secret_ref names env/file server-side only.

CREATE TABLE IF NOT EXISTS ai_gateway_configs (
    gateway_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    gateway_type TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    auth_mode TEXT NOT NULL,
    secret_ref TEXT,
    route TEXT NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    is_local BOOLEAN NOT NULL DEFAULT FALSE,
    fallback_gateway_id TEXT REFERENCES ai_gateway_configs (gateway_id),
    config_version INTEGER NOT NULL DEFAULT 1,
    updated_by TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_test_at TIMESTAMPTZ,
    last_test_ok BOOLEAN,
    CONSTRAINT ai_gateway_configs_type CHECK (gateway_type IN ('nine_router', 'openai_compatible', 'ollama', 'local_model')),
    CONSTRAINT ai_gateway_configs_auth CHECK (auth_mode IN ('api_key', 'none')),
    CONSTRAINT ai_gateway_configs_no_self_fallback CHECK (fallback_gateway_id IS NULL OR fallback_gateway_id <> gateway_id)
);

CREATE TABLE IF NOT EXISTS ai_runtime_state (
    singleton_id INTEGER PRIMARY KEY DEFAULT 1,
    active_gateway_id TEXT REFERENCES ai_gateway_configs (gateway_id),
    CONSTRAINT ai_runtime_state_singleton CHECK (singleton_id = 1)
);

INSERT INTO ai_runtime_state (singleton_id, active_gateway_id)
VALUES (1, NULL)
ON CONFLICT (singleton_id) DO NOTHING;
