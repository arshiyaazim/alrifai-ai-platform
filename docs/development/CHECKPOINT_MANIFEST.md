# Task 03B Checkpoint Commit Manifest

**Status:** Proposed only; nothing staged or committed.
**Base HEAD:** `e8b67e0e1af844a4970755858c5a3a253e874d3d`
**Branch:** `feat/windows-local-dev`

This manifest classifies the current dirty worktree. It is intentionally explicit; do not use `git add -A`.

## 1. Architecture and continuity

Proposed inclusion:

- `AGENTS.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/SESSION_HANDOFF.md`
- `docs/architecture/MASTER_ARCHITECTURE.md`
- `docs/architecture/ARCHITECTURE_DECISIONS.md`
- `docs/architecture/ADR-003B-AUTHORIZATION.md`
- `src/alrifai/authorization/__init__.py`
- `src/alrifai/authorization/policy.py`
- `tests/test_authorization_policy.py`
- `docs/architecture/LEGACY_GAP_REGISTER.md`
- `docs/development/ACTIVE_TASK.md`
- `docs/development/AGENT_HANDOFF.md`
- `docs/development/BLOCKERS.md`
- `docs/development/CURRENT_STATE.md`
- `docs/development/CHECKPOINT_MANIFEST.md`
- `docs/development/TEST_STATUS.md`

## 2. Task 01 — phone normalization

- `src/alrifai/__init__.py` — package scaffolding; shared with later tasks.
- `src/alrifai/identity/__init__.py` — identity package export.
- `src/alrifai/identity/phone_normalizer.py`
- `tests/test_phone_normalizer.py`

## 3. Task 02 — identity resolution and PostgreSQL

- `src/alrifai/identity/identity_resolver.py`
- `tests/test_identity_resolution.py`
- `tests/test_identity_resolver.py`
- `tests/integration/test_identity_resolver_postgres.py`
- `requirements.txt`

## 4. Task 03A — applicant, employee, and security correction

- `src/alrifai/applicant/__init__.py`
- `src/alrifai/applicant/applicant_service.py`
- `src/alrifai/employee/__init__.py`
- `src/alrifai/employee/employee_service.py`
- `src/alrifai/services/__init__.py`
- `src/alrifai/services/_common.py`
- `tests/test_employee_service_security.py`
- `tests/integration/test_core_services_postgres.py`

## 5. Windows local development

- `.gitignore`
- `docker-compose.yml`
- `docs/development/LOCAL_WINDOWS_SETUP.md`

## 6. Copilot and 9Router local work

- `docs/development/9ROUTER_LOCAL_SETUP_REPORT.md`
- `docs/development/COPILOT_MULTI_PROVIDER.md`
- `scripts/copilot-providers.json`
- `scripts/select-copilot-provider.ps1`
- `scripts/start-9router-tunnel.ps1`

## 7. Mixed or unclassified

No source file currently contains visibly mixed hunks that require hunk-level staging. The package initializers are shared scaffolding and should be reviewed with the implementation files. The historical reports may contain stale verification claims; preserve them as evidence and rely on current-state documents for status.

## Proposed commit boundary

The safest checkpoint is a reviewed multi-scope snapshot with the explicit files above, preferably split into logical commits for architecture, implementation, Windows development, and Copilot/9Router work. If one checkpoint commit is required, stage only this manifest's file list after owner approval. Do not include `.env`, local data, caches, credentials, or generated `__pycache__` files.
