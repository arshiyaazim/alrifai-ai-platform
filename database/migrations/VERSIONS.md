# AL-RIFAI Database Migration Versions

## Versioning Scheme
- `V001__identity_foundation.sql` — Core identity tables (persons, identifiers, phones, aliases, contact_methods, payout_accounts, external_platform_ids)
- `V002__business_entities.sql` — employees, applicants, clients
- `V003__audit_and_events.sql` — business_events, audit_log, provenance_records
- `V004__domain_extensions.sql` — Attendance, Payroll, Billing domain tables
- `V005__MCP_and_scheduler.sql` — Task registry, MCP tool registry

Each migration has:
- Up SQL
- Down SQL (rollback where supported)
- Provenance tracking

`V006__authentication.sql` adds trusted principals, Argon2id credentials,
server sessions, roles, password resets, and authentication audit attribution.
It is approved only for the isolated local development database.

`V007__conversations_identity.sql` adds the unified conversation/thread and
canonical-message relationship foundation plus source-account-scoped platform
identity uniqueness for C2. It is approved only for the isolated local
development database; it does not activate channels or Hermes.

`V008__conversation_topics.sql` adds restart-safe C4 topic state and immutable
topic transition history. It is approved only for isolated local qualification;
it does not implement semantic classification, Hermes, or outbound behavior.
