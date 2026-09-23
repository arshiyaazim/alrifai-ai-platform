# AL-RIFAI Web Authentication Schema Proposal

**Status:** Proposal only — not approved for migration or execution
**Scope:** Local web authentication foundation for Task 03B-02

## Current limitation

The current AL-RIFAI schema contains canonical `persons`, but no trusted
principal, username credential, password-reset, session, role-assignment, or
authentication-audit persistence. A person ID cannot authenticate a caller and
must not be used as an Owner credential.

The existing authorization ADR requires separate owner approval before adding
or executing authentication schema changes. This document is therefore a
design proposal only. It has not been applied to the preserved PostgreSQL
verification container or any other database.

## Minimum proposed persistence model

The names below are provisional and require owner approval before becoming
migrations.

### `auth_principals`

- server-generated principal ID;
- optional unique `person_id` reference;
- explicit principal type, including `OWNER`;
- account status and timestamps;
- `must_change_password` state;
- constraint allowing at most one Owner principal.

Owner authority is represented by principal type and the central policy, not by
a caller-supplied role, phone number, username, or person ID.

### `auth_password_credentials`

- unique normalized username;
- principal reference;
- password hash and algorithm metadata;
- password-created/changed timestamps;
- failed-attempt and lockout state;
- no plaintext password or reversible secret.

The bootstrap command must prompt interactively, hash in memory, and never
print or persist the temporary password. The final password-hashing algorithm
and dependency must be approved before implementation.

### `auth_sessions`

- server-generated session ID;
- only a hash of the session token;
- principal reference;
- issued, expiry, last-used, and revoked timestamps;
- channel and safe request metadata for audit/correlation.

The browser would receive a Secure, HttpOnly, SameSite session cookie. A raw
session token must not be stored in the database or logs.

### `auth_password_resets`

- one-time reset-token hash;
- principal reference and expiry;
- consumed/revoked timestamp;
- requesting actor/channel and audit correlation.

No delivery claim may be made until an actual delivery provider exists. A local
development recovery flow must be Owner-controlled and separately audited.

### Roles, permissions, and audit

The existing pure policy contract remains authoritative. Persistence may use
role assignments and permission definitions if delegated roles are needed, but
the Owner must bypass delegated restrictions by policy. The existing audit
mechanism must be checked for an actor reference that can represent an
authenticated principal; if it cannot, it needs an approved extension or a
separate authentication-audit table. Every login, logout, failed login,
bootstrap, reset, authorization denial, and privileged action must retain the
trusted actor/correlation context without credential contents.

## Required constraints and transaction rules

- username uniqueness must be case-normalized server-side;
- only one Owner principal may exist;
- public signup may create only an unprivileged pending account;
- disabled/revoked principals cannot create sessions;
- session creation and credential/account status changes are transactional;
- logout and reset-token consumption are idempotent;
- authorization is checked server-side at the domain boundary;
- no AI tool argument can select or create an Owner principal;
- no migration is executed until the target is confirmed as the isolated local
  test database and owner migration approval is recorded.

## Exact approval required before implementation

The owner must approve:

1. the principal/account table model and whether principals may link to
   `persons`;
2. the password-hashing dependency and policy;
3. session lifetime, cookie, lockout, and reset policy;
4. the delegated role/permission persistence model;
5. reuse or extension of the existing audit table;
6. creation and execution of a local-only migration against the preserved
   `alrifai-identity-verify-02c` container;
7. the explicit bootstrap procedure for username `azimpolcu`.

Until these approvals exist, the web login, Owner bootstrap, signup, reset,
and dashboard authorization remain blocked. Hiring remains fail-closed.
