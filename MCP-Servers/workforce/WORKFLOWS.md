# Workforce Workflows

Employee-ID workflow: normalize `+`, `00`, `88`, or local input to the canonical final 11-digit Bangladesh mobile, validate uniqueness, and preserve historical IDs. Hiring and explicit edits are transactional and audited; inbound messages and contact discovery cannot change Employee ID.

Message: employee/attendance message → identity resolution → parse evidence → Workforce validation/draft → idempotent attendance or lifecycle service → audit/event → reply.

Form: authenticated employee/attendance action → validation → same Workforce service → transaction → audit/event.

Inactive reactivation, employee uniqueness, daily attendance idempotency, and ambiguous phone matches require explicit policy. A payout number never resolves identity.
