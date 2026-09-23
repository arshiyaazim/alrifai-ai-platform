# Recruitment MCP — Final Implementation Specification

**Status:** implementation-ready design; documentation only. No MCP runtime, migration, database, authentication, Docker, or VPS change is included.

**Owner:** Recruitment/HR. Recruitment owns the applicant and application lifecycle until the authorized Workforce handoff. Workforce owns the employee after handoff. Conversations & AI owns channels, message storage, extraction, Hermes, and replies. Platform/Admin owns cross-domain approval/orchestration and shared audit/provenance views.

## 1. Architecture and non-goals

```text
Messaging / Frontend / Agent
          |
          v
    Recruitment MCP adapter
          |
          v
Canonical Recruitment domain service
          |
          v
Identity + authorization + business rules
          |
          v
PostgreSQL
          |
          v
Audit / provenance / domain events
```

Recruitment MCP is a controlled adapter. It does not contain SQL, duplicate ApplicantService or EmployeeService rules, resolve authority from caller text, own channel transport, call Hermes directly, own payroll, or create an independent `mcp_recruitment_*` schema.

The internal AL-RIFAI frontend should call the canonical application/API service directly (option B), while external agents and Conversations & AI use Recruitment MCP. This avoids an unnecessary internal network hop; both paths must invoke the same canonical services.

## 2. Evidence-based decisions

| Decision | Evidence | Result |
|---|---|---|
| Applicant is canonical identity-bearing recruitment record | AL-RIFAI `applicants` schema and `ApplicantService`; live Fazle has 741 candidates and 759 recruitment sessions | Use `applicants` linked to shared `persons`; preserve legacy candidate/session provenance |
| No separate Prospect/Lead entity yet | No canonical lead table/service; Fazle’s populated path is `wbom_candidates`/sessions, while `wbom_job_applications` is empty | Treat “interested” as a recruitment interaction/status before or at applicant creation; add a lead entity only after an owner-approved requirement |
| Recruitment is year-round | Owner-approved business policy; live role/recruitment evidence | A valid canonical Role is sufficient for normal interest/application; Vacancy is optional context |
| Role and vacancy are different | Live roles are represented in policy/knowledge and recruitment flow, but no canonical AL-RIFAI role/vacancy tables exist | Define canonical Role service now; Vacancy/Opening is optional metadata, not a gate for ordinary applications |
| Existing EmployeeService owns handoff | `EmployeeService.hire_applicant()` is the canonical intended boundary and currently fails closed without trusted Admin authorization | Recruitment requests Workforce handoff; it never creates employee rows itself |
| Current applicant states are limited | `applicants.status` constraint is `new`, `screening`, `interviewing`, `offered`, `hired`, `rejected`, `withdrawn` | Preserve these Application states; model `joining_pending` as a handoff substate/event until a canonical joining record exists |
| AI is not authority | Business rules AI-001..005 and live Hermes/source audit | AI may extract and draft; deterministic services authorize, validate, persist, and emit events |

## 3. Domain model

### 3.1 Person and applicant

- `person_id` is the immutable UUID and canonical Person identity; it is not the authoritative business Employee ID.
- `applicant_id` is the recruitment aggregate identifier.
- `application_code` is a unique human/reference code, not identity.
- `position` is the selected role reference or canonical role code.
- `source` records channel/form/referral provenance.
- `status` is owned by Recruitment service.
- Applicant history, reusable profile data, candidate-provided document references, and application-specific documents/readiness/interview/handoff events are append-only or auditable domain records; they are not MCP-owned tables.

“Interested person” is not a second person or lead identity. If a person only asks a question, Conversations & AI answers from policy and does not create an applicant. If they express interest in a valid canonical Role, Recruitment resolves or creates the shared Person, reuses or creates the Applicant profile, and creates a new Application in `new`; no Vacancy is required. A partial interest with insufficient identity or role becomes a draft/review request, not a fabricated role or applicant.

The reusable Applicant profile contains the canonical Person link, normalized contacts, aliases, reusable profile information, and candidate-provided document references where appropriate. Each Application contains the requested Role, optional Vacancy/campaign context, application date/source, screening, interview, offer, joining readiness, outcome, and any rejection/withdrawal reason. A Person/Applicant may have multiple historical Applications.

### 3.2 Role and vacancy

`Role` describes the job: stable role code, title, duties, eligibility, duty pattern, policy references, document requirements, and sensitivity classification.

`Vacancy`/`Opening` describes optional demand context: vacancy ID, role code, status (`open`, `paused`, `closed`, `expired`), headcount, opening/closing dates, approved policy version, campaign, location, client/program demand, priority, and reviewer. A Role can exist without any Vacancy, and normal year-round applications remain allowed. An explicitly selected closed campaign/opening cannot accept a vacancy-specific application. A Vacancy cannot invent salary, benefits, hours, or eligibility values; missing policy remains unknown.

The canonical Role/Vacancy service is not yet present in this repository. Implementers must add the Role catalog behind the domain service boundary before enabling Role-based writes; Vacancy writes are optional and must remain separate. Until then, `list_recruitment_roles` may read approved policy records and `list_open_vacancies` returns only verified openings or an explicit `POLICY_VALUE_UNAVAILABLE`/empty result. Absence of an opening does not block `register_interest` or Role-based `create_application`.

### 3.3 Current legacy mapping

Fresh live evidence: `wbom_candidates` has 741 rows, `fazle_recruitment_sessions` 759, `wbom_candidate_conversations` exists, and `wbom_job_applications` has 0 rows. `modules/recruitment_flow` persists candidate intake, staged fields, source bridge/message, score, post-intake state, and linked employee; `modules/message_router` and `bridge_poller` route recruitment messages. These are import/provenance inputs only.

| Legacy | Canonical target | Reader/writer evidence | Treatment |
|---|---|---|---|
| `wbom_candidates` | `persons` + `applicants` + recruitment history | `recruitment_flow`, router | Import with source IDs, status mapping, and review for ambiguous identity |
| `fazle_recruitment_sessions` | application/intake history | recruitment flow | Preserve collection step, score, source bridge/message, timestamps |
| `wbom_candidate_conversations` | conversation evidence/event provenance | recruitment flow | Preserve as message-linked evidence, not canonical policy |
| `wbom_job_applications` | `applicants`/application history | schema exists; live count 0 | Do not treat as authoritative populated history |
| `linked_employee_id` | Workforce employee reference | live candidate column | Validate identity and handoff provenance; never copy blindly |

## 4. Lifecycle and state machine

Persisted application states:

```text
new -> screening -> interviewing -> offered -> hired
 |       |             |             |
 +----> withdrawn      +-----------> rejected
```

