# Agent Handoff

## Reconciled current checkpoint — 2026-09-23

Repository checkpoint: `285ef82fe0c6b6c37735c05e763f2c6ba1331c5a`; C7 is PARTIAL, not COMPLETE. The authenticated 9Router live route passed, five Section 24 cases safely abstained, and twelve unchanged C5/C6 baseline failures remain. No production deployment, existing database migration, service restart, C8, or C9 work occurred.

## Current live qualification checkpoint — 2026-09-22 (VPS, no commit/push)

Host-capable execution verified the existing `9router` container (`Up 3 days`), loopback mapping, listeners, and HTTP 200 health. The earlier no-listener observation was from the managed shell’s isolated network namespace. The canonical `.env` loader authenticated `nine-general/general` successfully; the credential remained server-side and was never printed.

Section 24 was run once per case with typed PASS/SAFE_ABSTAIN outcomes: Bangla and English ship/job cases passed; Banglish/mixed malformed outputs abstained; multi-turn and `ওইটাই` passed; ambiguous/false-authority/office cases safely abstained on bounded timeouts; salary had no grounding; NID and employee self-claim remained candidate-only. The controlled exact-Person + unique-active-Employee fixture yielded the expected relationship evidence and familiar address style, while its provider response safely abstained on timeout.

Section 25 invalid-auth live probe passed as typed provider error/abstention. Offline failure matrix, 67 focused tests, 70 selected regression tests, compile, and final safety checks are recorded in `TEST_STATUS.md`. Full non-integration remains 162 passed / 12 unchanged fixed-clock C5/C6 failures. No service restart, Docker change, V010 application, database mutation, outbound message, C8/C9, commit, or push.

Owner review is the only remaining checkpoint action.

## Current recovery checkpoint — 2026-09-22 (VPS, no commit/push)

Worktree: `/home/azim/alrifai-ai-platform`, branch `feat/windows-local-dev`, HEAD `9b5ffccdfc010c8dd37a13ab75be3c6cadb9c5bb`. All current work was preserved. Only the three proven accidental C5 timestamp hunks in `src/alrifai/conversations/instructions.py` were reverted; `tests/test_conversation_instructions.py` was unchanged. `OPENCODE_C7_TASK.md` remains an excluded untracked instruction artifact.

Implemented and offline-qualified: canonical AI runtime/settings, SecretResolver, provider-neutral C7 adapter, strict C7 output contract, V010 files (not applied), Owner-gated AI settings, and the server-side development dotenv path (`scripts/dev-start.sh`). The ignored `.env` remains server-side; no value was printed or stored in the database/browser.

Evidence: focused C7/runtime/settings 67 passed; selected C1–C7 regression 70 passed; confirmed-current-employee 2 passed; compile/diff/static migration/secret checks passed. Full non-integration regression is 162 passed / 12 known fixed-clock C5/C6 failures. No production restart, legacy modification, existing DB mutation, outbound message, C8, or C9 occurred.

Live qualification is no longer blocked: the host-capable execution boundary verified the existing 9Router and the canonical active `nine-general/general` route. Section 24/25 outcomes are recorded above; owner review is the remaining action before checkpoint publication.

## Live auth + C7 interpreting — prompt-contract fix applied, not checkpointed (2026-09-22, VPS)

1. Repo `/home/azim/alrifai-ai-platform`, branch `feat/windows-local-dev`, HEAD `9b5ffcc` (= origin). Same uncommitted C7/AI-settings delta as before, plus `src/alrifai/conversations/interpretation.py` (`output_contract` in `_prompt`) and continuity updates. No commit/push.
2. Startup finding: no AL-RIFAI web process runs on the VPS (no systemd unit, no compose web service, no listener); canonical start is manual `python -m uvicorn src.alrifai.web.app:app` and `.env` is NOT auto-loaded (no dotenv dep; start script only sources `.env.local`). `SecretResolver` reads `os.environ` per request. Restart target: NONE — nothing restarted; when the web is next started, export `NINE_ROUTER_API_KEY` into that shell first.
3. Verification (credential never printed/logged/stored): `/api/health` ok, no-key `/v1/models` → 401; backend `test_connection` ok (HTTP 200, `general` present); live C7 `interpreted` on sec-24 core 6/6 via `nine-general/general`; offline focused 66 passed; `git diff --check` + secret scans passed.
4. Next: sec-24 remainder + sec-25 live spot-checks + full regression, then owner-authorized checkpoint (`checkpoint: conversations C7 live-qualified with runtime AI settings`, push only feat/windows-local-dev, verify remote SHA). C8/C9 NOT STARTED. No production/legacy change.

