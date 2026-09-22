# Conversations & AI MCP — Final Implementation Specification

**Status:** Specification only; runtime implementation is not authorized by this document.
**Owner:** Communications / AI
**Server count:** One consolidated Conversations & AI MCP. Channels, Hermes, topics, message storage, and Admin AI instructions are capabilities of this server, not separate MCP servers.

## 1. Scope and authority

Conversations & AI owns transport-neutral conversation orchestration:

```text
Inbound message/media
  → channel adapter
  → canonical persistence
  → phone/platform/Person resolution
  → conversation/thread resolution
  → ordered history
  → burst/turn aggregation
  → bounded semantic context retrieval
  → topic state
  → latest applicable Admin/Owner instruction
  → Hermes interpretation/extraction
  → deterministic domain dispatch
  → canonical domain service
  → authorization, policy, transaction, persistence
  → structured result
  → contextual reply generation
  → outbound authorization/delivery
  → delivery evidence and audit
```

Conversations & AI does not own authorization, hiring, Employee-ID mutation, application lifecycle, payroll, cash, roster assignment, escort completion, billing, or other protected domain state. MCP is an adapter over canonical services; it must not duplicate business rules.

Evidence labels used below: `VERIFIED_LIVE`, `VERIFIED_SOURCE`, `DOCUMENTED_ONLY`, `INFERRED`, and `UNKNOWN`.

## 2. C1 premature implementation review

The currently unapproved files are preserved unchanged:

- `src/alrifai/conversations/models.py`
- `src/alrifai/conversations/__init__.py`
- `tests/test_conversation_models.py`

**C1_SPEC_ALIGNMENT: PARTIALLY_ALIGNED.** The files correctly model a transport-neutral `Conversation` and `Message`, typed channel/direction/actor/content/delivery values, timestamps, reply linkage, normalized sender mobile, platform identity, media references, correlation, provenance, domain, and topic. They are useful contract evidence and do not touch persistence.

They are incomplete for the final architecture: they do not model external ordering evidence, received/occurred timestamp validation, canonical source-account identity, recipient identity, historical phone references, Employee business ID context, subject-versus-sender identity, burst/turn state, topic history, instruction references, extraction confidence/evidence, processing state, idempotency, delivery attempts, human handoff, or audit records. `dict` provenance/platform fields are intentionally not yet stable schemas, `UUID` IDs are not persistence contracts, and the model does not normalize or validate Bangladesh mobile numbers. The C1 files are therefore not an approved implementation baseline and must not trigger C2.

## 3. Canonical message and conversation model

Canonical persistence is one shared model for every supported channel. A message record contains:

| Field | Rule |
|---|---|
| `message_id` | Immutable internal identifier |
| `external_message_id` | Provider/bridge identifier plus source account; unique within provider scope |
| `conversation_id` | Canonical thread reference |
| `channel` / `source_account` | Typed transport and bridge/account; never inferred from free text |
| `direction` | `inbound` or `outbound` |
| `sender` / `recipient` | Provider-safe references, not authorization claims |
| `person_id` | Trusted Person link or null; never caller-asserted as proof |
| `normalized_sender_mobile` | Preserved business context and provenance; raw source is retained separately under restricted access |
| `platform_identity` | Typed platform/provider identity, scoped to channel/account |
| `actor_type` | `human`, `ai`, `device`, `system`, or `unknown` |
| `occurred_at` / `received_at` | Source event time and ingestion time, both retained |
| `sequence` / ordering evidence | Provider sequence, ingestion order, and ordering confidence where available |
| `reply_to_message_id` | Canonical reply relationship where available |
| `content_type` / `body` | Text/media classification and safe text representation |
| `media_refs` | References only; binary ownership remains with approved storage |
| `delivery_state` / attempts | Outbound lifecycle and delivery evidence; receipt is not delivery success unless provider confirms it |
| `domain` / `topic` | Classification evidence, not domain authorization |
| `correlation_id` / `causation_id` | Trace and causal chain |
| `extraction_refs` | Structured extraction/evidence references |
| `provenance` | Source event, bridge, ingestion, transformation, and policy versions |

