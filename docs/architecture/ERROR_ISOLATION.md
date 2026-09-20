# ERROR ISOLATION

## Design goals
- Make failures traceable to a domain
- Avoid unrelated restarts or redeploys
- Keep correlation IDs consistent across workflows
- Separate infrastructure failure from business validation failure

## Domain identifiers
Use stable prefixes:
- `IDENTITY-*`
- `COMM-*`
- `BUSINESS-*`
- `AI-*`
- `DATA-*`
- `PLAT-*`

Examples:
- `COMM-MSG-001`
- `IDENTITY-MATCH-002`
- `BUSINESS-PAYROLL-003`
- `DATA-IMPORT-004`
- `PLAT-HEALTH-005`

## Error code structure
`<DOMAIN>-<SUBSYSTEM>-<NUMBER>`

Example:
- `COMM-MSG-001` = message bridge ingestion failure
- `IDENTITY-MATCH-002` = identity match failed or ambiguous
- `BUSINESS-PAYROLL-003` = payroll processing validation failure

## Correlation IDs
Every message and form request should generate a correlation ID propagated through:
- API request
- domain service call
- DB transaction
- event emission
- audit log
- outbound messaging

## Log fields
Required fields:
- `correlation_id`
- `domain`
- `module`
- `service`
- `operation`
- `actor_id`
- `source`
- `status`
- `error_code`
- `retryable`
- `tenant` (if applicable)

## Health model
Use three health layers:
- Service health: runtime process / dependency health
- Tool health: specific worker/bridge/parser capability
- Module health: domain-level readiness

Examples:
- `service=communications` -> healthy/unhealthy
- `tool=whatsapp-bridge` -> degrade/warn
- `module=identity-resolution` -> healthy or degraded

## Structured exceptions
Use a typed exception model with:
- `error_code`
- `domain`
- `source`
- `retryable`
- `message`
- `details`
- `correlation_id`

No module should swallow unrelated failures silently.

## Failure isolation recommendation
The system should isolate by domain boundary, not by database table.
- communications fails without taking down payroll
- identity resolution fails without disabling form submission if the feature is isolated and degraded
- AI classification errors should not block core business writes when the core event is still valid

## Safe deployment advice
Do not promise independent deployment for every folder unless separate service boundaries clearly exist. The recommended pattern is modular monolith with bounded domain modules, not isolated deployables for every table.
