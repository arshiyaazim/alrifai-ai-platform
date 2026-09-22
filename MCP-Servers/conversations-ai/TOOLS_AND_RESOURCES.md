# Conversations and AI Tools and Resources

The canonical implementation specification is [`FINAL_IMPLEMENTATION_SPEC.md`](FINAL_IMPLEMENTATION_SPEC.md). The following catalog is design-only and is not an implemented API.

Final tools (18): `ingest_message`, `get_message`, `get_conversation`, `get_conversation_history`, `search_conversations`, `get_person_conversation_context`, `get_media_reference`, `compose_semantic_context`, `classify_domain_and_topic`, `extract_structured_message_data`, `get_missing_information`, `get_repeated_question_context`, `get_topic_state`, `update_topic_state`, `get_applicable_admin_instruction`, `prepare_domain_action`, `dispatch_domain_action`, `prepare_or_send_reply`.

Final resources (10): canonical message, conversation thread, media reference, Person conversation context, bounded semantic context, topic state, applicable Admin instruction, extraction draft, outbound delivery, and processing trace. AI outputs are evidence/drafts; domain services validate and commit. Raw NID/document content is not a default AI resource.
