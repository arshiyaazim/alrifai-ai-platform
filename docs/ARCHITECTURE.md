# AL-RIFAI AI Operations Platform — Architecture

**Version:** 1.0.0  
**Status:** DESIGN PHASE — Phase 0 Discovery Complete  
**Created:** 2026-09-19  
**Owner:** Fazle (azim)  
**Public Target:** https://alrifai.iamazim.com

---

## 1. Platform Overview

AL-RIFAI is an independent AI Operations Platform. It is **NOT** a migration of `chat.iamazim.com`, **NOT** a redesign of Fazle-Core, and **NOT** a replacement for the existing production application.

The platform provides:
- **AI Console** (Open WebUI) — human-facing chat interface with local + routed models
- **AL-RIFAI MCP Gateway** — business capability layer bridging AI agents to domain operations
- **Canonical Database** — independent structured data layer with identity-first design
- **Read-Only Connector** — safe import of historical information from Fazle-Core
- **Agents** — domain-specific AI agents with documented permissions
- **Scheduler** — controlled recurring tasks
- **Monitoring** — service health, model provider health, MCP health

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER (Browser)                               │
│                     https://alrifai.iamazim.com                      │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Open WebUI │  ← ghcr.io/open-webui/open-webui:v0.11.3
                    │  (Port 8502)│
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Ollama  │ │ 9Router  │ │  Local   │
        │ Direct   │ │ via ai-  │ │  Models  │
        │ hermes3  │ │ network  │ │ phi4-mini│
        │ phi4-mini│ │ http://  │ │ nomic-   │
        │          │ │9router:  │ │ embed    │
        │          │ │20128/v1  │ │          │
        └──────────┘ └──────────┘ └──────────┘
                           │
                           ▼
                 ┌───────────────────┐
                 │ AL-RIFAI MCP      │
                 │ Gateway           │
                 │ (Domain Tools)    │
                 └────────┬──────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌───────────┐ ┌───────────┐ ┌───────────┐
    │ Recruiting│ │Employee & │ │Billing &  │
    │ Agent     │ │Attendance │ │Accounting │
    │           │ │Agent      │ │Agent      │
    └───────────┘ └───────────┘ └───────────┘
                          │
                          ▼
                 ┌───────────────────┐
                 │  AL-RIFAI Database │
                 │  (PostgreSQL 17)   │
                 │  alrifai-postgres  │
                 └───────────────────┘
```

---

## 3. Independence Guarantees

The new platform is **fully independent** from the existing Fazle-Core system:

| Capability | New Platform | Status |
|---|---|---|
| Build | Own Docker Compose | ✅ Phase 1 |
| Test | Own test suite | ✅ Phase 1 |
| Database | Own PostgreSQL 17 | ✅ Phase 4 |
| Deploy | Own compose, own volumes | ✅ Phase 1 |
| Migrate | Own migration framework | ✅ Phase 4 |
| Backup/Restore | Own procedures | ✅ Phase 1 |
| Monitor | Own health probes | ✅ Phase 10 |
| Run | Own containers | ✅ Phase 1 |
| Upgrade | Own image tags (pinned) | ✅ Phase 1 |
| Log | Own log streams | ✅ Phase 1 |

**NO runtime dependency** on:
- `/home/azim/core`
- Fazle-Core Python modules
- Fazle-Core virtualenv
- Fazle-Core migrations
- Fazle-Core static files
- Fazle-Core systemd services
- `ai-postgres` (old database)

---

## 4. Network Topology

- **`alrifai-net`** (new bridge): Internal platform network for alrifai-postgres + alrifai-open-webui + alrifai-cli
- **`ai-network`** (existing, external): Bridge network connecting 9router (172.22.0.4) and ollama (172.22.0.3)
- Open WebUI joins both networks to reach Ollama and 9Router
- No public exposure of Ollama or 9Router ports

---

## 5. Model Architecture

```
Open WebUI
├── Ollama Direct (Docker network)
│   ├── hermes3:3b        (local chat, small/fast)
│   ├── phi4-mini:latest  (local chat, small/fast)
│   └── nomic-embed-text:latest (local embeddings)
└── 9Router via ai-network (http://9router:20128/v1)
    ├── general  combo
    ├── coding   combo
    ├── fast     combo
    └── auto     combo
```

9Router owns provider/model fallback. Open WebUI consumes the exposed model combos only.

---

## 6. Identity-First Design

Identity is designed **before** business tables. Core principle: human-readable names are attributes, not identity. See `docs/IDENTITY_MODEL.md`.

---

## 7. Security Boundaries

See `docs/SECURITY_BOUNDARIES.md`.

---

## 8. Documentation Index

| Document | Path |
|---|---|
| Architecture | `docs/ARCHITECTURE.md` |
| Domain Model | `docs/DOMAIN_MODEL.md` |
| Identity Model | `docs/IDENTITY_MODEL.md` |
| Data Dictionary | `docs/data-dictionary/DATA_DICTIONARY.md` |
| Business Rules | `docs/rules/BUSINESS_RULES.md` |
| MCP Architecture | `docs/MCP_ARCHITECTURE.md` |
| Agent Architecture | `docs/AGENT_ARCHITECTURE.md` |
| Deployment | `docs/deployment/DEPLOYMENT.md` |
| Backup/Restore | `docs/BACKUP_RESTORE.md` |
| Observability | `docs/OBSERVABILITY.md` |
| Old System Provenance | `docs/provenance/OLD_SYSTEM_PROVENANCE.md` |
| Decision Log | `docs/decisions/DECISION_LOG.md` |
| Security Boundaries | `docs/security/SECURITY_BOUNDARIES.md` |
| Session Handoff | `docs/SESSION_HANDOFF.md` |
| Implementation Status | `docs/IMPLEMENTATION_STATUS.md` |
