# Active Development Task

**Task:** Task 03B-03 — Owner account setup and frontend credential management
**Status:** Implemented and verified against the isolated local PostgreSQL database.
**Scope:** Initial Owner account, self-service username/password management, administrative user reset, and session revocation.

Follow-up completed in this worktree: local Open WebUI home integration and server-side Admin navigation gate. Open WebUI is intentionally local-only and uses its own `.local-data/open-webui` state.

## Next implementation task

Do not begin a broad rewrite. Continue through the existing FastAPI entrypoint and central policy. Keep production and message-driven auth separate until their trusted adapters are implemented.

## Explicitly not authorized by this task

- Schema migrations or database changes.
- Production deployment, external reset delivery, WhatsApp authentication, and MCP actor propagation.
- Production/VPS changes.
- WhatsApp bridge or webhook routing changes.
- 9Router/provider/credential changes.
- Broad domain implementation.
