# AL-RIFAI Agent Instructions

This repository is governed by [`docs/architecture/MASTER_ARCHITECTURE.md`](docs/architecture/MASTER_ARCHITECTURE.md), which contains the owner-provided Master Project Architecture Constitution. It is the single authoritative architecture document for AL-RIFAI.

## Required session initialization

Before implementation, every agent must:

1. Confirm the repository path, branch, and HEAD.
2. Inspect `git status` and preserve all existing work.
3. Read `docs/architecture/MASTER_ARCHITECTURE.md`.
4. Read `docs/development/CURRENT_STATE.md`, `docs/development/ACTIVE_TASK.md`, `docs/development/BLOCKERS.md`, `docs/development/TEST_STATUS.md`, and `docs/development/AGENT_HANDOFF.md`.
5. Read applicable architecture decisions in `docs/architecture/ARCHITECTURE_DECISIONS.md`.
6. Inspect relevant code, schema, tests, and reports.
7. Check whether the requested work is already partially implemented.
8. If the capability exists in legacy Fazle-Core, perform a targeted read-only audit before substantial implementation.

Do not treat an agent report as proof. Verify the current repository state.

## Authority and continuity

Use this precedence:

1. Current owner decisions.
2. `docs/architecture/MASTER_ARCHITECTURE.md`.
3. Approved architecture decision records.
4. Approved business rules.
5. Verified AL-RIFAI implementation and tests.
6. Verified legacy behavior.
7. Historical reports and assumptions.

When documents conflict, record the conflict and follow the higher-authority source. Update the continuity documents after meaningful work so another agent can resume without chat history.

## Boundaries

- Preserve uncommitted work; never reset, clean, overwrite, or discard it.
- Keep messaging and frontend entry paths converged on shared domain services.
- Do not create competing services, schemas, MCP tools, routers, or auth systems without checking existing components first.
- Legacy Fazle-Core inspection is read-only. Do not alter its code, database, services, credentials, webhooks, or WhatsApp bridges.
- Do not modify production, VPS services, bridge routing, 9Router, providers, credentials, or database schemas without explicit owner authorization.
- Do not run migrations or destructive tests against business-data databases.
- Caller-supplied person IDs, role flags, MCP descriptions, prompts, and frontend visibility are not authorization proof.
- Privileged operations fail closed when trusted authorization is unavailable.
- Never expose credentials, tokens, cookies, or secret values in files, output, or handoffs.
- Do not commit or push unless separately authorized.

## Verification and handoff

Distinguish implemented, locally verified, unverified, blocked, and production-verified behavior. Run focused tests and `git diff --check` for changes. Update `docs/development/AGENT_HANDOFF.md`, `CURRENT_STATE.md`, `ACTIVE_TASK.md`, `BLOCKERS.md`, and `TEST_STATUS.md` when their facts change.

Instruction files belonging to the legacy repository are reference material only. AL-RIFAI agents must follow this file and the master architecture, not legacy runtime conventions.
