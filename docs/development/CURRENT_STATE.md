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

# AL-RIFAI Current State

## Reconciled current state — 2026-09-23

Repository checkpoint: `285ef82fe0c6b6c37735c05e763f2c6ba1331c5a`. C7 is PARTIAL, not COMPLETE: authenticated 9Router live route PASS; five Section 24 cases are `SAFE_ABSTAIN`; twelve unchanged C5/C6 baseline failures remain. No production deployment, existing database migration, service restart, C8, or C9 work occurred. Older blocked-route entries below are historical.

## Live C7 qualification checkpoint — 2026-09-22 (VPS, uncommitted)

C7 STATUS: PARTIAL — live auth/route PASS, with five semantic SAFE_ABSTAIN outcomes and twelve unchanged C5/C6 baseline failures. This is not a COMPLETE qualification claim.

Host-capable qualification confirmed the owner’s correction: `9router` is `Up 3 days`, mapped `127.0.0.1:20129->20128/tcp`, and `/api/health` returned HTTP 200. The earlier refusal came from the managed shell’s isolated network namespace, not the VPS host. Using the canonical `.env` loader and an in-memory active `nine-general/general` configuration, authenticated model discovery passed (HTTP 200; 550 models observed; credential never printed).

Section 24 live cases: Bangla job `PASS`; Banglish ship `SAFE_ABSTAIN` (malformed provider output); English ship `PASS`; mixed surveyor `SAFE_ABSTAIN` (malformed provider output); multi-turn no-experience `PASS` with clarification; `ওইটাই` `PASS`; `কত?` `SAFE_ABSTAIN` (timeout); false authority `SAFE_ABSTAIN` (timeout); salary without knowledge `PASS` with zero grounding; office address `SAFE_ABSTAIN` (timeout); missing NID/birth registration `PASS` as candidate extraction with zero grounding; employee self-claim `PASS` as candidate extraction without relationship confirmation. Controlled exact-Person + unique-active-Employee evidence produced `FAMILIAR_TUMI`/`CONFIRMED_CURRENT_EMPLOYEE` evidence; the provider response for that one case timed out and safely abstained.

Section 25: controlled live invalid-credential probe passed as typed `PROVIDER_ERROR`/abstention without exposing the credential. Offline malformed, unreachable, timeout, disabled, unknown-gateway, prompt-injection, missing-knowledge, and no-mutation checks passed. No 9Router restart/configuration change, existing database mutation, production/legacy action, outbound message, C8, or C9 occurred.

## Recovery checkpoint — 2026-09-22 (VPS, uncommitted, no commit/push)

Repository is on `feat/windows-local-dev` at HEAD `9b5ffccdfc010c8dd37a13ab75be3c6cadb9c5bb`, with the current implementation preserved for owner review. The flagged C5 lifecycle timestamp drift in `src/alrifai/conversations/instructions.py` was reverted only at its three proven accidental hunks; `tests/test_conversation_instructions.py` had no diff. Intended C7, AI-runtime/settings, migration, tests, and continuity changes remain uncommitted. `OPENCODE_C7_TASK.md`, `OPENCODE_C7_REPORT.md`, and `pyproject.toml` remain untracked for owner review; the task artifact is excluded from any commit.

The development credential workflow now has a server-side `.env` loader and `scripts/dev-start.sh`. `.env` remains ignored; values are not printed, persisted to PostgreSQL, or returned to browsers. Existing environment values take precedence. Focused implementation tests pass (67), selected C1–C7 regression passes (70), and confirmed-current-employee evidence passes (2). The full non-integration suite is 162 passed / 12 known fixed-clock C5/C6 failures.

Live qualification is `BLOCKED`: no 9Router listener is currently present on `127.0.0.1:20129`, and this task did not start or modify the external 9Router project. No production/legacy service, existing database, outbound channel, C8, or C9 was touched.

## Live auth PASS + C7 interpreting — 2026-09-22 (VPS, uncommitted, no live checkpoint)

Branch `feat/windows-local-dev`, HEAD `9b5ffcc` (= origin). Dedicated credential configured server-side; authenticated `test_connection` passes and live C7 returns `interpreted` via `nine-general/general` on the sec-24 core suite (6/6, no invented facts, bypass-request captured without authority). Added provider-neutral `output_contract` to C7 `_prompt` (strict validation unchanged); offline focused 66 passed. No web-process restart was needed (none runs on the VPS); no production/legacy change; no commit/push. Remaining: sec-24 remainder, sec-25 live spot-checks, full regression, owner-authorized checkpoint.

