# AL-RIFAI AI PLATFORM

## MASTER PROJECT ARCHITECTURE CONSTITUTION

### Legacy Replacement, Unified Business Operations, AI Messaging, MCP Architecture & Agent Continuity

**Instruction Type:** Persistent project-wide development instruction

**Project:** AL-RIFAI AI Platform

**Repository:** `D:\apps\alrifai-ai-platform`

**Known development branch:** `feat/windows-local-dev`

**Legacy reference application:** Fazle-Core

**Primary objective:** Build a reliable, maintainable, secure, unified Business Operations and AI Messaging Platform that can eventually replace Fazle-Core.

---

# PART 01 — PROJECT IDENTITY AND NON-NEGOTIABLE OBJECTIVE

## 1.1 What This Project Is

AL-RIFAI AI Platform is being developed as a full replacement for the existing Fazle-Core application.

It is NOT merely:

* A recruitment application.
* An employee management application.
* A WhatsApp chatbot.
* A payroll application.
* An MCP server.
* A frontend dashboard.

It is a unified business operations platform integrating all these capabilities.

The existing Fazle-Core application is the legacy system being replaced because its implementation has experienced architectural, messaging, integration, operational, data integrity, and reliability problems.

The new application must preserve required business capabilities while correcting the underlying problems.

## 1.2 The Core Development Philosophy

**Understand the legacy behavior. Preserve the business requirement. Simplify the architecture. Correct the failure modes. Verify the replacement.**

Do not copy Fazle-Core's architecture simply because it already exists.

Do not discard proven business logic simply because it belongs to the legacy application.

Use Fazle-Core as:

1. A business requirements reference.
2. A source of existing workflow knowledge.
3. A source of known failure modes.
4. A reference for migration and compatibility.
5. A source for identifying missing functionality.

Fazle-Core is not the architectural authority for AL-RIFAI.

The new platform must be independently maintainable.

---

# PART 02 — PERSISTENT AGENT GOVERNANCE

## 2.1 Every Agent Must Follow the Same Architecture

This instruction applies to:

* Codex
* GitHub Copilot
* Kilo Code
* Claude
* Any future AI coding agent
* Any agent operating after a context reset
* Any agent continuing work after token exhaustion

No agent may independently redefine the project's architectural direction.

A new model or agent must continue the existing project rather than inventing a different implementation strategy.

## 2.2 Architecture Authority

Use the following precedence:

1. Explicit, current owner decisions.
2. This Master Architecture Constitution.
3. Approved architecture decision records.
4. Approved business policy documents.
5. Verified repository implementation.
6. Verified legacy Fazle-Core behavior.
7. Historical agent reports.
8. Agent assumptions.

If two instructions conflict, identify the conflict and follow the higher-authority source.

Do not silently replace a previously approved architectural decision.

A newer owner decision may supersede an older one, but the change must be documented.

## 2.3 Mandatory Session Initialization

Before beginning any implementation session:

1. Confirm the repository path.
2. Confirm the current branch and HEAD.
3. Inspect worktree status.
4. Read this architecture instruction.
5. Read the latest development handoff.
6. Read active architecture decisions.
7. Read the current task and known blockers.
8. Inspect relevant existing code and tests.
9. Identify uncommitted work.
10. Determine whether the requested task is already partially implemented.

Never assume that the previous agent's final message accurately represents the current repository state.

Never reset, overwrite, discard, or revert existing work merely to obtain a clean worktree.

## 2.4 No Architectural Drift

Before introducing a new:

* Service
* Database table
* API endpoint
* MCP tool
* Message router
* Background worker
* AI agent
* Authentication mechanism
* Business-event handler
* Frontend workflow

Verify whether an existing component already serves that purpose.

Prefer extending an appropriate existing component over creating a competing implementation.

However, do not force unrelated responsibilities into an existing component merely to reduce the number of files.

**The goal is fewer unnecessary concepts, not fewer files at the expense of maintainability.**

---

# PART 03 — LEGACY FAZLE-CORE AUDIT POLICY

## 3.1 Legacy Audit Is Mandatory When Relevant

