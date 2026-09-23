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

# Test Status

## Reconciled current checkpoint — 2026-09-23

Checkpoint commit: `285ef82fe0c6b6c37735c05e763f2c6ba1331c5a`. C7 is PARTIAL, not COMPLETE: authenticated 9Router route PASS; five Section 24 cases are `SAFE_ABSTAIN`; twelve unchanged C5/C6 baseline failures remain. No production deployment, existing database migration, service restart, C8, or C9 work occurred.

## Live C7 qualification — 2026-09-22 (VPS, uncommitted)

| Scope | Actual result | Notes |
|---|---:|---|
| Managed-shell vs host boundary | RESOLVED | Managed shell could not see loopback; host-capable execution saw `9router` Up 3 days, port mapping, listeners, and health HTTP 200. |
| Authenticated canonical route | PASS | Server-side `.env` loader; `nine-general/general`; HTTP 200; 550 models observed; credential never printed. |
| Section 24 live semantics | PASS / SAFE_ABSTAIN | Bangla PASS; Banglish SAFE_ABSTAIN malformed; English PASS; mixed SAFE_ABSTAIN malformed; multi-turn PASS; `ওইটাই` PASS; `কত?` SAFE_ABSTAIN timeout; false authority SAFE_ABSTAIN timeout; salary PASS with zero grounding; office SAFE_ABSTAIN timeout; NID/birth-registration PASS candidate-only; employee self-claim PASS candidate-only. |
| Confirmed-current-employee control | PASS evidence / SAFE_ABSTAIN response | Exact Person + unique active Employee evidence produced `CONFIRMED_CURRENT_EMPLOYEE`/`FAMILIAR_TUMI`; provider timed out, so no semantic response was claimed. |
| Section 25 live auth failure | PASS | Invalid in-memory credential produced typed provider error and abstention; no 9Router configuration change. |
| Section 25 offline matrix | PASS | Malformed output, unreachable, timeout, disabled/unknown gateway, prompt injection, missing knowledge, no mutation, and no outbound delivery covered by focused tests. |
| Focused C7/runtime/settings | PASSED — 67 | Rerun with existing project environment. |
| Selected C1–C7 regression | PASSED — 70 | Rerun; confirmed relationship subset 2 passed. |
| Full non-integration regression | 162 passed / 12 failed | Unchanged fixed-clock C5/C6 instruction/context assertions; no C5 changes made. |
| V010 | STATIC VERIFIED / NOT APPLIED | No existing database changed. |
| Compile / diff / secret checks | PASSED | Final checks pending after continuity edits. |

## Recovery verification — 2026-09-22 (VPS, uncommitted)

| Scope | Actual result | Notes |
|---|---:|---|
| Development dotenv workflow | PASSED | `tests/test_dev_env.py`; ignored `.env` names are loaded server-side without overriding existing environment values or printing values. |
| AI runtime/settings + adapter + C7 focused | PASSED — 67 | `tests/test_dev_env.py tests/test_ai_runtime_config.py tests/test_ninerouter_adapter.py tests/test_web_ai_settings.py tests/test_conversation_interpretation.py`; loopback fake gateway/TestClient only. |
| C1–C7 relevant non-DB regression | PASSED — 70 | Conversation C3, models, topics, resolution, identity, phone, authorization, and employee-security modules. |
| Confirmed-current-employee fixture | PASSED — 2 | Exact Person plus one unique active Employee yields `CONFIRMED_CURRENT_EMPLOYEE`; self/unresolved paths remain unknown in the existing tests. |
| Full non-integration regression | 162 passed / 12 failed | Failures are unchanged fixed-clock C5/C6 instruction-selection assertions; no C5 redesign or test weakening performed. |
| Live 9Router transport/auth | BLOCKED | No listener on `127.0.0.1:20129`; no external 9Router start/reconfiguration performed. |
| Section 24 semantic live suite | NOT RUN / BLOCKED | Required live cases cannot be truthfully classified until the approved gateway is running. |
| Section 25 live failure spot-checks | NOT RUN / BLOCKED | Offline fake-gateway failure matrix is covered by focused tests; live gateway was not intentionally broken. |
| V010 | STATIC VERIFIED / NOT APPLIED | UP/DOWN ordering and declarations checked; no existing database was changed. |
| Compile / diff / secret checks | PASSED | `compileall`; `git diff --check`; structural scan found no credential assignment/token in changed files; `.env` ignored. |

