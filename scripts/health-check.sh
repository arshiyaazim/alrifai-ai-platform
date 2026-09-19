#!/bin/bash
set -euo pipefail

echo "=== AL-RIFAI Health Check ==="

# PostgreSQL
PG_STATUS=$(docker inspect alrifai-postgres --format '{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
echo "PostgreSQL: $PG_STATUS"

# Open WebUI
OWH_STATUS=$(docker inspect alrifai-open-webui --format '{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
echo "Open WebUI: $OWH_STATUS"

# 9Router (external)
NINE_STATUS=$(curl -s --max-time 3 http://127.0.0.1:20128/v1/models 2>/dev/null && echo "OK" || echo "FAIL")
echo "9Router: $NINE_STATUS"

# Ollama (external)
OLLAMA_STATUS=$(curl -s --max-time 3 http://127.0.0.1:11434/api/tags 2>/dev/null && echo "OK" || echo "FAIL")
echo "Ollama: $OLLAMA_STATUS"

# Containers
docker compose ps
