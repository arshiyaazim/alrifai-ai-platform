# AL-RIFAI Backup & Restore

**Status:** Phase 1  
**Created:** 2026-09-19

---

## Database Backup

```bash
# Manual backup
docker compose exec alrifai-postgres pg_dump -U alrifai -d alrifai > /home/azim/alrifai-ai-platform/backups/alrifai-$(date +%Y%m%d-%H%M%S).sql

# Automated (script)
/home/azim/alrifai-ai-platform/scripts/backup-db.sh
```

## Restore

```bash
# Stop app first
docker compose stop alrifai-open-webui

# Restore
docker compose exec -i alrifai-postgres psql -U alrifai -d alrifai < backup.sql

# Restart
docker compose start alrifai-open-webui
```

## Volume Backup

```bash
# Docker volume backup
docker run --rm -v alrifai_db_data:/data -v $(pwd)/backups:/backup alpine tar czf /backup/alrifai-db-$(date +%Y%m%d).tar.gz -C /data .
```

## Retention

- Daily: keep 7 days
- Weekly: keep 4 weeks
- Monthly: keep 3 months

## Open WebUI Data

Volume `alrifai_open-webui-data` contains user data, conversations, settings. Backed up separately with the volume backup above.

## Backup Schedule (via new scheduler)

See `docs/scheduler/` for registered tasks.