## Live auth + C7 interpretation — 2026-09-22 (VPS, branch feat/windows-local-dev, HEAD 9b5ffcc)

| Scope | Actual result | Notes |
|---|---|---|
| 9Router reachability (no key sent) | PASS | `/api/health` ok; `/v1/models` without key → 401 as expected. |
| Authenticated connection (backend-side, InMemory store) | PASS | `credential_configured=True`, `test_connection` ok over HTTP 200, combo `general` present. Credential value never printed/logged/stored. |
| C7 live smoke + sec-24 core (6 prompts) | PASS | All interpreted/needs_clarification, zero abstentions this run; Bangla/Banglish/English job inquiry, bypass-request captured without authority, no invented salary/address facts. Route `nine-general/general`. |
| Offline focused (after prompt-contract fix) | PASSED — 66 | C7 interpretation 35, adapter 10, runtime config 14, web AI settings 7. |
| `git diff --check` / secret scan | PASSED | No whitespace errors; no credential assignments in tracked diff; key-pattern scan of new C7/AI files 0 hits; `.env` remains gitignored/untracked. |
| Full sec-24 remainder + sec-25 live | NOT RUN | Multi-turn, anaphora, NID, employee-claim, CONFIRMED fixture, live failure spot-checks still pending. |
| Web process restart | NOT REQUIRED / NOT PERFORMED | No AL-RIFAI web process runs on the VPS; no production/legacy service touched. |

## VPS C7 unblock + AI runtime settings — 2026-09-22 (VPS, branch feat/windows-local-dev, HEAD 9b5ffcc)

| Scope | Actual result | Notes |
|---|---:|---|
| AI runtime focused (new) | PASSED — 31 | `tests/test_ai_runtime_config.py` (14), `tests/test_ninerouter_adapter.py` (10), `tests/test_web_ai_settings.py` (7); fake loopback gateway + TestClient, no real credential. |
| C7 focused | PASSED — 35 | `tests/test_conversation_interpretation.py`; offline injected adapter. |
| Selected regression (C7/C3/topics/resolution/models/identity/phone/auth/employee) | PASSED — 136 | Explicit 14-module run incl. all 31 new tests; no DB URL. |
| V010 migration | PASSED | Disposable loopback PG17: foundation + UP, store roundtrip (save/save/set_active/view/audit rows=3), DOWN, RE-UP; container removed. |
| Real-gateway 401 path | PASS (manual) | Live 127.0.0.1:20129, no credential: adapter POST → 401 → C7 ABSTAINED/PROVIDER_ERROR, no mutation. |
| Live authenticated inference | BLOCKED / UNVERIFIED | No valid credential for VPS-local 9Router (see BLOCKERS). |
| Full no-DB suite | 161 passed, 12 FAILED (pre-existing) | 12 failures are C5-instruction/C6-context logic assertions, untouched by this diff; proven pre-existing by rerun with the new adapter import disabled (still 10 failed in instructions module alone). Windows-baseline evidence stands. |
| Compile/import | PASSED | `compileall` on ai_runtime, conversations, web. |
| `git diff --check` / secret scan | PASSED | No whitespace errors; no key/token/private-key patterns in changed/new files. |
| VPS env note | `psycopg[binary]==3.3.6` installed into `/home/azim/.venv` | Matches requirements.txt pin; was missing, blocked all psycopg imports there. No service/config change. |

## Fresh offline C7 qualification for authorized baseline checkpoint — 2026-09-22

Offline C7 checkpoint `9b5ffccdfc010c8dd37a13ab75be3c6cadb9c5bb` is independently verified on `origin/feat/windows-local-dev`. Later route-audit documentation is local-only; it records no approved usable route, so no live inference test ran.

## Fresh live-route gate verification — 2026-09-22

