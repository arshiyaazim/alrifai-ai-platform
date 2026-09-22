# Conversations and AI Legacy Mapping

The canonical target and implementation sequence are defined in [`FINAL_IMPLEMENTATION_SPEC.md`](FINAL_IMPLEMENTATION_SPEC.md). Legacy components remain read-only evidence and are not runtime dependencies of this specification.

Evidence: active `whatsapp-bridge`, `whatsapp-bridge2`, and `whatsapp-bridge3` services; `modules/bridge_poller`, `message_router`, `identity_brain`, `hermes_dispatch`, `conversation_canonical`, `message_archive`, `outbound`, social/Meta handlers; live `wbom_whatsapp_messages` (32,436), `fazle_conversations` (2), `fazle_messages` (8), Hermes task/approval tables, intents, drafts, and delivery tables (`VERIFIED_LIVE`/`VERIFIED_SOURCE`).

Gap: raw messages and conversation memory are separate models; Bridge 1/2/3, Meta, Messenger, and Facebook comments have uneven delivery/CRUD semantics. Live platform evidence verifies bridge1/2/3, meta, and whatsapp, but current Messenger/Facebook activity remains `UNKNOWN`. Existing duplicate prevention is not universal. Legacy source fields include normalized phone, platform, conversation key, actor, timestamp, workflow, and provenance, but AL-RIFAI must make phone preservation, ordered context, topic state, semantic retrieval, and instruction versioning explicit. Legacy remains read-only.
