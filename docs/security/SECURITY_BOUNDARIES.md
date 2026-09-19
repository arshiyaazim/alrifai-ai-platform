# AL-RIFAI Security Boundaries

**Status:** Phase 1  
**Created:** 2026-09-19

---

## Credential Management

**Rule:** Never print credentials. Never put secrets in Git.

Secrets are handled via:
- `.env` file (excluded from Git via `.gitignore`)
- Docker secrets (future)
- Environment variables injected at runtime

**Credential Status:**
- PostgreSQL password: **SET** (in .env)
- Open WebUI secret: **SET** (in .env)
- 9Router API key: **SET** (in .env, sourced from 9router/data/auth/cli-secret)
- SMTP credentials: **REQUIRED** (owner to provide)

## Access Boundaries

| Boundary | Rule |
|---|---|
| Fazle-Core | READ-ONLY. Never modify. |
| chat.iamazim.com | Untouched. |
| existing Open WebUI | Untouched (runs on port 8501). |
| ai-postgres | Untouched (old DB). New DB is alrifai-postgres. |
| WhatsApp bridges | Untouched. |
| Hermes services | Untouched. |
| current 9Router config | Untouched. |
| Ollama models | Untouched. |
| firewall | Untouched. |
| system-wide security | Untouched. |
| production Nginx | Untouched until Phase 11 approval. |

## Permission Model

Every MCP/tool declares a permission class:
- `READ` — search, list, view
- `DRAFT` — preview, draft
- `VALIDATE` — verify, check
- `WRITE` — create, update
- `ADMIN` — restart, deploy, config

Agents receive minimum required classes.

## Separation of Concerns

- **READ SYSTEM** — Discovery, queries, search
- **CHANGE SYSTEM** — Code, tests, commits (new repo only)
- **DEPLOY SYSTEM** — Docker compose, rollout

## Audit

All mutations logged to `audit_log` table. Every action has:
- Actor, action, before, after, IP, correlation ID, timestamp

## Secret Rotation

- `APP_SECRET_KEY`: Rotate quarterly
- `WEBUI_SECRET_KEY`: Rotate quarterly
- `POSTGRES_PASSWORD`: Rotate quarterly
- 9Router API key: Rotate per 9Router policy