`joining_pending` is a handoff substate after an authorized offer/approval and before Workforce confirms employee creation. It must have a durable handoff record/event or an approved extension to the canonical schema; it must not be faked by overloading an unrelated status.

| State | Meaning | Allowed previous | Allowed next | Actor/evidence |
|---|---|---|---|---|
| `new` | Applicant registered, not screened | none or imported | `screening`, `withdrawn` | applicant/staff; identity and role evidence |
| `screening` | Information/eligibility collection | `new` | `interviewing`, `rejected`, `withdrawn` | recruitment staff; required fields/policy check |
| `interviewing` | Interview or readiness assessment underway | `screening` | `offered`, `rejected`, `withdrawn` | recruitment staff; interview/readiness evidence |
| `offered` | Selection approved for joining offer | `interviewing` | `joining_pending`, `rejected`, `withdrawn` | authorized Recruitment/Admin approval |
| `joining_pending` | Workforce handoff requested/awaiting completion | `offered` | `hired`, `rejected`, `withdrawn` | authorized handoff; Workforce result |
| `hired` | Workforce accepted and employee exists/reused | `joining_pending` | none; later employee lifecycle belongs Workforce | Workforce confirmation and employee ID |
| `rejected` | This Application was declined | `screening`, `interviewing`, `offered`, `joining_pending` | none; create a new Application for a later attempt | recruitment/Admin reason |
| `withdrawn` | This Application was withdrawn | `new`, `screening`, `interviewing`, `offered`, `joining_pending` | none; create a new Application for a later attempt | applicant or staff evidence |

Rejected and withdrawn Applications remain immutable terminal history. The Person and Applicant profile are not rejected or withdrawn permanently. A later attempt reuses the same Person and Applicant, creates a new Application linked to the requested Role, and starts at `new` or `screening` according to the submitted evidence. Repeated transition to the same state is an idempotent no-op when the request key and target agree. Conflicting transition or stale version returns `INVALID_STATUS_TRANSITION`.

## 5. Shared request context

Every MCP call receives a server-created context:

```json
{
  "principal_id": "trusted UUID",
  "principal_type": "applicant|recruitment_staff|admin|owner|ai_service|...",
  "person_id": "trusted canonical UUID or null",
  "canonical_phone_ref": "trusted current/historical phone reference or null",
  "platform_identity": {"platform":"WHATSAPP","id":"typed external ID"},
  "capabilities": ["manage_applicants"],
  "source_channel": "whatsapp|meta|frontend|agent",
  "conversation_id": "optional",
  "message_id": "optional",
  "message_timestamp": "optional source timestamp",
  "reply_to_message_id": "optional",
  "topic": "optional current topic",
  "semantic_intent": "optional interpreted intent",
  "evidence_refs": ["message/document/event references"],
  "applicable_instruction_ref": "optional instruction ID/version",
  "correlation_id": "required",
  "causation_id": "optional",
  "idempotency_key": "required for writes",
  "request_time": "server timestamp"
}
```

Caller-supplied IDs, role fields, prompts, or MCP descriptions never create trusted authority. `TrustedPrincipal` and `authorize()` from `src/alrifai/authorization/policy.py` remain the only authorization boundary.

## 6. Resources

Resources are service-backed views, never raw-table exposure. Resource URIs use `recruitment://...`.

| Resource | URI | Backing service | Permission | Sensitivity / self-service |
|---|---|---|---|---|
| Recruitment policy | `recruitment://policy/{topic}` | Policy/knowledge service | READ | public-safe only when approved; applicant-safe filtered |
| Role catalog | `recruitment://roles` | Role service | READ | public-safe approved fields |
| Role details | `recruitment://roles/{role_code}` | Role service | READ | duties/eligibility; salary/private fields filtered |
| Open vacancies | `recruitment://vacancies/open` | Vacancy service | READ | applicant-safe approved openings |
| Applicant profile | `recruitment://applicants/{applicant_id}` | ApplicantService | scoped READ | applicant may read own masked profile; staff scope required |
| Application | `recruitment://applications/{application_code}` | ApplicantService | scoped READ | applicant own application only; staff broader |
| Status/history | `recruitment://applications/{application_code}/history` | Recruitment history service | scoped READ | applicant own safe timeline; sensitive review notes filtered |
| Joining requirements | `recruitment://applications/{application_code}/joining-requirements` | Policy + Recruitment service | scoped READ | applicant-safe checklist; NID contents never returned |
| Recruitment context | `recruitment://conversations/{conversation_id}/context` | Conversations contract | scoped READ | only evidence needed for recruitment action; no raw document dump |

Not-found is a typed result, not an empty success. Applicant-scoped reads must resolve the trusted principal’s person/applicant relationship first. Every sensitive read is audit-visible; public policy reads may use aggregate access logs without storing message contents.

## 7. Tool catalog

All tools return an envelope: `{status, data, audit_ref, event_refs, correlation_id, idempotent_replay}`. Writes call canonical domain services inside one transaction where the service owns the aggregate; cross-server handoff uses an outbox/event boundary.

### 7.1 Read-only tools

| Tool | Purpose | Required input | Capability | Service | AI direct |
|---|---|---|---|---|---|
| `find_applicant` | Find safely by trusted scope and evidence | phone/platform ID/name/`person_id`; at least one | scoped applicant read | Identity + ApplicantService | yes, filtered |
| `get_applicant` | Read one applicant | `applicant_id` or application code | scoped applicant read | ApplicantService | yes, filtered |
| `list_recruitment_roles` | List approved roles | filters optional | public/applicant read | Role service | yes |
| `list_open_vacancies` | List verified openings | role/status/date filters | public/applicant read | Vacancy service | yes |
| `get_role_details` | Read role policy | `role_code`/`vacancy_id` | public/applicant read | Role service | yes |
| `get_recruitment_policy` | Answer approved policy question | topic, policy version optional | public/applicant read | Policy service | yes; unknown stays unknown |
| `get_application_status` | Read applicant-scoped status | `application_code` or applicant ID | scoped applicant read | ApplicantService/history | yes, own scope |
| `get_joining_requirements` | Read checklist | application/role ID | scoped applicant read | Recruitment/policy service | yes, filtered |

Read tools never reveal NID, private notes, internal scoring rationale, credentials, or another person’s application.

### 7.2 Applicant self-service writes