## VPS C7 unblock + AI runtime settings — 2026-09-22 (uncommitted, no live checkpoint)

Branch `feat/windows-local-dev`, HEAD `9b5ffcc` (matches origin). `OPENCODE_C7_TASK.md` is an untracked instruction file, excluded from any commit. Existing AI/model/provider settings audit result: NONE — no prior implementation existed. New canonical implementation (all local, uncommitted):

- `src/alrifai/ai_runtime/` (`config.py`, `secrets.py`, `stores.py`, `service.py`): one runtime config service; gateway types nine_router/openai_compatible/ollama/local_model; validation (invalid can never become active); env/file server-side secrets with browser-visible `credential_configured` booleans only; application-level fallback reference (9Router keeps its internal fallback); enabling never auto-activates. Mutations require trusted `MANAGE_CONFIGURATION` (Owner-only).
- `database/migrations/V010__ai_runtime_config.sql` (+ down): `ai_gateway_configs` + singleton `ai_runtime_state`; qualified UP/DOWN/RE-UP on disposable PG17; NOT applied to any existing database.
- `src/alrifai/conversations/ninerouter_adapter.py`: concrete C7 adapter over OpenAI-compatible `/v1/chat/completions` with `response_format json_object`, timeout/bounds/correlation, classified errors; consumes the ACTIVE canonical config; no hardcoded route/model/credential. C7 authority boundary unchanged.
- `src/alrifai/web/app.py`: Owner-gated `/admin/ai-settings` page (backend state, save/set-active/backend-side test/discover), CSRF-checked, frozen auth untouched, no credential values rendered.
- Tests: 31 new (config/service/authz/secrets, adapter incl. fake-gateway failure matrix, web incl. authz/CSRF/no-leak); 136 selected regression passed; C7 35 passed.

Live authenticated inference is BLOCKED on the dedicated 9Router credential (see BLOCKERS). Real-gateway 401 path verified manually (typed abstention, no mutation). No commit/push performed. C8/C9 not started. No production/VPS/legacy change.

## Latest verified checkpoint — C7 offline baseline qualification (2026-09-22, Asia/Dhaka)

Repository `D:/apps/alrifai-ai-platform`; branch `feat/windows-local-dev`; C1–C6 remote baseline is `cf71c3b6b3f439003cd1ead0d2f5ce53583cab8c`. C7 offline checkpoint `9b5ffccdfc010c8dd37a13ab75be3c6cadb9c5bb` is independently verified at `origin/feat/windows-local-dev`. Current HEAD is that SHA; the nine C7 route/spec/continuity documents are local-only changes. Read-only VPS checks confirmed 9Router (image 0.5.75, loopback port 20129) and OmniRoute (loopback port 20128); both reject missing and invalid bearer credentials with HTTP 401. The existing SSH forward to local `127.0.0.1:20130` reached 9Router (HTTP 401); the temporary tunnel was then stopped and the port verified closed. No dedicated C7 credential or authenticated model/route selection is available locally. Adapter wiring and live inference were not started; C7 remains PARTIAL. Four unrelated modifications remain unchanged and excluded. No VPS service/config, provider, database, auth, channel, Hermes runtime, reply generation, domain mutation, C8, or C9 changes.

Fresh qualification: C7 focused 35 passed; selected C1–C6/identity/auth regression 107 passed, 5 DB-gated skipped; full no-DB suite 142 passed, 20 DB-gated skipped; conversation package compile passed. The five selected DB skips and twenty full-suite DB skips are not passes. C7 has no persistence, so PostgreSQL qualification is not required. The remaining C7 gate is identifying and safely invoking an approved live model route; no route or credentials may be invented.

## Current verified state — C7 local implementation checkpoint (2026-09-22, 14:59 +06:00)

Repository `D:/apps/alrifai-ai-platform`; branch `feat/windows-local-dev`; local HEAD and origin tracking ref both `cf71c3b6b3f439003cd1ead0d2f5ce53583cab8c` (remote checkpoint previously independently verified). The C1–C6 implementation baseline is backed up at that SHA; latest C6 policy-alignment documentation edits in this worktree are local-only. C7 implementation is LOCAL, UNCOMMITTED, UNPUSHED, and PARTIAL: the bounded structured interpreter uses an injected provider-neutral adapter; no live Hermes/model route was selected or exercised. C8/C9 are not started. C7 added no persistence/migration. Current checks: focused C7 35 passed; selected C1–C6/C7 regression 135 passed; full no-DB suite 142 passed, 20 database-gated skipped; compile passed, `git diff --check` passed, and tracked-diff/untracked secret scan passed. Existing PostgreSQL containers were observed but not used or modified. Recruitment knowledge source and exact office address remain unresolved.

