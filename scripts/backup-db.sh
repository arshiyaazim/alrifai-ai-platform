#!/bin/bash
set -euo pipefail

BACKUP_DIR="/home/azim/alrifai-ai-platform/backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/alrifai-${TIMESTAMP}.sql"

docker compose exec alrifai-postgres pg_dump -U "${POSTGRES_USER:-alrifai}" -d "${POSTGRES_DB:-alrifai}" > "$BACKUP_FILE"
echo "Backup created: $BACKUP_FILE"

# Cleanup old backups (keep 7 days)
find "$BACKUP_DIR" -name "alrifai-*.sql" -mtime +7 -delete