Before implementing a substantial business capability, investigate how the corresponding capability works in Fazle-Core.

The agent must ask:

1. Does Fazle-Core already implement this capability?
2. Where is the implementation located?
3. What triggers the workflow?
4. What information enters the workflow?
5. How is identity established?
6. Which business rules are enforced?
7. What database records are created or updated?
8. What authorization is required?
9. What messages or UI responses are produced?
10. What happens when the operation fails?
11. Is the workflow complete?
12. Are there known bugs or operational gaps?
13. Can the new implementation be simpler?
14. Can the new implementation eliminate unnecessary dependencies?
15. How will equivalent business behavior be verified?

## 3.2 Legacy Repository Discovery

Locate the legacy Fazle-Core repository using available workspace configuration or existing project documentation.

Do not assume a historical folder path is still correct.

If the legacy repository is accessible, perform a targeted read-only audit.

If it is unavailable, record the limitation and use verified documentation or prior evidence.

Do not fabricate legacy implementation details.

## 3.3 Legacy Audit Boundaries

The legacy application may still be operating in production.

Therefore:

* Do not modify legacy code.
* Do not modify legacy databases.
* Do not restart legacy services.
* Do not change legacy environment variables.
* Do not modify WhatsApp bridge sessions.
* Do not modify production webhooks.
* Do not rotate credentials.
* Do not run destructive legacy tests.

Legacy investigation is read-only unless the owner explicitly authorizes a separate operation.

## 3.4 Legacy Capability Classification

Classify each discovered capability as:

* PRESERVE — business behavior required in the replacement.
* IMPROVE — required behavior with implementation deficiencies.
* SIMPLIFY — required behavior implemented with unnecessary complexity.
* REDESIGN — architecture is unsuitable but business capability is required.
* DEFER — capability is not currently prioritized.
* RETIRE — owner-approved removal of unnecessary legacy behavior.
* UNKNOWN — insufficient evidence.

Never silently retire an existing business capability.

## 3.5 Legacy Audit Deliverable

For each significant capability, document:

| Field              | Required information                 |
| ------------------ | ------------------------------------ |
| Capability         | Business function                    |
| Legacy location    | Actual source references             |
| Trigger            | Message, API, UI, scheduler or event |
| Inputs             | Required information                 |
| Outputs            | Messages, records and events         |
| Business rules     | Verified rules                       |
| Dependencies       | Relevant components                  |
| Failure modes      | Observed or identified risks         |
| Replacement design | Proposed simpler implementation      |
| Verification       | Required tests                       |
| Status             | Implemented, blocked or pending      |

Historical agent reports are supporting evidence, not substitutes for inspecting the code.

---

# PART 04 — THE TWO PRIMARY WORKFLOWS

The platform has two primary business entry paths.

They must converge on shared domain services.

## 4.1 Workflow 01 — Message-Driven

Sources include:

* WhatsApp Bridge 1
* WhatsApp Bridge 2
* WhatsApp Bridge 3
* Meta WhatsApp
* Messenger
* Facebook Comments
* Authorized future messaging channels

The message-driven workflow is:

Message Source

→ Message Ingestion

→ Canonical Message Storage

→ Identity Resolution

→ Conversation Context

→ Domain Routing

→ Parsing and Extraction

→ Business Policy Validation

→ Authorized Domain Action

→ Audit and Business Events

→ Response Decision

→ Outbound Delivery

→ Delivery Status and Conversation Continuation

Each step must have a clear responsibility.

A message may result in:

* A conversational reply.
* A business record.
* A draft record.
* A pending approval.
* A request for missing information.
* An escalation.
* A report.
* A notification.
* No reply.

Not every incoming message should trigger a business transaction.

Not every incoming message requires an AI-generated response.

## 4.2 Workflow 02 — Frontend-Driven

Sources include:

* Admin dashboard
* Office dashboard
* Recruitment forms
* Employee management
* Attendance interfaces
* Escort assignment forms
* Release Slip submission
* Payroll interfaces
* Finance and payment interfaces
* Client management
* Authorized mobile interfaces

The frontend-driven workflow is:

Authenticated User