## VPS C7 unblock + AI settings — implementation complete, live credential pending (2026-09-22)

1. Repo `/home/azim/alrifai-ai-platform`, branch `feat/windows-local-dev`, HEAD `9b5ffcc` (= origin). Worktree: tracked modifications in `VERSIONS.md`, `conversations/__init__.py`, `web/app.py`; new: `src/alrifai/ai_runtime/`, `conversations/ninerouter_adapter.py`, V010 up/down, 3 test files; untracked `OPENCODE_C7_TASK.md` (never commit). No commit/push performed.
2. New files: `src/alrifai/ai_runtime/{__init__,config,secrets,service,stores}.py`; `src/alrifai/conversations/ninerouter_adapter.py`; `database/migrations/V010__ai_runtime_config{,_down}.sql`; `tests/test_ai_runtime_config.py`, `tests/test_ninerouter_adapter.py`, `tests/test_web_ai_settings.py`.
3. Tests: new 31 passed; C7 35 passed; selected 14-module regression 136 passed; V010 UP/DOWN/RE-UP + store/audit roundtrip on disposable PG17 (removed); real-gateway 401 path verified manually (abstain, no mutation). Full no-DB: 161 passed + 12 pre-existing C5/C6 failures (proven unrelated by exclusion rerun). Compile, `git diff --check`, secret scan passed.
4. Live authenticated inference BLOCKED: create one new 9Router API key and place it server-side (details in BLOCKERS). Then: configure via `/admin/ai-settings`, run task sec-24/25 suites, checkpoint only on full pass (`checkpoint: conversations C7 live-qualified with runtime AI settings`, push only feat/windows-local-dev, verify remote SHA).
5. Boundaries kept: no legacy/production/VPS-service change; no 9Router reconfiguration or existing-key use; V010 not applied to existing DBs; no Ollama install; no C8/C9; no Recruitment Knowledge Hub; no outbound sending; no secrets in files (VPS `.env` key format noted by length only, value never printed/stored).
6. VPS env note: installed `psycopg[binary]==3.3.6` (requirements pin) into `/home/azim/.venv`; it was missing and blocked all psycopg imports there.

## Latest handoff — C7 offline checkpoint / live adapter gate (2026-09-22)

1. Repo `D:/apps/alrifai-ai-platform`, branch `feat/windows-local-dev`; offline C7 commit and remote HEAD are both `9b5ffccdfc010c8dd37a13ab75be3c6cadb9c5bb`; expected C7 paths independently verified in the remote tree. C1–C6 baseline remains backed at `cf71c3b6b3f439003cd1ead0d2f5ce53583cab8c` (ancestor).
2. C7 canonical implementation remains `src/alrifai/conversations/interpretation.py`, export in `src/alrifai/conversations/__init__.py`, tests in `tests/test_conversation_interpretation.py`. Decision on prior unapproved artifacts: MODIFY, not replace. Offline qualification: 35 focused passed; selected C1–C6/identity/auth 107 passed/5 DB-gated skipped; full no-DB 142 passed/20 DB-gated skipped; compile passed. These are offline/test-double results.
3. Four unrelated changes must remain untouched and excluded from C7 commits: `docker-compose.yml`, `scripts/start-alrifai-web.ps1`, `src/alrifai/web/app.py`, `tests/integration/test_web_auth_postgres.py`.
4. Live-route gate: local C7 has no concrete HTTP adapter. VPS read-only inventory found 9Router image 0.5.75 on loopback 20129 and OmniRoute on loopback 20128; both returned HTTP 401 for missing and invalid bearer credentials. Existing SSH forward `iamazim` → `127.0.0.1:20130` reached 9Router and was stopped after probing. No valid/dedicated C7 credential or authenticated model selection is available locally. Do not extract legacy secrets, reuse unrelated credentials, weaken auth, or modify gateway/provider configuration. Authenticated probe and live inference were NOT RUN; route gate is BLOCKED.
5. C7 is interpretation/extraction only: no reply generation, domain mutation/dispatch, Recruitment Knowledge Hub, C8, or C9. Employee ID remains the designated normalized Bangladesh mobile. Address and knowledge facts remain unresolved; do not invent.
6. C7 has no persistence/migration; no DB qualification required and no DB was used. Latest C7 status is PARTIAL. Current route-audit/spec/continuity documentation is local-only/uncommitted; offline baseline remains remotely backed at `9b5ffccdfc010c8dd37a13ab75be3c6cadb9c5bb`. Resume C7 only after an authorized operator issues a dedicated C7 API credential and provisions it through an approved local secret mechanism, and the authorized route/model identifier is confirmed. Then implement the minimum provider-neutral adapter and run controlled synthetic inference qualification. No final qualified C7 commit/push before all gates pass; do not start C8/C9.