Conversation records contain canonical thread identity, channel/account scope, trusted Person link when resolved, participant/platform identities, timestamps, active topic reference, topic history, and processing state. Raw messages are stored once. Domain MCPs receive trusted references and bounded context, never duplicated raw message tables.

## 4. Identity and Employee-ID policy

Inbound WhatsApp/mobile identity is durable business evidence. Preserve the originating raw value as restricted provenance and normalize equivalent `+`, `00`, `88`, and local forms to the final 11 digits beginning with `0`. Raw formatting is never compared.

The authoritative business Employee ID is the designated normalized Bangladeshi mobile number. `person_id` and any physical employee-record UUID are internal technical keys only. A contact/platform number may be associated with a Person or Employee after safe resolution but must not mutate Employee ID. Only the authorized Workforce/frontend `Edit Employee ID` workflow may change it, with uniqueness validation, confirmation, audit, historical alias retention, and transactional rollback.

Resolution may use, in combination: trusted Person UUID, current contact phone, historical phone, designated Employee ID, typed platform identity, Applicant, Employee, aliases, and conversation provenance. Name alone cannot override a conflicting phone. Ambiguity fails closed or enters review. Sender identity and mentioned subject identity are separate.

Conversation history is scoped by trusted Person/participant and channel/thread. Historical phone lookup may find a linked Person, but does not create or merge records automatically. No context retrieval may cross Person boundaries because of a similar name or untrusted phone claim.

## 5. Channel adapter boundary

Adapters support Bridge1, Bridge2, Bridge3, Meta WhatsApp, Messenger, Facebook Comments, internal/admin sources, and future channels. Live evidence verifies Bridge1/2/3 and Meta/WhatsApp paths (`VERIFIED_LIVE`/`VERIFIED_SOURCE`); current Messenger/Facebook activity remains `UNKNOWN` unless separately verified.

Adapters translate transport events into the canonical envelope, preserve source/account IDs and timestamps, deduplicate redelivery, and submit outbound delivery evidence. Domain code never imports Bridge-specific modules or assumes a channel-specific schema.

## 6. Message order and burst/turn aggregation

Message order and time are semantic evidence. The composer preserves source timestamp, ingestion timestamp, provider sequence, reply relationship, gaps, and ordering confidence. Several short messages from one sender in one thread may form one turn.

Aggregation eligibility requires:

1. same trusted conversation and sender/subject scope;
2. compatible channel/account;
3. no intervening outbound business reply or human handoff;
4. configurable short inactivity window;
5. no strong topic/entity switch;
6. messages are continuations, fragments, corrections, or text followed by related media.

The window is configuration, not a business rule. Aggregation stops at an outbound response, a material topic/entity switch, an explicit correction boundary, or a late message outside the active window. Late continuations remain individually stored and may be related to the prior turn through evidence, but are not silently concatenated. The aggregate records member message IDs, ordering, timestamps, reason, configuration version, and decision audit.

## 7. Semantic understanding and historical references

Hermes/AI interprets the complete turn and relevant context, not isolated keywords. It must support standard and colloquial Bangla, Banglish, mixed language, misspellings, incomplete sentences, abbreviations, voice/media-derived text when available, pronouns, references, and follow-up questions. Keywords are hints, retrieval filters, safety triggers, or fallback evidence only.

Examples such as “আগে কাগজ দিছিলাম”, “কালকে যে কথা কইছিলাম”, “ওই জাহাজের কাজটা”, and “আপনি বলছিলেন আসতে” require retrieval of candidate evidence, prior document/media references, prior replies, timestamps, active/closed topics, and relevant historical conversations. “আগে” is not automatically the immediately previous message. The interpretation stores evidence references and confidence, not hidden chain-of-thought.

## 8. Context retrieval

