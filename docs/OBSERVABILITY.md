# AL-RIFAI Observability

**Status:** Phase 10 (planned) — Foundation in Phase 1  
**Created:** 2026-09-19

---

## Health Checks

All containers have Docker healthchecks:
- `alrifai-postgres`: `pg_isready`
- `alrifai-open-webui`: `curl -f http://localhost:8080/api/health`

## Observability Targets

| Target | Status | Method |
|---|---|---|
| Container health | ✅ | Docker healthchecks |
| Service health | ✅ | Health endpoints |
| Model provider health | ⏳ | Health probe (9Router, Ollama) |
| MCP health | ⏳ | Health probes |
| Database health | ✅ | pg_isready |
| Scheduler health | ⏳ | Task registry |
| Failed jobs | ⏳ | Error logging |
| Message backlog | ⏳ | Queue monitoring |
| Duplicate detection | ⏳ | Audit queries |
| Agent/tool failures | ⏳ | Error logging |
| API latency | ⏳ | Metrics |
| Model routing failures | ⏳ | 9Router logs |

## Log Streams

```bash
# All platform logs
docker compose logs

# Specific service
docker compose logs alrifai-open-webui
docker compose logs alrifai-postgres
```

## Error Handling Standard

All errors internally record:
- Correlation ID
- Operation
- Service
- Tool/Agent
- Timestamp
- Retry state
- Underlying error

**Rule:** No raw stack traces to end users.

## Monitoring Without Mutation

Observability grants NO mutation rights. Monitoring ≠ admin access.