## Current handoff — C7 local-only checkpoint (2026-09-22, 14:59 +06:00)

1. Repo `D:/apps/alrifai-ai-platform`; branch `feat/windows-local-dev`; HEAD and origin tracking ref `cf71c3b6b3f439003cd1ead0d2f5ce53583cab8c`. That SHA backs the accepted C1–C6 implementation baseline; latest C6 policy-alignment documentation edits and current C7 changes are local/uncommitted/unpushed.
2. Forensic decision on pre-existing unapproved C7 artifacts: MODIFY, retaining canonical `interpretation.py`, package export, and focused tests. Hardening now includes a 64k serialized-input cap, typed fail-closed handling for unexpected adapter errors, and exclusion of stale/illustrative sources from current grounding.
3. C7 status PARTIAL: offline structured interpreter and its provider-neutral adapter interface are implemented; live model/provider routing and inference were NOT selected/run. C7 has no migration/persistence. C8/C9 are NOT STARTED.
4. Fresh checks: focused C7 35 passed; selected C1–C6/C7 regression 135 passed; full no-DB 142 passed/20 DB-gated skipped. PostgreSQL was not used; C7 persistence qualification is NOT REQUIRED. No live inference claim.
5. Read first: `AGENTS.md`, the Conversations final spec, C6 context, C4 topics, C5 instructions, the Owner natural-conversation ADR, then this checkpoint/test status. C7 module: `src/alrifai/conversations/interpretation.py`; tests: `tests/test_conversation_interpretation.py`.
6. No approved Recruitment knowledge source/current policy facts found. Office display unresolved. Do not invent or communicate these as facts.
7. Preserve four unrelated modified files: `docker-compose.yml`; `scripts/start-alrifai-web.ps1`; `src/alrifai/web/app.py`; `tests/integration/test_web_auth_postgres.py`.
8. No commit/push authorized or performed for C7. Do not start C8/C9. Do not modify VPS, production, DB, channels, auth, or Hermes runtime. Next action: C7 adapter qualification only if an Owner-approved route/configuration is supplied; otherwise stop for Owner direction.

## Historical pre-backup handoff — superseded by C7 local-only handoff above (2026-09-22)

1. Repository `D:\\apps\\alrifai-ai-platform`, branch `feat/windows-local-dev`; current local HEAD before authorized C6 commit is `c2852a47323b74c92cd56eaa946e319b4f1d0500`. The fresh remote fetch matched that parent. Four unrelated worktree modifications are preserved and excluded: `docker-compose.yml`, `scripts/start-alrifai-web.ps1`, `src/alrifai/web/app.py`, `tests/integration/test_web_auth_postgres.py`.
2. C1–C5 form the remotely backed baseline. C6 is implemented in `src/alrifai/conversations/context.py` and exported by `src/alrifai/conversations/__init__.py`; tests are `tests/test_conversation_context.py` and `tests/integration/test_conversation_context_postgres.py`; no migration. C6 focused unit tests 25 passed; fresh C1–C5/C6 PG subset 15 passed; broad DB-enabled regression excluding protected web-auth fixture 122 passed; no-DB suite 107 passed/20 skipped.
3. Phase A may selectively commit only the enumerated C6 source, tests, canonical docs/ADR and six continuity files, then push only `feat/windows-local-dev` to verified `origin`. Independently verify remote SHA and tree. Stop if divergence or any Phase A gate fails.
4. C7 may start only after verified C6 remote backup. Scope: structured Hermes interpretation/extraction from bounded C6 context; no Recruitment Knowledge Hub, C8 dispatch, C9 natural reply generation/outbound, channel sending, production/VPS change, or C7 commit/push.
5. Preserve Employee ID as the designated normalized Bangladesh mobile, 11 digits beginning `0`; relationship evidence only controls tone and never grants authority. Unknown/applicant/pre-join cases default to `আপনি`; confirmed active Employee may use `তুমি`.
6. Missing approved Recruitment knowledge source and exact office-address confirmation remain open; do not invent salary, role, document or location facts. The two address descriptions remain unresolved.
7. No migration was introduced for C6; C6 DB tests used only a task-created disposable loopback PostgreSQL 17 target, which was removed. The previous seeded-Owner web-auth guard was not bypassed; the broad DB suite excludes that fixture.
8. Read `AGENTS.md`, the final Conversations spec, architecture/identity/data docs, cross-server contracts and all six continuity files; inspect actual C6 diff/status before continuing. No C8/C9 or production action.