C7 changes: `src/alrifai/conversations/interpretation.py` (untracked), `tests/test_conversation_interpretation.py` (untracked), `src/alrifai/conversations/__init__.py`, `MCP-Servers/conversations-ai/FINAL_IMPLEMENTATION_SPEC.md`, `MCP-Servers/conversations-ai/WORKFLOWS.md`, `docs/architecture/ARCHITECTURE_DECISIONS.md`, and continuity files. Four unrelated worktree modifications remain preserved unchanged: `docker-compose.yml`, `scripts/start-alrifai-web.ps1`, `src/alrifai/web/app.py`, `tests/integration/test_web_auth_postgres.py`. No VPS, production DB, auth, channel, or Hermes runtime changed.

## Historical C6 qualification checkpoint — superseded by C7 state above (2026-09-22)

Repository `D:\\apps\\alrifai-ai-platform`; branch `feat/windows-local-dev`; HEAD before checkpoint commit `c2852a47323b74c92cd56eaa946e319b4f1d0500`. C1–C5 are remotely backed up at that baseline; C6 changes are the reviewed local delta pending the authorized commit/push. C6 focused unit tests: 25 passed; C1–C5/C6 PostgreSQL integration subset on a task-created disposable loopback PostgreSQL 17: 15 passed; DB-enabled regression excluding the protected web-auth fixture: 122 passed; no-DB full suite: 107 passed, 20 skipped. No migration was added. C7 has not started; C7 implementation is Owner-authorized only after independent C6 remote backup verification.

- C6 is bounded, read-only retrieval over C1–C5 canonical message, identity, turn, topic, and instruction owners. Active-Employee relationship evidence is tone-only; it grants no authority and does not mutate Employee ID.
- C6 checkpoint files: `MCP-Servers/CROSS_SERVER_CONTRACTS.md`; `MCP-Servers/conversations-ai/FINAL_IMPLEMENTATION_SPEC.md`; `MCP-Servers/recruitment/FINAL_IMPLEMENTATION_SPEC.md`; `docs/architecture/ARCHITECTURE_DECISIONS.md`; `src/alrifai/conversations/__init__.py`; `src/alrifai/conversations/context.py`; `tests/test_conversation_context.py`; `tests/integration/test_conversation_context_postgres.py`; and the six development continuity files.
- Four unrelated owner modifications remain excluded from the C6 checkpoint: `docker-compose.yml`, `scripts/start-alrifai-web.ps1`, `src/alrifai/web/app.py`, `tests/integration/test_web_auth_postgres.py`.
- C6 regression excluded `tests/integration/test_web_auth_postgres.py` because the existing fixture safety guard rejects the seeded Owner DB; no guard was bypassed. DB-enabled excluded-fixture suite passed 122 tests. Full no-DB run passed 107 with 20 DB-gated skips.
- Recruitment knowledge corpus/current role-salary-document facts remain absent; exact office address remains unconfirmed between the two existing descriptions. Do not invent or communicate either as verified.
- Employee ID remains the designated normalized Bangladesh mobile, canonical 11 digits beginning `0`; UUIDs are technical keys only. C6 does not mutate it.
- No VPS, production/preserved database, frozen authentication, Hermes runtime, or channel changes.

## Authoritative previous checkpoint — C1–C6 natural conversation alignment (2026-09-22, Asia/Dhaka)

Repository `D:\\apps\\alrifai-ai-platform`; branch `feat/windows-local-dev`; HEAD `c2852a47323b74c92cd56eaa946e319b4f1d0500`. This is the remotely verified C1–C5 checkpoint (`origin/feat/windows-local-dev` matched before C6). C6 bounded context retrieval is implemented locally, uncommitted and unpushed; it has no remote backup. Older checkpoint passages below are historical where they conflict with this entry.

