# Conversations & AI MCP

Purpose: normalize inbound/outbound channels, preserve raw messages and media references, manage conversation context, classify domains, extract structured drafts, coordinate Hermes/assistant behavior, and dispatch approved domain actions. Business owner: Communications/AI. It excludes direct business database writes, authorization decisions, and financial/HR/operations policy.

Hermes is consolidated here because it interprets and dispatches conversations; it is not a separate business server.

The implementation-ready contract is [`FINAL_IMPLEMENTATION_SPEC.md`](FINAL_IMPLEMENTATION_SPEC.md). C1–C4 are implemented and locally qualified within their approved scopes. C5 and later runtime work require separate explicit Owner approval.

Conversations & AI is the canonical owner of `Person → typed channel/platform identity → conversation/thread → ordered messages`. For every inbound WhatsApp message it preserves the normalized source phone and provenance, even when no domain action occurs. Recruitment receives trusted identity/context references and domain facts; it does not receive duplicated raw message tables.

Conversation understanding is stateful and semantic across misspellings, Bangla/Banglish, mixed language, incomplete follow-ups, message order, timestamps, reply relationships, topic state, relevant older turns, applicant facts, policy, and the latest applicable authorized Admin/Owner AI instruction. Keywords are hints/fallbacks only. Admin instructions are versioned, scoped, auditable guidance—not authorization to mutate business state.
Normalized sender mobile can resolve a trusted Applicant or Employee business ID for context, but a contact number observed in a message never mutates Employee ID. Employee-ID edits remain authorized Workforce/business operations.

The final catalog contains 10 scoped resources and 18 tools. Canonical messages are stored once; semantic context, topics, Admin instruction versions, structured extraction, dispatch, reply, delivery evidence, and audit remain within this consolidated server boundary.
