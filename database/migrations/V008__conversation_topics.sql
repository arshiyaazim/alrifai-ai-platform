-- C4 topic state and immutable transition history.
-- Apply only to an isolated local AL-RIFAI database.

CREATE TABLE conversation_topics (
    topic_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversation_threads(conversation_id) ON DELETE CASCADE,
    conversation_scope TEXT NOT NULL CHECK (
        conversation_scope IN ('private', 'group', 'public', 'internal')
    ),
    channel TEXT NOT NULL CHECK (channel IN (
        'bridge1', 'bridge2', 'bridge3', 'whatsapp', 'meta_whatsapp',
        'messenger', 'facebook_comment', 'internal'
    )),
    source_account TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN (
        'opened', 'gathering', 'awaiting_user', 'awaiting_approval',
        'suspended', 'completed', 'closed', 'reopened', 'unresolved'
    )),
    domain TEXT,
    semantic_label TEXT,
    related_topic_id UUID REFERENCES conversation_topics(topic_id) ON DELETE SET NULL,
    evidence_message_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_turn_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    last_activity_at TIMESTAMPTZ,
    state_version INTEGER NOT NULL DEFAULT 0 CHECK (state_version >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT topic_scope_owner_boundary CHECK (
        conversation_scope IN ('group', 'public') OR conversation_scope IN ('private', 'internal')
    )
);

CREATE INDEX conversation_topics_conversation
    ON conversation_topics(conversation_id, updated_at DESC);
CREATE INDEX conversation_topics_state
    ON conversation_topics(conversation_id, state);

CREATE TABLE conversation_topic_transitions (
    transition_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID NOT NULL REFERENCES conversation_topics(topic_id) ON DELETE CASCADE,
    from_state TEXT CHECK (from_state IS NULL OR from_state IN (
        'opened', 'gathering', 'awaiting_user', 'awaiting_approval',
        'suspended', 'completed', 'closed', 'reopened', 'unresolved'
    )),
    to_state TEXT NOT NULL CHECK (to_state IN (
        'opened', 'gathering', 'awaiting_user', 'awaiting_approval',
        'suspended', 'completed', 'closed', 'reopened', 'unresolved'
    )),
    transition_kind TEXT NOT NULL,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    conversation_id UUID NOT NULL REFERENCES conversation_threads(conversation_id) ON DELETE CASCADE,
    message_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    turn_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    actor TEXT NOT NULL,
    source TEXT NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    correlation_id TEXT,
    causation_id TEXT,
    idempotency_key TEXT,
    state_version INTEGER NOT NULL CHECK (state_version >= 0),
    UNIQUE (topic_id, idempotency_key)
);

CREATE INDEX conversation_topic_transitions_topic
    ON conversation_topic_transitions(topic_id, state_version, occurred_at);
