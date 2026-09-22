# Cross-Server Contracts

These are design contracts only. They are not implemented APIs.

## Shared request context

Every call carries a trusted server-created context: `actor`, `capabilities`, `person_id`, `canonical_phone_ref`, `platform_identity`, `source_channel`, `conversation_id`, `message_id`, `message_timestamp`, `reply_to_message_id`, `topic`, `semantic_intent`, `extracted_fields`, `confidence`, `evidence_refs`, `applicable_instruction_ref`, `correlation_id`, `causation_id`, `idempotency_key`, and `request_time`. Where an existing Employee is trusted, the context may also carry the authoritative normalized `employee_business_id`; an inbound phone claim is never sufficient to set or change it. Caller-supplied actor IDs, phone claims, AI fields, and MCP descriptions are never sufficient authority.

Conversations & AI additionally preserves source-account scope, received timestamp, provider ordering evidence, burst/turn member IDs, subject identity, topic state, retrieval metadata, extraction schema/version, and outbound delivery evidence where applicable. For natural-language tone only, it may pass `relationship_status=confirmed_current_employee` when C2 resolves the same Person and the canonical Employee status is active; all other/unverified cases are `unknown` and use respectful `আপনি`. This is evidence/context, not authorization, and never changes the authoritative Employee ID.

The Recruitment-facing envelope is conceptually:

```json
{
  "person_id": "trusted UUID or null",
  "employee_business_id": "trusted normalized Bangladesh mobile or null; context only, never caller-set",
  "relationship_status": "confirmed_current_employee|unknown",
  "relationship_evidence_refs": ["C2 resolution and active Employee record evidence IDs"],
  "canonical_phone_ref": {"normalized": "+880...", "kind": "current|historical"},
  "platform_identity": {"platform": "WHATSAPP", "external_id": "typed ID"},
  "conversation_id": "thread ID",
  "message_id": "message ID",
  "message_timestamp": "source timestamp",
  "reply_to_message_id": "optional message ID",
  "source_channel": "bridge1|bridge2|bridge3|meta|whatsapp|frontend",
  "topic": "C4 topic reference/state plus C7 association hypothesis; never a transition claim",
  "semantic_intent": "C7 non-authoritative hypothesis or null",
  "extracted_fields": {"claims": "typed values with evidence state, confidence, and message refs"},
  "confidence": 0.0,
  "evidence_refs": ["message/document/event IDs"],
  "grounding_refs": [{"ref": "canonical source/version", "class": "authoritative_fact|mandatory_rule|operational_guidance|style_guidance|illustrative_example|historical"}],
  "applicable_instruction_ref": "instruction ID/version or null",
  "correlation_id": "trace ID",
  "idempotency_key": "stable request key"
}
```

`relationship_status`, `semantic_intent`, `extracted_fields`, `topic`, `grounding_refs`, and `confidence` are evidence supplied by trusted canonical services/Conversations & AI, not authorization claims. Receiving domains validate against canonical identity, current policy, state, and capabilities. C7 never promotes illustrative examples or external messages into policy. Missing approved policy/source evidence remains unknown; it is not filled by model inference.

The canonical Conversations & AI specification defines the same envelope for Workforce, Finance & Payroll, Operations & Clients, and Platform/Admin dispatch. Receiving services must validate trusted actor/capabilities, domain policy, identity, idempotency, and persistence; AI interpretation never authorizes a mutation.

## Shared result classes

- `READ`: authoritative result or explicit not-found.
- `DRAFT`: proposed structured action with evidence and missing fields.
- `VALIDATE`: policy and invariant result without mutation.
- `WRITE`: committed mutation plus event/audit reference.
- `ADMIN`: privileged cross-domain action requiring trusted authorization and, where applicable, explicit approval.

## Contract boundaries

| Contract | Provider | Consumers | Rule |
|---|---|---|---|
| Resolve canonical identity | Shared identity service | All servers | Person UUID remains an internal Person key; designated normalized Bangladesh mobile is authoritative Employee ID only in the Employee business domain; payout numbers are never identity |
| Recruitment-to-workforce joining | Recruitment | Workforce, Platform/Admin | Verified identity and approved status transition required |
| Recruitment conversation dispatch | Conversations & AI | Recruitment | Pass trusted identity/context, extraction, evidence, correlation, and idempotency; classification never authorizes a write |
| Recruitment document handoff | Recruitment | Workforce, Platform/Admin | Pass candidate-provided storage reference, document type, provenance, Person/Application IDs, and intake/review state; Workforce performs formal employee-document verification without duplicating the binary |
| Recruitment conversation context | Conversations & AI | Recruitment | Preserve normalized source phone, typed platform identity, Person/context links, ordered message references, topic state, semantic extraction, confidence, evidence, and applicable instruction version; Recruitment receives trusted context, not duplicated raw messages |
| Employee business identifier | Workforce with shared identity support | Recruitment, Operations, Finance | Designated normalized Bangladesh mobile is the authoritative Employee ID; internal record keys are technical only; contact numbers do not mutate it; historical IDs, explicit edit audit, and conflicts are preserved/fail closed |
| Workforce-to-finance employee reference | Workforce | Finance & Payroll | Finance receives the authoritative normalized Employee ID and approved employment state, plus an internal technical reference only when needed for joins |
| Operations-to-finance bill/settlement | Operations | Finance & Payroll | Operational completion and financial settlement are separate events |
| Conversation domain dispatch | Conversations & AI | All business servers | Classification does not authorize a write |
| Audit/provenance | Shared platform service | All servers | Every mutation records actor, source, time, entity, action, outcome, correlation |
| Outbound delivery confirmation | Conversations & AI | Finance, Operations, Platform | Delivery is authoritative only for explicitly approved workflows, notably payment completion |

## Failure and retry

Use bounded, classified retries. Duplicate inbound messages, webhook redelivery, and delivery callbacks must be idempotent. Preserve exact message timestamps/order and reply relationships when rebuilding context. A failed AI call must not roll back an unrelated committed business transaction. A failed domain transaction must not be reported as successful. Cross-server calls must expose pending/review/failed outcomes rather than guessing.