Every reasoning request uses a bounded context:

1. current inbound message or aggregated turn;
2. direct reply target;
3. recent relevant turns in the current thread;
4. active topic state and open tasks;
5. semantically relevant older messages;
6. relevant historical conversation/document references;
7. canonical Person, Applicant, Employee, client, or operational facts allowed by scope;
8. current canonical domain policy/data;
9. latest applicable Admin/Owner instruction;
10. authorized domain-tool results.

Retrieval applies configurable limits, recency and relevance thresholds, direct-reference priority, topic/entity weighting, stale-context exclusion, and summarization. It returns source message/evidence IDs and retrieval metadata. Lifetime history remains stored but is not inserted wholesale into a prompt. Sensitive document binaries and raw NID content are references by default, not general AI resources.

## 9. Topic state

Topics are domain-neutral records with `topic_id`, domain, semantic label, opened/last-activity times, status, relevant entities, summary, evidence message IDs, and closure/reopen history. Recruitment examples include job interest, role, salary, eligibility, documents, application, interview, joining, office/address, duty conditions, benefits, and follow-up; other domains may add attendance, payment, escort, vessel, client, roster, billing, or administration.

Topic lifecycle: `opened → gathering → awaiting_user|awaiting_approval → completed → closed`; a user request may create `reopened` or a new related topic. Completed topics are not active forever. A topic switch changes the active context and must not mutate the previous entity or Applicant silently. A message mentioning a brother, friend, employee, or another applicant requires subject resolution or clarification; the sender is not automatically the subject.

Repeated semantically equivalent questions use recent answer evidence after checking current policy/data and instruction version. They may receive a concise reminder; material policy/data changes require a fresh answer. Exact-text matching is not the primary mechanism.

Missing-information extraction distinguishes `unknown`, `provided`, `candidate_claimed`, `staff_reviewed`, and `verified`. A candidate statement such as “I will join today” is not a hiring authorization or state transition.

## 10. Admin/Owner AI instruction service

Admin/Owner instructions are versioned guidance records containing instruction ID/version, domain, topic/role/audience/channel scope, priority, instruction text or approved reference, issuer, issued/effective/expiry times, supersession, active status, and provenance/audit references. Historical versions are immutable.

Applicable instruction selection is deterministic:

1. security and authorization constraints;
2. canonical deterministic business rules and authoritative domain data;
3. effective time window and active status;
4. most specific domain/topic/role/audience/channel scope;
5. explicit priority;
6. latest version;
7. otherwise review/error on unresolved conflict.

The reply/extraction audit stores the selected instruction IDs and versions, policy/data references, and applicability decision. Free-text instructions may guide wording, questions, collection, escalation, temporary priorities, and response style; they cannot authorize writes, override identity, change Employee ID, approve hiring, create payments, assign rosters, or bypass domain validation.

## 11. Hermes and structured extraction boundary

Hermes is a replaceable interpretation/extraction/reply adapter. It may classify likely domain/topic, retrieve context, detect missing information, produce structured extraction, propose tool calls, and draft replies. It is not canonical identity, authorization, persistence, payment, payroll, hiring, Employee-ID, roster, or business-rule authority.

Structured extraction must include schema version, fields, confidence, evidence references, source message IDs, subject identity, missing/ambiguous fields, and model/provider metadata. Unstructured prose is never sent directly to a privileged mutation API. Domain services validate all extracted values and capabilities.

## 12. Deterministic domain dispatch

Dispatch uses a trusted server-created envelope containing `person_id` when resolved, `employee_business_id` only when trusted, normalized phone reference, typed platform identity, conversation/message IDs, message timestamp, reply target, source channel/account, topic, semantic intent, extracted fields, confidence, evidence references, applicable instruction version, correlation/causation IDs, and idempotency key. AI-generated fields are evidence, never authorization claims.