→ Frontend Interaction

→ Backend API

→ Request Validation

→ Authorization

→ Shared Domain Service

→ Business Policy Validation

→ Database Transaction

→ Audit and Business Events

→ UI Response

## 4.3 Shared Business Logic Requirement

The message-driven and frontend-driven workflows must not implement separate versions of the same business rule.

Example:

An employee created from an authorized frontend operation and an employee created from an authorized message-driven operation must use the same employee domain service.

The same applies to:

* Applicant registration
* Employee activation
* Attendance
* Escort assignment
* Payroll
* Payment transactions
* Client management
* Release Slip processing

Channel-specific adapters may differ.

Business rules must remain consistent.

---

# PART 05 — TARGET ARCHITECTURAL STRUCTURE

The preferred architecture is a modular monolith with clear boundaries, unless repository evidence demonstrates a concrete reason to adopt another structure.

Do not prematurely split the platform into numerous microservices.

Use separate processes where justified by isolation, resource requirements, protocol boundaries, or operational reliability.

The logical layers are:

## Layer A — External Adapters

WhatsApp bridges, Meta webhooks, frontend APIs, file ingestion and authorized external integrations.

## Layer B — Ingestion and Identity

Canonical message storage, source normalization, identity resolution, contact mapping, conversation association and media references.

## Layer C — Orchestration

Domain routing, conversation coordination, AI tool invocation, approval routing, workflow continuation and event dispatch.

## Layer D — Domain Services

Recruitment, Employee, Attendance, Payroll, Escort Operations, Finance, Client, Administration and related business capabilities.

## Layer E — Persistence

PostgreSQL repositories, transactions, constraints, migrations, audit records and business events.

## Layer F — AI and MCP

AI model adapters, conversation engine, MCP tools, knowledge retrieval, reporting and assistant capabilities.

## Layer G — Presentation

Web and mobile interfaces, dashboards, forms, chat frontend, reports and document generation.

These are logical responsibilities, not instructions to create seven separate applications.

Use the existing repository structure where it supports these boundaries.

---

# PART 06 — CANONICAL BUSINESS DOMAINS

The platform must support the following business domains.

## 6.1 Identity and Person

A person may simultaneously be:

* Applicant
* Employee
* Client contact
* Admin
* Office staff
* Accountant
* Other authorized business participant

Do not create separate person identities merely because the person participates in multiple workflows.

Identity resolution must distinguish between:

* Verified identity
* Probable identity
* Ambiguous identity
* Unknown identity

A phone number is a contact identifier, not an infallible unique person identifier.

Shared phone numbers must not cause automatic merging of unrelated people.

## 6.2 Recruitment

Support:

* Job inquiries
* Applicant registration
* Role selection
* Application submission
* Applicant identity reuse
* Document collection
* Application status
* Office verification
* Admin hiring approval
* Applicant-to-employee transition
* Recruitment conversations
* Approved recruitment knowledge and policies

The system must not invent vacancies, salaries, benefits, fees, working hours or other employment policies.

Use approved business data.

## 6.3 Employee Management

Support:

* Employee identity
* Employee profile
* Employment status
* Activation and reactivation
* Employment history
* Role and assignment history
* Employee communications
* Relevant documents
* Payroll association
* Attendance association

Inactive employees must be considered during identity matching.

An existing employee must not be duplicated merely because their status is inactive.

## 6.4 Attendance

Support the attendance requirements applicable to each role and duty type.

Do not assume that office attendance and vessel escort attendance follow identical rules.

Determine the relevant:

* Duty assignment
* Attendance period
* Presence evidence
* Start and end times
* Corrections
* Approval
* Payroll implications

Avoid introducing a generic attendance rule that incorrectly changes escort duty accounting.

## 6.5 Payroll

Support:

* Employee-linked payroll
* Approved pay structures
* Attendance and duty-based calculations
* Adjustments
* Payment drafts
* Review and approval
* Payment status
* Payroll history
* Employee ledger reconciliation
* Audit and reporting

AI may explain or prepare payroll information.

AI must not independently approve payroll or execute privileged payment operations.