| Tool | Purpose | Input | Validation/service | Idempotency | Approval |
|---|---|---|---|---|---|
| `register_interest` | Register interest for a valid canonical Role, optionally tied to a Vacancy/Opening | identity observation, `role_code`, optional `vacancy_id`, source, correlation | canonical identity resolution then ApplicantService; year-round Role-based intake; selected closed Vacancy is rejected only as vacancy-specific context | message/event ID or explicit key | no for registration; draft/review if ambiguous |
| `create_application` | Submit a new Application for a canonical Role, optionally tied to a Vacancy/Opening | applicant/person scope, `role_code`, optional `vacancy_id`, required fields, source | ApplicantService; Role must be valid; no open Vacancy required; identity not ambiguous | application key/message ID | no for submission; staff screening later |
| `update_applicant_profile` | Add/change applicant information | applicant ID, patch fields, evidence | scoped identity, field policy, optimistic version | key + field/version | staff review for sensitive identity changes |
| `record_applicant_document` | Receive/register candidate-provided document metadata/reference for an Applicant/Application | applicant ID, optional application ID, document type, storage ref, checksum, source | recruitment document-intake service; no raw binary through MCP; intake does not assert authenticity | checksum + document type + applicant/application | no approval merely to receive; status is `received`/`linked`, later `reviewed`; `formally_verified` is Workforce-owned after handoff |

MCP carries metadata and safe storage references, not document binaries unless a future approved document contract requires it. Applicant intake accepts CVs, NID images/PDFs, photos, certificates, experience documents, and other supported references without marking them verified. Self-service writes cannot change status to offered/hired or change canonical identity without review. Formal employee-document verification is Workforce authority after handoff.

### 7.3 Staff writes

| Tool | Purpose | Input | Capability/service | Approval |
|---|---|---|---|---|
| `update_application_status` | Move through allowed state machine | application ID, target, reason, evidence, expected version | `manage_applicants`; Recruitment service | approval required for `offered`, rejection policy as configured |
| `record_interview` | Record interview outcome | applicant/application, time, interviewer, result, notes reference | `manage_applicants`; Recruitment service | trusted Recruitment staff; sensitive notes filtered |
| `record_joining_readiness` | Record readiness/checklist result | application, checklist results, document intake/review states, availability | `manage_applicants`; Recruitment service | staff-controlled lifecycle decision; does not perform Workforce formal employee-document verification or hire |

### 7.4 Privileged, approval, and handoff actions

| Tool | Class | Purpose | Capability | Canonical owner |
|---|---|---|---|---|
| `approve_applicant` | APPROVAL_REQUIRED | Approve selection/offer | `approve_business_operations` plus recruitment policy | Recruitment service; Platform/Admin may orchestrate |
| `mark_joining_pending` | HANDOFF_ACTION | Create reviewed Workforce handoff request | `hire_applicant`/approved recruitment capability | Recruitment handoff service |
| `convert_applicant_to_employee` | HANDOFF_ACTION | Request/complete authorized employee conversion | trusted `hire_applicant`; never AI-only | `EmployeeService.hire_applicant()` / Workforce |

`approve_applicant` and `mark_joining_pending` may return `DRAFT` when invoked from AI or an unapproved channel. `convert_applicant_to_employee` must fail closed until a trusted Admin/Owner adapter exists; the current `EmployeeService.hire_applicant()` intentionally does so.

### 7.5 Exact tool input/result contracts

The following compact contracts complete the catalog. Types use JSON notation; omitted fields are optional. Every write also receives the shared request context and returns the common envelope.

| Tool | Input schema | Result data | Retry/approval/self-service |
|---|---|---|---|
| `find_applicant` | `{phone?, external_platform?, name?, person_id?, limit?}` | `{matches:[ApplicantSummary], ambiguity:bool}` | read-only; scoped; applicant may receive only own match |
| `get_applicant` | `{applicant_id? , application_code?}` | `{applicant:ApplicantView}` | read-only; scoped |
| `list_recruitment_roles` | `{active_only?, query?, limit?}` | `{roles:[RoleSummary]}` | read-only; policy-filtered |
| `list_open_vacancies` | `{role_code?, as_of?, limit?}` | `{vacancies:[VacancySummary]}` | read-only; only verified openings |
| `get_role_details` | `{role_code? , vacancy_id?}` | `{role:RoleDetails}` | read-only; policy-filtered |
| `get_recruitment_policy` | `{topic, role_code?, policy_version?}` | `{value, status, source_ref, effective_at}` | read-only; unknown remains explicit |
| `get_application_status` | `{application_code? , applicant_id?}` | `{status, history_summary, next_allowed_action}` | read-only; applicant own scope |
| `get_joining_requirements` | `{application_code? , role_code?}` | `{requirements:[Requirement], completion}` | read-only; sensitive values masked |
| `register_interest` | `{identity, role_code, vacancy_id?, source, evidence_ref}` | `{person_id, applicant_id, application_code, created, status}` | idempotent; self-service allowed; no Vacancy required; ambiguity becomes review |
| `create_application` | `{applicant_id?, identity?, role_code, vacancy_id?, fields, source}` | `{person_id, applicant_id, application_id, application_code, status}` | idempotent; self-service allowed; Role required, Vacancy optional; historical terminal Applications do not block a new one |
| `update_applicant_profile` | `{applicant_id, patch, expected_version}` | `{applicant, changed_fields}` | idempotent; own safe fields or staff scope |
| `record_applicant_document` | `{applicant_id, application_id?, document_type, storage_ref, checksum, metadata, provenance}` | `{document_id, intake_status, review_status, verification_status}` | idempotent checksum; self-service intake; initial status is `received`/`linked`, never formally verified |
| `update_application_status` | `{application_code, target_status, reason_ref, expected_version}` | `{previous_status, status, event_id}` | idempotent; staff; approval for offer/reject per policy |
| `record_interview` | `{application_code, interviewer_id, occurred_at, outcome, notes_ref}` | `{interview_id, readiness_status}` | staff write; no direct offer |
| `record_joining_readiness` | `{application_code, checklist, available_date?, evidence_refs}` | `{readiness_id, complete, missing}` | staff write; no direct hire |
| `approve_applicant` | `{application_code, approval_reason, expected_version}` | `{status, approval_id, event_id}` | privileged; human approval; AI draft only |
| `mark_joining_pending` | `{application_code, workforce_payload, expected_version}` | `{handoff_id, status}` | privileged handoff; human approval; outbox |
| `convert_applicant_to_employee` | `{application_code, designated_employee_id, display_name, designation?, department?}` | `{handoff_id, employee_business_id, person_id, internal_employee_record_ref?, status}` | trusted Admin/Owner only; Workforce service; idempotent; designated ID is normalized Bangladesh mobile |

Canonical result types are `READ`, `DRAFT`, `VALIDATE`, `WRITE`, `PENDING_REVIEW`, `HANDOFF`, and `ERROR`. A tool never returns a successful mutation until the domain transaction and required audit/event write have committed.

## 7.6 Contract examples

1. **Available jobs**

```json
{"tool":"list_open_vacancies","input":{"role_code":"ESCORT"},"result":{"status":"READ","data":{"vacancies":[]}}}
```

2. **Register interest**

