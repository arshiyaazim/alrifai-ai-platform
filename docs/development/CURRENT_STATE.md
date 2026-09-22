# AL-RIFAI Current State

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
