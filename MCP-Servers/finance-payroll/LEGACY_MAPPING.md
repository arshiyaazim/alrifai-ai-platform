# Finance and Payroll Legacy Mapping

Evidence: `modules/fazle_payroll_engine`, `modules/payment*`, `modules/payment_relay*`, `modules/client_billing`; live `fpe_employee_ledger` (747), `fpe_cash_transactions` (4,901), `wbom_cash_transactions` (1,428), `wbom_payroll_runs` (705 drafts), empty `wbom_salary_records` and `wbom_billing_records`, plus approval tables (`VERIFIED_LIVE`/`VERIFIED_SOURCE`).

Gap: WBOM/FPE cash records overlap; message parsing and explicit forms can duplicate writes. Import must reconcile transaction references, accounting periods, approval state, reversals, source provenance, and exactly-once behavior across callbacks (the latter remains `UNKNOWN`).