## 6.6 Escort Operations

Support:

* Client
* Mother vessel
* Lighter vessel
* Escort personnel
* Escort roster
* Assignment
* Duty start
* Duty continuation
* Personnel replacement
* Completion
* Release Slip
* Verification
* Billing
* Operational history

Escort assignments must be modeled as a business lifecycle, not merely a free-text message or spreadsheet row.

Define valid status transitions through an approved state machine.

Do not assume that assignment, duty completion, Release Slip completion and client billing are the same event.

## 6.7 Finance and Cash Transactions

Support:

* Admin-to-accountant communication
* Payment instructions
* Payment drafts
* Cash transactions
* Employee ledger entries
* Payment history
* Reconciliation
* Financial audit

Preserve the previously approved business rule:

A successful delivery of the approved owner/admin-to-accountant payment-format WhatsApp message is the authoritative business signal for completing the corresponding cash transaction.

The accounting integration must be deterministic and idempotent.

A failed outbound delivery must not be treated as a successful payment instruction.

A repeated delivery callback must not duplicate the cash transaction.

The AI conversation engine must not be responsible for directly deciding whether the accounting transaction has completed.

## 6.8 Client Management

Support:

* Client identity
* Client contacts
* Vessel and operation associations
* Escort requests
* Operational communication
* Service history
* Billing
* Outstanding amounts
* Relevant reports

Client identity and employee identity may share the person/contact infrastructure without sharing inappropriate business permissions.

---

# PART 07 — MESSAGE INGESTION AND STORAGE

## 7.1 Canonical Message Model

Store inbound and outbound messages.

Preserve:

* Source platform
* Source bridge or integration
* External message ID
* Internal message ID
* Conversation ID
* Sender identity
* Recipient identity
* Group identity where applicable
* Message direction
* Timestamp
* Message content
* Media references
* Delivery state
* Processing state
* Actor classification
* AI/human/device origin
* Relevant domain classification
* Correlation and causation identifiers

Preserve raw evidence separately from interpreted business facts.

Do not overwrite the original message merely because AI later extracts different information.

## 7.2 Known Legacy Failure Modes to Prevent

Specifically investigate and prevent:

* Inbound messages not being stored.
* Outbound messages not being stored.
* Bridge self-chat messages missing.
* AI relay replies missing from canonical history.
* Duplicate dispatch.
* Duplicate AI replies.
* Missing intent classification.
* Truncated history causing context loss.
* Incorrect conversation association.
* Outbound failure without controlled recovery.
* Repeated processing after restart.

## 7.3 Ingestion Idempotency

Where the source provides stable identifiers, use them to detect repeated deliveries.

Define behavior for sources without reliable message IDs.

Do not assume that every webhook event represents a new message.

---

# PART 08 — CONVERSATION ENGINE

The AI conversation engine must be context-aware, identity-aware and domain-aware.

It must distinguish:

* Applicant conversations
* Employee conversations
* Client conversations
* Escort operations
* Admin conversations
* Accountant conversations
* General inquiries
* Unknown or ambiguous conversations

## 8.1 Conversation Context

Maintain relevant conversation history and structured business context.

Do not rely exclusively on an arbitrarily truncated recent-message window.

Do not send unnecessary historical messages to the AI model.

Use retrieval, summaries and structured state where appropriate.

## 8.2 Topic Lifecycle

Support:

* Topic opened
* Information gathering
* Awaiting user
* Awaiting approval
* Completed
* Closed
* Reopened by the user

Do not repeatedly reopen a completed topic without a new user request.

Avoid unnecessary repeated answers.

## 8.3 AI Reply Control

Ensure that one eligible message does not accidentally produce multiple independent replies.

Use appropriate:

* In-flight controls
* Idempotency
* Conversation locking
* Retry classification
* Delivery-state tracking

Retries must not produce uncontrolled duplicate messages.

## 8.4 Language and Tone

Respect the user's conversation language and context.

Avoid unexplained language switching.

Apply relationship-aware communication policies for applicants, employees, clients and administrators.

Personality or stylistic configuration must not override business policy, security or factual accuracy.

---

