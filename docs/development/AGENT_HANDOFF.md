# Agent Handoff

**Date:** 2026-09-21
**Repository:** `D:\apps\alrifai-ai-platform`
**Branch:** `feat/windows-local-dev`
**HEAD:** `c44a932b1291fc6901c80bd6a2944198727da0d` before this milestone checkpoint

## Completed this session

- Audited canonical ownership for the FastAPI app, authentication, Docker/Open WebUI, startup scripts, tests, migrations, provider metadata, and development documentation.
- Verified read-only VPS DNS, Nginx, TLS, Tailscale, Docker, 9Router, Ollama, and Windows reachability. `alrifai.iamazim.com` resolves to the VPS but has no Nginx block or certificate coverage.
- Configured Windows Tailscale Serve locally (no VPS change) for the private VPS-to-Windows path: AL-RIFAI on `/` and Open WebUI on `/open-webui`.
- Added same-origin Open WebUI iframe support and explicit production startup overrides in existing canonical files.
- VPS Nginx/certificate work was not performed because `azim` has no passwordless sudo; exact error: `sudo: a password is required`.

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

1. Read `AGENTS.md`, the master architecture, `CURRENT_STATE.md`, `ACTIVE_TASK.md`, `BLOCKERS.md`, and `ARCHITECTURE_DECISIONS.md`.
2. Inspect the worktree before editing; existing uncommitted work is intentional.
3. Set `ALRIFAI_DATABASE_URL` to the currently verified isolated local database and run `scripts/start-alrifai-web.ps1` for local web work.
4. Use `/owner/account` for Owner self-management; password changes require the current password. Administrative resets require a fresh Owner session.
5. Keep legacy inspection read-only and use `/home/azim/core` only as evidence.
6. Authenticated web login lands on `/home`, which embeds the local Open WebUI service at `127.0.0.1:8502`; `/admin` is limited to OWNER/ADMIN and `/owner` remains OWNER-only.
7. Open WebUI v0.11.3 is locally pulled and healthy. Its local-only auth is disabled; AL-RIFAI authentication gates `/home`. The first boot may download the embedding model before becoming healthy.
8. For a public deployment, start the app with `-AlrifaiEnvironment production -OpenWebUIUrl /open-webui/`; do not expose Windows PostgreSQL, Open WebUI, Ollama, or 9Router directly.
9. The next authorized VPS step is an isolated `alrifai.iamazim.com` Nginx server block and certificate using the existing `/var/www/certbot` webroot pattern, followed by `nginx -t`, reload, and verification of existing domains.
10. Do not enable hiring or apply V006 to any database other than the approved isolated local test database without separate owner approval.
