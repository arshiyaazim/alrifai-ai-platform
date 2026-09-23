# Conversations & AI MCP — Final Implementation Specification

**Status:** Canonical staged implementation specification. C1–C6 are backed up at checkpoint cf71c3b6b3f439003cd1ead0d2f5ce53583cab8c. C7 is PARTIAL, not COMPLETE: the authenticated 9Router live route passed, five Section 24 cases safely abstained, and twelve unchanged C5/C6 baseline failures remain. No production deployment, existing database migration, service restart, C8, or C9 work occurred. C8/C9 and later stages are not started.
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

Applicable instruction selection is deterministic. First exclude unauthorized, inactive, not-yet-effective, expired, revoked, superseded, or out-of-scope versions. Partition remaining guidance by canonical subject. For each subject, same-authority candidates rank by scope specificity, explicit priority, effective time, then version; unresolved equal-rank differences fail closed with evidence, never by row order or database ID. When effective Owner and Admin instructions conflict on the same subject, Owner wins only for that subject. Unrelated subjects remain independently applicable; equivalent guidance may both be retained. Canonical business policy and authorization constraints remain above every instruction.

C5 stores immutable versions and append-only lifecycle evidence in `conversation_ai_instruction_versions` and `conversation_ai_instruction_events` (V009), with every lifecycle write authorized via `TrustedPrincipal` and central `MANAGE_CONVERSATIONS`, plus canonical `audit_log` attribution. Admins cannot revise or alter Owner-issued instruction lifecycle. A future-effective superseding version leaves the prior version applicable until its effective time. Topic-scoped guidance is excluded for closed/completed C4 topics and never reopens them. Selection returns inclusion/exclusion evidence; unresolved same-authority conflict raises a structured conflict with evidence.

Free-text instructions guide communication only. They cannot authorize writes, override identity, change Employee ID, approve hiring, create payments, assign rosters, or bypass domain validation. External messages and media-derived text are not privileged instructions without a separately verified Owner/Admin principal. C5 does not classify natural language, retrieve semantic history, call Hermes, dispatch domains, or generate/send replies.

## 11. Hermes and structured extraction boundary

Hermes is a replaceable interpretation/extraction adapter for C7 and a separate response-generation capability in C9. C7 may interpret, extract structured evidence, detect missing information, and propose domain-read needs; it does not retrieve context itself, draft final replies, or execute tools. C9 owns natural-language reply generation and outbound orchestration. Hermes is not canonical identity, authorization, persistence, payment, payroll, hiring, Employee-ID, roster, or business-rule authority.

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
| C5 | Versioned Admin/Owner instruction state and selection | trusted lifecycle, scoped deterministic selection, Owner-over-Admin same-subject conflict precedence, audit/evidence, expiry/supersession tests | included in remotely backed C1–C6 checkpoint cf71c3b6b3f439003cd1ead0d2f5ce53583cab8c |
| C6 | Bounded, authorized context retrieval over canonical messages, turns, topics, and instructions | scope/privacy, evidence, bounds, stale exclusion and reconstruction tests; revert to minimal context | qualified and remotely backed up at cf71c3b6b3f439003cd1ead0d2f5ce53583cab8c |
| C7 | Structured semantic interpretation and extraction through a provider-neutral adapter; no final reply | Focused C7 tests and C1–C6 unit regression pass; disable interpreter | PARTIAL: offline baseline backed up at `9b5ffccdfc010c8dd37a13ab75be3c6cadb9c5bb`; authenticated 9Router route PASS with five Section 24 SAFE_ABSTAIN outcomes; twelve unchanged C5/C6 baseline failures |
| C8 | Domain dispatch contracts | authorization, schema, idempotency, failure tests; stop dispatch | no writes |
| C9 | Reply and outbound orchestration | approval, duplicate, delivery evidence tests; stop outbound | draft/approval |
| C10 | Audit, observability, recovery/reprocessing | trace, retry, redaction, recovery tests; disable workers | shadow |
| C11 | Full semantic regression and cross-channel consistency | isolated end-to-end tests; rollback to prior adapters | no production activation |
| C12 | Controlled channel activation | canary, monitoring, rollback plan, owner sign-off | explicit owner approval required |

### C3 qualification decision

C3 is implemented as a deterministic, in-memory reconstruction over canonical C1 messages and C2 conversation linkage. Ordering and turn aggregation remain separate operations. Source/ingestion timestamps, provider ordering evidence, reply references, sender/thread boundaries, media references, and aggregation decisions remain available as structured evidence; C3 does not infer topic, intent, domain, or business meaning.

