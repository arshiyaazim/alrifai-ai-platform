## Recruitment knowledge contract — 2026-09-23

- Starting SHA: `fa73d6795127da872998822cb3260915ed72e9ed`; branch `feat/windows-local-dev`. Existing C5/C6 and C7 work, plus the unrelated untracked `OPENCODE_C7_REPORT.md`, `OPENCODE_C7_TASK.md`, and `pyproject.toml`, were preserved. No commit or push was performed.
- Source inventory: current AL-RIFA'I recruitment documents are approved for lifecycle and grounding boundaries but do not provide a current operational knowledge corpus. Legacy `/home/azim/core` sources were read-only historical reference; legacy fee/seed material is explicitly conflicting. `/home/azim/core` was not modified and is not a runtime dependency.
- Approved facts: recruitment is year-round and Role-based; Vacancy is optional for ordinary interest/application; the documented application lifecycle is `new → screening → interviewing → offered → hired` with `rejected`/`withdrawn` paths; document intake is provenance/metadata rather than formal verification; candidate claims do not establish selection or joining; joining remains authorized identity-resolution and lifecycle controlled.
- Protected-fact register: brand, exact address, hours/Friday, role catalog, vacancies, responsibilities, eligibility, documents, interview/immediate-joining policy, duty schedule, overtime/leave, salary, joining salary, accommodation/food, charges/deposits, and authorized contacts remain unresolved unless a current approved domain read supplies them. No value is hardcoded.
- Address status: `OWNER_CONFIRMATION_REQUIRED`; the register preserves both `AK Khan Mor, Pahartali, Chattogram` and `AK Khan Mor, Victoria No. 1 Gate` and selects neither. Salary/joining salary are unavailable; legacy salary values are historical only. Charges/deposits are conflicting because legacy policy and legacy seed replies disagree.
- Implementation: added the immutable, language-neutral `src/alrifai/recruitment/knowledge.py` register and `MCP-Servers/recruitment/KNOWLEDGE_CONTRACT.md`; it returns values only for approved process rules and fail-closes unresolved facts to authorized domain read or owner confirmation. No dispatcher, mutation, persistence, or outbound path was added.
- Verification: focused recruitment/C5/C6/C7/runtime suites `114 passed`; full non-integration C1–C7 selection `184 passed` (`180` prior regression plus four contract tests); no new regressions. Compile, diff, and structural secret checks remain required before any future checkpoint.
- Owner decisions required: confirm the recruitment brand/legal display name; exact office address; and one current versioned policy bundle covering hours/Friday, roles/vacancies, duties/eligibility/documents, interview/joining, schedules/overtime/leave, salary/benefits/food, charges/deposits, and contact details.
- C5/C6 remain `PASS`; C7 remains `PARTIAL` due provider variability; C8/C9 have not started. No protected mutation, outbound message, deployment, restart, existing-database migration, legacy modification, or recruitment message occurred.

## C5/C6 fixed-clock regression reconciliation — 2026-09-23

- Starting SHA: `7d9c77c9bd2108ab95f666b53be2a28a55f8d9c1`; branch `feat/windows-local-dev`. The pushed C7 checkpoint and excluded untracked artifacts were preserved. No commit or push was performed for this fix.
- Original failure matrix: all twelve failures were reproduced. C6 context failures: `test_context_includes_c5_effective_owner_instruction_and_keeps_external_text_untrusted` and `test_c5_selection_evidence_is_preserved_with_context` expected an active Owner instruction/APPLICABLE evidence but observed empty selection. C5 failures: Owner precedence, unrelated subjects, expired/revoked/future Owner with effective Admin, supersession, same-authority conflict, topic scope, channel/account/conversation scope, and idempotent injection guidance all observed empty selection or missing conflict.
- Clock evidence: C5 tests select at fixed `2026-09-22 12:00:00+00:00`; C6 tests select/retrieve at fixed `2026-09-22 10:00:00+00:00`. `InstructionService` lifecycle events were stamped with real current UTC (`2026-09-23`), so `_status(events, context.at)` correctly excluded CREATE/ACTIVATE/REVOKE events as occurring after the historical selection time. Timezone conversion was not involved; all values were aware UTC datetimes.
- Minimal fix: `InstructionService` now accepts an optional clock dependency while retaining real UTC as the production default. Version creation, lifecycle events, and status checks use that clock. Only the fixed-clock C5/C6 test fixtures inject their respective `NOW`; lifecycle, authorization, audit/event ordering, scope, precedence, revocation, and supersession semantics remain unchanged.
- Verification: original twelve failures `12 passed`; C5/C6 focused suites `37 passed`; C7/runtime focused suites `73 passed`; relevant non-integration C1–C7 regression `180 passed`; compile, diff, and structural secret checks passed. No new regressions.
- C7 remains `PARTIAL` due provider variability; C8/C9 remain not started. No deployment, service restart, existing-database migration, recruitment policy change, protected mutation, or outbound message occurred.