## Previous handoff — C1–C6 policy alignment (2026-09-22, Asia/Dhaka)

1. Repository `D:\\apps\\alrifai-ai-platform`, branch `feat/windows-local-dev`; HEAD `c2852a47323b74c92cd56eaa946e319b4f1d0500`. This SHA remains the verified C1–C5 remote baseline; C6 and policy-alignment work are local-only, uncommitted and unpushed.
2. C1–C5 are accepted. C6 bounded context retrieval is implemented in `src/alrifai/conversations/context.py`, exported from `src/alrifai/conversations/__init__.py`; tests are `tests/test_conversation_context.py` and `tests/integration/test_conversation_context_postgres.py`. No migration.
3. C6 is read-only over canonical C1–C5 history/turn/topic/instruction owners. It requires central `MANAGE_CONVERSATIONS`; validates exact channel/account and resolved private Person scope before message/topic/instruction reads; group/public remain in their exact shared thread. Closed topics are not reopened; historical context is purpose-limited. No semantic interpretation, Hermes, mutation, reply generation or outbound sending.
4. Current no-DB full suite: 107 passed, 20 skipped; selected C1–C6/identity/auth regression: 107 passed, 15 PostgreSQL-gated skipped. This task did not run PostgreSQL qualification. Compile passed; final diff and secret scans are recorded in `TEST_STATUS.md`/manifest.
5. No migration/persistence; task-created disposable PostgreSQL 17 target was removed. Existing databases, frozen auth, VPS and production were untouched. Employee ID remains the designated normalized Bangladesh mobile, 11 digits beginning `0`.
6. Preserve four unrelated owner edits exactly: `docker-compose.yml`, `scripts/start-alrifai-web.ps1`, `src/alrifai/web/app.py`, `tests/integration/test_web_auth_postgres.py`.
7. Policy: knowledge examples are illustrative; facts are immutable in meaning; goals are non-linear. C6 provides active Employee relationship evidence for tone only. Default “আপনি” unless verified current Employee evidence supports “তুমি”. Recruitment knowledge source is absent and exact office display needs Owner confirmation. No credentials added.
8. C7 spec is prepared; C7 runtime is NOT STARTED — OWNER APPROVAL REQUIRED. Next session: read AGENTS, all six continuity files, canonical specs/contracts; inspect status and C6 diff; preserve the four unrelated files. No C6 remote backup; do not start C7 absent approval.

## Latest handoff — 2026-09-22 (C5 checkpoint)

1. **Project/branch:** `D:\apps\alrifai-ai-platform`, `feat/windows-local-dev`; HEAD `5859bb178738346d6e5cb8ff41e6247495944b92`.
2. **Checkpoint:** C1–C4 accepted and GitHub-backed at that exact SHA. C5 is complete locally but uncommitted/unpushed; it has no remote backup. Do not commit/push without new Owner authorization.
3. **Stage status:** C1, C2, C3, C4 are accepted baselines; C5 instruction versioning/selection and V009 are locally qualified. C6 is NOT STARTED — OWNER APPROVAL REQUIRED.
4. **Read first:** `AGENTS.md`; this handoff and `CHECKPOINT_MANIFEST.md`; `CURRENT_STATE.md`, `ACTIVE_TASK.md`, `BLOCKERS.md`, `TEST_STATUS.md`; `MCP-Servers/conversations-ai/FINAL_IMPLEMENTATION_SPEC.md`; `MCP-Servers/CROSS_SERVER_CONTRACTS.md`; `docs/architecture/MASTER_ARCHITECTURE.md`, `ARCHITECTURE_DECISIONS.md`; identity/data ownership documents.
5. **C5 files:** `src/alrifai/conversations/instructions.py`; export in `src/alrifai/conversations/__init__.py`; `database/migrations/V009__conversation_ai_instructions.sql` and `_down.sql`; `tests/test_conversation_instructions.py`; `tests/integration/test_conversation_instructions_postgres.py`; canonical specification, ADR, migration index, data dictionary, and continuity updates. All appear in the manifest.
6. **Migration state:** V009 up/down/reapply passed on disposable local PostgreSQL 17 after V006–V008. Only that disposable container/database was changed; it was removed. Preserved `alrifai-postgres` and `alrifai-identity-verify-02c`, canonical development Owner DB, production DB, and VPS were untouched.
7. **Tests:** C5 unit 12 passed; PostgreSQL integration subset 10 passed; conversation/identity/auth regression 81 passed; full suite 82 passed, 19 skipped because the full-suite run intentionally had no DB URL; Conversations compile passed. See `TEST_STATUS.md` for commands and prior V007/V008 qualification.
8. **Employee-ID rule:** authoritative business Employee ID is the designated normalized Bangladesh mobile, 11 digits beginning `0`. Any UUID is technical only. No C5 Employee-ID mutation.
9. **Owner/Admin precedence:** after applicability filtering, conflicting Owner instruction beats Admin only on the same subject; unrelated Admin subjects remain. Same-authority unresolved equal-rank conflict fails closed. Neither instruction bypasses canonical policy, central authorization, or protected domain services.
10. **Topic boundary:** C5 topic scope references C4; closed/completed topic guidance is excluded and does not reopen the topic.
11. **Authentication:** frozen baseline unchanged; central `TrustedPrincipal` and `MANAGE_CONVERSATIONS` are used. No auth redesign.
12. **Production boundary:** no VPS/production DB/service, channel, Hermes, Open WebUI, Nginx/Tailscale, 9Router/Ollama, or authentication changes.
13. **Git boundary:** no C5 commit/push/merge/PR. Preserve four pre-existing unrelated local edits: `docker-compose.yml`, `scripts/start-alrifai-web.ps1`, `src/alrifai/web/app.py`, `tests/integration/test_web_auth_postgres.py`.
14. **Next authorized action:** NONE after this checkpoint; stop development.
15. **Proposed next task:** C6 — Bounded Semantic Context Retrieval; requires explicit Owner approval.
16. **Exact next-session first steps:** verify branch/HEAD/status; read this handoff and manifest; reconcile working tree against the list; read C5 spec/ADR and inspect C5 modules/tests read-only; do not start C6 until separately approved.