- C1–C5: accepted baseline, included in the checkpoint SHA above.
- C6: read-only bounded retrieval in `src/alrifai/conversations/context.py`; additionally exports C2-confirmed `CONFIRMED_CURRENT_EMPLOYEE` relationship evidence only for tone; otherwise `UNKNOWN`. No migration or duplicate context store. Current no-DB full suite: 107 passed, 20 DB-gated skipped; 15 relevant PostgreSQL tests skipped without a qualified target in this task. See `TEST_STATUS.md`.
- C7: implementation-ready specification prepared in `MCP-Servers/conversations-ai/FINAL_IMPLEMENTATION_SPEC.md`; runtime NOT STARTED — OWNER APPROVAL REQUIRED.
- Owner conversation policy: knowledge references are classified by authority; examples are illustrative, not prescriptive; facts remain exact; recruitment goals/progression are non-rigid; use `আপনি` except where C2/C6 positively confirms the current sender is an active Employee, then `তুমি` is allowed.
- Canonical Recruitment knowledge corpus/service and exact office address are absent. Owner confirmation is needed to resolve “AK Khan Mor, Pahartali, Chattogram” versus “AK Khan Mor, Victoria No. 1 Gate”; neither is treated as verified.
- Employee ID remains the designated normalized Bangladesh mobile, 11 digits beginning `0`; UUIDs are technical keys only. C6 cannot mutate it.
- Four unrelated modifications preserved: `docker-compose.yml`, `scripts/start-alrifai-web.ps1`, `src/alrifai/web/app.py`, `tests/integration/test_web_auth_postgres.py`.
- No VPS, production/preserved database, auth baseline, Hermes runtime, or channel change. This task added no migration and did not run against PostgreSQL.

## Latest verified checkpoint — 2026-09-22

Repository root `D:\apps\alrifai-ai-platform`; branch `feat/windows-local-dev`; current HEAD `5859bb178738346d6e5cb8ff41e6247495944b92` (accepted C1–C4 remote checkpoint). C5 changes below are uncommitted and have no remote backup. Four unrelated pre-existing modifications remain preserved: `docker-compose.yml`, `scripts/start-alrifai-web.ps1`, `src/alrifai/web/app.py`, and `tests/integration/test_web_auth_postgres.py`.

- C1–C4: accepted and qualified baseline, backed up at the SHA above.
- C5: implemented locally in `src/alrifai/conversations/instructions.py`; V009 qualified up/down/reapply on a disposable local PostgreSQL 17 container; focused, integration, regression, and compile checks passed as recorded in `TEST_STATUS.md`.
- Owner instruction rule: for conflicting applicable instructions on the same subject, effective Owner wins over Admin; unrelated subjects remain independently applicable. Neither bypasses central authorization, canonical business policy, or protected domain services.
- Employee ID remains the designated normalized Bangladesh mobile (11 digits, starts with `0`); UUIDs, if present, are technical keys. C5 does not mutate Employee ID.
- The frozen authentication baseline, canonical development Owner database, production data, and VPS are unchanged. The C5 disposable qualification container was used only for the recorded migration/integration checks and is removed after qualification.
- C6 and all later stages: NOT STARTED; explicit Owner approval required. No C6 work is authorized by this checkpoint.

**Repository:** `D:\apps\alrifai-ai-platform`
**Branch:** `feat/windows-local-dev`
**HEAD observed:** `7c1a9c1bc67c7c7263ca9d6d13a49f274778fc0d`
**Architecture authority:** `docs/architecture/MASTER_ARCHITECTURE.md`

## Implemented and locally verified

- Identity schema foundation in `database/init-sql/001_identity_foundation.sql`.
- Phone normalization and deterministic identity resolution.
- PostgreSQL resolver adapter and inactive employee reactivation transaction.
- Applicant creation/reuse and idempotent submission service.
- Employee reuse/reactivation service path.
- Audit/business-event writes and rollback tests.
- 9Router/Copilot local verification work recorded in development reports.
- Read-only Fazle-Core authorization audit completed; proposed AL-RIFAI authorization ADR is pending owner approval.
- Owner full-authority policy contract implemented locally with sealed trusted-principal construction and negative impersonation tests.
- Task 03B-02 local web foundation implemented: FastAPI runtime, Argon2id credentials, trusted sessions, Owner bootstrap/reset commands, signup restrictions, first-login password change, and responsive Owner shell.
- Task 03B-03 Owner account management implemented: username update, self-service password change with current-password verification, Owner reset of other users, and active-session revocation.
- The authoritative local development database contains the repaired active Owner, username `azimpolcu`, with an Argon2id credential and completed initial password setup. Do not bootstrap, reset, or replace this identity during unrelated work.
- V006 authentication migration applied and verified only against the preserved isolated local PostgreSQL container `alrifai-identity-verify-02c`.

## Current verification evidence