| Domain | Conversations & AI may request | Domain service remains authoritative for |
|---|---|---|
| Recruitment | role information, interest/application drafts, status, documents, interview/joining readiness | Person/Applicant/Application facts, lifecycle, documents, handoff |
| Workforce | employee lookup, attendance/assignment drafts, employee-document workflow | Employee lifecycle, Employee ID, attendance, workforce state |
| Finance & Payroll | salary/payment information or approved payment workflow proposal | payroll, approvals, cash, ledger, payment state |
| Operations & Clients | vessel/client/escort/roster extraction or draft | programs, assignments, replacements, release, completion, operational billing facts |
| Platform / Admin | scoped reports, audit/provenance, administrative workflow proposal | authorization, approvals, cross-domain orchestration, audit |

An operation is committed only after the receiving service authenticates the trusted actor/capabilities, validates identity and policy, applies idempotency, persists state and required event/audit atomically, and returns a structured result.

## 13. Replies, outbound delivery, and human handoff

Reply context combines trusted identity, current turn, relevant ordered history, topic state, canonical domain facts, current policy, latest applicable instruction, and authorized tool results. Hermes drafts a response; deterministic safety and authorization checks run before any privileged action or outbound send.

Outbound is a separate state machine: `drafted → approved/authorized → queued → sent → provider_acknowledged → delivered|failed`, with `cancelled` and `human_review` where applicable. “AI generated” or “queued” is not “delivered.” Delivery attempts, provider IDs, timestamps, failure class, and correlation are recorded. Recruitment may identify candidates for follow-up; outbound infrastructure controls actual delivery and messaging policy.

Human handoff is required for unresolved identity, subject ambiguity, conflicting instructions, low-confidence protected extraction, authorization failure, repeated delivery failure, sensitive document concerns, or domain review. The handoff record contains reason, evidence, assigned queue/actor, status, and resume/close action. It must not silently mutate business state.

## 14. Processing, idempotency, retries, and recovery

Canonical processing states are `received`, `persisted`, `deduplicated`, `resolving`, `context_ready`, `interpreting`, `awaiting_domain`, `awaiting_approval`, `reply_pending`, `outbound_pending`, `completed`, `failed`, and `review`. State transitions are durable and auditable.

External message IDs are deduplicated within channel/account scope. Processing and outbound commands use stable idempotency keys derived from source event/correlation and operation version. Duplicate inbound events return the original processing result. Retries are bounded and classified: transient adapter/provider/database failures may retry; validation, authorization, ambiguity, and policy errors require review. A failed AI call cannot roll back unrelated committed domain state. A failed domain transaction cannot be reported as successful. Reprocessing uses the original evidence and records a new attempt/version.

Finance delivery semantics are special: payment completion requires the approved accountant/payment workflow, outbound evidence, cash transaction, and employee financial ledger side effects as defined by Finance; ordinary replies do not use this shortcut.

## 15. Resources

The final resource catalog is **10 resources**. Resources are scoped service-backed views, never raw tables or unrestricted binaries:

1. `canonical_message` — message metadata/body according to authorization, provenance, and delivery evidence.
2. `conversation_thread` — participants, channel/account, state, topic summary, and bounded history references.
3. `media_reference` — type, storage reference, provenance, review state, and safe metadata; not raw NID by default.
4. `person_conversation_context` — trusted Person/phone/platform links and relevant ordered context.
5. `semantic_context` — bounded retrieval result with evidence and retrieval metadata.
6. `topic_state` — active/history topics, lifecycle, entities, summaries, and evidence.
7. `admin_ai_instruction` — applicable version and audit-safe instruction metadata.
8. `extraction_draft` — structured fields, confidence, missing/ambiguous values, and evidence.
9. `outbound_delivery` — authorization, attempts, provider acknowledgement, and delivery status.
10. `processing_trace` — correlation, causation, idempotency, state transitions, and audit references.

## 16. Tools

The final tool catalog is **18 tools**. All tools require a trusted server context; read tools are scoped and mutation tools fail closed without authorization.

