# Finance and Payroll Workflows

Message: trusted Admin/Owner instruction → Conversations extraction/draft → Finance validation and recipient matching → accountant review → approved outbound delivery event → Finance transaction/ledger commit → audit and confirmation.

Form: payroll/cash/billing form → validation → same Finance service → transaction/audit → result. Payroll uses approved attendance; calculation is once per period. Delivery failure, retry, reversal, duplicate callback, and ambiguous recipient all fail safely or enter review.