No C3 turn table or migration is required. A turn is deterministically identified from its canonical conversation and ordered message IDs, so restart/reprocessing can reconstruct the same logical result. Late arrivals produce an auditable re-evaluation result rather than a duplicate downstream effect. C3 qualification is pure local code/test verification; no PostgreSQL qualification or production database change is applicable. C4 is implemented as described below.

### C4 qualification decision

C4 is implemented in `src/alrifai/conversations/topics.py` as a deterministic topic state machine over typed topic/transition proposals. It persists `conversation_topics` and immutable `conversation_topic_transitions` through V008 so state and history survive restart. Valid transitions, optimistic state versions, scoped idempotency, closure evidence, explicit reopening evidence, conversation scope, and C3 late-arrival conflicts are validated without semantic classification.

C4 does not classify natural language, select Admin instructions, call Hermes, retrieve semantic history, generate replies, dispatch domain actions, or send outbound messages. C5 adds instruction state/selection only. C6 and C7 implementation/qualification are recorded below; C8/C9 and later remain unimplemented and require separate Owner approval.

### C5 implementation decision

C5 is implemented in `src/alrifai/conversations/instructions.py`. V009 persists immutable instruction versions and append-only created/activated/revoked/superseded events, enforces canonical conversation/topic scope and links audit events to the trusted principal. PostgreSQL qualification covers V009 up/down/reapply and restart reconstruction. Owner precedence applies only to conflicting instructions on the same subject; it never cancels unrelated Admin guidance and never authorizes domain mutations.

### C6 implementation decision — bounded context retrieval

C6 is implemented locally in `src/alrifai/conversations/context.py` as a read-only composer over canonical C1 messages, C2 identity/conversation resolution, C3 ordered turns, C4 topic state, and C5 instruction selection. It creates no competing history store and no migration. The PostgreSQL adapter reads existing canonical tables only. Server-enforced defaults are 32 messages, 12 turns, 5 topics, 12,000 context-content characters, 200 candidate records, 90 days of history, reply depth 5, and 8 media references per message; callers cannot raise these limits. Messages and extracted text remain untrusted conversation data with source/order evidence and provenance.

Retrieval requires central `MANAGE_CONVERSATIONS` authorization and exact channel/account/conversation scope. Before any message, topic, or instruction reads, private retrieval requires a resolved C2 Person matching the private conversation's Person; unresolved, ambiguous, mismatched, or unlinked private identity fails closed. Group/public requests remain confined to their exact shared thread and never inherit private Person history. Topic references are validated against conversation/channel/account/scope before associated evidence is read. Closed-topic evidence is omitted from ordinary active context; historical retrieval may return it only for an explicit authorized historical purpose and does not reopen the topic. Closed-topic guidance is not selected as current. The current C3 turn is checked against canonical message membership/order. Missing context returns explicit insufficiency/omission evidence; no facts are fabricated.

C6 does not classify meaning, perform lexical routing, call Hermes, author instructions, dispatch domains, mutate protected state, generate replies, or send outbound messages. It preserves reply/prior-answer references, C3 ordering/late-arrival evidence, C4 state, and C5 selection provenance for C7. Retrieval is deterministic/read-only. Qualification used a disposable loopback PostgreSQL 17 target for adapter integration; no schema migration or context persistence was introduced. C6 is included in the remotely verified baseline at cf71c3b6b3f439003cd1ead0d2f5ce53583cab8c.

No stage may begin automatically because the preserved C1 files exist. Each later stage remains blocked until the Owner explicitly approves it and the listed prerequisites are satisfied.

## 20. Definition of ready

This specification remains the authority for staged implementation. C1–C6 are accepted and remotely backed up at cf71c3b6b3f439003cd1ead0d2f5ce53583cab8c. C7's offline baseline is remotely backed up at `9b5ffccdfc010c8dd37a13ab75be3c6cadb9c5bb`; the authenticated 9Router route passed controlled live qualification, with five Section 24 SAFE_ABSTAIN outcomes and twelve unchanged C5/C6 baseline failures. C7 remains PARTIAL, not COMPLETE. C8/C9 are not started.

### C6-to-C7 relationship evidence correction