### Conversation and evidence reads

1. `ingest_message` — accept a normalized adapter event idempotently.
2. `get_message` — retrieve one authorized canonical message.
3. `get_conversation` — retrieve thread metadata and scoped participants.
4. `get_conversation_history` — retrieve ordered, bounded history.
5. `search_conversations` — search authorized semantic/topic/time evidence.
6. `get_person_conversation_context` — retrieve Person-linked current/historical context.
7. `get_media_reference` — retrieve safe media/document metadata.

### Context and interpretation

8. `compose_semantic_context` — construct bounded context with evidence references.
9. `classify_domain_and_topic` — produce non-authoritative domain/topic evidence.
10. `extract_structured_message_data` — produce versioned extraction draft.
11. `get_missing_information` — compare trusted facts against requested workflow requirements.
12. `get_repeated_question_context` — retrieve semantically equivalent recent question/answer evidence.

### Topic and instructions

13. `get_topic_state` — retrieve current and historical topic state.
14. `update_topic_state` — create/close/reopen topic state under authorized orchestration policy.
15. `get_applicable_admin_instruction` — select applicable instruction version and provenance.

### Dispatch, reply, and operations

16. `prepare_domain_action` — create a structured, evidence-backed draft; never commits domain state.
17. `dispatch_domain_action` — call the receiving canonical service with trusted authorization and idempotency.
18. `prepare_or_send_reply` — generate/queue an authorized reply and return delivery evidence; it cannot claim delivery without provider confirmation.

Tool results use `READ`, `DRAFT`, `VALIDATE`, `PENDING_REVIEW`, `WRITE`, or typed error classes. No tool accepts caller-supplied role, capability, Person ID, Employee ID, or AI confidence as authority.

## 17. Authorization, errors, audit, and privacy

Conversations & AI uses the platform authorization service; it has no second RBAC system. Read access is scoped to trusted actor, Person/participant, channel, domain, and sensitivity. Draft/extraction tools may be available to the AI service identity. Domain writes require the receiving service’s trusted capability and approval policy. Admin instructions never grant capability.

Errors are stable and non-sensitive: `INVALID_MESSAGE`, `DUPLICATE_MESSAGE`, `INVALID_PHONE`, `AMBIGUOUS_IDENTITY`, `SUBJECT_AMBIGUOUS`, `CONTEXT_SCOPE_DENIED`, `INSTRUCTION_CONFLICT`, `EXTRACTION_INVALID`, `DOMAIN_DISPATCH_DENIED`, `DOMAIN_VALIDATION_FAILED`, `IDEMPOTENCY_CONFLICT`, `OUTBOUND_NOT_AUTHORIZED`, `DELIVERY_FAILED`, `HUMAN_REVIEW_REQUIRED`, and `TEMPORARY_UNAVAILABLE`. Internal provider/database details are logged securely, not exposed as MCP responses.

Every significant operation records actor/service identity, source/channel/account, time, Person/entity scope, action, before/after references where permitted, outcome, evidence message IDs, instruction versions, model/provider metadata, correlation/causation, idempotency key, retry/attempt, and delivery evidence. Never store hidden chain-of-thought. Sensitive phone/document values are redacted from ordinary logs; raw media remains in approved storage.

## 18. Legacy mapping and form relationship

Fresh audit evidence identifies Bridge1/2/3, `message_router`, `identity_brain`, `hermes_dispatch`, `conversation_canonical`, `message_archive`, outbound paths, `wbom_whatsapp_messages` (32,436), `fazle_conversations`, `fazle_messages`, Hermes task/approval tables, intent/draft/delivery tables (`VERIFIED_LIVE`/`VERIFIED_SOURCE`). The legacy split between raw messages and conversation memory, uneven channel semantics, and incomplete duplicate prevention are migration risks, not future ownership boundaries. Messenger/Facebook activity is `UNKNOWN` where not verified.

