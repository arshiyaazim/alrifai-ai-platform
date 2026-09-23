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

# Active Development Task

## Reconciled current checkpoint — 2026-09-23

Current repository checkpoint: `285ef82fe0c6b6c37735c05e763f2c6ba1331c5a`. C7 remains PARTIAL, not COMPLETE: authenticated 9Router live route PASS; five Section 24 cases are `SAFE_ABSTAIN`; twelve unchanged C5/C6 baseline failures remain. No production deployment, existing database migration, service restart, C8, or C9 work occurred.

## Live C7 qualification completed — owner checkpoint pending (2026-09-22)

Status: PARTIAL pending owner review, not blocked on 9Router. Host-capable execution confirmed the existing `9router` container and HTTP 200 health. The canonical server-side `.env` loader authenticated `nine-general/general` successfully without exposing the credential. Section 24 completed with PASS/SAFE_ABSTAIN outcomes recorded in `CURRENT_STATE.md`; Section 25 live auth-failure and offline failure-matrix checks are recorded there.

Focused C7/AI-runtime tests: 67 passed. Selected C1–C7 regression: 70 passed; confirmed relationship subset: 2 passed. Full non-integration regression: 162 passed / 12 unchanged fixed-clock C5/C6 failures. No C5 lifecycle changes, restart, Docker change, migration application, outbound message, C8, C9, commit, or push.

Next action: owner review of the uncommitted checkpoint. Do not commit or push until explicitly approved.

## Recovery handoff — 2026-09-22 (VPS)

Status: PARTIAL / BLOCKED at live qualification. The worktree is preserved on `feat/windows-local-dev` HEAD `9b5ffcc`; no commit or push was made. Proven C5 timestamp drift was reverted only in `instructions.py`; intended C7 and AI-runtime/settings work remains. `scripts/dev-start.sh` loads the ignored repository `.env` server-side without echoing or exposing values.

Offline gates: focused C7/runtime/settings 67 passed; selected C1–C7 regression 70 passed; confirmed-current-employee fixture 2 passed; compile, diff, migration static checks, and secret scan passed. Full non-integration regression is 162 passed / 12 known fixed-clock C5/C6 failures.

Live Section 24/25 cannot proceed because `127.0.0.1:20129` has no listener. Do not start or reconfigure `/home/azim/9router` without separate owner authorization. The next action is owner review of this checkpoint and, if authorized, bringing up the already-approved development gateway before rerunning live qualification.

## Live C7 qualification in progress — credential gate cleared (2026-09-22)

Status: authenticated transport PASS; C7 live `interpreted` on sec-24 core suite; prompt-contract fix applied (uncommitted) with offline 66 passed. Next: sec-24 remainder (multi-turn, anaphora, NID, employee-claim, CONFIRMED fixture) + sec-25 live spot-checks + full regression, then owner-authorized checkpoint only if all gates pass. C8/C9 NOT STARTED. No restart performed (no AL-RIFAI web process on VPS); no production/legacy change.

## OPENCODE_C7_TASK — VPS-native C7 unblock + AI model/provider settings (2026-09-22, in progress)

Status: implementation + offline/failure qualification complete; live authenticated inference BLOCKED on the dedicated 9Router credential (minimal owner action in BLOCKERS). Next action after credential is placed: configure the canonical gateway via `/admin/ai-settings`, run the sec-24 synthetic live suite + sec-25 failure suite, then checkpoint ONLY if all gates pass. C8/C9 remain NOT STARTED.

## Current authorized sequence — offline C7 checkpoint, then live-route qualification (2026-09-22)

Phase A PASS: offline C7 baseline commit `9b5ffccdfc010c8dd37a13ab75be3c6cadb9c5bb` equals independently verified `origin/feat/windows-local-dev` and expected files are present. Phase B identified private loopback gateways: 9Router at VPS `127.0.0.1:20129`, OmniRoute at VPS `127.0.0.1:20128`; both require valid bearer authorization (missing and invalid probes returned HTTP 401). The existing SSH forward to Windows `127.0.0.1:20130` was verified, then stopped. Phase B remains BLOCKED because no dedicated authorized C7 credential and model/route selection are available locally. No adapter code or live model call was started. Next action requires a dedicated C7 credential made available through an approved local secret mechanism and confirmation of an authorized route/model identifier; then resume C7 only. C8/C9 remain not started.

