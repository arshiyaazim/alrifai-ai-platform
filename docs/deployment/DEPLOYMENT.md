# AL-RIFAI Deployment Guide

**Status:** Phase 1 — Docker Compose Ready  
**Created:** 2026-09-19

---

## Quick Start

```bash
# 1. Copy env template
cp .env.example .env
# Edit .env with real credentials (NEVER commit .env)

# 2. Create .env with secrets
# Required: POSTGRES_PASSWORD, WEBUI_SECRET_KEY, NINE_ROUTER_API_KEY

# 3. Start platform
docker compose up -d alrifai-postgres alrifai-open-webui

# 4. Wait for DB ready, then init database
docker compose exec alrifai-postgres psql -U alrifai -d alrifai -c "SELECT 1"

# 5. Check status
docker compose ps
docker compose logs alrifai-open-webui
```

---

## Services

| Service | Container | Port | Image |
|---|---|---|---|
| PostgreSQL | `alrifai-postgres` | 127.0.0.1:5433 | `postgres:17-alpine@sha256:f021...` |
| Open WebUI | `alrifai-open-webui` | 127.0.0.1:8502 | `ghcr.io/open-webui/open-webui:v0.11.3` |
| CLI Shell | `alrifai-cli` | — | `postgres:17-alpine` (profile: admin) |

---

## Pinned Releases

| Component | Version | Digest | Notes |
|---|---|---|---|
| Open WebUI | v0.11.3 | ghcr.io/open-webui/open-webui:v0.11.3 | Latest stable release (2026-08-31) |
| PostgreSQL | 17-alpine | sha256:f02121de6f74d30d8a94cd1d9584125e2178d7e6c377d8130112d4e52d867995 | Matching existing |
| 9Router | 0.5.75 | External (existing) | Already running on ai-network |
| Ollama | latest | External (existing) | Already running on ai-network |

---

## Network Access

- **9Router:** `http://9router:20128/v1` via `ai-network`
- **Ollama:** `http://ollama:11434` via `ai-network`
- **Admin Dashboard:** `http://127.0.0.1:20129/dashboard`
- **New Open WebUI:** `http://127.0.0.1:8502`
- **New PostgreSQL:** `127.0.0.1:5433`

---

## Backup Strategy

See `docs/BACKUP_RESTORE.md`.

## Monitoring

See `docs/OBSERVABILITY.md`.

---

## Rollback

If Open WebUI v0.11.3 has issues:
1. Stop: `docker compose stop alrifai-open-webui`
2. Rollback to previous compose revision
3. Data volume persists (separate volume)
