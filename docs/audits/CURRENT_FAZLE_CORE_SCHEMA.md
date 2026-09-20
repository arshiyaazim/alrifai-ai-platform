# CURRENT FAZLE-CORE SCHEMA AUDIT

This audit uses live introspection from the current `ai-postgres` container (`docker exec ai-postgres psql -U postgres -d postgres ...`). It reflects the running production-ish current schema, not a documentation-only guess.

## 1. Schema scope and access status
- DB: `ai-postgres`
- Database: `postgres`
- Status: live and readable
- Scope: real schema and key domain tables used by the current messaging and form workflows

## 2. Live domain tables relevant to the audit

### A. Identity and messaging
- `wbom_contacts`
- `wbom_whatsapp_messages`
- `wbom_group_identities`
- `wbom_identity_links`
- `wbom_message_intents`
- `fazle_unified_contacts`
- `fazle_contact_roles`
- `fazle_contact_aliases`
- `fazle_conversations`
- `fazle_messages`

### B. Employees and recruitment
- `wbom_employees`
- `wbom_candidates`
- `wbom_job_applications`
- `wbom_employee_requests`
- `fpe_employees`
- `fpe_employee_aliases`
- `fpe_employee_resolution_links`

### C. Attendance and payroll
- `ops_attendance`
- `wbom_cash_transactions`
- `fpe_cash_transactions`
- `fpe_employee_ledger`
- `wbom_payroll_runs`
- `wbom_salary_records`
- `wbom_payroll_approval_log`

### D. Escort / operations / billing
- `escort_roster_entries`
- `escort_roster_change_requests`
- `escort_slip_extractions`
- `ops_programs`
- `ops_rates`
- `wbom_client_billing_profiles`
- `wbom_billing_records`
- `wbom_billing_payment_log`

### E. Admin and audit
- `fazle_admins`
- `fazle_users`
- `fazle_audit_log`
- `fpe_review_audit_logs`
- `fazle_draft_replies`
- `fazle_payment_drafts`

## 3. Key struct inventory (selected live tables)

### `wbom_contacts`
Columns:
- `contact_id` integer PK
- `whatsapp_number` varchar NOT NULL
- `display_name` varchar NOT NULL default ''
- `company_name` varchar
- `relation_type_id` integer
- `business_type_id` integer
- `is_active` boolean default true
- `created_at` timestamptz default now()
- `updated_at` timestamptz default now()
- `notes` text
- `platform` varchar default 'whatsapp'
- `relation` varchar default 'unknown'
- `personality_hint` varchar default ''
- `interaction_count` integer default 0

### `wbom_employees`
Columns:
- `employee_id` integer PK
- `employee_mobile` varchar NOT NULL
- `employee_name` varchar NOT NULL
- `designation` varchar NOT NULL
- `joining_date` date
- `status` varchar default 'Active'
- `bank_account` varchar
- `emergency_contact` varchar
- `address` text
- `created_at` timestamptz default now()
- `updated_at` timestamptz default now()
- `bkash_number` varchar
- `nagad_number` varchar
- `basic_salary` numeric default 0
- `nid_number` varchar

### `wbom_whatsapp_messages`
Columns:
- `message_id` integer PK
- `whatsapp_msg_id` varchar
- `contact_id` integer FK-like reference pattern
- `sender_number` varchar default ''
- `message_type` varchar default 'text'
- `content_type` varchar default 'text'
- `message_body` text default ''
- `classification` varchar default 'unclassified'
- `is_processed` boolean default false
- `template_used_id` integer
- `received_at` timestamptz default now()
- `processed_at` timestamptz
- `related_program_id` integer
- `related_transaction_id` integer
- `platform` varchar default 'whatsapp'
- `direction` varchar
- `contact_identifier` varchar
- `ai_response` text default ''
- `metadata_json` jsonb default '{}'
- `status` varchar default 'sent'
- `identity_role` text
- `identity_confidence` integer
- `workflow_triggered` text
- `canonical_phone` text
- `phone_last10` text
- `source_message_ref` text
- `source_timestamp` timestamptz
- `source_context` text
- `message_hash` text
- `critical_contact` boolean default false
- `critical_log_path` text
- `original_sender_number` text
- `conversation_key` text
- `receiver_number` text
- `intent_detected` text
- `extracted_text` text
- `actor_type` text
- `actor_id` text
- `sender_name_snapshot` text
- `sender_name_source` varchar
- `sender_name_confidence` smallint
- `canonical_message_key` text
- `resolved_phone` text
- `resolved_at` timestamptz

### `wbom_candidates`
Columns:
- `candidate_id` bigint PK
- `phone` varchar NOT NULL
- `full_name` varchar
- `age` integer
- `area` varchar
- `job_preference` varchar
- `experience_years` integer
- `available_join_date` date
- `funnel_stage` varchar default 'new'
- `collection_step` varchar default 'name'
- `score` integer default 0
- `score_bucket` varchar default 'cold'
- `assigned_recruiter` varchar
- `assigned_at` timestamptz
- `last_contact_at` timestamptz
- `next_follow_up_at` timestamptz
- `source` varchar default 'whatsapp'
- `source_message` text
- `notes` text
- `created_at` timestamptz default now()
- `updated_at` timestamptz default now()
- `post_intake_status` text
- `linked_employee_id` bigint

### `wbom_clients`
Columns:
- `client_id` integer PK
- `name` varchar NOT NULL
- `phone` varchar
- `company_name` varchar
- `client_type` varchar default 'Standard'
- `outstanding_balance` numeric default 0
- `credit_terms` varchar
- `notes` text
- `is_active` boolean default true
- `created_at` timestamptz default now()
- `updated_at` timestamptz default now()