# PART 09 — AI, LOCAL MODELS AND MCP ARCHITECTURE

## 9.1 AI Is an Assistant, Not the Database Authority

AI may:

* Understand conversations.
* Extract structured information.
* Ask clarifying questions.
* Summarize messages.
* Retrieve approved business information.
* Prepare drafts.
* Generate reports.
* Assist with bills.
* Explain operational status.
* Recommend a proposed next workflow action.

AI must not independently bypass domain services or authorization.

## 9.2 Local AI and Model Routing

The platform should support local AI models and approved external model providers through replaceable adapters.

Do not hardcode business rules into a particular model provider.

Model replacement must not require rewriting recruitment, payroll or escort business logic.

A model failure must not corrupt business data.

## 9.3 MCP Server Strategy

Develop MCP capabilities around stable domain services.

Potential MCP tool groups include:

* Identity
* Recruitment
* Employee
* Attendance
* Payroll
* Escort Roster
* Escort Lifecycle
* Client
* Finance
* Messaging
* Reports
* Billing
* Knowledge Retrieval

Do not create an independent database or business-rule implementation for every MCP server.

MCP tools must use approved domain services and authorization boundaries.

Separate read-only tools from state-changing tools.

## 9.4 MCP Authorization

A tool must not gain Admin privileges merely because an AI model invoked it.

The tool must receive and validate a trusted authorization context.

The authorization decision belongs to the backend, not to the model's natural-language reasoning.

Privileged operations require the appropriate authenticated identity and approval policy.

## 9.5 Structured Extraction

For escort operations, the system may extract:

* Client
* Mother vessel
* Lighter vessel
* Escort name
* Duty date
* Duty start
* Duty end
* Release information
* Other approved operational fields

However, extraction is not equivalent to verification.

Use confidence, validation and missing-field handling.

Ambiguous information must not silently become authoritative business data.

---

# PART 10 — ESCORT CONVERSATION TO BUSINESS RECORD

This is a major platform capability.

The system must be able to process conversations involving:

* Admin
* Escort
* Client
* Office staff
* Operations personnel

and derive structured escort-program information.

Target workflow:

Incoming Conversation

→ Identity Resolution

→ Escort Domain Detection

→ Relevant Context Retrieval

→ Structured Field Extraction

→ Existing Escort Program Matching

→ Business Validation

→ Draft or Proposed Update

→ Required Authorization

→ Domain Service

→ Database Transaction

→ Audit and Business Event

→ Conversation Continuation

A message mentioning a vessel must not automatically create a new escort assignment.

A message mentioning duty completion must not automatically create a completed Release Slip.

A message mentioning payment must not automatically mark an invoice as paid.

Each operation requires its own business rules and evidence.

---

# PART 11 — REPORTING, BILLING AND ASSISTANT CAPABILITIES

The platform must support generating information for Admin and authorized users.

Examples:

* Recruitment summaries
* Employee status reports
* Attendance reports
* Escort roster reports
* Active escort programs
* Completed escort programs
* Vessel-wise operational summaries
* Client-wise service summaries
* Payroll summaries
* Payment and ledger reports
* Billing drafts
* Outstanding invoice reports
* Operational exceptions
* Missing-information reports

Reports must be derived from authoritative business records.

AI may summarize and explain the results.

Do not fabricate missing figures.

Billing calculations must use approved rates and business rules.

Separate draft invoices from issued or approved invoices.

Generated documents should be traceable to their underlying business records.

---

# PART 12 — DATABASE AND DATA INTEGRITY

PostgreSQL is the intended authoritative relational database.

The architecture must enforce:

* Referential integrity
* Appropriate uniqueness
* Valid status transitions
* Transactional consistency
* Idempotency
* Audit persistence
* Concurrency safety
* Migration discipline

Application-level duplicate checks are not always sufficient under concurrency.

Investigate database-level constraints where appropriate.

## 12.1 Existing Task 03A Findings

The latest reported Task 03A state includes:

