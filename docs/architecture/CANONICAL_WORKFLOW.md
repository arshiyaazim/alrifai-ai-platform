# CANONICAL WORKFLOW

## Goal
Converge both message-driven and form-driven business entry points onto one canonical business engine.

## Canonical model
Message path and form path should both become:

`Entry → Normalization → Validation → Canonical Domain Service → Transaction → Database → Audit/Event`

## Canonical flow

### Messaging
`Inbound WhatsApp / Messenger / admin relay → bridge event → normalization → identity resolution → intent validation → canonical business service → transaction + DB writes + audit → outbound confirmation`

### Frontend form
`Form submission → API route → request validation → identity resolution → canonical business service → transaction + DB writes + audit → response payload`

## Shared canonical steps
1. Accept raw input
2. Normalize phone, names, identifiers, and IDs
3. Resolve canonical person/employee/client/applicant identity
4. Validate business invariants
5. Call the canonical domain service
6. Commit DB transaction
7. Emit business event + audit log
8. Return final response or delivery confirmation

## Existing Fazle-Core influences
The current Fazle-Core system already contains useful building blocks for this design:
- `core/modules/identity_brain/__init__.py` for identity resolution and normalization
- `core/modules/message_router/__init__.py` for inbound dispatch
- `core/modules/bridge_poller/__init__.py` for dedupe and source handling
- `core/modules/admin_employees/__init__.py` for employee creation and FPE seeding
- `core/modules/attendance/routes.py` for validation-driven form entries
- `core/modules/fazle_payroll_engine/routes.py` for business rule enforcement and review paths
- `core/modules/escort_roster/routes.py` for operational workflow and approval flows

## Required design rule
Do not duplicate business logic by re-implementing equivalent logic in both message handlers and form handlers. Both must funnel into a single canonical service.

## Safe canonical service boundary
Examples of canonical services:
- `EmployeeService.create_employee(...)`
- `ApplicantService.submit_application(...)`
- `AttendanceService.record_attendance(...)`
- `PayrollService.process_payout(...)`
- `ClientService.upsert_client(...)`
- `MessagingService.ingest_conversation_event(...)`

These should be domain-scoped and used by both interfaces.

## Final recommendation
Build the new platform around a single canonical business layer, with message and UI as inbound adapters only.
