-- Manual rollback for V008. Apply only to an isolated local database.

DROP TABLE IF EXISTS conversation_topic_transitions;
DROP TABLE IF EXISTS conversation_topics;
