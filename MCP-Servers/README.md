# AL-RIFAI MCP Architecture Workspace

**Status:** Documentation-only audit and design. No MCP runtime is implemented here.

This workspace defines a consolidated six-server MCP boundary for the future AL-RIFAI platform. It does not create servers, tools, schemas, Docker services, migrations, or an alternative authentication system.

## Authority and evidence

- AL-RIFAI architecture authority: [`../docs/architecture/MASTER_ARCHITECTURE.md`](../docs/architecture/MASTER_ARCHITECTURE.md).
- Canonical workflow: [`../docs/architecture/CANONICAL_WORKFLOW.md`](../docs/architecture/CANONICAL_WORKFLOW.md).
- Legacy evidence: [`FAZLE_CORE_AUDIT.md`](FAZLE_CORE_AUDIT.md), freshly rechecked read-only against `/home/azim/core` at the recorded VPS HEAD.
- Fresh VPS recheck status: complete. The audit verified the running Fazle-Core service, all three bridge services, source modules/routes, migrations, and the `ai-postgres` Fazle schema without changing VPS state.
- Current Owner authentication remains frozen; MCP design does not alter it.

Evidence labels used throughout:

- `VERIFIED_LIVE`: directly rechecked against a running system during this task.
- `VERIFIED_SOURCE`: supported by inspected source/schema evidence already present in repository audit records.
- `DOCUMENTED_ONLY`: recorded by prior repository reports but not rechecked in this task.
- `INFERRED`: design conclusion derived from evidence.
- `UNKNOWN`: requires a future authorized read-only verification.

## Proposed servers

1. [Recruitment MCP](recruitment/README.md)
2. [Workforce MCP](workforce/README.md)
3. [Finance & Payroll MCP](finance-payroll/README.md)
4. [Conversations & AI MCP](conversations-ai/README.md)
5. [Operations & Clients MCP](operations-clients/README.md)
6. [Platform / Admin MCP](platform-admin/README.md)

The count is intentionally six. Identity, authorization, audit, and persistence remain shared AL-RIFAI platform services, not additional table-oriented MCP servers. Fresh live evidence continues to validate six servers.

## Non-goals

- No runtime source code, `src/` tree, Docker service, migration, deployment, VPS operation, or database change.
- No direct legacy database writes.
- No business logic duplicated in MCP tool handlers.
- No MCP tool grants authority that the trusted server-side authorization context does not already grant.