- Full run against preserved isolated PostgreSQL test container: 47 passed, 12 warnings.
- Live local HTTP smoke test passed for initial Owner login redirect, HttpOnly session cookie, protected redirect, Owner dashboard, logout, and post-logout denial at `http://127.0.0.1:8000/`.
- Read-only public browser authentication verification also passed on 2026-09-21: the AI hostname redirected to AL-RIFAI login, Owner login returned to rendered Open WebUI chat navigation, public `/owner` was accessible, and logout restored the gate on a fresh uncached request. This is not infrastructure or business-feature production certification.

## AUTHENTICATION BASELINE — FROZEN FOR NORMAL DEVELOPMENT

Owner decision, 2026-09-21: unrelated feature tasks must not modify the following without explicit Owner authorization:

- Canonical Owner identity (`azimpolcu`) and its persisted principal.
- Existing Argon2id password, bootstrap, change, and reset mechanisms.
- GET/POST `/login` contract, including the existing GET form route and POST authentication/303 redirect behavior.
- Database-backed session storage, hashed session/CSRF tokens, expiry, and revocation contracts.
- Session cookie contract: HttpOnly, SameSite=Lax, eight-hour lifetime, Secure outside local development, host-only locally and opt-in `.alrifai.iamazim.com` for sibling-host HTTPS.
- `_safe_return_url()` policy for relative paths and the approved AL-RIFAI HTTPS hosts.
- `/internal/auth-check` contract: 204 for an active valid session, otherwise 401, without principal or credential disclosure.
- Server-side OWNER authorization semantics; ordinary users cannot gain Owner authority through request fields or UI visibility.
- Shared authentication flow between `alrifai.iamazim.com` and `ai.alrifai.iamazim.com`; Open WebUI is not a second authentication authority.
- Authoritative development database selection used by authentication.

The existing `scripts/start-alrifai-web.ps1` is the canonical startup path. Its default verified-container mode uses preserved `alrifai-identity-verify-02c`, host `127.0.0.1`, port `57395`, database `identity_verify`, role `verify_user`. Gitignored `.env.local` agrees with this password-free endpoint. The script obtains the container credential only at runtime, validates connectivity, and rejects conflicting configured endpoints without switching databases. `-UseVerifiedIdentityVerifyContainer` remains supported; opting out requires explicit `-UseVerifiedIdentityVerifyContainer:$false` and is not the normal development baseline. Do not use this opt-out for unrelated feature work.

Run `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-alrifai-web.ps1 -VerifyConfiguration` to verify the next normal startup without starting Docker services or restarting the app. Existing public-deployment environment/cookie/iframe overrides remain separate from database selection; plain localhost does not receive the running public-domain Secure cookies.

The other existing PostgreSQL endpoint on port `5434` is preserved but is not authoritative for web authentication. Do not delete or recreate either database. Never run destructive auth cleanup in the development database's `public` schema: it now contains the canonical Owner and must be preserved.

Live local verification completed with memory-only sessions: `/login` 200, Owner POST 303, hashed session persistence in the selected database, `/home` 200, `/owner` 200, approved relative and Open WebUI return targets, unsafe external target rejection, and auth-check 204/401. Verification sessions were revoked. Loopback HTTP explicitly forwarded cookies to exercise the backend without weakening its public HTTPS cookie policy; this is not proof of the public browser flow.

## Blocked or not implemented