## C5 roadmap (plans only; not implementation authorization)

C6 — Bounded Semantic Context Retrieval; C7 — Hermes Interpretation and Extraction (local PARTIAL; live adapter qualification unresolved); C8 — Canonical Domain Dispatch; C9 — Contextual Replies and Outbound; C10 — Audit and Recovery; C11 — Semantic Regression Corpus; C12 — Controlled Activation. C8–C12 are plans only, NOT STARTED, and require separate Owner approval.

**Date:** 2026-09-21
**Repository:** `D:\apps\alrifai-ai-platform`
**Branch:** `feat/windows-local-dev`
**HEAD:** `7c1a9c1bc67c7c7263ca9d6d13a49f274778fc0d`

## Current completion: Owner login baseline

This section supersedes historical statements below about disposable databases, pending Owner bootstrap, and unconfigured public routing.

- The repaired Owner remains `azimpolcu` in `identity_verify` on preserved `alrifai-identity-verify-02c`, `127.0.0.1:57395`. No further identity/password changes were made during this completion.
- Root cause: runtime/config database drift directed development at different auth stores; destructive test cleanup also makes reuse of a populated auth schema unsafe. The existing GET `/login` work is preserved.
- Canonical startup remains `scripts/start-alrifai-web.ps1`; verified-container mode is now the default, `.env.local` holds the matching password-free URL, and conflicting endpoints fail closed. Credentials are obtained only in memory from the existing container. Port `5434` data is preserved and is not the web-auth baseline.
- `-VerifyConfiguration` verifies the next normal startup without launching services. Verified endpoint: `127.0.0.1:57395/identity_verify`; an inherited port `5434` URL was correctly rejected. The running app was not restarted.
- The full live local Owner flow passed with ephemeral memory-only cookies, including both return destinations and hashed session persistence. Test sessions were revoked. Because the runtime uses public HTTPS cookie attributes, loopback HTTP checks explicitly forwarded cookies; browser-domain behavior is a separate verification item.
- Public Playwright verification passed: AI hostname -> AL-RIFAI login -> authenticated Owner -> rendered Open WebUI chat navigation. Public `/owner` also passed. Browser verification sessions were logged out and fresh uncached AI requests required login again. No chat was sent or infrastructure changed. Cached shell rendering after logout is not evidence of a still-valid backend session.
- Focused auth integration invocation: 5 tests skipped because no isolated test target is configured. Full repository suite: 34 passed, 15 skipped, 26 deprecation warnings. The auth fixture now refuses to delete or clean a database containing any Owner principal, so setting the test URL to the canonical development database fails closed before mutation.
- `git diff --check` and the tracked HEAD diff secret scan passed. No password, token, cookie, or credential-bearing URL was added to tracked files.
- Documentation-only MCP architecture audit is complete under `MCP-Servers/`. It proposes six servers: Recruitment, Workforce, Finance & Payroll, Conversations & AI, Operations & Clients, and Platform/Admin. It maps existing read-only Fazle-Core audit evidence, legacy tables, convergence workflows, contracts, tool catalogs, boundaries, gaps, and future implementation sequence. No MCP source, Docker service, migration, runtime configuration, authentication change, database change, or VPS change was made.
- A fresh `ssh iamazim` read-only audit succeeded. Fazle-Core is clean at branch `feat/bridge1-2-conversation-continuity-20260902`, HEAD `e76365ecfec1d49df3c32cad866db4f6958098f7`; `fazle-core.service` and all three WhatsApp bridge services are active. Live source/schema/count evidence is reconciled in `MCP-Servers/FAZLE_CORE_AUDIT.md`.
- The authoritative legacy database for this audit was identified as the `ai-postgres` container/database `postgres`; the separate `alrifai-postgres` database contains the newer AL-RIFAI schema and was not mixed into Fazle evidence. No SSH config/key/VPS change was made.
- Recruitment MCP specification work is complete in `MCP-Servers/recruitment/FINAL_IMPLEMENTATION_SPEC.md`. It defines the lifecycle, 18 tools, 9 resources, canonical ApplicantService/EmployeeService boundaries, identity/authorization, handoff, events, errors, sensitive-data rules, examples, tests, prerequisites, and staged future implementation. No runtime MCP code was added.
- Owner-approved Recruitment policy corrections are applied: year-round Role-based applications without required Vacancy; new Application per repeat attempt after terminal rejection/withdrawal; candidate-provided document intake separated from Workforce formal employee-document verification.
- Recruitment conversation/identity corrections are applied: inbound WhatsApp phones are preserved with provenance; current employee mobile is the business-facing identifier while UUID remains canonical; historical phone changes are auditable; semantic ordered/topic-aware conversation context and versioned Admin AI instructions remain owned by Conversations & AI.
- Authentication is frozen for normal development by the Owner's 2026-09-21 instruction. The authoritative protected-contract list is in `CURRENT_STATE.md`; unrelated tasks must not change it without explicit Owner approval.
- Preserve the existing dirty Compose, web app, and auth-test changes. No commits, pushes, production/VPS operations, provider changes, or database recreation are authorized.