| Scope | Actual result | Notes |
|---|---:|---|
| VPS gateway inventory | PASSED | Read-only: 9Router image `0.5.75` loopback `20129`; OmniRoute loopback `20128`; no service/provider configuration changed. |
| Gateway auth enforcement | PASSED | Both gateways returned HTTP 401 for missing and deliberately invalid bearer values. This does not verify valid authentication. |
| Windows SSH transport | PASSED | Existing SSH forward `127.0.0.1:20130` reached 9Router and returned HTTP 401; temporary tunnel stopped and listener closure verified. |
| Local C7 credential / model route | BLOCKED | No relevant credential variable in process environment or `.env.local` key names; no valid dedicated C7 key/model identifier was available. Secret values were not read or exposed. |
| Authenticated model probe / live inference | NOT RUN | No authorized C7 credential; live request count 0. |
| Adapter wiring and C7 live tests | NOT RUN | Connectivity/auth prerequisite not passed; offline C7 source/tests unchanged. |
| Offline C7 focused rerun | PASSED — 35 | `.venv/Scripts/python.exe -m pytest -q tests/test_conversation_interpretation.py` with `PYTHONPATH=src`; test doubles only. |
| Conversation package compile | PASSED | `.venv/Scripts/python.exe -m compileall -q src/alrifai/conversations`. |

| Scope | Actual result | Notes |
|---|---:|---|
| C7 focused | PASSED — 35 | `PYTHONPATH=src .venv/Scripts/python.exe -m pytest -q tests/test_conversation_interpretation.py`; injected test adapter only, not live inference. |
| Selected C1–C6 conversation/identity/auth regression | PASSED — 107; SKIPPED — 5 | Explicit selected modules including C1–C6 unit tests, identity/phone/auth tests, and PostgreSQL-gated conversation integrations; no DB URL supplied. |
| Full no-DB suite | PASSED — 142; SKIPPED — 20 | `PYTHONPATH=src .venv/Scripts/python.exe -m pytest -q`; all 20 skips DB-gated. |
| Compile/import | PASSED | `.venv/Scripts/python.exe -m compileall -q src/alrifai/conversations`. |
| PostgreSQL | NOT REQUIRED for C7 | No C7 persistence/migration; no database was used or changed. Historical C1–C6 PostgreSQL results were not rerun here. |
| Live model inference | NOT RUN / UNVERIFIED | No approved route is established yet. |
| Provider route audit | BLOCKED | Local repo has no app model adapter; local tunnel/API was unavailable. Read-only VPS inventory showed legacy Hermes and 9Router/OmniRoute candidates, but no approved C7 auth/integration contract. No live request attempted. |
| `git diff --check` / secret scan | PASSED | Run against intended offline C7 file scope before checkpoint; secret scan must include untracked C7 files and staged content. |

## C7 local implementation qualification — 2026-09-22, 14:59 +06:00

| Scope | Actual result | Notes |
|---|---:|---|
| C7 focused | PASSED — 35 | `PYTHONPATH=src .venv/Scripts/python.exe -m pytest -q tests/test_conversation_interpretation.py`; offline fake adapter only. |
| Selected C1–C6 + C7 conversation/identity/authorization regression | PASSED — 135 | Explicit selected-module run; no DB URL supplied. |
| Full repository, no DB target | PASSED — 142; SKIPPED — 20 | All skipped tests are DB-gated; no skip counted as pass. |
| Compile/import | PASSED | `.venv/Scripts/python.exe -m compileall -q src/alrifai/conversations`. |
| PostgreSQL qualification | NOT REQUIRED for C7 | C7 adds no persistence or migration. Existing development containers were inspected but not used or modified. C1–C6 PG subset was not rerun in this task; historical separate PG qualification remains historical evidence only. |
| Live model inference | NOT RUN / UNVERIFIED | No provider/model route was selected or called; offline adapter contract is not live inference evidence. |
| `git diff --check` | PASSED | Only Git LF-to-CRLF working-copy warnings; no whitespace errors. |
| Tracked-diff/untracked high-confidence secret scan | PASSED | Private-key, cloud/GitHub/OpenAI token and JWT-shaped credential patterns: 0 matches. |

## C6 fresh qualification for authorized checkpoint (2026-09-22, Asia/Dhaka)

