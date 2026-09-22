# Platform and Admin Legacy Mapping

Evidence: `rbac`, `user_role`, `authority_lanes`, `business_action_execution`, `draft_approval`, admin routes, live `hermes_tasks` (29), `hermes_action_approvals` (32), `fazle_admins`, `fazle_users`, roles, `fazle_audit_log`, and review logs (`VERIFIED_LIVE`/`VERIFIED_SOURCE`).

Gap: legacy internal-key and relay gates are not AL-RIFAI authority. Legacy user/role records must not become runtime auth. Import audit history as provenance only; public operations require the frozen AL-RIFAI authentication baseline. Hermes task/action approval is orchestration evidence, not domain persistence authority.