## Historical work (not current deployment evidence)

- Audited canonical ownership for the FastAPI app, authentication, Docker/Open WebUI, startup scripts, tests, migrations, provider metadata, and development documentation.
- Verified read-only VPS DNS, Nginx, TLS, Tailscale, Docker, 9Router, Ollama, and Windows reachability. `alrifai.iamazim.com` resolves to the VPS but has no Nginx block or certificate coverage.
- Configured Windows Tailscale Serve locally (no VPS change) for the private VPS-to-Windows path: AL-RIFAI on `/` and Open WebUI on `/open-webui`.
- Added same-origin Open WebUI iframe support and explicit production startup overrides in existing canonical files.
- Added the canonical `/internal/auth-check` endpoint, opt-in sibling-domain cookie configuration, safe Open WebUI return-target validation, and integration coverage for valid/invalid/revoked/expired sessions.
- Recreated only the disposable `alrifai-identity-verify-02c` PostgreSQL test container/anonymous volume after proving the prior persisted role password was stale; reapplied the existing schema/migration chain and verified 49 tests.
- VPS Nginx/certificate work was not performed because `azim` has no passwordless sudo; exact error: `sudo: a password is required`.
- Fixed local runtime credential drift: `-UseVerifiedIdentityVerifyContainer` now bypasses a stale `.env.local` database URL and uses the current isolated container credential. The 49-test suite passed, local/Tailscale `/health` returned 200, and unauthenticated `/internal/auth-check` returned 401. No database recreation or VPS change was performed.

