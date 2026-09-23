-- V010 rollback: remove canonical AI runtime configuration tables.

DROP TABLE IF EXISTS ai_runtime_state;
DROP TABLE IF EXISTS ai_gateway_configs;
