# Legacy Capability and Gap Register

**Status:** Initial verified baseline
**Authority:** Supporting evidence for the Master Architecture Constitution; not an AL-RIFAI implementation specification.

## Legacy repository

The accessible Fazle-Core repository is `/home/azim/core` on the SSH host alias `iamazim`. Read-only inspection confirmed:

- Git repository: `/home/azim/core`
- HEAD: `e76365ecfec1d49df3c32cad866db4f6958098f7`
- Branch: `feat/bridge1-2-conversation-continuity-20260902`
- Working tree: no status output observed during inspection
- Legacy instruction files: `.github/copilot-instructions.md`, `.claude/CLAUDE.md`, `.kilo/kilo.jsonc`
- Relevant legacy areas: `app/main.py`, `modules/bridge_poller`, `modules/identity_brain`, `modules/message_router`, `modules/recruitment_flow`, `modules/admin_employees`

The Windows folder `C:\Users\aslsg\shebabandhu` is not the Fazle-Core repository; it contains `github-models` and unrelated project files. The historical `/home/azim/core` path is therefore the verified legacy source for read-only audits.

## Initial register

| Capability | Verified legacy evidence | AL-RIFAI disposition | Current gap/status |
|---|---|---|---|
| Bridge/message ingestion | `modules/bridge_poller`; prior audit records bridge polling, persistence, and deduplication | PRESERVE and IMPROVE | No AL-RIFAI canonical message store or bridge adapter implemented |
| Identity resolution | `modules/identity_brain`; historical audit identifies role/contact/employee resolution | PRESERVE, SIMPLIFY | Phone normalizer and deterministic resolver implemented locally; shared-phone and uniqueness decisions remain open |
| Recruitment | `modules/recruitment_flow`; prior audit records recruitment intake and candidate tables | PRESERVE and IMPROVE | Applicant service exists and is locally tested; frontend/message adapters absent |
| Employee creation | `modules/admin_employees` and payroll employee helpers | PRESERVE and REDESIGN | Employee service reuse/reactivation is locally tested; trusted Admin authorization is blocked |
| RBAC/admin | Legacy `modules/rbac`, `shared/auth_deps.py`, and `app/main.py`: hashed API/login credentials, role levels, command checks, and audit rows | REDESIGN independently | AL-RIFAI has no runtime Admin authorization mechanism; do not reuse legacy tables as permanent runtime dependency |
| Conversation history | Legacy audit identifies `fazle_conversations`, `fazle_messages`, and bridge/message tables | PRESERVE and SIMPLIFY | AL-RIFAI canonical message storage is not implemented |
| Outbound delivery | Prior audit records queue and delivery-state paths in `app/main.py` | PRESERVE and IMPROVE | No AL-RIFAI outbound adapter or durable delivery state |
| Attendance | Legacy `modules/attendance` and `ops_attendance` evidence | PRESERVE, domain-specific | Not implemented in AL-RIFAI |
| Escort operations | Legacy escort roster/lifecycle modules and tables | PRESERVE and REDESIGN | Not implemented; state machine requires owner decisions |
| Payroll/finance | Legacy payroll engine and `fpe_cash_transactions` evidence | PRESERVE and IMPROVE | Not implemented; payment completion and idempotency must be explicitly designed |
| MCP/AI tools | Legacy MCP and AI-console evidence exists in reports, but no AL-RIFAI gateway code is present | SIMPLIFY and constrain | MCP boundaries and permission classes remain unresolved |

Legacy evidence is useful for business behavior and failure modes, but it does not prove production correctness and does not authorize copying its architecture or credentials.

## Authorization-specific findings

- Legacy API access accepts `X-Internal-Key`; the configured internal key is treated as unrestricted owner-level access, while per-admin keys resolve through hashed `fazle_admins` records.
- Role enforcement exists in `modules/rbac.check_permission()` and `app/main.py` command dependencies, but many routes use only the binary valid-key dependency. This is a warning against relying on authentication alone for AL-RIFAI privileged domain operations.
- Admin WhatsApp relay requires all three of: RBAC `superadmin`, exact configured `settings.admin_bridge2_number`, and a trusted `source_bridge` in the approved control-channel set. Group messages and message text are not sufficient authority.
- Bridge 2 self-chat handling relies on `is_from_me`, bridge identity, sender provenance, and echo guards. This is a useful channel-adapter pattern, not a replacement for platform-wide authorization.
- Frontend pages commonly place API keys in browser `localStorage`; AL-RIFAI should not reproduce a universal browser-held owner key as its final human authorization model.
- Legacy actor classification and role data are spread across RBAC, identity-brain seeds, environment allowlists, and actor-provenance constants. This creates authority-drift risk and should be consolidated behind one AL-RIFAI policy service.