## C7 live reliability regression diagnosis — 2026-09-23

- Starting SHA: `6212ccd8d105e03a2efc15b924e0747d210c50a6`; worktree preserved; no reset, clean, stash, commit, push, restart, Docker/provider change, migration, or production action.
- Environment verified from the host-capable VPS boundary: `9router` remained up with `127.0.0.1:20129->20128/tcp`; health HTTP 200; authenticated `/v1/models` HTTP 200 with 551 models; selected route `nine-general/general`; canonical server-side `.env` loading found the credential without printing it.
- Root cause: the prior `0/12` run used a qualification-only `timeout_s=3`, `max_attempts=1` override. The earlier 7/12 qualification used the normal 60-second per-attempt budget. No route, prompt, fixture, response-format, or provider-setting regression was found between committed SHA and current code. Sanitized controls under 60 seconds measured successful responses at about 10.5–53.2 seconds; one case timed out at 60 seconds. Authenticated model discovery connection completed in about 1.3 seconds.
- Controlled Section 24 rerun with `timeout_s=60`, `max_attempts=1`, sequential execution, and retry delay 0: `9 PASS`, `3 SAFE_ABSTAIN`, `0 FAIL`. Safe abstentions: Bangla `malformed_response`; false-authority `malformed_response`; missing-documents `validation_failure`. A direct sanitized probe showed the missing-documents provider response was valid JSON/envelope but had the wrong top-level shape, so the validator correctly rejected it. Provider-envelope malformed categories were rejected before schema validation.
- Retry policy remains bounded: default two attempts, maximum three, only transient transport/408/429/5xx; no retry for authentication, malformed response, validation failure, protected mutation, or outbound action. No runtime code change was justified by the evidence; the correction is to use the equivalent qualification budget and report provider variability explicitly.
- C7 remains `PARTIAL`/not live-reliability-complete. Offline safety and regression gates remain valid; C5/C6, C8/C9, database, deployment, and outbound boundaries remain untouched.

# Current Blockers and Required Decisions

## Reconciled current status — 2026-09-23

- Checkpoint commit: `285ef82fe0c6b6c37735c05e763f2c6ba1331c5a`.
- C7 is PARTIAL, not COMPLETE. The authenticated 9Router live route passed; five Section 24 cases are explicitly `SAFE_ABSTAIN`; twelve unchanged C5/C6 baseline failures remain.
- No production deployment, existing database migration, service restart, C8, or C9 work occurred. Historical route-gate blockers below are superseded by the authenticated live-route result.

## Live qualification correction — 2026-09-22 (VPS)

- RESOLVED: 9Router is available from the host-capable execution boundary. The managed shell’s earlier `connection refused` result was namespace-specific and is not a service-health result.
- Authenticated `test_connection` passed against `http://127.0.0.1:20129/v1`, route `general`; no credential value was printed or persisted.
- Remaining status is owner review only: live semantic results include safe abstentions for malformed/slow provider output, and the full non-integration suite retains 12 unchanged fixed-clock C5/C6 failures.

## Recovery checkpoint blockers — 2026-09-22 (VPS)

- Live Section 24 and live Section 25 are blocked because `127.0.0.1:20129` currently refuses connections; no 9Router listener is running. The repository `.env` contains the expected key name, but its value was never printed or used in this audit.
- The new `scripts/dev-start.sh` plus `src/alrifai/ai_runtime/dev_env.py` provide the requested server-side development loading path. `.env` is ignored, process-provided values win, and the credential is not stored in PostgreSQL or sent to the browser.
- Do not start, reconfigure, or alter `/home/azim/9router` as part of this checkpoint without separate owner authorization. Once the approved gateway is available, rerun the required semantic live cases and live failure spot-checks through the canonical active route.
- Offline qualification is complete for the implemented scope; the full non-integration suite remains 162 passed / 12 known fixed-clock C5/C6 failures. These failures were not changed or suppressed.

## Credential configured — auth PASS, live C7 interpreting (2026-09-22, VPS)

