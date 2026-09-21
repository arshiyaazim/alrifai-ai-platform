# Active Development Task

**Task:** Task 03B-03 — Owner account setup and frontend credential management
**Status:** Shared authentication gate implemented locally; public VPS HTTPS configuration remains intentionally blocked.
**Scope:** Initial Owner account, self-service username/password management, administrative user reset, and session revocation.

Follow-up completed in this worktree: local Open WebUI home integration, server-side Admin navigation gate, and an Nginx-compatible session check. Open WebUI uses its own `.local-data/open-webui` state. Public hostname routing and Nginx installation remain disabled.

## Next implementation task

Before any public Nginx/certificate step, verify the shared parent-domain cookie and `auth_request` flow in an isolated HTTPS environment. Do not expose Open WebUI while `WEBUI_AUTH=false` lacks this gate.

## Explicitly not authorized by this task

- Schema migrations or database changes.
- Production deployment, external reset delivery, WhatsApp authentication, and MCP actor propagation.
- Public HTTPS configuration until an authorized sudo-capable VPS operation is available.
- Production/VPS changes.
- WhatsApp bridge or webhook routing changes.
- 9Router/provider/credential changes.
- Broad domain implementation.