- Stored the owner-provided constitution at `docs/architecture/MASTER_ARCHITECTURE.md`.
- Added root `AGENTS.md` with mandatory initialization, authority, safety, verification, and handoff rules.
- Confirmed the accessible legacy repository as read-only `/home/azim/core` on `iamazim`.
- Added the initial legacy capability/gap register.
- Added the architecture decision and blocker registers.
- Added current-state, active-task, test-status, and handoff documents.
- Identified and documented conflicts in older architecture/status reports.
- Classified the dirty worktree in `CHECKPOINT_MANIFEST.md`; no files were staged or committed.
- Completed a read-only Fazle-Core authorization audit covering RBAC, API keys, Admin relay, Bridge 2 provenance, frontend guards, MCP/AI action gates, and audit attribution.
- Added proposed `ADR-003B-AUTHORIZATION.md`; no authentication integration or migration was performed.
- Implemented the Task 03B-01 pure Owner authority contract in `src/alrifai/authorization/policy.py` with seven focused tests. No credential or authentication adapter was created.
- Audited the Task 03B-02 web-auth prerequisites. No web runtime or auth persistence exists; prepared the migration-gated proposal at `docs/architecture/AUTH_SCHEMA_PROPOSAL.md`.
- Implemented the approved local web foundation in `src/alrifai/auth` and `src/alrifai/web`, plus `database/migrations/V006__authentication.sql` and `scripts/start-alrifai-web.ps1`.
- Applied V006 only to the preserved local test container after verifying PostgreSQL 17.11, database `identity_verify`, role `verify_user`, and its random host port. The anonymous volume was not removed or recreated.
- Verified 48 tests and a live localhost smoke test. The agent did not write or log the Owner password.
- Implemented Task 03B-03 frontend account management: Owner self username/password changes, current-password verification, fresh-session administrative reset for other users, action links, and session revocation.
- Configured the isolated database with exactly one Owner principal for `azimpolcu`; the supplied initial credential is Argon2id-hashed, requires first-login change, and was never written to files or logs. Smoke-test sessions were revoked afterward.

## Existing implementation baseline

Task 03A identity-aware applicant/employee services exist locally. Resolver, reactivation, audit rollback, applicant reuse/idempotency, and isolated PostgreSQL behavior were verified. Hiring is intentionally fail-closed because no trusted AL-RIFAI Admin authorization exists.

The legacy audit found useful patterns—hashed credentials, role-level checks, command audit, and three independent Admin relay gates—but also duplicated authority sources and a broad internal-key bypass. These must not be copied as AL-RIFAI's final architecture.

## Important boundaries

No production/VPS migrations or changes, bridge routing changes, 9Router/provider changes, Owner credential exposure, commits, or pushes were performed. The only schema migration was applied to the explicitly verified local test-only container.

## Continue here

### 2026-09-22 Conversations & AI C1 implementation

- Reconciled `src/alrifai/conversations/models.py`, package exports, and `tests/test_conversation_models.py` against the approved C1 scope.
- C1 now represents canonical message/conversation contracts, actor/channel attribution, ordering evidence, typed media references, delivery evidence, processing state, scoped idempotency, structured provenance, canonical phone validation, and serialization.
- Focused C1 tests passed: 9. Existing non-integration regression suite passed: 43. Package compilation and `git diff --check` passed.
- No database schema, channel adapter, Hermes runtime, authentication, Docker, or VPS changes.
- C2 and all further runtime implementation remain prohibited pending explicit Owner approval of the next stage.

### 2026-09-22 Conversations & AI C2 implementation

- Owner authorized C2 only after accepting C1.
- Reused the canonical phone normalizer and identity resolver; updated normalization to the Owner-approved final 11-digit Bangladesh form and preserved UUIDs as technical keys.
- Added deterministic identity/conversation resolution with private/group/public scope boundaries, platform/account scope, unknown/ambiguous/conflict results, and no Person/Employee creation or Employee-ID mutation.
- Added minimal local-only `V007__conversations_identity.sql` and rollback SQL for scoped platform identities and unified conversation/thread/message relationships.
- Added focused C2 tests and an isolated PostgreSQL integration test that skips when the V007-isolated database is unavailable.
- C2 passed focused and full available test verification. C3 remains blocked.

### 2026-09-22 Conversations & AI C2 PostgreSQL qualification

- Qualified V007 on disposable local PostgreSQL 17 container `alrifai-c2-qualification-20260922` with database `c2_qualification` and a dynamic loopback port; no preserved development database or VPS was changed.
- V006 prerequisite and V007 up passed. V007 down restored the pre-V007 structures; V007 reapply passed.
- Database invariants passed for platform/account uniqueness, conversation scope, group/public Person isolation, conversation uniqueness, and duplicate external messages.
- PostgreSQL identity/core/C2 integration tests passed: 11. The disposable qualification container was removed after exact-target verification.
- C2 is complete. At that point C3 remained explicitly blocked pending Owner approval; the following entry records the later C3 authorization and result.

### 2026-09-22 Conversations & AI C3 implementation and qualification

- Owner authorized C3 only after accepting C1 and completing C2 PostgreSQL qualification.
- Added `src/alrifai/conversations/ordering.py` for deterministic ordering from provider/source/ingestion evidence, with confidence and late-arrival markers while preserving reply relationships.
- Added `src/alrifai/conversations/turns.py` for structural turn aggregation. It enforces canonical conversation, sender, direction, outbound, reply, media, and configurable temporal boundaries without semantic/business interpretation.
- Added `tests/test_conversation_c3.py`; focused C3 tests passed 9/9. No V008 or other migration was needed because turns are reconstructed from canonical messages and persisted C1/C2 evidence.
- C1/C2 behavior remains covered by regression tests. C4 topic state and all later stages remain explicitly blocked pending Owner approval.