### `wbom_cash_transactions`
Columns:
- `transaction_id` integer PK
- `employee_id` integer NOT NULL
- `program_id` integer
- `transaction_type` varchar NOT NULL
- `amount` numeric NOT NULL
- `payment_method` varchar NOT NULL
- `payment_mobile` varchar
- `transaction_date` date default current_date
- `transaction_time` timestamptz default now()
- `status` varchar default 'Completed'
- `reference_number` varchar
- `remarks` text
- `whatsapp_message_id` varchar
- `created_by` varchar
- `idempotency_key` varchar
- `approved_by` varchar
- `approved_at` timestamptz
- `source` varchar default 'web'
- `is_reversed` boolean default false
- `reversal_of` integer
- `correction_note` text
- `employee_phone` text
- `payment_number` text

### `fpe_employees`
Columns:
- `id` bigint PK
- `employee_code` text
- `full_name` text NOT NULL
- `name_normalized` text NOT NULL
- `primary_phone` text
- `employee_id_phone` text
- `department` text
- `status` text default 'active'
- `created_source` text default 'whatsapp_auto_create'
- `created_at` timestamptz default now()
- `updated_at` timestamptz default now()
- `canonical_employee_id` bigint
- `resolution_status` text default 'unresolved'
- `confidence_score` numeric default 0.000
- `wbom_employee_id` bigint
- `basic_salary` numeric default 10000.00
- `designation` text
- `joining_date` date
- `official_name` text

### `fpe_cash_transactions`
Columns:
- `id` bigint PK
- `txn_ref` text NOT NULL
- `fpe_wa_message_id` bigint
- `employee_id` bigint
- `employee_name_raw` text
- `amount` numeric NOT NULL
- `payout_phone` text
- `payout_method` text
- `txn_date` date NOT NULL
- `txn_category` text default 'salary'
- `source_message_text` text
- `is_reversal` boolean default false
- `reversed_txn_id` bigint
- `accounting_period` text
- `created_at` timestamptz default now()
- `created_by` text default 'fpe_engine'
- `deleted_at` timestamptz
- `deleted_by` text
- `updated_at` timestamptz default now()
- `employee_id_phone` varchar
- `employee_phone` varchar
- `source` text default 'whatsapp'
- `source_channel` text
- `source_message_id` text
- `transaction_status` text default 'final'
- `approval_status` text
- `approved_by` text
- `approved_at` timestamptz
- `review_status` text
- `submitted_by` text
- `submitted_at` timestamptz
- `program_id` bigint
- `original_payload` jsonb
- `metadata` jsonb
- `legacy_wbom_transaction_id` bigint

### `ops_attendance`
Columns:
- `id` integer PK
- `employee_id` varchar NOT NULL
- `name` text
- `location` text
- `client_name` text
- `date` date default current_date
- `created_at` timestamp default now()
- `shift` char

### `escort_roster_entries`
Columns:
- `id` integer PK
- `program_id` integer NOT NULL
- `mother_vessel` text
- `lighter_vessel` text
- `master_mobile` text
- `escort_name` text
- `escort_mobile` text
- `destination` text
- `start_date` date
- `start_shift` char
- `end_date` date
- `end_shift` char
- `total_shifts` integer
- `total_days` numeric
- `salary` numeric
- `conveyance` numeric
- `total` numeric
- `release_point` text
- `roster_status` varchar default 'draft'
- `calc_version` integer default 1
- `notes` text
- `last_synced_at` timestamptz
- `created_at` timestamptz default now()
- `updated_at` timestamptz default now()
- `expires_at` timestamptz
- `food_bill` numeric default 0
- `advance_deduction` numeric default 0
- `net_payable` numeric default 0
- `escort_employee_id` integer

### `fazle_conversations` / `fazle_messages`
Columns:
- `fazle_conversations`: `id`, `user_id`, `conversation_id`, `title`, `created_at`, `updated_at`
- `fazle_messages`: `id`, `conversation_id`, `role`, `content`, `created_at`

### `fazle_admins` / `fazle_users`
Columns:
- `fazle_admins`: `id`, `phone`, `name`, `api_key_hash`, `status`, `created_at`, `last_seen_at`, `notes`, `username`, `password_hash`, `login_token_hash`
- `fazle_users`: `id`, `email`, `hashed_password`, `name`, `relationship_to_azim`, `role`, `is_active`, `created_at`, `updated_at`, `username`, `status`, `deletion_scheduled_at`

### `fazle_audit_log`
Columns:
- `id` uuid PK
- `actor_id` varchar NOT NULL
- `actor_email` varchar NOT NULL default ''
- `action` varchar NOT NULL
- `target_type` varchar NOT NULL default ''
- `target_id` varchar default ''
- `detail` text default ''
- `ip_address` varchar default ''
- `created_at` timestamptz default now()

## 4. Data ownership and duplication
This live schema shows clear duplication across conceptual domains:
- `wbom_contacts` vs `fazle_unified_contacts` vs `fazle_contact_roles`
- `wbom_employees` vs `fpe_employees`
- `wbom_clients` vs `fazle_clients`
- `wbom_cash_transactions` vs `fpe_cash_transactions`
- `wbom_whatsapp_messages` vs `fazle_conversations` / `fazle_messages`

This is exactly the sort of duplication the AL-RIFAI canonical identity model should eliminate.

## 5. Status summary
- Current DB access: live, read-only, verified
- Schema confidence: high for the tables examined
- Live table inventory: verified
- Full database schema: not enumerated exhaustively in this summary, but the relevant workflow tables are inspected and mapped
- Unverified / absent: any table not present in the live DB is marked absent in the final architecture summary, not assumed.