| Scope | Actual result | Notes |
|---|---:|---|
| C6 focused unit tests | PASSED — 25 | `tests/test_conversation_context.py -q`. |
| C1–C5/C6 PostgreSQL integration subset | PASSED — 15 | Fresh task-created disposable PostgreSQL 17, loopback-only; included C6 relationship-status correction and C1–C5 conversation/identity/instruction/topic integration tests. |
| Migration chain/schema check | PASSED | Initial identity schema plus V006–V009 applied to the disposable database; required canonical tables verified. No C6 migration, so C6 up/down/reapply was NOT REQUIRED. |
| DB-enabled broad repository regression | PASSED — 122 | `pytest -q --ignore=tests/integration/test_web_auth_postgres.py` against fresh disposable PG17. The protected seeded-Owner safety fixture was deliberately excluded, not weakened or bypassed. |
| Full repository suite, no DB target | PASSED — 107; SKIPPED — 20 | `PYTHONPATH=src .venv/Scripts/python.exe -m pytest -q`; skips are environment-gated and are not passes. |
| Compile/import | PASSED | `.venv/Scripts/python.exe -m compileall -q src/alrifai/conversations`. |
| Diff check | PASSED | `git diff --check`; only Git line-ending normalization warnings were emitted. |
| Secret scan | PASSED | All 14 intended C6 files scanned for private-key, AWS/GitHub/OpenAI token and credential-bearing DB URL patterns; no matches (values suppressed). |

Disposable database: task-created PostgreSQL 17 container `alrifai-c6-qual-20260922`, loopback ephemeral binding; removed after the run. Existing local databases/containers, production and VPS were not changed. Previous broad DB-enabled run reported five web-auth fixture safety errors against a seeded Owner target; this run excluded that fixture, and no safety guard was bypassed.

## C1–C6 natural conversation policy alignment — 2026-09-22 (Asia/Dhaka)

| Scope | Actual result | Notes |
|---|---:|---|
| Focused C6 + C1–C5 / identity / authorization regression | PASSED — 107; SKIPPED — 15 | Exact selected-module run for conversation, identity, authorization and PG integration; all skipped cases were PostgreSQL-gated because no approved target was configured. |
| Full repository suite, no DB target | PASSED — 107; SKIPPED — 20 | `PYTHONPATH=src .venv\\\\Scripts\\\\python.exe -m pytest -q`; skips are not passes. |
| C6 PostgreSQL adapter integration | SKIPPED — 1 | No approved isolated PostgreSQL target configured in this task. No migration was added or applied. |
| Compile/import | PASSED | `PYTHONPATH=src .venv\\\\Scripts\\\\python.exe -m compileall -q src/alrifai/conversations` after runtime correction. |
| Diff check | PASSED | `git diff --check`; no whitespace errors. |
| Secret scan | PASSED | Tracked modifications and untracked files scanned for private-key headers, AWS/GitHub/OpenAI token patterns, and credential-bearing DB URLs; zero hits. |

Disposable test target: newly created `alrifai-c6-qualify-20260922`, PostgreSQL 17, loopback port `51110`, removed after qualification. Existing local containers were untouched. No C6 migration was added, so migration up/down/reapply was NOT REQUIRED. No skipped test is counted as passed.

C6 implementation remains bounded and has no schema change. Current database integration is unverified/skipped for this alignment task; the earlier C6 PG qualification is historical, not rerun here. C7 is NOT STARTED — OWNER APPROVAL REQUIRED.

## Latest verified C5 run — 2026-09-22

| Scope | Result | Notes |
|---|---:|---|
| C5 focused unit tests | PASSED — 12 | `PYTHONPATH=src .venv/Scripts/python.exe -m pytest tests/test_conversation_instructions.py -q`; Owner conflict precedence, subject isolation, lifecycle/effective windows, authorization, same-authority conflict, topic closure, scope, idempotency, and prompt-injection boundary. |
| V009 migration | PASSED | Up applied after V006/V007/V008 on new disposable PostgreSQL 17; tables/indexes/triggers verified; down preserved V008; reapply restored C5. |
| C5/C2/C4 PostgreSQL integration | PASSED — 10 | C5 instruction persistence/reconstruction and DB constraints (2), plus identity resolver, conversation resolver, and topic integration regressions; all ran against the isolated loopback PostgreSQL 17 target. |
| Conversation/identity/authorization regression | PASSED — 81 | C1 contracts, C2 resolution/normalization, C3 ordering/turns, C4 topics, C5 units, central authorization. |
| Full repository suite | PASSED — 82 passed, 19 skipped | No integration database URL was set for this run; the 19 environment-dependent DB tests were skipped, not counted as passed. |
| Conversations package compile | PASSED | `compileall -q src/alrifai/conversations`. |
| V007/V008 prior qualification | PASSED — baseline evidence | C2 V007 and C4 V008 up/down/reapply and prior PostgreSQL integration results remain documented above; C5 did not alter those migrations. |
| `git diff --check` | PASSED | Final worktree check completed after C5 and continuity edits; only Git line-ending normalization warnings appeared. |
| Tracked and untracked diff secret scan | PASSED | Scanned tracked HEAD diff and all five untracked C5 files for private-key headers, AWS keys, common API-token patterns, and credential-bearing database URLs; no matches. |

