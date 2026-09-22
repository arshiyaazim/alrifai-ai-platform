# AL-RIFAI Architecture Decisions and Open Decisions

This register records decisions that future agents must not silently reopen. Decisions marked **OPEN** require owner approval before implementation that depends on them.

## Accepted baseline

### ADR-001 — Modular monolith with bounded domain services

**Status:** Accepted by the Master Architecture Constitution.
Use one independently maintainable AL-RIFAI platform with clear adapters, orchestration, domain services, persistence, AI/MCP, and presentation boundaries. Do not create microservices or one-MCP-per-table abstractions without demonstrated need.

### ADR-002 — Canonical person identity

**Status:** Implemented locally, further hardening open.
`persons.person_id` is canonical for internal Person identity. Names are attributes, phone numbers are contact identifiers for Person resolution, and payout numbers are never identity keys. Owner policy separately makes the designated normalized Bangladeshi mobile the authoritative business Employee ID; ambiguous matches require review and internal UUID employee-record keys remain technical only.

### ADR-003 — Privileged operations fail closed

**Status:** Accepted and enforced for current hiring path.
The existence of a person record or caller-supplied actor ID is not authorization. Hiring remains disabled until a trusted server-side Admin authorization context is available.

### ADR-009 - Owner full-authority semantics

**Status:** Owner business requirement accepted; foundation implemented, authentication pending.
The Owner is a distinct trusted principal type with high-assurance authentication and full platform capability semantics. Delegated user permissions cannot restrict the Owner. The Owner foundation is implemented in `src/alrifai/authorization/policy.py`; credential verification, principal persistence, bootstrap, frontend login, WhatsApp authentication, and MCP integration remain pending.

### ADR-010 — Owner/Admin AI instruction conflict precedence

**Status:** Accepted by explicit Owner decision; implemented for C5.

Evaluate trusted issuer, central `MANAGE_CONVERSATIONS` authorization, lifecycle/effective window, expiry/revocation/supersession, and scope before precedence. Resolve applicable guidance per subject: an effective Owner instruction wins over a conflicting Admin instruction on that same subject only. Instructions on unrelated subjects remain applicable. Same-authority instructions use scope specificity, priority, effective time, and version ordering; unresolved equal-rank conflicts fail closed with selection evidence. This rule does not bypass central authorization, canonical business policy, or protected domain-service mutation rules. An external message claim cannot establish privileged issuer authority.

Implemented in `src/alrifai/conversations/instructions.py`, persisted in V009. C5 does not implement semantic classification, Hermes, dispatch, or reply generation.

## Open decisions

### ADR-004 — AL-RIFAI authentication and authorization

**Status:** OPEN / BLOCKER.
See the proposed audit record [`ADR-003B-AUTHORIZATION.md`](ADR-003B-AUTHORIZATION.md). Decide the trusted actor source, role/permission model, session/API authentication, and service-layer enforcement for Owner, Super Admin, Admin, office staff, operator, accountant, employee, client, applicant, and AI identities. Do not create a parallel role system before this decision.

### ADR-005 — Database uniqueness and identity concurrency

**Status:** OPEN.
Determine approved constraints or transaction strategy for unique employee-to-person association, normalized phone sharing, and database-level business-event idempotency. No migration has been created or executed.

### ADR-006 — Canonical message storage

**Status:** OPEN.
Define tables and ownership for inbound/outbound raw messages, external IDs, conversations, media references, delivery state, processing state, actor classification, and correlation/causation IDs. Preserve raw evidence separately from interpreted facts.

### ADR-007 — MCP boundaries and permissions

**Status:** OPEN.
Define domain tool groups, READ/DRAFT/VALIDATE/WRITE/ADMIN permissions, trusted actor propagation, confirmation requirements, audit behavior, and whether tools call domain services directly or through an orchestration layer.

### ADR-008 — Cross-channel service reuse

**Status:** Accepted principle; implementation pending.
Messaging, frontend, MCP, and background workers must call the same domain services. Channel adapters may validate transport-specific input but may not duplicate business rules.
