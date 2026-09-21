# Current Blockers and Required Decisions

| Blocker | Impact | Required action | Owner approval |
|---|---|---|---|
| Trusted Admin authorization absent | Hiring must fail closed; authorized hiring cannot be verified | Approve credential/bootstrap, principal persistence, and trusted actor adapter design | Required |
| `employees.person_id` lacks uniqueness | Duplicate employee associations remain possible under future paths | Approve constraint/transaction strategy and migration plan | Required |
| Normalized phone values may be shared | Cross-request person creation needs an explicit concurrency policy | Approve shared-phone and locking/constraint policy | Required |
| `business_events.idempotency_key` lacks unique constraint | Database-level exactly-once effects are not guaranteed for every caller | Approve idempotency contract and schema strategy | Required |
| Canonical message model absent | Messaging cannot yet converge safely on domain services | Approve message storage and ownership design | Required |
| MCP boundaries absent | AI tools cannot be safely exposed for business mutations | Approve domain grouping, permission classes, actor propagation, and confirmation policy | Required |

## Task 03B authorization audit decisions pending

See [`ADR-003B-AUTHORIZATION.md`](../architecture/ADR-003B-AUTHORIZATION.md). No authentication integration or migration was created by this task. Hiring remains fail-closed.

Task 03B-01 adds only pure policy contracts. It does not resolve the Owner credential, bootstrap path, password reset flow, or authentication storage.

The preserved disposable PostgreSQL verification container remains local test-only. It must not be removed, recreated, reset, or repurposed without separate owner approval.
# Task 03B-02 blockers

- Production HTTPS deployment and external email/SMS reset delivery remain pending.
- WhatsApp authentication and MCP trusted actor propagation remain pending.
- Actual bootstrap with the Owner-supplied temporary password must be performed
  interactively by the Owner.

The preserved `alrifai-identity-verify-02c` PostgreSQL container remains a
local test-only resource. V006 was applied only after verifying its identity;
no production database was modified.