## Latest recorded runs

2026-09-21 Owner-login completion (HEAD `7c1a9c1bc67c7c7263ca9d6d13a49f274778fc0d`, uncommitted work preserved):

| Scope | Result | Notes |
|---|---:|---|
| Live local Owner flow | Passed | GET `/login` 200; POST 303; hashed session persisted; `/home` and `/owner` 200; relative and approved AI-host redirects; unsafe target blocked; auth-check 204/401; verification sessions revoked |
| Canonical startup database verification | Passed | Normal startup and existing explicit verified-container switch select `127.0.0.1:57395/identity_verify`; conflicting port/database/user/query settings rejected; `-VerifyConfiguration` did not restart services |
| Database-independent tests | 34 passed | Authorization policy, employee-service security, identity resolution/resolver, phone normalization |
| Focused PostgreSQL auth integration | 5 skipped | Safe by default because no explicitly isolated test target is configured; fixture now refuses any target containing an Owner before cleanup |
| Full repository suite | 34 passed, 15 skipped | Default local run; PostgreSQL integration remains opt-in and guarded |
| Public HTTPS browser authentication flow | Passed | AI hostname redirected to AL-RIFAI `/login`; repaired Owner authenticated and returned to rendered Open WebUI chat navigation; public `/owner` verified; verification session logged out; fresh uncached AI request redirected to login |
| Tracked HEAD diff secret scan | Passed | Known runtime credentials, credential-bearing PostgreSQL URLs, session/CSRF values, API tokens, and private-key patterns; matched values are never printed |
| MCP documentation-only scope validation | Passed | 32 new Markdown files under `MCP-Servers/`; no runtime source, migration, Docker, or VPS operation; new documents contain no secret-like values |
| Fresh live Fazle-Core read-only audit | Passed | Existing `iamazim` SSH access; clean VPS source at `e76365e`; active Fazle-Core and Bridge 1/2/3 services; read-only source/schema/count/distribution audit; no VPS changes |
| Recruitment MCP final specification validation | Passed | Final implementation handoff defines 18 tools, 9 resources, lifecycle, identity, authorization, idempotency, audit/events, errors, scenarios, tests, and implementation sequence; no runtime code or migration added |
| Recruitment phone/semantic conversation specification correction | Passed | Durable inbound phone/provenance, current/historical employee mobile identifiers, ordered Person-linked conversation context, semantic topic state, bounded retrieval, and versioned Admin AI instructions reconciled; documentation-only |
| Fresh Fazle-Core SSH recheck | Blocked | `ssh iamazim` was rejected by the current environment; prior repository audit artifacts were used with evidence labels and no VPS mutation |
| Existing SSH identity diagnosis | Blocked | Alias resolved safely; configured and available existing identities failed non-interactive authentication; no config/key/VPS changes made |
| Direct Fazle-Core SSH retry | Blocked | Owner-confirmed `ssh azim@5.189.131.48` failed with `Permission denied (publickey,password)`; no password collected and no security configuration changed |

## Historical runs

| Scope | Result | Notes |
|---|---:|---|
| Full local suite with restored isolated PostgreSQL | 49 passed | Test-only container `alrifai-identity-verify-02c`; no production database used |
| Shared authentication integration | Passed | `/internal/auth-check`, session revocation/expiry/disabled checks, shared-cookie scope/delete semantics, and return-target validation |
| Local 9Router HTTP verification | Passed | Authenticated real completions previously verified for `general`, `coding`, `fast`, and `auto`; secrets omitted |
| VPS HTTPS/Nginx configuration | Blocked | SSH succeeds, but `sudo` requires an interactive password; no VPS change was attempted |
| `git diff --check` | Passed | Warning only about Git line-ending normalization |
| Verified-container runtime credential drift | Passed | Startup derives the current password from the isolated test container; local and Tailscale `/health` returned 200; unauthenticated `/internal/auth-check` returned 401 |