* ApplicantService implemented and locally verified.
* EmployeeService partially verified.
* Inactive employee reactivation locally verified.
* PostgreSQL integration locally verified.
* Hiring authorization fail-closed.
* Trusted Admin authorization not implemented.
* Employee person uniqueness unresolved.
* Normalized phone uniqueness unresolved.
* Business-event idempotency uniqueness unresolved.

These findings are the starting point for verification, not permanent assumptions.

## 12.2 Migration Policy

Before proposing a migration:

1. Inspect the current schema.
2. Inspect existing data assumptions.
3. Identify affected services.
4. Determine migration compatibility.
5. Determine rollback or recovery requirements.
6. Identify concurrency implications.
7. Write appropriate tests.
8. Document owner approval requirements.

Do not execute production migrations without explicit authorization.

Do not modify the production database during local development.

---

# PART 13 — AUTHENTICATION AND AUTHORIZATION

AL-RIFAI must have its own coherent authentication and authorization architecture.

It must not depend on the legacy Fazle-Core role tables as a permanent runtime requirement.

Investigate appropriate permissions for:

* Owner
* Super Admin
* Admin
* Office staff
* Operator
* Accountant
* Employee
* Client
* Applicant
* AI service identity

The final permission matrix requires explicit business approval.

Do not invent privileges based only on role names.

Use trusted server-side identity resolution.

Caller-supplied person IDs are not proof of authorization.

Authorization must be enforced at the business operation boundary.

Frontend visibility restrictions are not sufficient.

MCP tool descriptions are not sufficient.

AI system prompts are not sufficient.

If trusted authorization is unavailable, privileged operations must fail closed.

---

# PART 14 — BUSINESS EVENTS AND AUDIT

Significant business operations should produce traceable events.

Examples:

* Application submitted
* Applicant verified
* Hiring approved
* Employee activated
* Employee deactivated
* Escort assigned
* Escort started
* Escort completed
* Release Slip verified
* Payment instruction delivered
* Cash transaction recorded
* Payroll approved
* Invoice issued

Where a business transaction and its event must succeed together, use an appropriate transactional pattern.

Do not commit the business state while silently losing a mandatory audit record.

For asynchronous integrations, investigate an outbox pattern or another verified durable mechanism.

Every important operation should be traceable to:

* Actor
* Source
* Time
* Business entity
* Action
* Outcome
* Correlation ID

---

# PART 15 — FAILURE RECOVERY AND OPERATIONAL RELIABILITY

Design for failure from the beginning.

Consider:

* WhatsApp bridge disconnection
* Webhook redelivery
* Database unavailability
* AI provider failure
* Local model timeout
* MCP tool failure
* Worker restart
* Partial outbound delivery
* Duplicate events
* Network interruption
* Concurrent updates

A failed AI call must not roll back an already completed unrelated business transaction.

A failed business transaction must not be reported as successful.

A restart must not silently lose queued work.

Retries must be bounded and classified.

Where useful, introduce durable queues, outbox processing or controlled background workers.

Do not introduce infrastructure without a demonstrated requirement.

---

# PART 16 — FRONTEND ARCHITECTURE

The frontend must represent the same authoritative business state used by message-driven workflows.

It should support responsive web and mobile use.

Major areas may include:

* Dashboard
* Conversations
* Recruitment
* Employees
* Attendance
* Escort Operations
* Clients
* Payroll
* Finance
* Reports
* Administration

Use consistent navigation, forms, status labels and permissions.

Do not create separate frontend-only business rules that contradict backend behavior.

The backend remains responsible for authorization and data integrity.

Do not mark a business action successful in the UI before the backend confirms its outcome.

---

# PART 17 — TESTING AND VERIFICATION

Every substantial capability must have an appropriate verification strategy.

Testing layers include:

1. Unit tests.
2. Domain service tests.
3. PostgreSQL integration tests.
4. Authorization tests.
5. Idempotency tests.
6. Concurrency tests.
7. Messaging adapter tests.
8. MCP tool tests.
9. Frontend/API tests.
10. End-to-end workflow tests.

Use isolated test resources.

Do not run destructive tests against production.

Test both entry paths where a capability is available through messaging and frontend.

## 17.1 Cross-Channel Consistency Tests

