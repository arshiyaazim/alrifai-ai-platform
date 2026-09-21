# AL-RIFAI Current State

**Repository:** `D:\apps\alrifai-ai-platform`
**Branch:** `feat/windows-local-dev`
**HEAD observed:** `c44a932b1291fc6901c80bd6a2944198727da0d`
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
- The isolated local database contains exactly one Owner principal, username `azimpolcu`, with an Argon2id credential and first-login password change required. The initial credential was not written to repository files or logs.
- V006 authentication migration applied and verified only against the preserved isolated local PostgreSQL container `alrifai-identity-verify-02c`.

## Current verification evidence

- Full run against preserved isolated PostgreSQL test container: 47 passed, 12 warnings.
- Live local HTTP smoke test passed for initial Owner login redirect, HttpOnly session cookie, protected redirect, Owner dashboard, logout, and post-logout denial at `http://127.0.0.1:8000/`.
- No production verification is implied.

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
- Verified-container startup now takes precedence over a stale `.env.local` database URL and derives the current test credential from `alrifai-identity-verify-02c`; local and Tailscale health checks returned HTTP 200.
- Production HTTPS deployment, email/SMS reset delivery, verified WhatsApp authentication, and MCP actor propagation are not implemented.
- `alrifai.iamazim.com` DNS resolves to the VPS, but no isolated Nginx server block or certificate exists yet. VPS configuration is blocked because the SSH user lacks passwordless sudo; no VPS files or services were changed.
- Hiring remains fail-closed until its complete trusted authorization path is integrated.
- Database uniqueness hardening for employee/person, normalized phones, and business-event idempotency.
- Canonical message storage and channel adapters.
- MCP gateway/tools, AI orchestration, frontend, mobile layout, attendance, escort, payroll, finance, and client services.

## Worktree note

The current milestone contains only the reviewed local startup, iframe, integration-test, and continuity-documentation changes. Runtime state remains excluded in `.gitignore`.