## Current checkpoint — C7 bounded interpretation (2026-09-22, 14:59 +06:00)

C1–C6 implementation baseline is backed up at `cf71c3b6b3f439003cd1ead0d2f5ce53583cab8c`; latest C6 policy-alignment documentation edits in this worktree are local-only. C7 artifacts were forensically reviewed: MODIFY the existing implementation while keeping the canonical module/test location; harden bounded input, safe typed adapter failure, and current non-illustrative grounding. C7 is PARTIAL pending an approved real adapter/live inference qualification; offline focused tests pass. C7 is local-only/uncommitted/unpushed. C8/C9 are NOT STARTED. No Recruitment Knowledge Hub, reply generation, dispatch, or outbound sending.

## Historical Phase A / pre-C7 task record — superseded above (2026-09-22)

Phase A is C6 qualification and authorized checkpoint backup. C6 unit 25 passed; disposable PostgreSQL 17 integration subset 15 passed; broad DB-enabled suite excluding protected seeded-Owner web-auth fixture 122 passed; full no-DB suite 107 passed/20 skipped. No C6 migration. Remote fetch matched parent `c2852a47323b74c92cd56eaa946e319b4f1d0500` before the checkpoint. C7 must begin only after the C6 checkpoint commit is pushed and remote HEAD/tree are independently verified. No C7 changes are part of the C6 commit.

Phase B, if the Phase A hard gate passes: implement and qualify C7 Hermes Interpretation and Extraction only. Do not build the Recruitment Knowledge Hub; do not implement C8 dispatch, C9 reply generation/outbound delivery, or channel sending. Preserve missing Recruitment knowledge and unconfirmed office address as explicit gaps. C7 is not remotely backed up and must remain uncommitted/unpushed.

**Next task:** Complete C7 live adapter qualification only if an approved route becomes available; otherwise preserve the exact C7 gap and await Owner direction. C8/C9 are NOT STARTED and require explicit Owner approval.

## Previous task checkpoint — C1–C6 policy alignment (2026-09-22)

C1–C6 remain local C6 baseline plus bounded policy alignment; no commit/push. The C6 package now includes positive active-Employee relationship evidence for tone only; all uncertain/applicant/pre-join/inactive cases default to respectful `আপনি`. Canonical specs document authoritative-fact vs guidance/style/example/historical distinction and non-rigid natural conversation. C7 implementation-ready specification is updated but runtime is NOT STARTED — OWNER APPROVAL REQUIRED. Missing Recruitment knowledge source and office-address confirmation are recorded in `BLOCKERS.md`.

**Next proposed task:** C7 — Hermes Interpretation and Extraction.

**C7 status:** NOT STARTED — OWNER APPROVAL REQUIRED.

## Latest checkpoint — 2026-09-22

**Current status:** C5 — Versioned Admin/Owner AI Instruction State and Selection is implemented and locally qualified. C5 work is uncommitted; do not commit or push without separate Owner authorization. The C1–C4 accepted baseline remains backed up at `5859bb178738346d6e5cb8ff41e6247495944b92`.

**Next proposed task:** C6 — Bounded Semantic Context Retrieval.

**C6 status:** NOT STARTED — OWNER APPROVAL REQUIRED. No work may begin automatically.

The confirmed Owner/Admin precedence applies only when instructions conflict on the same subject: effective Owner wins there; instructions about other subjects remain applicable. Same-authority unresolved conflict fails closed. Canonical policy/auth/domain services remain authoritative. The four pre-existing unrelated local edits are preserved; see `CHECKPOINT_MANIFEST.md`.

