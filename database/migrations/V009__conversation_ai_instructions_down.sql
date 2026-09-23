-- Manual rollback for V009. Apply only to a disposable isolated local database.
DROP TRIGGER IF EXISTS conversation_ai_instruction_events_immutable ON conversation_ai_instruction_events;
DROP TRIGGER IF EXISTS conversation_ai_instruction_versions_immutable ON conversation_ai_instruction_versions;
DROP TRIGGER IF EXISTS conversation_ai_instruction_topic_scope ON conversation_ai_instruction_versions;
DROP FUNCTION IF EXISTS enforce_instruction_topic_conversation_scope();
DROP FUNCTION IF EXISTS reject_conversation_ai_instruction_mutation();
DROP TABLE IF EXISTS conversation_ai_instruction_events;
DROP TABLE IF EXISTS conversation_ai_instruction_versions;
