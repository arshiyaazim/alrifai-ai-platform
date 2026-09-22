# Workflow Convergence

## Messaging workflow

`Inbound text/media → channel adapter → canonical message storage → identity resolution → conversation/domain classification → extraction → domain service → policy validation → transaction → audit/event → outbound delivery`

Fresh live evidence confirms this shape in Fazle-Core: three active bridge services feed `wbom_whatsapp_messages` (32,436 rows across bridge1/2/3, Meta, and WhatsApp), then `bridge_poller`/`message_router`/identity modules route to domain handlers or Hermes drafts and outbound delivery.

Relevant channels from prior source audit: Bridge 1/2/3, Meta WhatsApp, Messenger, Facebook comments, and admin relay. Channel provenance, external IDs, actor/source flags, attachments, delivery state, and correlation IDs remain message concerns. A message mentioning a person, payment, vessel, or release is not itself authority to mutate that aggregate.

## Frontend/form workflow

`Authenticated frontend action → request validation → shared identity resolution → same domain service used by messaging → policy validation → transaction → audit/event → response`

The fresh audit confirms divergent form/message behavior for employees, recruitment, attendance, escort, cash, clients, and payroll: static/API routes coexist with message handlers, and draft/approval/idempotency behavior is not uniform. AL-RIFAI must make the domain service the convergence point, not the MCP handler or UI route.

## Per-server convergence

| Server | Messaging entry | Form entry | Shared convergence service |
|---|---|---|---|
| Recruitment | Recruitment conversation extraction | Applicant/job forms | Recruitment service |
| Workforce | Employee/attendance messages | Employee and attendance forms | Workforce service |
| Finance & Payroll | Approved payment-format conversation and delivery event | Payroll, cash, billing forms | Finance/payroll service |
| Conversations & AI | All inbound/outbound channels | Conversation search/admin tools | Conversation service and domain dispatch contract |
| Operations & Clients | Client/escort instructions and extracted roster data | Client, vessel, roster, release forms | Operations service |
| Platform / Admin | Approved administrative command/draft | Admin/report/approval forms | Cross-domain orchestration and approval service |

No AI model writes directly to the database. No frontend path bypasses the domain service.