C6 now includes `relationship_status` and `relationship_evidence` in its bounded context package. It returns `CONFIRMED_CURRENT_EMPLOYEE` only when C2 resolves the same Person and its unique employee candidate has canonical status `active`; group/public requests additionally require the resolved Person to match a sender on the current inbound turn. All other cases return `UNKNOWN`. C7/C9 use the respectful default **“আপনি”** unless this positive evidence is present; identity familiarity, applicant history, self-claim, or pre-join selection never authorizes **“তুমি”**. This evidence is for tone only, not authorization. C6 does not currently expose a verified Applicant/selected-pre-join state.

### C7 — implementation-ready semantic interpretation and extraction contract

**Boundary:** C7 interprets the C6 bounded context and produces evidence-linked structured hypotheses. It does not author final replies (C9), retrieve arbitrary documents/history (C6/domain read services), select/reject/hire candidates, decide eligibility, mutate any domain, dispatch writes (C8), schedule notifications, or send messages. It must not turn a proposed intent, confidence, or extracted claim into authorization.

**Input:** one C6 `ContextPackage` for one authorized conversation turn, including ordered current-turn messages, C3 timing/reply/late-arrival evidence, C4 topic/state references, applicable C5 instruction versions, trust classifications, and—only when available through an authorized canonical read contract—domain facts and their provenance. External message/media-derived content remains untrusted. C7 must not enlarge context limits or bypass C6 scope.

**Interpretation output (versioned structured result):**

| Field | Contract |
|---|---|
| `status` | `interpreted`, `needs_clarification`, `insufficient_context`, or `abstained`; uncertainty is explicit. |
| `language_evidence` | Observed language/mix and uncertainty; supports Bangla, Banglish, English, colloquial forms, spelling variants, fragments and incomplete messages without rewriting source text. |
| `intent_hypotheses` | Zero or more ranked, non-authoritative intent/domain/topic hypotheses with confidence and supporting message/turn IDs. No keyword-only result may be represented as fact. |
| `subject_references` | Sender/known Person/third-party mention candidates, canonical reference only when trusted evidence resolves it, otherwise `unresolved`/clarification required. Never assume a mentioned relative is the sender. |
| `extracted_claims` | Typed candidate statements/facts with value, `unknown|provided|candidate_claimed|staff_reviewed|verified` evidence state, source references, confidence and extractor/schema version. A claim is not a verified fact. |
| `missing_information` | Fields missing relative to an explicitly supplied canonical role/workflow requirement set; absent requirements mean “not assessed,” not “missing.” |
| `goal_evidence` | Flexible current user goal and optional next-step candidates grounded in current/relevant turns. This is a hypothesis, not a mandatory dialogue state or linear Recruitment workflow. |
| `topic_association` | C4 topic reference or typed association proposal plus evidence; C7 does not transition, close, or reopen topics. A closed topic is only resumed after a new user event and a later authorized C4 transition. |
| `prior_answer_evidence` | Relevant prior outbound message/turn IDs; no semantic duplicate-question claim unless the later approved capability supplies that determination. |
| `address_form` | `respectful_apni` by default; `familiar_tumi` only with C6 `CONFIRMED_CURRENT_EMPLOYEE` evidence for the resolved current sender. Include evidence reference. |
| `grounding` | References classified by the authority model below; preserve source/version/currentness and conflicts. C7 must not manufacture missing sources or values. |
| `required_domain_reads` | Typed read needs for C8/canonical services, such as current role conditions or application status; no writes or tool execution by C7. |
| `clarification_or_escalation` | Minimal clarification or human-review reason when subject, identity, source authority, missing policy or protected decision is unresolved. |

Do not expose hidden chain-of-thought. Return concise decision/evidence summaries, not private reasoning traces. Preserve original messages and media references; never transform media receipt into document verification.

**Knowledge authority and use:**

| Class | How C7 treats it |
|---|---|
| Authoritative business fact | Current approved canonical source value (for example salary range, hours, address, role condition). Preserve exact amount/value/unit/version; may be summarized in C9 but never numerically altered. Missing, stale or conflicting source means unknown/escalate. |
| Mandatory business rule | Enforce only when explicitly designated by authorized canonical policy/legal/approval contract. An example or tone instruction cannot promote itself to mandatory. |
| Flexible operational guidance | Helpful, defeasible advice; may be adapted to the person and context but cannot override a mandatory rule or promise approval. |
| Conversation style guidance | Tone/address/clarity guidance; flexible expression, subordinate to verified relationship and safety/policy. |
| Illustrative example | Demonstrates possible meaning or conversation only. Never an exact-match trigger, required sentence, fixed dialogue tree, or policy source. |
| Historical/superseded material | Historical evidence only; not current facts or rules unless the authorized source explicitly marks it applicable. |

