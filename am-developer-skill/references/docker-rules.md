# Docker Management Rules

Deploy and manage Docker services with consistent conventions.

## Directory Convention

```
/docker/
├── {app_name}/
│   ├── docker-compose.yml
│   ├── .env                    # app-specific env vars
│   ├── data/                   # persistent data (volumes mount here)
│   ├── config/                 # config files mounted into containers
│   ├── logs/                   # log volumes (if needed)
│   └── backups/                # local backup snapshots
```

**All volumes MUST be bind-mounted within `/docker/{app_name}/`** — no Docker named volumes.
This makes backup simple: `tar -czf backup.tar.gz /docker/{app_name}/`

## Mandatory Rules

### 1. Always `restart: unless-stopped`
Every service MUST have:
```yaml
restart: unless-stopped
```

### 2. Always pin image versions
```yaml
# ✅ Good
image: falkordb/falkordb:v4.2.1

# ❌ Bad
image: falkordb/falkordb:latest
```
Exception: development/testing environments.

### 3. Always use `.env` for secrets
```yaml
# docker-compose.yml
environment:
  - DB_PASSWORD=${DB_PASSWORD}

# .env
DB_PASSWORD=supersecret
```
Never hardcode secrets in docker-compose.yml.

### 4. Always set resource limits (when relevant)
```yaml
deploy:
  resources:
    limits:
      memory: 512M
```

### 5. Always use explicit port mapping
```yaml
ports:
  - "127.0.0.1:6379:6379"   # ✅ bind to localhost only
  - "6379:6379"               # ⚠️ exposed to all interfaces
```
Default: bind to `127.0.0.1` unless external access is needed.

### 6. Always label containers
```yaml
labels:
  - "com.app={app_name}"
  - "com.managed-by=agent"
```

### 7. Network isolation
- Each app gets its own network (auto-created by compose)
- Cross-app communication: create shared network explicitly

### 8. Health checks when available
```yaml
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Workflow

### Deploy new app
```bash
APP_NAME="myapp"
mkdir -p /docker/$APP_NAME/{data,config,logs,backups}

# Create docker-compose.yml following rules above
# Create .env with secrets

cd /docker/$APP_NAME
docker compose up -d

# Verify
docker compose ps
docker compose logs --tail=20
```

### Backup app
```bash
APP_NAME="myapp"
cd /docker/$APP_NAME
docker compose stop
tar -czf backups/$(date +%Y%m%d_%H%M%S).tar.gz data/ config/ .env docker-compose.yml
docker compose start
```

### Update app
```bash
APP_NAME="myapp"
cd /docker/$APP_NAME

# Backup first
tar -czf backups/pre-update-$(date +%Y%m%d).tar.gz data/ config/ .env docker-compose.yml

# Update image version in docker-compose.yml
# Then:
docker compose pull
docker compose up -d
docker compose logs --tail=20
```

### Status check
```bash
# All apps
for d in /docker/*/; do
  echo "=== $(basename $d) ==="
  cd "$d" && docker compose ps 2>/dev/null
  echo
done

# Specific app
cd /docker/$APP_NAME && docker compose ps && docker compose logs --tail=10
```

### Teardown (careful!)
```bash
APP_NAME="myapp"
cd /docker/$APP_NAME

# Backup first!
tar -czf backups/final-$(date +%Y%m%d).tar.gz data/ config/ .env docker-compose.yml

# Stop and remove containers
docker compose down

# Data remains in /docker/$APP_NAME/data/ until manually deleted
```

## Registry

Maintain a list of deployed apps in `/docker/REGISTRY.md`:

```markdown
# Docker Registry

| App | Port(s) | Status | Notes |
|-----|---------|--------|-------|
| graphiti | 6379, 3000 | running | FalkorDB knowledge graph |
```

**Update REGISTRY.md after every deploy/teardown.**

## Backup Strategy

- **Manual:** `tar -czf` as shown above
- **Automated:** Create cron job per app if critical
- **Off-site:** Push to R2/S3 if needed

## Key Principles

- **Convention over configuration** — every app follows the same structure
- **Backup-friendly** — all state in one directory
- **Secure by default** — localhost binding, env secrets, resource limits
- **Reproducible** — docker-compose.yml + .env = full rebuild
