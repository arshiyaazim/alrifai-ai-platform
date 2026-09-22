-- Manual rollback for V007. Apply only to an isolated local database.

DROP TABLE IF EXISTS conversation_messages;
DROP TABLE IF EXISTS conversation_threads;
DROP INDEX IF EXISTS external_platform_identity_scope;

ALTER TABLE external_platform_ids
    DROP COLUMN IF EXISTS source_account;

ALTER TABLE external_platform_ids
    ADD CONSTRAINT external_platform_ids_person_id_platform_platform_user_id_key
    UNIQUE (person_id, platform, platform_user_id);