**Natural conversation policy:** “Examples are illustrative, not prescriptive.” Meaning and required facts remain faithful, while wording, length, question form and progression may vary naturally. Do not implement percentage similarity thresholds, fixed scripts, keyword-to-reply rules, or an obligatory closing question. Understand the full C3 turn and relevant C6 context, including multi-message references, corrections, topic switches, declines and returns. A Recruitment goal is a helpful, non-linear guide: accept out-of-order information, do not repeatedly ask for known trusted facts, do not push after decline/topic change, and offer a relevant next step only when useful.

If a candidate lacks a document, C7 must not infer rejection. It may identify the missing requirement and request approved alternatives through a C8 read or escalate when an alternative needs staff approval. Do not waive an explicitly mandatory legal/protected requirement or promise hiring. Joining-preparation advice and combining visits are optional operational guidance only when current approved Recruitment policy permits it; illustrative document lists are not universal requirements. Candidate interest/readiness is not selection. A selection notification can be stated only after canonical Recruitment returns an authorized selection decision; the Owner's “around two hours” example is not a default timer. C7 never selects, schedules or sends that notification.

**Routing/provider constraints:** C7 uses a replaceable interpretation interface behind the existing approved model-routing architecture (9Router/OmniRoute where configured). Do not hard-code a provider/model or bypass the approved router. Provider failure, timeout, malformed output, unsupported language, or low-confidence material fact returns typed insufficiency/clarification; no business mutation follows. No live service, route, model or credential changes are part of C7 specification or this task.

**C7 tests required before implementation acceptance:** semantic multi-turn Bangla/Banglish/misspelling and incomplete fragments; cross-turn references and correction handling; subject ambiguity; exact preservation of salary/fees/hours/address facts; source authority classification and example non-promotion; missing policy stays unknown; missing document does not trigger automatic rejection; no mandatory question/script; respectful address default and active-employee-only familiar address; closed topic not reopened; refusal/decline and topic change respected; no unsupported applicant selection or two-hour notification; prompt injection remains untrusted; no cross-Person/group/public leakage; no protected mutation/tool dispatch; timeout/malformed/low-confidence fail safely; deterministic versioned output and evidence references.

**Prerequisites/open source gaps:** no approved Recruitment knowledge corpus/service or concrete role/salary/document policy records were found in the current repository. Recruitment specification already identifies the canonical Role/policy source as an implementation prerequisite. C7 must emit `required_domain_reads`/unknown until that authorized read source exists; do not add a knowledge store inside Conversations. No canonical office address was found in repository search. The Owner must confirm whether “AK Khan Mor, Pahartali, Chattogram” and “AK Khan Mor, Victoria No. 1 Gate” are the same location and provide the exact approved display address before either is communicated as a fact.

### C7 local implementation and qualification record

The local implementation is `src/alrifai/conversations/interpretation.py`, exported through the existing Conversations package, with focused coverage in `tests/test_conversation_interpretation.py`. It consumes exactly one bounded C6 package, preserves source text and evidence references, produces versioned structured hypotheses/claims/goal/topic associations, applies the C6 verified-current-employee tone evidence, and refuses unsupported canonical references, closed-topic reopening, verified/staff-review promotion, protected actions, and untrusted instruction elevation. It performs no persistence, dispatch, reply generation, or outbound delivery.

The adapter boundary is injected and provider-neutral; the authenticated 9Router route was used for controlled live qualification. Five Section 24 cases safely abstained on malformed or slow provider output, while validation remained fail-closed. No production route was changed, no outbound message was sent, and no domain mutation occurred. C7 serialized adapter input is capped at 64,000 characters and model output at 32,000 characters. Only current evidence that is neither illustrative nor historical/superseded can be returned as current grounding. Adapter failures are converted to typed abstention without exposing exception text. PostgreSQL qualification is not required because C7 adds no persistence or migration. Offline and live qualification outcomes are recorded in `docs/development/TEST_STATUS.md`; database-gated tests remain explicitly skipped in the full no-DB run.

C7 offline baseline is committed and independently verified remotely at `9b5ffccdfc010c8dd37a13ab75be3c6cadb9c5bb`; subsequent route-audit status/documentation is local-only and uncommitted. C7 live qualification remains blocked pending an explicitly approved usable route and secure local authentication availability. C8 dispatch, C9 reply/outbound, the full Recruitment Knowledge Hub, and live channel/model activation are not implemented. Missing approved Recruitment knowledge and the unresolved office display remain blockers to grounded claims about those facts.
