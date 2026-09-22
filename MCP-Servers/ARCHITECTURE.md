# Consolidated MCP Architecture

## Decision

Propose six domain-facing MCP servers. Each server is a transport/tool adapter over canonical AL-RIFAI domain services. It is not a database owner, an AI authority, or a replacement for the authenticated API.

The six-server grouping is supported by `VERIFIED_SOURCE` evidence in `docs/audits/DUAL_WORKFLOW_AUDIT.md`: Fazle-Core has recruitment, employee/attendance, payroll/cash, messaging/Hermes, escort/client/billing, and administration concerns, but their current implementation overlaps tables and routes. Splitting by screen or table would reproduce that failure.

## Boundary rules

1. Domain services enforce invariants and authorization; MCP handlers only validate transport shape, attach trusted actor context, and call them.
2. The AL-RIFAI canonical database is authoritative after migration. Fazle-Core is a read-only import/reference source.
3. Identity resolution is shared. A phone, payout number, caller-supplied ID, role flag, prompt, or tool description is not authorization proof.
4. Mutations require a stable idempotency key, an audit event, correlation metadata, and a domain-specific policy decision.
5. AI/Hermes may classify, extract, search, summarize, and prepare drafts. Deterministic services validate and execute mutations.
6. Cross-server calls are explicit domain contracts, not hidden SQL joins or shared mutation logic.
7. READ, DRAFT, VALIDATE, WRITE, and ADMIN permission classes are required. Owner authentication stays governed by the frozen AL-RIFAI baseline.

## Shared platform services, not MCP servers

- Canonical identity and phone normalization.
- Trusted authorization and capability evaluation.
- Transaction and event/audit boundary.
- Provenance/import connector for legacy records.
- Outbox and delivery status for messages.
- Correlation, retry, health, and observability.

## Candidate alternatives rejected

- One MCP per table or UI screen: rejected because the audited legacy system has overlapping `wbom_*`, `fpe_*`, `ops_*`, and `fazle_*` ownership.
- Separate Hermes MCP: rejected; Hermes interpretation and dispatch belong with Conversations & AI, while business mutations remain in domain services.
- Separate Client MCP: rejected; client identity, vessels, assignments, release, and billing context form one Operations & Clients aggregate. Finance owns monetary settlement.
- Broad Platform MCP with unrestricted writes: rejected; it may aggregate approved cross-domain operations but cannot bypass domain authorization.
