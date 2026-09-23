# Historical Session Handoff

> Current continuity authority is [`docs/development/AGENT_HANDOFF.md`](development/AGENT_HANDOFF.md), together with `CURRENT_STATE.md`, `ACTIVE_TASK.md`, `BLOCKERS.md`, and `docs/architecture/MASTER_ARCHITECTURE.md`. This document is retained as historical project context.

**Last Completed Phase:** GitHub repository, local development, and VPS deployment audit
**Current Commits:**
- `d4920cc` — Phase 0-1: AL-RIFAI AI Operations Platform foundation
- `5e0407e` — Phase 2-3: Deploy NEW Open WebUI v0.11.3, Ollama + 9Router integration, database tests
- `73b32a5` — Dual-workflow architecture audit and schema inventory for current Fazle-Core and AL-RIFAI
- `pending audit commit` — GitHub remote, publication safety, Windows development, and VPS deployment audit
**Branch:** main
**Current Running New Services:** alrifai-postgres (5434, healthy), alrifai-open-webui (8502, healthy)
**Verified Tests:** 11/11 pass (phone normalization + identity resolution)
**Open Blockers:** GitHub CLI/account authentication and owner approval of the first private remote repository are pending
**Next Safe Action:** Owner verifies `arshiyaazim`, creates the empty private repository, then approves the first push

**Owner Action Required:**
- Review .env (not committed, in working tree) for credential rotation
- Restrict VPS `.env` permissions to owner-only and rotate any exposed credentials
- Approve the canonical domain-service design before implementation begins
- Approve the GitHub owner, private visibility, and first-push plan
- Phase 11 (Nginx publication for alrifai.iamazim.com) requires explicit approval

---

## Phase Summary

### PHASE 0: Discovery (Complete)
Read-only inspection of:
- Fazle-Core domain modules, migrations, schemas
- 9Router config (compose, .env, model catalog, auth)
- Ollama models (hermes3:3b, phi4-mini:latest, nomic-embed-text:latest)
- Existing Open WebUI (`:main` mutable tag, port 8501)
- Docker networks (ai-network: 172.22.0.0/16)
- Open WebUI latest release: v0.11.3 (2026-08-31)

### PHASE 1: Repository Foundation (Complete)
Created:
- `/home/azim/alrifai-ai-platform/` directory structure
- `.gitignore`, `.env.example`
- `docker-compose.yml` with pinned Open WebUI v0.11.3 + PostgreSQL 17
- Architecture, Identity, Data Dictionary, Business Rules, Old System Provenance docs
- Deployment, Backup, Observability, Security docs

### PHASE 2: NEW Open WebUI Deploy (Complete)
- Image: `ghcr.io/open-webui/open-webui:v0.11.3` (pinned release)
- Port: 127.0.0.1:8502
- Database: alrifai-postgres (new volume, independent)
- Health: confirmed serving at port 8502

### PHASE 3: Ollama + 9Router Integration (Complete)
- Ollama: reachable via ai-network → hermes3:3b, phi4-mini:latest, nomic-embed-text:latest confirmed
- 9Router: reachable at http://9router:20128/v1 via ai-network, API key configured
- Admin dashboard: http://127.0.0.1:20129/dashboard

### PHASE 4: Database Foundation (Complete)
- PostgreSQL 17: port 5434, healthy
- 13 tables created: persons, person_identifiers, person_phones, person_aliases, contact_methods, payout_accounts, external_platform_ids, employees, applicants, clients, business_events, audit_log, provenance_records
- Indexes for identity resolution

### PHASE 5: Identity + Data Dictionary + Business Rules (Complete)
- docs/identity/IDENTITY_MODEL.md
- docs/data-dictionary/DATA_DICTIONARY.md
- docs/rules/BUSINESS_RULES.md
- 20+ documented rules with provenance

### PHASE 6: Current System Audit (Complete)
- Messaging workflow audit: bridge polling → identity resolution → message routing → validation → domain DB writes → outbound reply
- Frontend form workflow audit: API route → validation → domain service → DB transaction → audit trail
- Fazle-Core schema audit: hybrid legacy + FPE + operations tables; identified overlapping identity and ledger tables
- AL-RIFAI live schema audit: all 13 tables confirmed and matched to the live database
- Canonical convergence model documented: single business layer, not duplicate per-channel logic

### PHASE 7: Domain Architecture Review (Complete)
- Six-domain ownership matrix defined
- Canonical workflow model documented
- Error isolation and domain codes defined
- Audit files under `docs/audits` and `docs/architecture` created

### PHASE 8: Safe implementation gate (Current)
- Do not implement new business features yet
- Do not create new MCP servers yet
- Use canonical service contracts and integration boundaries before any implementation

### PHASE 9: GitHub and deployment audit (Complete)
- Local Git repository verified: `main`, clean, no remote, no upstream
- Commits `d4920cc`, `5e0407e`, and `73b32a5` verified locally
- GitHub CLI unavailable on VPS; account and push permission remain unverified
- No accessible matching repository found through read-only GitHub search
- Publication safety reviewed; real `.env` remains ignored and untracked
- Windows setup, GitHub-to-VPS release flow, rollback, and secrets policy documented
- Backup SQL paths added to `.gitignore`
- PostgreSQL documentation port corrected to `5434`

---

## Imported Knowledge
- Fazle-Core identity modules → canonical identity model
- Fazle-Core business modules → domain boundaries
- Fazle-Core migrations → schema patterns
- Fazle-Core ownership matrix → integration boundaries
- 9Router model catalog → available model combos
- Current Fazle-Core dual-workflow audit → canonical convergence model

## Identity/Data Decisions
- UUID primary keys, never name/phone as PK
- Phone normalization via canonical library (Bangladeshi +880XXXXXXXXX)
- Payout number = financial routing, not identity
- External platform IDs explicitly typed
- Provenance tracking for all imports
- Messaging and form flows must converge via a shared canonical business engine
- GitHub remote creation and first push require explicit owner approval

## Running Services
| Service | Container | Port | Status |
|---|---|---|---|
| PostgreSQL 17 | alrifai-postgres | 127.0.0.1:5434 | healthy |
| Open WebUI v0.11.3 | alrifai-open-webui | 127.0.0.1:8502 | healthy |

## Not Yet Running
- MCP Gateway
- Agents
- Scheduler
- Read-only Connector
- Monitoring (Prometheus/Grafana)
- Nginx publication (alrifai.iamazim.com)

## Blocked
- GitHub account verification on VPS because `gh` is not installed
- First remote creation and push pending owner approval

## Owner Approval Required
- Phase 11 (Nginx publication) requires explicit approval
- Production credential rotation
- Canonical domain service design approval before feature implementation
- GitHub account/visibility and first-push approval