```json
{"tool":"register_interest","input":{"identity":{"phone":"+88017...","name":"Applicant"},"role_code":"SECURITY_GUARD","source":"whatsapp","evidence_ref":"msg-123"},"result":{"status":"WRITE","data":{"applicant_id":"...","status":"new"}}}
```

3. **Existing applicant status**

```json
{"tool":"get_application_status","input":{"application_code":"APP-..."},"result":{"status":"READ","data":{"status":"screening","next_allowed_action":"record_interview"}}}
```

4. **Additional information**

```json
{"tool":"update_applicant_profile","input":{"applicant_id":"...","patch":{"area":"...","experience_years":3},"expected_version":4},"result":{"status":"WRITE","data":{"changed_fields":["area","experience_years"]}}}
```

5. **Staff interview**

```json
{"tool":"record_interview","input":{"application_code":"APP-...","interviewer_id":"...","occurred_at":"2026-09-22T10:00:00Z","outcome":"pass","notes_ref":"doc-..."},"result":{"status":"WRITE","data":{"interview_id":"..."}}}
```

6. **Authorized approval**

```json
{"tool":"approve_applicant","input":{"application_code":"APP-...","approval_reason":"verified interview","expected_version":7},"result":{"status":"WRITE","data":{"status":"offered"}}}
```

7. **Joining pending**

```json
{"tool":"mark_joining_pending","input":{"application_code":"APP-...","workforce_payload":{"joining_date":"2026-10-01"},"expected_version":8},"result":{"status":"HANDOFF","data":{"handoff_id":"...","status":"pending"}}}
```

8. **Employee handoff**

```json
{"tool":"convert_applicant_to_employee","input":{"application_code":"APP-...","designated_employee_id":"01XXXXXXXXX","display_name":"Applicant"},"result":{"status":"HANDOFF","data":{"employee_business_id":"01XXXXXXXXX","person_id":"...","internal_employee_record_ref":"...","status":"completed"}}}
```

9. **Repeated message**

```json
{"tool":"register_interest","context":{"idempotency_key":"bridge1:msg-123"},"result":{"status":"WRITE","idempotent_replay":true,"data":{"applicant_id":"..."}}}
```

10. **Ambiguous identity**

```json
{"tool":"find_applicant","input":{"name":"Rahim"},"result":{"status":"ERROR","error":{"code":"AMBIGUOUS_IDENTITY","retryable":false,"next":"provide verified phone or staff review"}}}
```

## 8. Tool contract requirements

Every write input includes a stable `idempotency_key`, `correlation_id`, source/provenance, and an expected aggregate version where state transitions are involved. Every tool must:

1. validate shape and policy through the canonical service;
2. resolve identity deterministically;
3. authorize using `TrustedPrincipal` capabilities;
4. use the service transaction boundary;
5. write audit/event records through shared helpers;
6. return a typed result or classified error;
7. safely replay the same request;
8. never retry a non-idempotent external side effect without the service’s outbox contract.

Hermes may invoke read tools and prepare self-service/staff drafts. Hermes may not directly invoke privileged writes, supply authority, approve applicants, or complete employee conversion.

## 9. Identity and ambiguity

Resolution order is deterministic: verified typed external platform ID or verified national identifier; normalized phone evidence; verified alias/name evidence; then review. Bangladeshi phones use the shared `phone_normalizer`; raw input is retained as provenance and normalized value is used for matching. WhatsApp/Meta IDs are typed external identities, not interchangeable phone values. NID is a sensitive identifier and only a verified, authorized value may strengthen identity.

Name spelling differences create aliases, not new people and not automatic merges. Shared phones, changed phones, payout numbers, and unverified names cannot prove identity. Existing active or inactive employees must be detected before creating an applicant/person; an inactive employee is not a new person. Ambiguous matches return `AMBIGUOUS_IDENTITY` and create a reviewable event without mutation.

## 10. Phone persistence and employee business identifier

An inbound WhatsApp/mobile number is durable business evidence, not disposable transport metadata. Conversations & AI must preserve the normalized source phone and provenance for every inbound conversation and message, even when no recruitment action is created. The association is:

```text
Person
  → normalized phone/contact method
  → typed platform identity (for example WhatsApp)
  → conversation/thread
  → ordered messages
  → Applicant/Application when recruitment applies
```

Recruitment receives the trusted phone reference and uses it for applicant lookup, returning-person recognition, follow-up, personalization, application correlation, and future Workforce lookup. Recruitment does not duplicate raw messages; Conversations & AI remains the canonical message/history owner.

The immutable `person_id` remains the internal Person identity. It is not the authoritative business Employee identity. For an employee, the designated normalized Bangladeshi mobile is the authoritative business `employee_business_id`/Employee ID used by employee management, payroll, ledger, cash, attendance, roster, escort, messaging, and reporting workflows. A physical database may retain an internal UUID employee-record key for foreign keys and technical joins, but that key is an implementation detail and must not redefine Employee ID.

| Phone identity record | Rule |
|---|---|
| Designated Employee ID | One normalized Bangladeshi mobile, validated as the final 11 digits beginning with `0`; stable during normal operation |
| Contact/messaging number | A current or observed number/platform identity used to communicate; it may differ from Employee ID and does not mutate it automatically |
| Historical Employee ID | A prior designated Employee ID retained as a typed, time-bounded historical identifier/alias with provenance and replacement reason |
| Contact/phone change | A new sender/contact number is resolved and associated safely; it never changes Employee ID automatically |
| Explicit Employee ID edit | Only an authorized, confirmed `Edit Employee ID` operation may change the designated Employee ID |
| Uniqueness | No two Employees may use the same normalized Employee ID. Historical IDs cannot be silently reassigned when they create ambiguity |
| Conflict | Current Employee ID, contact number, or Person conflict fails closed with `AMBIGUOUS_IDENTITY`/review; name alone never overrides phone conflict |
| Old-ID lookup | Returns the linked Employee/Person and historical-match signal; it must not create a new Person/Employee |
| Audit | Record old/new Employee ID, actor, source, evidence, effective time, correlation, affected references, and outcome |

If an authorized Employee ID edit changes the designated mobile, the previous Employee ID remains a historical alias. A later person must not silently inherit it. Payout numbers remain financial routing attributes and are never Employee ID.

Identity resolution may consider Person UUID, designated Employee ID, current/contact phone, historical Employee ID, typed platform ID, Applicant, Employee, aliases/name, and conversation provenance. A matching name alone cannot override a conflicting phone. Identity resolution and Employee ID mutation are separate operations. Ambiguity fails closed or enters resolution; it never creates a duplicate Person/Applicant/Employee.

### 10.1 Bangladesh mobile normalization and validation