Frontend/form workflows may call canonical domain services directly. They must converge with message-driven workflows at identity, validation, business service, persistence, audit, and result layers. AI is not a mandatory hop for deterministic forms.

## 19. Implementation prerequisites and sequence

Prerequisites: owner approval of this specification; approved canonical persistence schema and migration plan; stable identity/phone normalizer contract; trusted authorization context; audit/event and idempotency strategy; approved media storage; domain dispatch DTOs; provider/channel adapter contracts; safe AI provider abstraction; isolated test fixtures and semantic regression corpus; Workforce Employee-ID policy; Recruitment contracts; and privacy/retention approval.

Future sequence:

| Stage | Purpose / expected modules | Tests and rollback boundary | Activation |
|---|---|---|---|
| C1 | Canonical message/thread contracts and persistence DTOs | schema/serialization tests; remove adapter only | no runtime activation |
| C2 | Identity, phone, platform, Person, and subject resolution | ambiguity, historical phone, isolation tests; disable resolver | shadow/read-only |
| C3 | Ordered history and burst/turn aggregation | ordering, late continuation, reply-boundary tests; disable aggregation | shadow |
| C4 | Topic state, closure, switching, repetition | lifecycle and contamination tests; disable topic writes | shadow |
| C5 | Versioned Admin instruction service | precedence, expiry, supersession, reproducibility tests; disable instruction application | draft-only |
| C6 | Bounded semantic retrieval/context composer | relevance, stale exclusion, sensitive-scope tests; revert to minimal context | draft-only |
| C7 | Hermes/provider adapter and structured extraction | semantic corpus, timeout, confidence/evidence tests; disable provider | draft-only |
| C8 | Domain dispatch contracts | authorization, schema, idempotency, failure tests; stop dispatch | no writes |
| C9 | Reply and outbound orchestration | approval, duplicate, delivery evidence tests; stop outbound | draft/approval |
| C10 | Audit, observability, recovery/reprocessing | trace, retry, redaction, recovery tests; disable workers | shadow |
| C11 | Full semantic regression and cross-channel consistency | isolated end-to-end tests; rollback to prior adapters | no production activation |
| C12 | Controlled channel activation | canary, monitoring, rollback plan, owner sign-off | explicit owner approval required |

### C3 qualification decision

C3 is implemented as a deterministic, in-memory reconstruction over canonical C1 messages and C2 conversation linkage. Ordering and turn aggregation remain separate operations. Source/ingestion timestamps, provider ordering evidence, reply references, sender/thread boundaries, media references, and aggregation decisions remain available as structured evidence; C3 does not infer topic, intent, domain, or business meaning.

No C3 turn table or migration is required. A turn is deterministically identified from its canonical conversation and ordered message IDs, so restart/reprocessing can reconstruct the same logical result. Late arrivals produce an auditable re-evaluation result rather than a duplicate downstream effect. C3 qualification is pure local code/test verification; no PostgreSQL qualification or production database change is applicable. C4 remains blocked pending explicit Owner approval.

### C4 qualification decision

C4 is implemented in `src/alrifai/conversations/topics.py` as a deterministic topic state machine over typed topic/transition proposals. It persists `conversation_topics` and immutable `conversation_topic_transitions` through V008 so state and history survive restart. Valid transitions, optimistic state versions, scoped idempotency, closure evidence, explicit reopening evidence, conversation scope, and C3 late-arrival conflicts are validated without semantic classification.

C4 does not classify natural language, select Admin instructions, call Hermes, retrieve semantic history, generate replies, dispatch domain actions, or send outbound messages. C5 and later stages remain unimplemented and require separate Owner approval.

No stage may begin automatically because the preserved C1 files exist. Each later stage remains blocked until the Owner explicitly approves it and the listed prerequisites are satisfied.

## 20. Definition of ready

This specification remains the authority for staged implementation. C1, C2, C3, and C4 are implemented and locally qualified within their approved scopes; C5 and later stages remain pending explicit Owner approval.