**Task:** Complete repaired development Owner login and freeze authentication baseline; complete approved Conversations & AI stages through C4
**Status:** Owner authentication baseline completed; Conversations & AI C1–C4 implemented and qualified; development checkpoint saved for Owner break.
**Scope:** Existing login/session contracts, deterministic development database selection, isolated regression coverage, continuity updates, and read-only public-flow verification.

The existing Open WebUI integration, server-side Admin gate, and Nginx-compatible session check are preserved. Open WebUI uses its own `.local-data/open-webui` state. The Owner reports public routing is already configured; earlier deployment-blocker statements are historical.

## Next implementation task

C5 — Versioned Admin/Owner AI Instruction State and Selection. **NOT STARTED — OWNER APPROVAL REQUIRED.** Do not begin during the Owner break.

## MCP documentation checkpoint

The documentation-only Fazle-Core/MCP architecture audit is complete for Owner review in `MCP-Servers/`. It proposes six servers: Recruitment, Workforce, Finance & Payroll, Conversations & AI, Operations & Clients, and Platform/Admin. A fresh read-only VPS audit succeeded through `iamazim`; live service/source/schema evidence is reconciled in `MCP-Servers/FAZLE_CORE_AUDIT.md`. No runtime implementation was started, and the audit is not migration approval.

The Recruitment MCP final implementation specification is now complete at `MCP-Servers/recruitment/FINAL_IMPLEMENTATION_SPEC.md`. It is a documentation-only implementation handoff; runtime MCP work remains prohibited by the attached specification until its listed prerequisites and owner policy decisions are approved.

Owner policy reconciliation is applied: recruitment is year-round and Role-based; terminal rejected/withdrawn Applications are never reopened and repeat attempts create new Applications for the same Person/Applicant; applicant document intake is distinct from Workforce formal employee-document verification. No Owner policy decisions remain for these three items.

At the prior checkpoint, Owner authorization covered Conversations & AI C1 only. The C1 files under `src/alrifai/conversations/` and `tests/test_conversation_models.py` were reconciled against `MCP-Servers/conversations-ai/FINAL_IMPLEMENTATION_SPEC.md` and provide the canonical message/conversation foundations.

C2 is complete. Preflight confirmed canonical identity ownership in `src/alrifai/identity`, central authorization in `src/alrifai/authorization`, existing Person/Applicant/Employee tables, and no existing canonical conversation store. C2 implementation adds deterministic identity/thread resolution and the minimal local-only V007 conversation/platform-scope foundation. V007 was qualified through up/down/reapply on a disposable PostgreSQL 17 target; 11 PostgreSQL integration tests and database invariants passed.

C3 is implemented and locally qualified under Owner authorization. It provides separate deterministic ordering and structural multi-message turn aggregation over C1 messages/C2 threads, with late-arrival re-evaluation, reply/media evidence, hard sender/thread/outbound/time boundaries, and deterministic restart reconstruction. No C3 migration or persistence store was added.

C4 is implemented and qualified. `src/alrifai/conversations/topics.py` provides typed topic contracts, deterministic lifecycle validation, explicit closure/reopening evidence, scoped optimistic concurrency, idempotency, restart-safe PostgreSQL persistence, immutable transition history, and C3 late-arrival safeguards. V008 was qualified up/down/reapply on disposable PostgreSQL 17; C4 PostgreSQL integration passed. C5 and all later stages are not started.

Recruitment conversation correction is also applied: normalized inbound WhatsApp phone and provenance are durable business identity context; employee business-facing ID is the canonical current mobile with historical aliases; Conversations & AI owns ordered semantic conversation state, topic context, and versioned Admin AI instructions.

## Explicitly not authorized by this task

- Schema migrations or database changes.
- Production deployment, external reset delivery, WhatsApp authentication, and MCP actor propagation.
- Public HTTPS configuration until an authorized sudo-capable VPS operation is available.
- Production/VPS changes.
- WhatsApp bridge or webhook routing changes.
- 9Router/provider/credential changes.
- Broad domain implementation.
