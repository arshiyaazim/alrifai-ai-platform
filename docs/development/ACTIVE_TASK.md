# Active Development Task

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
