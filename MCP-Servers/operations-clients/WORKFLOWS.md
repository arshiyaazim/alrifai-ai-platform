# Operations and Clients Workflows

Message: client/admin/escort instruction → identity and program matching → extract vessel/roster fields → draft or request missing data → Operations validation/state transition → audit/event → response.

Form: authenticated client/roster/release action → validation → same Operations service → state transition/audit → response. Vessel mention never creates an assignment automatically. Assignment, completion, release, and billing are distinct events. Finance consumes settlement events.
