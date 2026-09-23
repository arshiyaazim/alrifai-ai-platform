# Workforce Legacy Mapping

Legacy phone and employee identifiers require deterministic Bangladesh normalization and duplicate review. The future authoritative business Employee ID is the designated normalized mobile; legacy UUIDs/links remain migration provenance or technical references unless explicitly mapped by Workforce policy.

Evidence: `modules/admin_employees`, `modules/attendance`, `modules/employee_verification`; live `wbom_employees` (250), `fpe_employees` (593), aliases/resolution links, `ops_attendance`, and `wbom_attendance` (2) (`VERIFIED_LIVE`/`VERIFIED_SOURCE`). The two employee stores contain overlapping lifecycle, salary, phone, and canonical-link fields.

Gap: duplicate employee matching and phone normalization differ across paths. Import must reconcile records before canonical writes; financial fields, payout destinations, and ledger effects move to Finance ownership.