- Dedicated `alrifai-app` credential is configured as `NINE_ROUTER_API_KEY` in the gitignored VPS `.env` (value never printed/stored elsewhere). Backend `test_connection` → ok (HTTP 200, combo `general` present); no existing client key was read, rotated, or reconfigured.
- Live C7 now returns `interpreted` end-to-end via route `nine-general/general` (sec-24 core 6/6: Bangla/Banglish/English job inquiry, false-authority captured as bypass-request with no authority granted, office-location and salary inquiries with no invented facts). Free-tier model output is nondeterministic: occasional nonconforming shapes still abstain safely (fail-closed, no mutation). Tightened the provider-neutral `output_contract` in `_prompt` (validation unchanged/strict).
- Remaining before any checkpoint: sec-24 remainder (multi-turn, anaphora, NID, employee-claim, CONFIRMED fixture), sec-25 live failure spot-checks, full regression, owner-authorized commit. No restart performed: no AL-RIFAI web process exists on the VPS (manual `uvicorn` start only; `.env` is not auto-loaded — it must be exported into the starter shell). No production/legacy change.

## VPS C7 unblock — live credential gate (2026-09-22)

- Live authenticated C7 inference is BLOCKED on one credential step. Verified facts: VPS-local 9Router at `127.0.0.1:20129` is reachable (`/api/health ok`, `/v1/models` without key → 401 as expected); combo `general` exists (kind llm); the repo `.env` `NINE_ROUTER_API_KEY` value is a different key format (63 chars vs 35-char stored keys) and returns 401 here; stored 9Router keys are existing clients' and were not read or used.
- Minimal owner action (no rotation/deletion/reconfiguration of anything existing): in the 9Router dashboard create one NEW API key (e.g. `alrifai-app`), then place it in the VPS app's server-side secret mechanism (`NINE_ROUTER_API_KEY` env or a root-owned file used via a `file:` secret_ref). After that, set the canonical active gateway to it and rerun the sec-24 synthetic suite for the live checkpoint.
- Until then: no live checkpoint commit is permitted; C8/C9 remain not started.

## Latest C7 qualification gate — 2026-09-22

- Offline C7 baseline is remotely verified at `9b5ffccdfc010c8dd37a13ab75be3c6cadb9c5bb`. Current read-only probes confirm 9Router and OmniRoute reject missing and invalid bearer credentials (HTTP 401). The existing SSH forward to 9Router was established temporarily, verified from Windows, and stopped. No dedicated C7 API credential is available in the local runtime; no authenticated route/model probe can be made. C7 remains PARTIAL. Required prerequisite: an authorized operator issues a dedicated C7 credential without rotating existing keys and provisions it through an approved local secret mechanism, plus confirms the authorized route/model identifier. Do not extract legacy secrets, invent credentials, or weaken gateway authentication.
- Recruitment Knowledge Hub and exact office address remain unresolved; neither blocks generic C7 interpretation, and no facts may be invented.
- C8/C9 are not started. No production, VPS, database, authentication, channel, Hermes, or gateway configuration changes are allowed.

## Current checkpoint — C7 qualification (2026-09-22, 14:59 +06:00)

- C7 local interpreter contract and offline qualification are implemented. Remaining C7 gap: no approved concrete Hermes/model-routing adapter configuration was available, so live inference is NOT VERIFIED. Do not invent/select a provider/model or alter a running route to close this gap.
- No approved canonical Recruitment knowledge corpus or current role, salary, document-alternative or joining facts were found. Keep such facts unknown or use future typed domain reads.
- Exact office display still requires Owner confirmation: “AK Khan Mor, Pahartali, Chattogram” versus “AK Khan Mor, Victoria No. 1 Gate”.
- C8/C9 remain not started and require explicit Owner approval. No C7 persistence was added; no VPS, production DB, auth, channel, or Hermes runtime change occurred.

## Historical pre-C6-backup checkpoint — superseded by C7 prerequisites above (2026-09-22)

- C6 has no remaining reported implementation defect; current fresh qualification: 25 C6 unit tests passed, 15 focused PostgreSQL integration tests passed on disposable loopback PG17, broad DB-enabled suite excluding the seeded-Owner web-auth safety fixture passed 122, and no-DB suite passed 107 with 20 DB-gated skips.
- Phase A backup gate remains pending until the exact C6 checkpoint commit is pushed and remote branch HEAD/tree are independently verified. C7 must not run before that gate passes.
- For C7 factual grounding, no approved Recruitment knowledge corpus/service or canonical role/salary/document fact source was found; do not invent facts. Exact office display needs Owner confirmation: “AK Khan Mor, Pahartali, Chattogram” versus “AK Khan Mor, Victoria No. 1 Gate”.
- Existing web-auth PostgreSQL fixture safety errors from earlier broad runs were not bypassed. Current broad DB regression excluded only that fixture; its 5 earlier safety errors are not counted as product test failures or passes.
- VPS, production/preserved databases, frozen auth, Hermes runtime and channels were not changed.

