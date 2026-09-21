# ADR-003B: AL-RIFAI Trusted Authentication and Authorization

**Status:** Proposed — owner approval required
**Date:** 2026-09-21
**Scope:** Platform-wide authorization for message-driven, frontend-driven, domain-service, and MCP workflows.

## Context

AL-RIFAI currently has canonical `persons` identity and identity-aware applicant/employee services, but no trusted authentication or authorization mechanism. The hiring operation therefore fails closed. A caller-supplied `admin_actor_id`, person existence, client role flag, prompt, or generated tool call is not authorization proof.

The current AL-RIFAI schema has no role, permission, credential, session, or authenticated-principal tables. No migration is authorized by this audit.

Read-only inspection of Fazle-Core at `/home/azim/core` found:

- `fazle_admins` with active/disabled status and hashed API/login credentials.
- `fazle_roles`, `fazle_admin_roles`, and role levels used by `modules/rbac`.
- `shared/auth_deps.py` and `app/main.py` API-key dependencies.
- Command-to-required-role enforcement through `rbac.check_permission()`.
- Admin relay authorization requiring RBAC superadmin, exact configured Admin phone, and trusted `source_bridge`.
- Bridge 2 self-chat handling based on transport provenance and `is_from_me`, not message text alone.
- Frontend pages commonly storing `X-Internal-Key` in browser `localStorage`.
- AI/Hermes actions protected by a mixture of RBAC, authority lanes, proposal approval, and channel gates.

These patterns are useful evidence, but legacy implementation contains multiple duplicated identity lists and a broad internal-key bypass that must not become AL-RIFAI's permanent architecture.

## Decision proposal

AL-RIFAI should implement one platform authorization policy with channel-specific authentication adapters and a shared trusted actor context.

## Task 03B-01 owner decision

The Owner has approved a highest-authority Owner/Admin business requirement. The Owner must be a distinct principal type, authenticated through a trusted server-side mechanism with high assurance, and must receive all defined platform capabilities independently of delegated permissions. This task implements only the pure contract and policy semantics. It does not create credentials, bootstrap an account, persist principals, or enable any workflow.

### Trusted actor context

After authentication, adapters produce a server-created immutable context containing:

- AL-RIFAI principal ID and optional canonical `person_id`.
- Authentication method and credential/session reference, never the secret.
- Effective roles and permissions, resolved server-side.
- Channel and source identity, such as frontend session, bridge identifier, or MCP service identity.
- Authentication time, correlation ID, and assurance level.

Domain services receive this context for privileged operations. They must not accept authorization solely as `admin_actor_id`, role text, or a caller-supplied boolean.

### Policy enforcement

- Deny by default.
- Enforce authorization at the domain-operation boundary, not only in frontend routes or MCP metadata.
- Resolve roles and permissions centrally and record the policy decision.
- Separate authentication, identity resolution, authorization, business validation, and audit attribution.
- Keep owner/superadmin/admin distinctions explicit; do not infer privileges from a person's existence or employment status.
- Require fresh authorization for sensitive operations where appropriate.

### Message-driven workflows

1. Ingest and persist the raw message with trusted transport provenance.
2. Authenticate the channel/source and resolve the sender identity.
3. Reject ambiguous or unverified identity for privileged actions.
4. Bind Admin relay permissions to both authenticated actor and approved channel/control context.
5. Pass the trusted actor context into the shared domain service.
6. Record actor, channel, source message, policy decision, business outcome, and correlation ID.

Bridge 2 self-chat may be supported as an adapter-specific verified channel, but `is_from_me`, sender phone, bridge name, and group/direct-chat constraints must be checked as independent provenance facts. Message text must never grant authority.

### Frontend-driven workflows

1. Authenticate the frontend request through a server-validated session or approved credential mechanism.
2. Resolve the authenticated principal and effective permissions server-side.
3. Pass the same actor context to the shared domain service used by messaging.
4. Treat UI visibility as convenience only; backend policy remains authoritative.

Browser-stored raw API keys are not the preferred final design. If API keys are retained for controlled service use, store only hashes, scope them, support revocation/rotation, and avoid treating one universal internal key as unrestricted human authority.

### MCP and AI authorization

MCP tools are capability adapters, not principals. The MCP gateway must authenticate the calling service/user context and inject the trusted actor context. The model's tool call is an untrusted request.

- Tool descriptions and system prompts never grant permission.
- A model cannot select an Admin actor ID or role.
- Read, draft, validate, write, and admin capabilities are explicitly scoped.
- Sensitive writes require domain authorization and, where policy requires, explicit human confirmation or one-time approval.
- Tool calls must produce audit records with the real authenticated actor and service identity.

### First target: hiring

The first implementation target is to replace the current fail-closed placeholder with:

- authenticated Admin context;
- an authorization decision requiring the approved hiring permission;
- applicant row locking and identity-aware employee reuse/reactivation;
- atomic applicant/employee/audit/event transaction;
- idempotency and concurrent-request tests;
- rejection of arbitrary person IDs and model-generated authority claims.

Hiring must remain disabled until this context is implemented and verified.

## Alternatives considered

### Reuse Fazle-Core role tables at runtime

Rejected as the permanent design. It creates runtime coupling to the legacy application and database, conflicts with AL-RIFAI independence, and would make cutover and authorization ownership unclear. Legacy RBAC remains read-only evidence.

### Accept `admin_actor_id` from callers

Rejected. A UUID identifies an entity but does not authenticate or authorize the caller.

### Separate authorization logic per channel

Rejected. It causes policy drift between WhatsApp, frontend, background jobs, and MCP. Adapters may authenticate differently, but all must produce the same policy context and call shared domain services.

### One universal internal key as owner authority

Rejected for human and AI workflows. A service credential may exist for controlled internal calls, but it must be scoped, attributable, revocable, and distinct from a human Admin identity.

## Schema and migration implications

The likely minimum AL-RIFAI persistence model requires owner-approved tables or equivalent structures for:

- authenticated principals linked to `persons` where applicable;
- credential/session metadata and revocation state;
- role assignments and permission definitions;
- channel/service identities and source bindings;
- authorization decisions or audit references;
- optional approval grants with one-time consumption and idempotency.

No schema change is selected or executed by this ADR. Before migration, inspect existing data, define bootstrap ownership, password/key handling, rollback, and uniqueness/concurrency requirements.

## Security boundaries

- Legacy Fazle-Core remains read-only.
- No production or VPS changes.
- No bridge, webhook, provider, or credential changes.
- No privileged operation is enabled by an AI model.
- No authorization is inferred from names, phone numbers, employment status, or frontend state.
- Audit attribution must use the authenticated actor context, not free-form caller input.

## Implementation sequence

1. Owner approves the principal, credential, role, and permission model.
2. Define the trusted actor context and policy interfaces with pure unit tests.
3. Define the minimum schema/migration plan; obtain separate migration approval.
4. Implement one authentication adapter and server-side policy resolver.
5. Integrate hiring while keeping the fail-closed guard until end-to-end authorization tests pass.
6. Add frontend and messaging adapters using the same domain service.
7. Add MCP gateway context propagation and negative authorization tests.
8. Expand the pattern to other privileged domains.

## Required owner decisions

- Authoritative Admin/Super Admin bootstrap and recovery process.
- Role and permission matrix for all listed actor classes.
- Accepted frontend authentication mechanism.
- Accepted messaging identity assurance and Bridge 2 control-channel policy.
- Whether AI service identities can propose, draft, or execute each operation.
- Minimum schema and migration strategy.
- Approval/confirmation requirements for hiring, payroll, finance, and external messaging.
