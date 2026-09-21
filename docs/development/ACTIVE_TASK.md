# Active Development Task

**Task:** Task 03B-03 — Owner account setup and frontend credential management
**Status:** Implemented locally and verified; public VPS HTTPS configuration is blocked by missing sudo authorization.
**Scope:** Initial Owner account, self-service username/password management, administrative user reset, and session revocation.

Follow-up completed in this worktree: local Open WebUI home integration and server-side Admin navigation gate. Open WebUI uses its own `.local-data/open-webui` state. The public design is Nginx on `alrifai.iamazim.com` → Windows Tailscale Serve → AL-RIFAI/Open WebUI; it has not been enabled on VPS.

## Next implementation task

After an authorized VPS administrator performs the isolated Nginx/certificate step, verify the real HTTPS login and browser/mobile flow. Do not duplicate provider routing in Open WebUI.

## Explicitly not authorized by this task

- Schema migrations or database changes.
- Production deployment, external reset delivery, WhatsApp authentication, and MCP actor propagation.
- Public HTTPS configuration until an authorized sudo-capable VPS operation is available.
- Production/VPS changes.
- WhatsApp bridge or webhook routing changes.
- 9Router/provider/credential changes.
- Broad domain implementation.
