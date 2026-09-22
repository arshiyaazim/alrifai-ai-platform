-- C2 conversation/thread and scoped platform-identity foundation.
-- Apply only to an isolated local AL-RIFAI database.

ALTER TABLE external_platform_ids
    ADD COLUMN IF NOT EXISTS source_account TEXT NOT NULL DEFAULT 'default';

ALTER TABLE external_platform_ids
    DROP CONSTRAINT IF EXISTS external_platform_ids_person_id_platform_platform_user_id_key;

CREATE UNIQUE INDEX IF NOT EXISTS external_platform_identity_scope
    ON external_platform_ids (platform, source_account, platform_user_id);

CREATE TABLE conversation_threads (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel TEXT NOT NULL CHECK (channel IN (
        'bridge1', 'bridge2', 'bridge3', 'whatsapp', 'meta_whatsapp',
        'messenger', 'facebook_comment', 'internal'
    )),
    source_account TEXT NOT NULL,
    external_thread_id TEXT NOT NULL,
    conversation_scope TEXT NOT NULL CHECK (
        conversation_scope IN ('private', 'group', 'public', 'internal')
    ),
    person_id UUID REFERENCES persons(person_id) ON DELETE SET NULL,
    CONSTRAINT conversation_non_private_unlinked CHECK (
        conversation_scope NOT IN ('group', 'public') OR person_id IS NULL
    ),
    platform_identity JSONB,
    processing_state TEXT NOT NULL DEFAULT 'persisted' CHECK (
        processing_state IN ('received', 'persisted', 'pending', 'failed', 'retryable_failure')
    ),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (channel, source_account, external_thread_id, conversation_scope)
);

CREATE TABLE conversation_messages (
    message_id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL REFERENCES conversation_threads(conversation_id) ON DELETE CASCADE,
    external_message_id TEXT,
    channel TEXT NOT NULL,
    source_account TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    sender TEXT,
    recipient TEXT,
    person_id UUID REFERENCES persons(person_id) ON DELETE SET NULL,
    normalized_sender_mobile TEXT CHECK (
        normalized_sender_mobile IS NULL
        OR normalized_sender_mobile ~ '^0[0-9]{10}$'
    ),
    platform_identity JSONB,
    actor_type TEXT NOT NULL CHECK (
        actor_type IN ('external_user', 'human_device', 'human_operator',
                       'hermes_ai', 'automation', 'system', 'unknown')
    ),
    occurred_at TIMESTAMPTZ,
    received_at TIMESTAMPTZ,
    provider_sequence TEXT,
    previous_external_id TEXT,
    next_external_id TEXT,
    ordering_confidence NUMERIC CHECK (
        ordering_confidence IS NULL OR ordering_confidence BETWEEN 0 AND 1
    ),
    reply_to_message_id UUID REFERENCES conversation_messages(message_id),
    content_type TEXT NOT NULL,
    body TEXT,
    media_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    delivery_state TEXT,
    delivery_evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    processing_state TEXT NOT NULL DEFAULT 'persisted' CHECK (
        processing_state IN ('received', 'persisted', 'pending', 'failed', 'retryable_failure')
    ),
    idempotency_scope TEXT,
    idempotency_key TEXT,
    causation_id TEXT,
    correlation_id TEXT,
    provenance JSONB NOT NULL DEFAULT '[]'::jsonb,
    extraction_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    domain TEXT,
    topic TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (channel, source_account, external_message_id),
    UNIQUE (idempotency_scope, idempotency_key)
);

CREATE INDEX conversation_threads_person ON conversation_threads(person_id);
CREATE INDEX conversation_messages_thread_order
    ON conversation_messages(conversation_id, occurred_at, received_at, message_id);
CREATE INDEX conversation_messages_person ON conversation_messages(person_id);