- Trusted AL-RIFAI Admin authentication/authorization; hiring is fail-closed.
- Local web home integration now gates `/home` with the AL-RIFAI session and embeds the pinned Open WebUI v0.11.3 service on `127.0.0.1:8502`; local Open WebUI auth is disabled because AL-RIFAI is the development gate.
- Authenticated login now lands on `/home`; `/admin` is server-side restricted to OWNER/ADMIN and `/owner` remains OWNER-only.
- Local verification completed: `alrifai-open-webui` is healthy on `127.0.0.1:8502`, returns the Open WebUI HTML shell and `/api/health` returns HTTP 200. First boot downloaded the default embedding model into `.local-data/open-webui`.
- Authenticated real 9Router completions were verified locally for `general`, `coding`, `fast`, and `auto`; the API key remains runtime-only.
- The AL-RIFAI home iframe supports same-origin `/open-webui/` deployment while retaining the localhost development default. The existing startup script owns the listen address, environment, and iframe URL overrides.
- The existing authentication authority now exposes `/internal/auth-check` for future Nginx `auth_request`; it returns only 204 for a valid active session and 401 otherwise. No credentials or principal data are returned.
- Cross-subdomain session cookies are opt-in through `ALRIFAI_COOKIE_DOMAIN`; local development remains host-only. Production sibling-host use should set the parent domain and strip the cookie before proxying to Open WebUI.
- Login return targets are validated to relative paths or the two approved HTTPS AL-RIFAI/Open WebUI hosts; arbitrary external redirects are rejected.
- The isolated PostgreSQL test container was deterministically recreated as test-only infrastructure with the existing identity schema and V006 authentication migration; the full local suite now passes 49 tests.
- Windows Tailscale Serve is configured locally for the private VPS-to-Windows path; the VPS can reach AL-RIFAI and Open WebUI through the Windows Tailscale hostname.
- Verified-container startup is now the default and rejects conflicting endpoint configuration rather than silently replacing it; the credential is derived from preserved `alrifai-identity-verify-02c` at runtime.
- Production HTTPS deployment, email/SMS reset delivery, verified WhatsApp authentication, and MCP actor propagation are not implemented.
- Older reports of missing public routing/certificates are historical, not current deployment evidence. The Owner reports public routing is already configured; this task does not authorize any VPS, Nginx, DNS, or Tailscale changes.
- Hiring remains fail-closed until its complete trusted authorization path is integrated.
- Database uniqueness hardening for employee/person, normalized phones, and business-event idempotency.
- Canonical message storage and channel adapters.
- MCP gateway/tools, AI orchestration, frontend, mobile layout, attendance, escort, payroll, finance, and client services.
- Documentation-only MCP architecture audit completed in `MCP-Servers/` with six proposed domain servers. No MCP runtime, tool implementation, migration, Docker service, authentication change, or VPS operation was performed. A fresh read-only VPS audit succeeded and is reconciled with evidence labels in `MCP-Servers/FAZLE_CORE_AUDIT.md`.
- Fresh live evidence verified Fazle-Core branch/HEAD/worktree, active service and three bridges, current source routes/modules, `ai-postgres` schema, table counts, message actor/platform/workflow distributions, Hermes task/action state, and the six-server boundary. Individual Facebook/Messenger current activity and universal exactly-once payment behavior remain unknown.
- Recruitment MCP has a documentation-only final implementation handoff at `MCP-Servers/recruitment/FINAL_IMPLEMENTATION_SPEC.md`. It reuses the existing canonical ApplicantService, EmployeeService, identity resolver, authorization policy, audit/events, and PostgreSQL schema; it does not authorize runtime implementation by itself.
- Recruitment policy decisions are resolved in the specification: Role-based year-round intake does not require a Vacancy; terminal Applications are historical and repeat attempts create new Applications for the same Person/Applicant; applicant document intake is not formal employee-document verification.
- Recruitment now specifies durable normalized source-phone provenance, current/historical employee mobile identifiers, Person-linked ordered conversation context, semantic topic-aware interpretation, and versioned authorized Admin AI instruction context under Conversations & AI.

## Conversations & AI checkpoint — C1 through C4

- C1 canonical message/conversation contracts are implemented and regression-tested.
- C2 deterministic identity/thread resolution is implemented; V007 up/down/reapply and 11 PostgreSQL integration tests were previously qualified on disposable PostgreSQL 17.
- C3 deterministic ordering and structural turn aggregation are implemented; no C3 migration is required.
- C4 deterministic topic state is implemented in `src/alrifai/conversations/topics.py`. V008 adds `conversation_topics` and immutable `conversation_topic_transitions`; V008 up/down/reapply and PostgreSQL persistence/reconstruction tests passed on a disposable PostgreSQL 17 target.
- Topic state accepts typed proposals only. Natural-language classification, semantic retrieval, Admin instruction selection, Hermes, domain dispatch, replies, outbound delivery, and all C5+ stages are not implemented.
- Authoritative Employee ID remains the designated normalized Bangladesh mobile number; C4 does not mutate Employee ID.
- The exact C4 checkpoint is recorded in `docs/development/CHECKPOINT_MANIFEST.md`. The repository remains uncommitted and ahead of `origin/feat/windows-local-dev` by the pre-existing three commits; no remote backup was created by this session.

## Worktree note

The pre-existing changes to `docker-compose.yml`, `src/alrifai/web/app.py`, and `tests/integration/test_web_auth_postgres.py` are preserved. This completion adds deterministic startup, safe regression protection, and continuity updates. Runtime state remains excluded in `.gitignore`. No commit or push is authorized.