All comparison and uniqueness checks use one deterministic normalizer. Acceptable textual forms may begin with `+`, `00`, `88`, or local `0`. The normalizer removes permitted formatting separators, validates Bangladesh mobile structure, converts the number to the final 11 digits, and accepts it only when those 11 digits begin with `0` (conceptually `01XXXXXXXXX`). Examples such as `+8801XXXXXXXXX`, `008801XXXXXXXXX`, `8801XXXXXXXXX`, and `01XXXXXXXXX` therefore compare as one canonical Employee ID when they represent the same final 11 digits. Raw formatting strings are never compared.

Invalid length, non-Bangladeshi structure, unsupported prefixes, or ambiguous normalization returns a validation error and cannot create or edit an Employee ID. Store raw observed values only as provenance; store the normalized 11-digit value for comparison and business lookup.

### 10.2 Explicit Employee ID edit

The future authorized frontend/business workflow must expose `Edit Employee ID` with: existing Employee ID, requested new mobile, deterministic normalization result, conflict/uniqueness check, explicit confirmation, trusted actor/capability, affected-reference/index plan, and correlation/idempotency key. The operation runs transactionally: validate and lock the Employee, verify the requested normalized ID is unused, update the designated Employee ID and dependent business references, append the old ID to historical identifiers, write audit/event records, then commit. Any validation, conflict, reference-update, or audit failure rolls back the complete edit. Inbound messages, automatic phone discovery, profile edits, and contact association cannot invoke this operation.

## 11. Applicant-to-employee handoff

Prerequisites:

1. applicant has canonical person identity;
2. application is `offered` and required approval/readiness evidence exists;
3. trusted Admin/Owner authorization is present;
4. Workforce accepts the handoff with stable idempotency key;
5. existing employee lookup uses the same person/identity resolver;
6. the designated Employee ID is supplied as a Bangladesh mobile, normalized and validated, and required employee fields are valid.

The handoff reuses the canonical Person identity, retains applicant/application history, and passes an event/command containing applicant ID, application code, person ID, designated normalized `employee_business_id`, approved role, joining data, actor, correlation, provenance, and idempotency key. Workforce validates uniqueness before creating or reusing the Employee record. Any internal employee-record UUID returned by the adapter is technical only; it is not the authoritative Employee ID. If an inactive employee is the same person, Workforce applies its reactivation policy; Recruitment does not mutate the employee.

On success Workforce returns the authoritative normalized `employee_business_id` and emits `recruitment.applicant_joined`/`recruitment.employee_handoff_completed`; Recruitment marks the current Application `hired`. Candidate-provided document references and provenance travel with the handoff; the Person identity and storage reference are reused, not duplicated. Workforce may mark documents `formally_verified` under its employee-document policy. On timeout, the handoff remains pending and is retryable. On invalid or duplicate Employee ID, return a reviewable failure; do not create a second person or employee. Partial failure is resolved by the outbox/idempotency protocol, not compensating ad hoc SQL.

## 12. Conversations & AI contract

Conversations & AI passes:

```json
{
  "trusted_person_id": "resolved or null",
  "conversation_id": "canonical thread",
  "source_channel": "bridge1|bridge2|bridge3|meta|whatsapp|frontend",
  "source_message_id": "external/internal message reference",
  "intent": "job_interest|vacancy_question|application|status_query|joining_query",
  "extracted_fields": {"role_code": "...", "name": "...", "phone": "..."},
  "person_id": "trusted canonical UUID or null",
  "canonical_phone_ref": "trusted normalized current/historical phone reference",
  "platform_identity": {"platform":"WHATSAPP","id":"typed external ID"},
  "message_timestamp": "source timestamp",
  "reply_to_message_id": "optional",
  "topic": "job_interest|role|salary|documents|application|status|joining|...",
  "confidence": 0.0,
  "evidence_refs": ["message/event IDs"],
  "applicable_instruction_ref": "instruction ID/version or null",
  "correlation_id": "...",
  "idempotency_key": "...",
  "requested_action": "read|draft|write"
}
```

Recruitment validates the extracted fields, performs identity and policy checks, and returns `READ`, `DRAFT`, `VALIDATE`, `WRITE`, `PENDING_REVIEW`, or typed error. Conversations & AI creates the natural-language reply and carries the domain result back to the channel. Recruitment does not retrieve raw messages, choose models, or send WhatsApp replies.

### 12.1 Stateful semantic conversation contract

Recruitment conversation understanding is not a keyword chatbot. Conversations & AI interprets the semantic meaning of the complete message and relevant context, including correctly spelled or misspelled Bangla, colloquial Bangla, Banglish, mixed Bangla/English, incomplete sentences, multiple clauses, pronouns, follow-up questions, and references to earlier messages. Keywords may provide hints, indexing, safety triggers, or fallback evidence only; they are not the principal intent engine.

The canonical conversation history is owned by Conversations & AI and preserves:

- stable message ID, Person/contact identity, normalized source phone, typed platform ID, channel/source;
- inbound/outbound direction, actor/sender, exact timestamp, ordered position, and reply-to relationship;
- conversation/thread ID, gaps, media/document references, delivery state, AI/human/device attribution;
- domain/topic association, extraction evidence, confidence, correlation, and provenance.

Conversation context is stateful and topic-aware. Recruitment topics include job interest, role inquiry, salary, eligibility, ship duty, documents, application, status, interview, joining, office/address, duty conditions, benefits, and follow-up. A thread may move `job interest → role → salary → documents → application → joining`; it has one current active topic plus completed topic history, not one permanent topic. Completed topics are not reopened unless the person raises them again.

Message order and timing are semantic inputs. For example, “চাকরি করতে চাই” followed by “জাহাজে” and then “আগে কাজ করি নাই” is one contextual sequence. “কালকে যে কাগজ পাঠাইছিলাম” requires the prior document/message reference. Repeated questions may use recent context and existing trusted facts to avoid inconsistent answers.

The bounded context composition for a reply or domain action is:

1. current inbound message;
2. directly replied-to message, if available;
3. recent relevant turns in order;
4. active topic and recent completed topics;
5. semantically relevant older messages, not the entire history;
6. trusted Person/Applicant/Application facts, including current and historical phone references;
7. current canonical Role and recruitment policy;
8. latest applicable authorized Admin AI instruction;
9. authorized Recruitment tool results.

Conversation history remains stored even when older irrelevant messages are excluded from a particular context window. Conversations & AI returns context references and extracted claims; Recruitment decides whether a claim may become a domain fact.

### 12.2 Admin/Owner AI instruction layer

Authorized Admin/Owner instructions guide interpretation, information collection, reply behavior, recruitment priorities, current role information, escalation, and temporary conversation policy. They never directly authorize identity mutation, application state changes, hiring, Employee creation, financial effects, or protected writes.

