# Test Status

## Fresh offline C7 qualification for authorized baseline checkpoint — 2026-09-22

| Scope | Actual result | Notes |
|---|---:|---|
| C7 focused | PASSED — 35 | `PYTHONPATH=src .venv/Scripts/python.exe -m pytest -q tests/test_conversation_interpretation.py`; injected test adapter only, not live inference. |
| Selected C1–C6 conversation/identity/auth regression | PASSED — 107; SKIPPED — 5 | Explicit selected modules including C1–C6 unit tests, identity/phone/auth tests, and PostgreSQL-gated conversation integrations; no DB URL supplied. |
| Full no-DB suite | PASSED — 142; SKIPPED — 20 | `PYTHONPATH=src .venv/Scripts/python.exe -m pytest -q`; all 20 skips DB-gated. |
| Compile/import | PASSED | `.venv/Scripts/python.exe -m compileall -q src/alrifai/conversations`. |
| PostgreSQL | NOT REQUIRED for C7 | No C7 persistence/migration; no database was used or changed. Historical C1–C6 PostgreSQL results were not rerun here. |
| Live model inference | NOT RUN / UNVERIFIED | No approved route is established yet. |
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
