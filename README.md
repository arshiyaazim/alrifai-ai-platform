# AL-RIFAI AI Operations Platform

**Independent AI Operations Platform**  
**Target:** https://alrifai.iamazim.com  
**Status:** Phase 1 — Repository Foundation Complete

## Overview

A new, fully independent AI operations platform. Not a migration of chat.iamazim.com. Not a redesign of Fazle-Core. Not a replacement for the existing production application.

## Quick Start

```bash
cp .env.example .env
# Edit .env with real credentials
docker compose up -d alrifai-postgres alrifai-open-webui
```

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
