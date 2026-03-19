# Cloudflare Tunnel Setup (one-time per project)

Hướng dẫn tạo Cloudflare Named Tunnel cho dev preview. Chỉ cần làm 1 lần cho mỗi project.

## Domain Pattern

- **API:** `<project>-api.storims.com`
- **Web:** `<project>-web.storims.com`

Ví dụ cho open-ship:
- `openship-api.storims.com` → localhost:3002
- `openship-web.storims.com` → localhost:3003

## Setup Steps

```bash
# 1. Tạo tunnel
cloudflared tunnel create <project>-dev

# 2. Route DNS
cloudflared tunnel route dns <project>-dev <project>-api.storims.com
cloudflared tunnel route dns <project>-dev <project>-web.storims.com

# 3. Update ~/.cloudflared/config.yml — thêm ingress rules:
#   - hostname: <project>-api.storims.com
#     service: http://localhost:<api-port>
#   - hostname: <project>-web.storims.com
#     service: http://localhost:<web-port>

# 4. Update frontend .env với tunnel URLs (nếu cần)
```

## Run / Stop / Check

```bash
# Start (persistent — KHÔNG chạy foreground trong exec session)
nohup cloudflared tunnel run <tunnel-name> &>/tmp/cloudflared.log &
# hoặc
tmux new-session -d -s tunnel "cloudflared tunnel run <tunnel-name>"

# Check
pgrep -f "cloudflared tunnel" && echo "running" || echo "dead"
tail -5 /tmp/cloudflared.log

# Stop
pkill -f "cloudflared tunnel run"
# hoặc
tmux kill-session -t tunnel
```

⚠️ **Không bao giờ chạy foreground** (`cloudflared tunnel run ...` trực tiếp) — tunnel sẽ die khi exec session timeout.
