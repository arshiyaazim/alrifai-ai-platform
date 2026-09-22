# Current Blockers and Required Decisions

| Blocker | Impact | Required action | Owner approval |
|---|---|---|---|
| Trusted Admin authorization absent | Hiring must fail closed; authorized hiring cannot be verified | Approve credential/bootstrap, principal persistence, and trusted actor adapter design | Required |
| `employees.person_id` lacks uniqueness | Duplicate employee associations remain possible under future paths | Approve constraint/transaction strategy and migration plan | Required |
| Normalized phone values may be shared | Cross-request person creation needs an explicit concurrency policy | Approve shared-phone and locking/constraint policy | Required |
| `business_events.idempotency_key` lacks unique constraint | Database-level exactly-once effects are not guaranteed for every caller | Approve idempotency contract and schema strategy | Required |
| Canonical message model absent | Messaging cannot yet converge safely on domain services | Approve message storage and ownership design | Required |
| MCP runtime and trusted actor integration absent | AI tools cannot yet be safely exposed for business mutations | Review `MCP-Servers/` six-server documentation; approve domain grouping, permission classes, actor propagation, and confirmation policy before implementation | Required |
| Recruitment MCP prerequisites absent | Role/vacancy policy service, joining persistence, trusted Recruitment/Workforce handoff, document references, and durable idempotency are not yet implemented | Approve the final Recruitment specification and prerequisites; keep runtime activation disabled | Required |

## Task 03B authorization audit decisions pending

See [`ADR-003B-AUTHORIZATION.md`](../architecture/ADR-003B-AUTHORIZATION.md). No authentication integration or migration was created by this task. Hiring remains fail-closed.

Task 03B-01 adds only pure policy contracts. It does not resolve the Owner credential, bootstrap path, password reset flow, or authentication storage.

The preserved PostgreSQL container `alrifai-identity-verify-02c` now holds the authoritative development Owner. It must not be removed, recreated, reset, or subjected to destructive public-schema test cleanup. The 2026-09-21 Owner instruction selects it as the stable development auth database, superseding earlier disposable/test-only assumptions.
# Task 03B-02 blockers

- Production HTTPS deployment and external email/SMS reset delivery remain pending.
- WhatsApp authentication and MCP trusted actor propagation remain pending.
- Development Owner bootstrap/recovery is complete; no further reset or bootstrap is needed for this task.

V006 was previously applied to this local container. This completion does not authorize migrations to its development schema or any production database. PostgreSQL regressions must use isolated disposable schemas, never the canonical Owner's schema.

## Conversations & AI C4 checkpoint

- C4-specific blockers: **NONE**. V008 was qualified up/down/reapply on a disposable PostgreSQL 17 target, and C4 integration tests passed.
- C5 and later stages are not blocked by an unresolved technical defect; they are intentionally unstarted and require explicit Owner approval.
- The Owner-approved Employee-ID rule remains unchanged: designated normalized Bangladeshi mobile number is the authoritative business Employee ID. C4 does not mutate it.
- No production/VPS database, service, bridge, authentication baseline, or preserved development/auth container was changed.