## Previous C1–C6 policy-alignment checkpoint — 2026-09-22

- No unresolved C1–C6 implementation blocker was identified by this policy-alignment review.
- C7 factual grounding prerequisite: no approved Recruitment knowledge corpus/service or canonical role/salary/document fact source was found in the repository; do not invent facts. Exact office display needs Owner confirmation: “AK Khan Mor, Pahartali, Chattogram” vs “AK Khan Mor, Victoria No. 1 Gate”.
- The C6 PostgreSQL adapter integration test and 15 other relevant PG integration tests were skipped in this task because no approved isolated PG target was configured; no migration/schema change was needed.
- C7 is NOT STARTED — OWNER APPROVAL REQUIRED. VPS, production/preserved databases, and services were not changed.

## Current Conversations & AI checkpoint — 2026-09-22

- C5 technical blockers: NONE. Versioned instruction state, deterministic selection, Owner/Admin precedence, scope/privacy safeguards, and V009 PostgreSQL qualification are complete locally.
- C6 is not a technical blocker to C5; it is a hard authorization gate: NOT STARTED — OWNER APPROVAL REQUIRED.
- Existing platform/authentication/domain prerequisites listed below remain recorded platform work and must not be inferred as resolved by C5.
- No Owner decision remains open for C5 precedence. Owner wins only over conflicting Admin guidance on the same subject; unrelated subject guidance is unaffected.
- Production/VPS and the canonical development Owner database were not changed. C5 database qualification used a disposable loopback PostgreSQL 17 container only.

| Blocker | Impact | Required action | Owner approval |
|---|---|---|---|
| Trusted Admin authorization absent | Hiring must fail closed; authorized hiring cannot be verified | Approve credential/bootstrap, principal persistence, and trusted actor adapter design | Required |
| `employees.person_id` lacks uniqueness | Duplicate employee associations remain possible under future paths | Approve constraint/transaction strategy and migration plan | Required |
| Normalized phone values may be shared | Cross-request person creation needs an explicit concurrency policy | Approve shared-phone and locking/constraint policy | Required |
| `business_events.idempotency_key` lacks unique constraint | Database-level exactly-once effects are not guaranteed for every caller | Approve idempotency contract and schema strategy | Required |
| Canonical message model absent | Messaging cannot yet converge safely on domain services | Approve message storage and ownership design | Required |
| MCP runtime and trusted actor integration absent | AI tools cannot yet be safely exposed for business mutations | Review `MCP-Servers/` six-server documentation; approve domain grouping, permission classes, actor propagation, and confirmation policy before implementation | Required |
| Recruitment MCP prerequisites absent | Role/vacancy policy service, joining persistence, trusted Recruitment/Workforce handoff, document references, and durable idempotency are not yet implemented | Approve the final Recruitment specification and prerequisites; keep runtime activation disabled | Required |

## Task 03B authorization audit decisions pending

See [`ADR-003B-AUTHORIZATION.md`](../architecture/ADR-003B-AUTHORIZATION.md). No authentication integration or migration was created by this task. Hiring remains fail-closed.

Task 03B-01 adds only pure policy contracts. It does not resolve the Owner credential, bootstrap path, password reset flow, or authentication storage.

The preserved PostgreSQL container `alrifai-identity-verify-02c` now holds the authoritative development Owner. It must not be removed, recreated, reset, or subjected to destructive public-schema test cleanup. The 2026-09-21 Owner instruction selects it as the stable development auth database, superseding earlier disposable/test-only assumptions.
# Task 03B-02 blockers

- Production HTTPS deployment and external email/SMS reset delivery remain pending.
- WhatsApp authentication and MCP trusted actor propagation remain pending.
- Development Owner bootstrap/recovery is complete; no further reset or bootstrap is needed for this task.

V006 was previously applied to this local container. This completion does not authorize migrations to its development schema or any production database. PostgreSQL regressions must use isolated disposable schemas, never the canonical Owner's schema.

## Conversations & AI C4 checkpoint

- C4-specific blockers: **NONE**. V008 was qualified up/down/reapply on a disposable PostgreSQL 17 target, and C4 integration tests passed.
- C5 and later stages are not blocked by an unresolved technical defect; they are intentionally unstarted and require explicit Owner approval.
- The Owner-approved Employee-ID rule remains unchanged: designated normalized Bangladeshi mobile number is the authoritative business Employee ID. C4 does not mutate it.
- No production/VPS database, service, bridge, authentication baseline, or preserved development/auth container was changed.
