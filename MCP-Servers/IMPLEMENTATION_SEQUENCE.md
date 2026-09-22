# Future Implementation Sequence

This is a future plan only. No phase is implemented by this documentation task.

## Phase A — Shared contracts and read-only queries

Prerequisites: owner approval of MCP ADR, trusted actor propagation, canonical message/identity contracts. Define capability classes, correlation/idempotency envelopes, provenance import boundaries, and read-only legacy connector tests. Keep all legacy writes offline.

## Phase B — Recruitment

Prerequisites: AL-RIFAI applicant service, canonical identity, role/application state machine. Import candidate history with provenance; verify message/form equivalence, duplicate identity review, and applicant-to-workforce handoff. Mutations remain behind approval until tested.

## Phase C — Workforce

Prerequisites: employee uniqueness/concurrency decision, attendance policy, identity links. Reconcile WBOM/FPE employees; test lifecycle, attendance idempotency, inactive reactivation, and assignment history. Keep financial ledger writes offline until Finance is ready.

## Phase D — Finance & Payroll

Prerequisites: trusted Accountant/Owner authorization, payroll rules, ledger schema, idempotency constraints, payment delivery event contract. Implement calculation/review before cash mutation; test duplicate delivery, reversal, approval, period closure, and failed outbound behavior. Do not connect live payment execution until validated.

## Phase E — Operations & Clients

Prerequisites: escort state machine, client/vessel identity decisions, release/completion semantics, rate/billing boundary. Import programs and rosters read-only first; test assignment/replacement/release and client instruction provenance. Financial settlement remains a Finance event.

## Phase F — Conversations & AI dispatch

Prerequisites: canonical message model, channel adapters, media/provenance, domain contracts, bounded Hermes role. Start with read/search/context and draft extraction. Test bridge redelivery, source attribution, duplicate outbound prevention, and ambiguous identity. Keep AI writes disabled until domain approvals pass.

## Phase G — Platform / Admin aggregation

Prerequisites: all domain capability contracts, trusted auth integration, audit/event query model. Add cross-domain reports, approval queues, and controlled orchestration. Test least privilege and fail-closed behavior. Do not expose unrestricted SQL or legacy role authority.

## Rollout boundary

Each phase must support shadow/read-only comparison against Fazle-Core before any AL-RIFAI write or cutover. Production routing, bridge ownership, legacy writes, and financial execution remain offline until separately authorized and verified.
