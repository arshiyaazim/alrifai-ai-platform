# Release and Rollback

## Release checklist

Before deployment:

- Confirm the approved commit hash or signed release tag.
- Confirm the VPS working tree has no unexpected changes.
- Confirm `.env` is present, private, and not copied into Git.
- Run `docker compose config`.
- Run tests and `git diff --check` in CI.
- Validate migration files; never apply destructive migrations automatically.
- Create and verify a PostgreSQL backup.
- Confirm the affected service list is AL-RIFAI-only.

During deployment:

```bash
cd /home/azim/alrifai-ai-platform
docker compose up -d alrifai-postgres alrifai-open-webui
```

After deployment:

```bash
./scripts/health-check.sh
docker compose ps
git show -s --format='%H %s' HEAD
```

Record the commit, timestamp, services changed, health result, and operator in the deployment log or approved release record. Do not store secrets in that record.

## Rollback

1. Stop the release and identify the last known-good commit.
2. Confirm the database backup and whether the release changed schema.
3. Check out the last known-good code commit in the AL-RIFAI repository only.
4. Re-run `docker compose config`.
5. Restart only affected AL-RIFAI services.
6. Run health checks and verify Open WebUI/database connectivity.
7. If schema changes were involved, use a reviewed, tested down-migration or restore procedure; do not guess and do not drop data automatically.
8. Record the rollback commit and reason.

Never roll back by deleting Docker volumes. The `alrifai_db_data` and `alrifai_open-webui-data` volumes are persistent state.

## Database policy

GitHub may contain schema definitions, migration scripts, seed templates, and sanitized fixtures. It must not contain live PostgreSQL data, production credentials, employee data, payroll transactions, WhatsApp exports, or database dumps.