## Verification boundary

### 2026-09-22 Conversations & AI C1

| Scope | Result | Notes |
|---|---:|---|
| Authorized C1 contract tests | Passed | 9 tests via repository `.venv`; contract-only canonical message/conversation foundation |
| New Conversations package compilation | Passed | `compileall` completed without errors |
| Runtime/database/VPS changes after correction | None beyond C1 | C1 source/tests only; no persistence engine, migration, channels, Hermes, or VPS changes; C2 is prohibited |

| Existing non-integration regression suite | Passed | 43 tests via repository `.venv`; integration database tests were not run in this focused C1 verification |

### 2026-09-22 Conversations & AI C2

| Scope | Result | Notes |
|---|---:|---|
| C2 focused tests | Passed | 39 tests covering canonical normalization, deterministic identity resolution, platform/account scope, private/group/public boundaries, ambiguity, unknown senders, and thread reuse |
| Full available test suite | Passed | 51 passed, 16 skipped because isolated PostgreSQL environment is not configured |
| PostgreSQL C2 integration | Skipped | Test is present; V007 was not applied because no isolated local database URL was configured |
| C2 package compilation | Passed | Identity and Conversations packages compile successfully |

| V007 disposable PostgreSQL qualification | Passed | V006 → V007 up; schema and invariants verified; V007 down restored prior schema; V007 reapply passed; exact disposable container removed afterward |
| PostgreSQL identity/core/C2 integration | Passed | 11 tests executed against the disposable local PostgreSQL 17 target |
| C2 database safety | Passed | Preserved `identity_verify`, `alrifai-postgres`, VPS, and production databases were not modified |

### 2026-09-22 Conversations & AI C3

| Scope | Result | Notes |
|---|---:|---|
| C3 focused tests | Passed | 9 tests covering source/provider ordering, timestamp ties, late arrival, reply evidence, fragments, media association, outbound/sender/time boundaries, stabilization, and deterministic re-evaluation |
| C3 persistence qualification | Not required | Turns are deterministic reconstruction over canonical C1 messages and C2 conversation linkage; no migration or turn table added |
| C1/C2 regression | Passed | Included in the full available suite: 60 passed, 16 integration tests skipped because no configured integration environment was active |
| C3 boundary | Passed | No topic state, semantic interpretation, Hermes, domain dispatch, reply generation, or outbound runtime added before C4 |

### 2026-09-22 Conversations & AI C4

| Scope | Result | Notes |
|---|---:|---|
| C4 focused tests | Passed | 10 tests covering lifecycle, suspension/resumption, closure/reopening evidence, invalid transitions, idempotency, stale versions, topic switching, scope boundaries, late-arrival protection, restart reconstruction, and authority separation |
| V008 migration up | Passed | Applied after identity foundation and V007 on disposable PostgreSQL 17 |
| V008 schema/invariants | Passed | Topic and immutable transition tables, state constraints, foreign keys, indexes, scoped idempotency, and restart-safe state verified |
| V008 down/reapply | Passed | Down restored the V007-only schema; reapply restored V008 structures |
| C4 PostgreSQL integration | Passed | 2 tests before and 2 tests after V008 reapply; exact disposable target removed afterward |
| C1/C2/C3 regression | Passed | Full available suite: 70 passed, 17 skipped environment-dependent integration tests |
| Compilation/diff/secret scan | Passed | `compileall`, `git diff --check`, and tracked-diff secret scan passed with zero secret hits |
| C4 boundary | Passed | No C5+ semantic, Admin instruction, Hermes, retrieval, dispatch, reply, or outbound runtime added |

The latest run verifies local behavior and the public browser authentication/return flow. It does not verify mobile layout, infrastructure configuration correctness, AI completions, live messaging, or end-to-end business/MCP workflows. Public checks changed no infrastructure and sent no chat messages. A cached Open WebUI shell was visible immediately after one logout; a fresh uncached navigation correctly required AL-RIFAI authentication. No browser session tokens were printed.

The old test-only/disposable designation does not apply to the selected database's `public` schema now: it contains the repaired canonical development Owner. Regression tests must not delete or recreate that identity. Earlier missing-VPS-configuration reports are historical; this task permits read-only public-flow verification, not infrastructure changes.