For shared business operations, verify that equivalent authorized actions from different entry paths produce consistent business results.

For example:

An authorized employee activation through the frontend and an authorized employee activation through messaging must use the same lifecycle rules.

## 17.2 Failure-Mode Regression Tests

When a Fazle-Core failure mode is identified, create a corresponding regression requirement for the replacement where practical.

The objective is not merely to make the new application pass tests.

The objective is to prevent recurrence of known operational failures.

---

# PART 18 — DEVELOPMENT CONTINUITY AND MEMORY

This section is mandatory.

Chat context is not the authoritative project memory.

Agent memory may disappear.

Token limits may interrupt implementation.

A different model may resume the task.

Therefore, development continuity must be maintained inside the repository.

## 18.1 Persistent Documentation

Create or maintain a dedicated architecture and development-continuity documentation structure.

Suggested structure:

`docs/architecture/`

* `MASTER_ARCHITECTURE.md`
* `SYSTEM_BOUNDARIES.md`
* `DOMAIN_MAP.md`
* `MESSAGE_WORKFLOW.md`
* `FRONTEND_WORKFLOW.md`
* `MCP_ARCHITECTURE.md`
* `DATA_OWNERSHIP.md`
* `SECURITY_MODEL.md`
* `LEGACY_GAP_REGISTER.md`
* `ARCHITECTURE_DECISIONS.md`

`docs/development/`

* `CURRENT_STATE.md`
* `ACTIVE_TASK.md`
* `NEXT_ACTIONS.md`
* `BLOCKERS.md`
* `TEST_STATUS.md`
* `AGENT_HANDOFF.md`

These are proposed document names.

First inspect existing documentation and reuse appropriate files rather than creating duplicates.

## 18.2 Current State Document

Maintain a concise description of:

* Implemented components
* Verified components
* Unverified components
* Blocked components
* Pending owner decisions
* Active development branch
* Relevant test evidence
* Known limitations

Never describe planned functionality as implemented.

Never describe local verification as production verification.

## 18.3 Agent Handoff Document

At the end of every meaningful development session, record:

* Date and task
* Repository and branch
* HEAD commit
* Worktree status
* Files changed
* Work completed
* Tests executed
* Tests not executed
* Known blockers
* Pending approvals
* Exact next actions
* Relevant commands
* Important architectural decisions

Do not include credentials, tokens, cookies or secrets.

## 18.4 Interruption Recovery

If a session ends unexpectedly, the next agent must be able to reconstruct the state from:

1. Git state.
2. Persistent architecture documentation.
3. Current task documentation.
4. Test results.
5. Handoff documentation.

No critical architectural decision should exist only in an AI chat transcript.

## 18.5 Commit Discipline

Do not automatically commit unrelated pre-existing work.

Do not reset or clean the worktree to simplify implementation.

Keep changes scoped and traceable.

Commit only when the task authorization and repository workflow permit it.

Do not push or deploy without the applicable authorization.

---

# PART 19 — ARCHITECTURE DECISION RECORDS

Record significant architectural decisions.

Each decision must contain:

* Decision ID
* Date
* Problem
* Context
* Considered alternatives
* Selected approach
* Reasoning
* Consequences
* Affected components
* Owner approval status
* Superseded decision, if applicable

Examples:

* Modular monolith versus microservices.
* Canonical person identity.
* Admin authorization model.
* Message storage strategy.
* MCP tool boundaries.
* Escort lifecycle state machine.
* Payment delivery accounting integration.
* Business-event idempotency.
* Legacy data migration strategy.

Do not repeatedly reopen an approved decision without new evidence or an explicit owner request.

---

# PART 20 — FEATURE IMPLEMENTATION PROTOCOL

Before implementing a new feature, complete the following analysis.

## Step 1 — Understand the Business Requirement

What real business problem does the feature solve?

Who uses it?

What triggers it?

What constitutes successful completion?

## Step 2 — Audit the Legacy Equivalent

How does Fazle-Core handle it?

What works?

What fails?

What is unnecessarily complex?

## Step 3 — Inspect the New Repository

Does AL-RIFAI already have relevant services, models, APIs or tests?