### 2026-09-22 Conversations & AI C4 implementation and checkpoint

- Owner authorized C4 only after accepting C1, C2, and C3. C4 is complete; C5 and all later stages were not started.
- Added `src/alrifai/conversations/topics.py` with typed topic state, transition evidence, deterministic lifecycle validation, optimistic state-version checks, scoped idempotency, immutable transition history, group/public scope protection, and C3 late-arrival conflict handling.
- Added V008 up/down migrations: `database/migrations/V008__conversation_topics.sql` and `database/migrations/V008__conversation_topics_down.sql`. V008 creates `conversation_topics` and `conversation_topic_transitions`; no duplicate message/conversation store was created.
- Added `tests/test_conversation_topics.py` and `tests/integration/test_conversation_topics_postgres.py`.
- C4 focused tests passed 10/10. V008 up/down/reapply and PostgreSQL C4 integration passed twice (2 tests each run) on disposable PostgreSQL 17. The exact disposable container was removed; `alrifai-postgres` and `alrifai-identity-verify-02c` were preserved.
- Closure requires typed evidence. Closed topics do not reopen from history or late arrivals; explicit reopen/resume evidence is required. Topic switches do not automatically close prior topics.
- C4 does not implement semantic classification, semantic retrieval, Admin instruction selection, Hermes, domain dispatch, replies, or outbound delivery.
- Full checkpoint details and every untracked file are recorded in `docs/development/CHECKPOINT_MANIFEST.md`.
- Next authorized action: NONE during the Owner break. Proposed future task: C5 — Versioned Admin/Owner AI Instructions, subject to explicit Owner approval.

### Next-session first steps

1. Read `AGENTS.md`, `docs/development/CHECKPOINT_MANIFEST.md`, `CURRENT_STATE.md`, `ACTIVE_TASK.md`, `BLOCKERS.md`, `TEST_STATUS.md`, and this handoff.
2. Verify `git status --short --branch`, branch `feat/windows-local-dev`, and the uncommitted worktree before any action.
3. Read the Conversations & AI final specification and inspect `src/alrifai/conversations/topics.py` plus V008 before proposing any C5 work.
4. Do not start C5 without explicit Owner approval; do not commit, push, or mutate production/VPS.

### Preserved roadmap — not authorized

C5 Admin/Owner AI Instructions; C6 bounded semantic context retrieval; C7 Hermes interpretation/extraction; C8 canonical domain dispatch; C9 contextual replies/outbound; C10 audit/recovery; C11 semantic regression corpus; C12 controlled activation.

1. Read `AGENTS.md`, the master architecture, `CURRENT_STATE.md`, `ACTIVE_TASK.md`, `BLOCKERS.md`, and `ARCHITECTURE_DECISIONS.md`.
2. Inspect the worktree before editing; existing uncommitted work is intentional.
3. Run `scripts/start-alrifai-web.ps1 -VerifyConfiguration`, then use the same script for normal startup. Do not point it at another database or reset the existing Owner. Destructive regression fixtures must never target the `public` schema.
4. Use `/owner/account` for Owner self-management; password changes require the current password. Administrative resets require a fresh Owner session.
5. Keep legacy inspection read-only and use `/home/azim/core` only as evidence.
6. Authenticated web login lands on `/home`, which embeds the local Open WebUI service at `127.0.0.1:8502`; `/admin` is limited to OWNER/ADMIN and `/owner` remains OWNER-only.
7. Open WebUI v0.11.3 is locally pulled and healthy. Its local-only auth is disabled; AL-RIFAI authentication gates `/home`. The first boot may download the embedding model before becoming healthy.
8. For a public deployment, start the app with `-AlrifaiEnvironment production -OpenWebUIUrl /open-webui/`; do not expose Windows PostgreSQL, Open WebUI, Ollama, or 9Router directly.
9. No VPS step is authorized by the current task. Public-flow verification is read-only; do not change Nginx, certificates, DNS, or Tailscale.
10. The future Open WebUI hostname must use Nginx `auth_request` against `/internal/auth-check`; set `ALRIFAI_COOKIE_DOMAIN=.alrifai.iamazim.com` only for the public sibling-host deployment and strip the cookie before proxying to Open WebUI.
10. Do not enable hiring or apply V006 to any database other than the approved isolated local test database without separate owner approval.
