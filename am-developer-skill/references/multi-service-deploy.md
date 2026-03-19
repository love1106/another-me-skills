# Multi-Service Deploy Reference

## Khi nào dùng

Project có ≥3 services interdependent (API, worker, dashboard, proxy, orchestrator...).
Deploy sai order hoặc thiếu step → runtime failures mà build/lint không catch.

## Pre-Deploy Checklist

### 1. Map Dependency Graph

Trước khi deploy, xác định:
```
Service A ──depends on──▶ Service B ──depends on──▶ Service C
```

Ví dụ (Another Me):
```
user-dashboard ──▶ another-me-api ──▶ D1 Database
admin-dashboard ──▶ another-me-api
stamina-proxy ──▶ billing worker ──▶ D1 Database
orchestrator ──▶ another-me-api + cliProxy
agent containers ──▶ orchestrator
```

**Rule:** Deploy leaf nodes (no dependents) FIRST, root nodes (most dependents) LAST.

### 2. DB Migrations FIRST

```bash
# LUÔN chạy migration trước deploy code
# CF Workers D1:
npx wrangler d1 migrations apply <DB_NAME> --remote

# PostgreSQL/MySQL:
npx prisma migrate deploy
# hoặc
npx drizzle-kit push
```

⚠️ **Migration phải backward-compatible** — code cũ vẫn chạy được với schema mới.
Nếu không → phải deploy theo sequence: migrate → deploy new code → cleanup old columns.

### 3. Deploy Order Template

```
Phase 1: Database migrations
Phase 2: Backend services (APIs, workers) — leaf → root
Phase 3: Proxy/middleware layers
Phase 4: Frontend (dashboards, UIs)
Phase 5: Orchestrator/scheduler (nếu manage other services)
Phase 6: Smoke test (xem verification-pipeline.md)
```

### 4. FK Dependency — Delete Order

Khi xóa records có foreign keys:
```
DELETE child tables FIRST → parent table LAST
```

Ví dụ: Xóa agent → phải xóa agent_skills, agent_configs, agent_logs... TRƯỚC khi xóa agent record.
**Gotcha:** Nếu quên → "stuck deleting" state, manual DB cleanup required.

## Rollback Strategy

### Stateless Services (CF Workers, containers)

```bash
# CF Workers: rollback to previous version
npx wrangler rollback

# Docker: rollback to previous image
docker compose down
docker tag <service>:latest <service>:rollback
docker compose up -d  # with previous image tag
```

### Stateful Changes (DB, config)

- **DB migration có down():** `npx prisma migrate resolve` hoặc `drizzle-kit rollback`
- **DB migration KHÔNG có down():** phải viết reverse migration thủ công
- **Config changes:** git revert + redeploy

### Cross-Service Rollback

Nếu Service A v2 phụ thuộc Service B v2:
1. Rollback B trước (leaf)
2. Rollback A sau (root)
3. Verify cả hai ở version cũ

## Common Gotchas

| Gotcha | Ví dụ | Prevention |
|--------|-------|------------|
| CF Worker→Worker fetch 503 | Market worker gọi API worker | Dùng Service Bindings, không fetch URL |
| NOT NULL constraint | Deploy code gửi field mới → DB chưa có column | Migrate TRƯỚC deploy |
| Port conflict | 2 services claim same port | Check docker-compose ports, dev server ports |
| Docker image stale | Edit code nhưng container dùng image cũ | `docker compose up -d --build` |
| Env var missing | New service cần env mà chưa set | Checklist env per service trước deploy |
| Auth middleware mismatch | JWT format khác nhau giữa services | Verify token format + claims match |

## Prompt Injection (cho Claude CLI)

Khi task liên quan deploy multi-service:
```
DEPLOY RULES:
- Map service dependencies before deploying
- Deploy leaf services first, root services last
- Run DB migrations BEFORE deploying code
- After deploy: smoke test each service endpoint
- If any service fails: rollback in reverse order (root first, leaf last)
```
