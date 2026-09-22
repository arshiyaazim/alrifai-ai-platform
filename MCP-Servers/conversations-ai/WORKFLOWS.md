# Conversations and AI Workflows

The complete design is [`FINAL_IMPLEMENTATION_SPEC.md`](FINAL_IMPLEMENTATION_SPEC.md). C1–C4 structural foundations are implemented and qualified; semantic/Admin/Hermes/dispatch/reply/outbound stages remain paused pending explicit Owner approval.

Inbound Bridge/Meta/Messenger/social/admin relay → preserve source phone/platform identity and timestamps → normalize source and IDs → persist raw evidence → deduplicate → resolve Person → retrieve ordered/relevant context → maintain topic state → semantic classify/extract → apply latest applicable Admin instruction → route to a domain service → receive policy/result → queue reply → track delivery.

Search/context is read-only. Domain dispatch carries trusted actor context, Person/current-phone reference, conversation/message IDs, timestamp/reply order, topic, semantic extraction, confidence, evidence, instruction version, and idempotency, but never upgrades authority. Media/OCR, Hermes, prompts, and model choice remain replaceable adapters. Duplicate inbound events and outbound retries must be safe. Recruitment owns applicant/application facts and actions; Conversations & AI owns canonical messages, semantic retrieval, topic/context construction, Admin instruction retrieval, and natural-language replies.
When a trusted Employee is recognized, context may include the normalized business Employee ID for lookup and personalization. A sender number that differs from that ID is retained as contact/provenance evidence and cannot trigger an Employee-ID mutation.

Several short same-thread messages may be aggregated into one turn only when sender, thread, reply boundary, timing, continuation evidence, and topic scope permit it. Topic closure, semantic repetition, subject ambiguity, versioned Admin instructions, bounded retrieval, structured extraction, deterministic domain dispatch, human handoff, outbound authorization, and delivery evidence are specified in the canonical document.