Can existing components be reused?

## Step 4 — Identify Shared Domain Logic

Will the capability be used by messaging, frontend, MCP tools or background workers?

Where should the authoritative business rule live?

## Step 5 — Design the Simplest Reliable Solution

Prefer explicit responsibilities, predictable state transitions and minimal dependencies.

Do not introduce unnecessary abstractions.

## Step 6 — Analyze Security and Data Integrity

Who may perform the operation?

What can be duplicated?

What happens under concurrency?

What happens after a partial failure?

## Step 7 — Implement Within Scope

Preserve unrelated work.

Avoid unnecessary schema or architecture changes.

## Step 8 — Verify

Run appropriate tests.

Report actual results.

## Step 9 — Update Persistent Documentation

Record implementation status, decisions, blockers and next actions.

## Step 10 — Prepare Agent Handoff

Ensure another agent can continue without rediscovering the entire task.

---

# PART 21 — PRODUCTION AND MIGRATION STRATEGY

The new platform is being developed as a replacement for Fazle-Core.

It must not accidentally interfere with the existing production system.

Until a separate migration and cutover plan is approved:

* Keep development isolated.
* Do not redirect production webhooks.
* Do not take over active WhatsApp bridge sessions.
* Do not modify production routing.
* Do not replace production database connections.
* Do not restart Fazle-Core.
* Do not deploy unfinished replacement components.

Eventually, a cutover plan must address:

* Business data migration.
* Identity reconciliation.
* Message history.
* Media references.
* Active escort programs.
* Employee records.
* Payroll and ledger continuity.
* Client records.
* Webhook ownership.
* WhatsApp bridge ownership.
* Pending outbound messages.
* Idempotency across cutover.
* Rollback and recovery.

Do not assume that successful local tests establish production readiness.

---

# PART 22 — CURRENT DEVELOPMENT BASELINE

The latest owner-provided Task 03A report identifies:

Repository:

`D:\apps\alrifai-ai-platform`

Branch:

`feat/windows-local-dev`

Reported HEAD:

`e8b67e0e1af844a4970755858c5a3a253e874d3d`

Reported local verification:

* PostgreSQL driver `psycopg 3.3.6`.
* 38 tests passed against isolated PostgreSQL.
* Applicant creation/reuse verified.
* Applicant idempotency verified.
* Inactive employee reactivation verified.
* Audit rollback verified.
* Hiring authorization fail-closed.

Known blockers:

* Trusted Admin authorization.
* Employee uniqueness.
* Phone identity concurrency.
* Database-level business-event idempotency.

This is a historical starting baseline.

Verify the current repository state before continuing.

---

# PART 23 — FIRST EXECUTION OF THIS INSTRUCTION

On receiving this Master Architecture Constitution:

1. Inspect the current repository.
2. Identify existing architecture documentation.
3. Identify existing agent instruction files.
4. Reconcile overlapping instructions.
5. Preserve all existing uncommitted work.
6. Identify the accessible legacy Fazle-Core repository.
7. Establish the initial domain and capability map.
8. Establish the legacy gap register.
9. Establish persistent agent handoff documentation.
10. Identify the current active implementation task.
11. Report architecture inconsistencies.
12. Recommend the smallest safe next implementation step.

Do not immediately begin a broad rewrite.

Do not immediately create all proposed services, tables or MCP servers.

Do not treat the proposed architecture as evidence that a component is already implemented.

First establish the authoritative development baseline.

---

# FINAL OPERATING PRINCIPLE

Every agent must continuously ask:

**How does Fazle-Core currently handle this business capability?**

**What is the actual business requirement behind that implementation?**

**What is incomplete, unreliable, duplicated or unnecessarily complicated?**

**Can AL-RIFAI implement the same business capability with fewer moving parts and stronger guarantees?**

**Will this implementation remain consistent across messaging, frontend, MCP and background workflows?**

**Can another agent understand, verify and continue this work after the current session ends?**

The project is successful only when AL-RIFAI becomes a coherent, independently maintainable, operationally reliable replacement for Fazle-Core—not when isolated features merely appear implemented.