Each instruction has: `instruction_id`, version, scope/domain, topic and role applicability, `issued_by`, `issued_at`, `effective_from`, optional expiry/supersession, active/inactive status, instruction text or safe reference, and audit/provenance. Instructions are append-only/versioned; historical versions are not overwritten. The context records the exact applicable instruction ID/version used for a reply or extraction so the decision is reproducible.

Selection is deterministic: trusted authorization and scope → effective time window → most specific applicable domain/topic/role → latest version. Conflicting or missing instructions remain unresolved and require review; an instruction cannot override canonical policy, authorization, identity, state transition, or persistence rules.

### 12.3 Semantic extraction and missing information

The semantic layer distinguishes `unknown`, `provided`, `candidate_claimed`, `staff_reviewed`, and `verified` for each extracted fact. It compares trusted Applicant/Application facts and recent evidence before asking for information. A reply may ask only for missing experience, documents, availability, or other role-required fields; it must not repeatedly request already-known sufficiently trusted data.

“আমার নতুন নাম্বার 01...” creates a candidate claim and phone-change review/update request; it does not destroy the old phone link automatically. “আমি আজই জয়েন করব” is candidate-provided readiness, not authorization to mark joining or hiring.

### 12.4 Personalization and proactive follow-up

With trusted identity resolution, Conversations & AI may personalize a reply using the Person’s current/history phone, prior document intake, requested Role, Application status, and missing fields without exposing another person’s data. Recruitment may identify suitable applicants for a future role offer or follow-up using canonical phone and application context. Conversations & AI/outbound infrastructure controls whether and how an outbound message is actually sent; Recruitment cannot bypass outbound authorization, rate limits, consent, or delivery controls.

### 12.5 Natural, knowledge-grounded conversation policy

The assistant is a natural, relationship-aware, goal-oriented business conversation assistant, not a fixed question-answer bot. Knowledge documents are a reference library; examples are illustrative, not prescriptive. C7 interprets meaning and evidence, C8/canonical domain read services supply authoritative business facts and protected decisions, and C9 produces the final natural-language response. No example sentence is an exact-match rule or mandatory script. Wording, explanation length and useful next-step suggestions may adapt while preserving verified facts exactly.

Classify source material before use:

- `AUTHORITATIVE_BUSINESS_FACT`: current approved role/policy value (salary, benefits, duty hours, address, eligibility, role requirements). Preserve numeric values, units, dates and conditions exactly; absent, stale or conflicting facts remain unknown and require a canonical read or escalation.
- `MANDATORY_BUSINESS_RULE`: only an explicitly identified legal, authorization, or protected canonical policy rule. A sample conversation or style preference cannot promote itself into this class.
- `FLEXIBLE_OPERATIONAL_GUIDANCE`: practical advice that may be adapted, but cannot override mandatory policy or promise an approval.
- `CONVERSATION_STYLE_GUIDANCE`: tone and presentation preference, subordinate to verified relationship state and safety.
- `ILLUSTRATIVE_EXAMPLE`: an example of possible conversation/meaning, never a reply template, policy source, or fixed dialogue tree.
- `HISTORICAL_OR_SUPERSEDED`: retained for provenance/history, never treated as current without explicit source applicability.

Goal progression is flexible, not a Recruitment state machine. The assistant may collect interest, role preference, experience, conditions, missing information and joining readiness in any order; it must support topic changes, declines and returns, avoid redundant requests, and not repeatedly push recruitment after a decline. A supplementary question or suggestion is optional and must be relevant. Document absence does not itself justify rejection: ask what the candidate has, use only approved alternatives, and mark pending/escalate when staff approval is required. Do not waive mandatory requirements, infer selection, promise employment, or schedule a notification. The example of a message about two hours after agreement is not an approved delay rule; only a canonical Recruitment selection decision and configured notification workflow can authorize selection communication.

Address form follows trusted relationship evidence: unknown persons, applicants, and selected-but-not-yet-joined candidates receive respectful **“আপনি”**. Only a C2-resolved Person with C6 `CONFIRMED_CURRENT_EMPLOYEE` evidence from an active canonical Employee record may be addressed as **“তুমি”**. In unresolved, inactive/former, ambiguous, group-member-mismatch or unsupported cases use **“আপনি”**. A familiar number, application history, user self-claim, or selection status cannot establish current employment; address choice never changes Employee ID.

No approved Recruitment knowledge corpus/service or concrete role/salary/document policy records were found in the current repository. The canonical Role/policy source remains an implementation prerequisite; until available, the assistant must request an authorized domain read or state that the value is unavailable rather than inventing it. Repository search found no canonical office address. Owner confirmation is required to establish whether **“AK Khan Mor, Pahartali, Chattogram”** and **“AK Khan Mor, Victoria No. 1 Gate”** are the same physical location and to approve the exact address string. Neither may be communicated as a verified fact before confirmation.

## 13. Frontend contract

Internal AL-RIFAI forms call the canonical Recruitment API/domain service directly. The request uses the same input types, trusted session principal, correlation ID, idempotency key, validation, transaction, audit, and event behavior as MCP. MCP is an additional adapter for agent/conversation access, not a required internal hop. Form and message paths must produce equivalent domain results for equivalent authorized inputs.

## 14. Documents and sensitive data

| Data | MCP treatment | Access |
|---|---|---|
| NID number/image | candidate-provided intake metadata/reference and provenance; status `received`/`linked`/`reviewed`/`formally_verified`; never infer authenticity from receipt | applicant own metadata; Recruitment staff may review; Workforce formally verifies after handoff |
| Photo | candidate-provided storage reference, checksum, type, provenance, intake status | applicant own; authorized staff; AI receives no binary by default |
| CV/resume/certificate/experience document | Applicant/Application-linked metadata/reference and provenance; receipt is not verification | applicant own checklist; Recruitment may review; Workforce owns employee verification after handoff where applicable |
| Family/emergency/reference | restricted applicant field; explicit purpose and consent | staff/admin only; no public or default Hermes exposure |
| Conversation evidence | message/event IDs and minimal extracted fields | scoped by conversation/person; raw content remains Conversations |

Storage remains the existing approved document/storage service; this specification creates no file store. Every intake record distinguishes `candidate_provided`, `staff_reviewed`, and `formally_verified` provenance/status where applicable, and records source channel, message/event or upload reference, timestamp, document type, linked Person/Application, and reviewer. Logs redact phone/NID/document values where not required and never record credentials or binary contents. Hermes receives references and extracted safe metadata only unless a separately authorized workflow requires raw content.

## 15. Authorization matrix

