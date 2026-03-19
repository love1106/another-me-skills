# Dev Preview (Cloudflare Tunnel)

Cho user/team access dev server từ bất kỳ đâu qua public URL.

**Trigger:** User nói "test thử", "cho anh xem", "manual test", "review UI", hoặc yêu cầu link preview.
**Bỏ qua** nếu task nhỏ, backend-only, hoặc user mở localhost trực tiếp được.

**Flow tự động (agent chạy hết, chỉ gửi link cho user khi ready):**

```
1. Start dev server (nếu chưa chạy)
2. Wait until dev server responds
3. Start Cloudflare tunnel
4. Wait until tunnel URL responds
5. Gửi link cho user
6. Giữ tunnel alive cho đến khi user nói xong
```

## 1. Start Dev Server

```bash
cd ~/projects/<repo>

# Re-detect package manager
if [ -f pnpm-lock.yaml ]; then PM="pnpm"
elif [ -f yarn.lock ]; then PM="yarn"
elif [ -f bun.lockb ]; then PM="bun"
else PM="npm"; fi

# Auto-detect port từ package.json/config
PORT=$(node -e "
  try {
    const pkg = require('./package.json');
    const dev = pkg.scripts?.dev || '';
    const m = dev.match(/(?:--port|PORT=?|-p)\s*(\d+)/);
    console.log(m ? m[1] : '3000');
  } catch { console.log('3000'); }
" 2>/dev/null)

# Kill dev server cũ nếu đang chạy (tránh port conflict)
tmux kill-session -t dev 2>/dev/null || true
lsof -ti:$PORT | xargs kill -9 2>/dev/null || true

# Start trong tmux (persistent)
tmux new-session -d -s dev "$PM run dev"
```

## 2. Wait Until Dev Server Ready

```bash
for i in $(seq 1 30); do
  if curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT | grep -qE "^(200|301|302|304)"; then
    echo "✅ Dev server ready on port $PORT"
    break
  fi
  [ $i -eq 30 ] && echo "❌ Dev server timeout after 30s" && exit 1
  sleep 1
done
```

## 3. Start Tunnel & Verify

```bash
pkill -f "cloudflared tunnel" 2>/dev/null || true
sleep 1

# Quick tunnel (tạo URL tạm)
cloudflared tunnel --url http://localhost:$PORT &>/tmp/cloudflared.log &
TUNNEL_PID=$!

# Chờ tunnel URL (max 15s)
TUNNEL_URL=""
for i in $(seq 1 15); do
  TUNNEL_URL=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" /tmp/cloudflared.log 2>/dev/null | head -1)
  [ -n "$TUNNEL_URL" ] && break
  sleep 1
done

if [ -z "$TUNNEL_URL" ]; then
  echo "❌ Tunnel failed to start"
  cat /tmp/cloudflared.log | tail -10
  exit 1
fi

# Verify
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$TUNNEL_URL" 2>/dev/null)
if echo "$HTTP_STATUS" | grep -qE "^(200|301|302|304)"; then
  echo "✅ Tunnel ready: $TUNNEL_URL"
else
  echo "⚠️ Tunnel URL returned $HTTP_STATUS — có thể cần vài giây nữa"
fi
```

Named tunnel (subdomain cố định): xem [tunnel-setup.md](tunnel-setup.md).

## 4. Gửi Link cho User

```
🔗 App ready for review:
- Local: http://localhost:<PORT>
- Public: <TUNNEL_URL>
Dev server đang chạy. Anh test xong báo em để cleanup nhé.
```

**KHÔNG cleanup cho đến khi user nói xong.** Giữ dev server + tunnel alive.

## 5. Cleanup (khi user nói xong)

```bash
pkill -f "cloudflared tunnel" 2>/dev/null || true
tmux kill-session -t dev 2>/dev/null || true
lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
rm -f /tmp/cloudflared.log
echo "✅ Cleaned up dev server + tunnel"
```
