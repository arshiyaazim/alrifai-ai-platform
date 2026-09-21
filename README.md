# AL-RIFAI AI Operations Platform

**Independent AI Operations Platform**  
**Target:** https://alrifai.iamazim.com  
**Status:** Phase 1 — Repository Foundation Complete

## Overview

A new, fully independent AI operations platform intended to replace Fazle-Core after safe verification and an approved migration/cutover plan. It has no runtime dependency on the legacy system during development.

## Quick Start

```bash
cp .env.example .env
# Edit .env with real credentials
docker compose up -d alrifai-postgres alrifai-open-webui
```

## Local AL-RIFAI Web Application

Create or preserve the Git-ignored `.env.local` connection file, then start the
local web application:

```powershell
.\scripts\start-alrifai-web.ps1
```

The launcher loads `.env.local` automatically and verifies the database before
starting. Never commit `.env.local` or copy it to production.

Open `http://127.0.0.1:8000/`, or use VS Code's Command Palette → **Simple
Browser: Show**. Bootstrap the approved Owner interactively without putting a
password in the command line:

```powershell
.venv\Scripts\python.exe -m src.alrifai.auth.bootstrap_owner
```

The bootstrap command requires username `azimpolcu`, hides password input, and
requires a first-login password change. Never use a production or business-data
database for local development.

## Access Points

| Service | URL |
|---|---|
| Open WebUI | http://127.0.0.1:8502 |
| 9Router Dashboard | http://127.0.0.1:20129/dashboard |
| PostgreSQL | 127.0.0.1:5434 |

## Architecture

- **Open WebUI v0.11.3** (pinned) — AI console
- **PostgreSQL 17** — Independent database
- **Ollama** — Local models (hermes3:3b, phi4-mini:latest)
- **9Router** — Routed models via ai-network
- **AL-RIFAI MCP Gateway** — Business capability layer
- **Agents** — Domain-specific AI agents

## Documentation

See `docs/` for full documentation.

## Independence

This platform has NO runtime dependency on Fazle-Core, chat.iamazim.com, or the existing production system.

## Git

```
Repository: /home/azim/alrifai-ai-platform
Branch: main
Status: New repository
```