| Actor | Read public policy/roles | Read own applicant | Self-service writes | Staff writes | Approve/offer | Handoff/convert |
|---|---:|---:|---:|---:|---:|---:|
| Anonymous/public | approved only | no | no | no | no | no |
| Identified applicant | yes | own only | own allowed fields | no | no | no |
| Office/operator | approved/read scope | assigned scope | no or delegated | limited `manage_applicants` | no unless capability | no |
| Recruitment staff | yes | permitted scope | permitted | yes | policy-dependent approval | no without hire capability |
| Admin | yes | authorized broad scope | no special bypass | yes | `approve_business_operations` | `hire_applicant` if granted |
| OWNER | yes | all authorized | no special duplicate path | yes | yes | yes; Owner remains distinct |
| Conversations/Hermes service | filtered reads | only trusted scoped context | draft only by default | no direct privileged write | no | no |
| Platform/Admin orchestration | derived reports/queues | scoped | no domain direct writes | orchestrates approved calls | approval workflow | submits trusted handoff |

No second Recruitment RBAC system is permitted. Capabilities are evaluated centrally; caller claims and frontend visibility are insufficient.

## 16. Idempotency and duplicate handling

| Case | Key and behavior |
|---|---|
| repeated WhatsApp message | source platform + source message ID; replay original result, no second write |
| webhook redelivery | external event ID + source; deduplicate before domain call |
| duplicate application submit | application idempotency key; same payload replays result; conflicting payload returns `IDEMPOTENCY_CONFLICT` |
| form double-submit | client/server idempotency key; one ApplicantService transaction |
| staff retry | command key + aggregate version; same transition replays, stale version rejects |
| repeated document | applicant + document type + checksum; replay existing metadata |
| reapplication after rejection/withdrawal | Person/Applicant identity is reused; new Role/Application identity creates a new Application; same submission key replays only that new Application; old terminal Application remains unchanged |
| repeated status | same target and key is no-op; different target is transition validation |
| repeated conversion | handoff key/application ID/person ID; return existing Workforce result |

Database uniqueness and event idempotency must be enforced by canonical schema/service implementation. `business_events.idempotency_key` currently lacks a unique constraint, so adding the required database constraint is an `IMPLEMENTATION_PREREQUISITE`, not part of this task.

## 17. Audit, provenance, and events

Material actions emit audit records containing actor/principal, person/applicant/application IDs, source/channel, correlation/causation, provenance references, timestamp, previous/new state, outcome, and idempotency key. Do not log NID/document content, credentials, or full sensitive messages.

Final event set:

| Event | Producer | Consumers | Payload policy |
|---|---|---|---|
| `recruitment.interest_registered` | Recruitment | Conversations, Platform | person/applicant/role/source IDs; no sensitive content |
| `recruitment.application_created` | Recruitment | Conversations, Platform | applicant/application/person IDs, role, source |
| `recruitment.application_updated` | Recruitment | Platform, Workforce when relevant | changed-field names, not sensitive values |
| `recruitment.status_changed` | Recruitment | Conversations, Platform | previous/new status, actor, reason ref |
| `recruitment.applicant_approved` | Recruitment | Platform, Workforce | applicant/application/person/role IDs and approval ref |
| `recruitment.joining_pending` | Recruitment | Workforce, Platform | handoff ID and required evidence refs |
| `recruitment.applicant_joined` | Workforce | Recruitment, Platform, Finance reference | applicant/person/employee IDs and result |
| `recruitment.employee_handoff_completed` | Workforce | Recruitment, Platform | handoff/application/employee IDs, outcome |

Events use an outbox/delivery contract with stable event ID and idempotency key. Consumers must tolerate replay.

## 18. Stable error model

Employee-ID-specific errors: `INVALID_EMPLOYEE_ID` rejects a designated value that is not a normalized Bangladesh mobile; `EMPLOYEE_ID_CONFLICT` fails closed when the normalized value is already assigned or historical ownership is ambiguous. Both reject before mutation and require Workforce/staff resolution rather than duplicate creation.

| Error | Meaning | Retry | Safe interpretation/audit |
|---|---|---:|---|
| `APPLICANT_NOT_FOUND` | scoped applicant/application absent | no | say status could not be found; audit read |
| `AMBIGUOUS_IDENTITY` | multiple plausible people | no automatic retry | request verified identifier/review; audit ambiguity |
| `DUPLICATE_APPLICATION` | same application/role already exists | no | return existing safe reference or ask staff; audit |
| `ROLE_NOT_FOUND` | role code unknown | no | ask applicant to choose approved role |
| `VACANCY_CLOSED` | explicitly selected campaign/opening is closed; does not apply to ordinary Role-based year-round applications | no | explain that selected opening is closed and offer valid Role-based intake where permitted |
| `INVALID_STATUS_TRANSITION` | state machine/version violation | no until corrected | ask staff/review; audit attempted transition |
| `MISSING_REQUIRED_DOCUMENT` | prerequisite absent | after data added | return checklist; audit workflow state |
| `AUTHORIZATION_REQUIRED` | trusted capability absent | no | fail closed; audit denial |
| `APPROVAL_REQUIRED` | draft needs human approval | no; approval action | return pending review, not success |
| `EMPLOYEE_ALREADY_EXISTS` | Workforce found conflicting employee | no automatic retry | route to identity review; audit |
| `IDEMPOTENCY_CONFLICT` | key reused with different payload | no | require new key/review; audit |
| `POLICY_VALUE_UNAVAILABLE` | no current approved answer | no | state unknown and request staff confirmation |
| `UNSUPPORTED_DOCUMENT_TYPE` | submitted document type/media is not accepted by intake contract | no | request a supported type; audit intake rejection |
| `DOCUMENT_REFERENCE_INVALID` | storage/media reference cannot be safely linked | bounded retry if external storage is transient | report intake pending/failed; never claim receipt or verification |
| `SERVICE_UNAVAILABLE` | canonical dependency unavailable | bounded retry | return pending/failed, never claim mutation |

Raw SQL, stack traces, credentials, and internal database details never cross the MCP boundary.

## 19. Policy uncertainty

Salary, benefits, hours, overtime, leave, accommodation, food, vessel duty, office address/hours, Friday policy, role duties, eligibility, and required documents are policy data, not hardcoded MCP constants. The answer path is: approved current policy → structured Role/Application state → human confirmation if missing/conflicting. Stale/conflicting policy creates `POLICY_VALUE_UNAVAILABLE` or staff review. UNKNOWN remains UNKNOWN. Absence of a Vacancy is not uncertainty or a rejection: year-round Role-based recruitment remains available.

## 20. Conversation scenario matrix

