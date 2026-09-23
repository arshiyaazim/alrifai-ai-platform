-- C5 immutable Admin/Owner instruction versions and append-only lifecycle evidence.
-- Apply only after V006, V007, and V008 on an isolated local database.

CREATE TABLE conversation_ai_instruction_versions (
    version_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    instruction_id UUID NOT NULL,
    version INTEGER NOT NULL CHECK (version > 0),
    subject_key TEXT NOT NULL CHECK (length(trim(subject_key)) > 0),
    content TEXT NOT NULL CHECK (length(trim(content)) > 0),
    issuer_type TEXT NOT NULL CHECK (issuer_type IN ('owner', 'admin')),
    issuer_principal_id UUID NOT NULL REFERENCES auth_principals(principal_id),
    scope JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(scope) = 'object'),
    conversation_scope_id UUID REFERENCES conversation_threads(conversation_id),
    topic_scope_id UUID REFERENCES conversation_topics(topic_id),
    priority INTEGER NOT NULL DEFAULT 0,
    effective_from TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ,
    supersedes_version_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    correlation_id TEXT,
    idempotency_key TEXT,
    provenance JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(provenance) = 'array'),
    UNIQUE (instruction_id, version),
    UNIQUE (version_id, instruction_id),
    UNIQUE (issuer_principal_id, idempotency_key),
    FOREIGN KEY (supersedes_version_id, instruction_id)
        REFERENCES conversation_ai_instruction_versions(version_id, instruction_id),
    CHECK (expires_at IS NULL OR expires_at > effective_from),
    CHECK (topic_scope_id IS NULL OR conversation_scope_id IS NOT NULL)
);

CREATE INDEX conversation_ai_instruction_subject
    ON conversation_ai_instruction_versions(subject_key, issuer_type, effective_from DESC);
CREATE INDEX conversation_ai_instruction_conversation
    ON conversation_ai_instruction_versions(conversation_scope_id);
CREATE INDEX conversation_ai_instruction_topic
    ON conversation_ai_instruction_versions(topic_scope_id);

CREATE FUNCTION enforce_instruction_topic_conversation_scope() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.topic_scope_id IS NOT NULL AND NOT EXISTS (
        SELECT 1 FROM conversation_topics
        WHERE topic_id = NEW.topic_scope_id
          AND conversation_id = NEW.conversation_scope_id
    ) THEN
        RAISE EXCEPTION 'instruction topic must belong to its conversation scope';
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER conversation_ai_instruction_topic_scope
    BEFORE INSERT ON conversation_ai_instruction_versions
    FOR EACH ROW EXECUTE FUNCTION enforce_instruction_topic_conversation_scope();

CREATE TABLE conversation_ai_instruction_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id UUID NOT NULL REFERENCES conversation_ai_instruction_versions(version_id),
    event_type TEXT NOT NULL CHECK (event_type IN ('created','activated','revoked','superseded')),
    actor_principal_id UUID NOT NULL REFERENCES auth_principals(principal_id),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    idempotency_key TEXT,
    correlation_id TEXT,
    reason TEXT,
    UNIQUE (version_id, event_type),
    UNIQUE (actor_principal_id, idempotency_key)
);
CREATE INDEX conversation_ai_instruction_events_version
    ON conversation_ai_instruction_events(version_id, occurred_at, event_id);

CREATE FUNCTION reject_conversation_ai_instruction_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'conversation AI instruction history is append-only';
END;
$$;
CREATE TRIGGER conversation_ai_instruction_versions_immutable
    BEFORE UPDATE OR DELETE ON conversation_ai_instruction_versions
    FOR EACH ROW EXECUTE FUNCTION reject_conversation_ai_instruction_mutation();
CREATE TRIGGER conversation_ai_instruction_events_immutable
    BEFORE UPDATE OR DELETE ON conversation_ai_instruction_events
    FOR EACH ROW EXECUTE FUNCTION reject_conversation_ai_instruction_mutation();
