# Finance and Payroll Tools and Resources

Proposed tools: `calculate_payroll`, `validate_payroll_run`, `approve_payroll`, `create_payment_instruction`, `get_accountant_queue`, `confirm_payment_delivery`, `record_cash_transaction`, `reverse_cash_transaction`, `get_employee_financial_ledger`, `create_billing_draft`, `get_receivables_summary`.

Resources: payroll period, approval queue, payment draft, cash transaction, employee ledger, payout account, billing/receivable summary. Financial writes require Accountant/Owner capabilities, stable idempotency, audit, and explicit confirmation where policy requires.