| Scenario | Identity | Tool/resource | Effect | Reply owner |
|---|---|---|---|---|
| “চাকরি করতে চাই” | phone/platform if available; otherwise ask | `register_interest` after role question | self write only when role/identity sufficient; otherwise draft | Conversations & AI |
| “কি কি পদ আছে?” | none required | `list_recruitment_roles`, `list_open_vacancies` | read | Conversations & AI |
| “বেতন কত?” | none for generic role policy; applicant ID for specific offer | `get_role_details`/`get_recruitment_policy` | approved policy or unknown | Conversations & AI |
| “জাহাজে কাজ আছে?” | none or role context | vacancy/role resources | read; no inferred opening | Conversations & AI |
| “আমার আবেদন হয়েছে?” | trusted phone/platform/person; ambiguity review | `get_application_status` | scoped read | Conversations & AI |
| “আগে আবেদন করেছিলাম” | deterministic match; ambiguity review | `find_applicant`, then status | read/review; no duplicate | Conversations & AI |
| “আজই জয়েন করতে চাই” | existing applicant required | `get_joining_requirements`; readiness draft | no hire/convert | Conversations & AI |
| NID/photo sent | trusted applicant scope | `record_applicant_document` | metadata/reference only; verification pending | Conversations & AI |
| phone changed | old trusted identity + new evidence | profile update | review if identity proof insufficient | Conversations & AI |
| employee asks another role | existing employee detection | role/vacancy read; application policy | never create duplicate person automatically | Conversations & AI |
| same applicant from another channel | typed platform ID + normalized phone | `find_applicant`/status | same person if deterministic; ambiguity otherwise | Conversations & AI |

These are contract scenarios, not hardcoded chatbot scripts.

## 21. Observability and security requirements

Measure tool invocation count, latency, success/failure, authorization denials, identity ambiguity, duplicate suppression, application creation, each transition, approval queue depth, handoff latency/failure, and domain errors. Correlate MCP call → domain transaction → audit/event → conversation reply without storing unnecessary content.

Security tests must prove applicant isolation, Hermes inability to self-authorize, Owner/Admin distinction, capability enforcement, typed external IDs, no payout-number identity, no raw sensitive document exposure, and no caller-supplied ID/role impersonation.

## 22. Future implementation test matrix

Employee-ID tests must prove Bangladesh prefix normalization to the final 11 digits beginning with `0`, uniqueness before hire and edit, stable Employee ID when a different contact number sends a message, historical-ID lookup, explicit authorized edit with audit and rollback, and no duplicate Employee after Recruitment handoff.

**Unit:** schemas and validation; identity ambiguity; phone normalization; role/vacancy policy filtering; state transitions; permissions; idempotency; error mapping; sensitive-field redaction.

**Integration:** PostgreSQL ApplicantService; identity resolver; audit/event writes; role/vacancy policy service; trusted authorization; document metadata; EmployeeService handoff and rollback; outbox delivery.

**Workflow:** WhatsApp recruitment message; form application; repeated inbound event; status query; interview/readiness; approval; joining pending; Workforce handoff; duplicate channel contact.

**Conversation/identity:** preserve normalized inbound WhatsApp phone and provenance; recognize returning Applicant by current phone; resolve historical phone lookup; change phone without duplicate Person; map Employee business identifier to current canonical phone; preserve message order/timestamps/reply links; interpret misspelled/colloquial Bangla and Banglish across multiple turns; retrieve prior document context; change topics without reopening completed topics; select the latest applicable Admin instruction; retain historical instruction audit; detect missing information; prevent candidate statements from becoming privileged state changes; personalize replies without leaking another applicant’s data.

**Security/regression:** applicant cannot read another applicant; Hermes cannot perform privileged write; ordinary staff cannot approve Owner-only capability; NID is not exposed; raw claims cannot forge authority; frozen authentication behavior remains unchanged.

No destructive test may target business-data databases. Use the approved isolated local PostgreSQL fixture only.

## 23. Implementation sequence

| Stage | Scope/files | Prerequisites/tests | Runtime activation/rollback |
|---|---|---|---|
| R1 | contracts/types under future Recruitment adapter and service DTOs | owner approves this spec; unit schemas/authorization | none; delete adapter branch |
| R2 | read resources/tools over existing ApplicantService/policy | canonical read repositories, scoped identity tests | read-only shadow; disable adapter |
| R3 | applicant self-service writes | ApplicantService extension, idempotency constraint, document metadata contract | feature flag; rollback by disabling writes |
| R4 | staff lifecycle/interview/readiness/approval | state machine, capability tests, audit/events | approval-only first; revert to drafts |
| R5 | Conversations & AI dispatch contract | canonical message IDs, extraction envelope, reply correlation | shadow/draft mode; stop dispatch |
| R6 | Workforce handoff | trusted Admin/Owner adapter, EmployeeService handoff, outbox | no live hiring until end-to-end verified |
| R7 | observability/regression | metrics, security, duplicate/retry tests | no business behavior change |
| R8 | controlled activation | owner approval, migration/provenance review, shadow comparison with Fazle | staged enablement and immediate feature disable |

## 24. Open decisions and prerequisites

### `IMPLEMENTATION_PREREQUISITE`

- Canonical Role/policy service and approved policy source; optional Vacancy/Opening metadata must remain separate and non-blocking for ordinary applications.
- Application history, interview/readiness, document metadata, and joining-handoff persistence contracts.
- Unique idempotency enforcement for business events/aggregate writes.
- Trusted authentication adapter capable of constructing `TrustedPrincipal` for Recruitment staff, Admin, Owner, and the verified Conversations service.
- Workforce handoff/outbox contract and EmployeeService authorization integration.
- Approved document storage/reference service.

### Owner policy decisions applied

- Application without an open Vacancy: **RESOLVED — ALLOWED.** Recruitment is year-round and Role-based.
- Rejected/withdrawn Application reapplication: **RESOLVED — old Application remains terminal; a new Application is created for the same Person/Applicant.**
- Applicant document/staff verification: **RESOLVED/REFINED — ordinary candidate profile and document intake does not require formal verification. Formal employee-document verification primarily belongs to Workforce after handoff. Privileged recruitment lifecycle decisions remain staff-controlled.**

### `REQUIRES_LIVE_VERIFICATION`

- Current approved recruitment policy values and active vacancies.
- Current Messenger/Facebook recruitment channel activity.

### `NON_BLOCKING`

- Exact MCP transport/resource URI implementation details, provided the contracts above remain stable.

There are no unresolved architectural blocking questions for the six-server boundary; implementation must stop at the listed prerequisites rather than guess policy or authorization.

## 25. Definition of ready

A future implementation agent can build the adapter when the prerequisites are approved: ownership, entities, services, resources, tools, permissions, lifecycle, idempotency, audit/events, errors, sensitive-data rules, Conversations contract, frontend convergence, Workforce handoff, legacy mapping, tests, and rollout sequence are defined here. This document is the implementation handoff; it does not authorize runtime activation by itself.
