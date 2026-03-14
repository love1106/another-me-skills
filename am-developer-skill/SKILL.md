---
name: am-developer-skill
description: "Developer workflow cho mọi coding tasks — spawn Claude Code CLI, planning, branching, verification, dev preview, PR. Code trên container hoặc user's device qua SSH."
---

# Another Me Developer Skill

Developer workflow cho MỌI coding tasks — từ quick edits đến complex multi-file features.

Workspace mặc định: `~/.openclaw/projects/<repo>`

## ⛔ Hard Rules (NEVER VIOLATE)

1. **NEVER self-code when Claude Code CLI is available.**
   Agent là orchestrator, KHÔNG PHẢI coder.
   Mọi task cần code → spawn Claude CLI (Bước 4).
   Duy nhất exception: edit < 3 dòng trivial (typo, config value).

2. **MUST report failures.**
   Sau 3 attempts fail → BÁO USER NGAY.
   Nội dung: lỗi gì, đã retry mấy lần, đề xuất hướng xử lý.
   KHÔNG ĐƯỢC: im lặng, tự code thay, hoặc bỏ qua task.

3. **MUST monitor background spawns.**
   Spawn background → poll mỗi 30-60s → report khi: done, fail, hoặc chạy > 5 phút.
   KHÔNG ĐƯỢC: spawn rồi quên.

4. **MUST update user on progress.**
   - Spawn: báo "Đang chạy Claude Code cho [task], ETA ~X phút"
   - Error/stderr: báo ngay, kèm log snippet
   - Done: báo kết quả + files changed
   - **Im lặng > 3 phút sau spawn = BUG** — phải fix ngay

## Prerequisites

```bash
# Claude CLI
which claude && claude --version || echo "❌ Claude CLI chưa install"

# Git
git --version && git config user.name && git config user.email || echo "❌ Git chưa config"

# GitHub CLI (cần cho PR)
which gh && gh auth status 2>/dev/null || echo "⚠️ gh CLI chưa setup (PR sẽ không tạo được)"

# Env vars
[ -n "$ANTHROPIC_API_KEY" ] && echo "✅ API key set" || echo "❌ ANTHROPIC_API_KEY chưa set"

# Tunnel (cần cho dev preview)
which cloudflared && echo "✅ cloudflared installed" || echo "⚠️ cloudflared chưa install (dev preview sẽ không có)"
```

**Nếu Claude CLI không available:** Agent code bằng `read`/`edit`/`write` tools trực tiếp. Báo user.

## Khi nào dùng

✅ **Dùng khi:** Bất kỳ task cần code — feature, bug fix, refactor, test, review, scaffolding
❌ **Không dùng khi:** Edit < 3 dòng trivial → `edit` tool. Chỉ đọc code → `read` tool.

### Task Size → Workflow

| Task size | Ví dụ | Workflow |
|-----------|-------|----------|
| **Quick** (1-3 files) | Fix CSS, update text | Bước 1 gọn → Skip 2-3 → Bước 4 → Bước 5 nhẹ (5.1 Build + 5.6 Diff). PR optional |
| **Medium** (3-10 files) | New component, refactor | Full workflow |
| **Large** (>10 files) | New feature, migration | Full workflow bắt buộc |

## Bước 1: Phân tích yêu cầu & Xác định Workspace

### 1.1 Phân tích Input/Output (BẮT BUỘC)

1. **Input** — Dữ liệu/điều kiện đầu vào
2. **Output mong đợi** — Kết quả cuối cùng
3. **Acceptance Criteria** — Tiêu chí "done" cụ thể
4. **Ambiguous → hỏi.** Suy luận được → ghi assumption, tiến hành.

> ⏩ Trình bày cùng plan ở Bước 2 → user confirm 1 lần duy nhất.

### 1.2 Xác định Workspace

#### Option A: Container (mặc định)
```bash
WORKSPACE=~/.openclaw/projects
mkdir -p $WORKSPACE && cd $WORKSPACE
[ ! -d "<project-name>" ] && git clone <repo-url> <project-name>
cd <project-name>
```

#### Option B: User's device (qua SSH)
Kết hợp với `am-devices` skill. Dùng khi cần native environment (iOS, GPU).
```bash
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519"
ssh $SSH_OPTS {user}@{ip} "ls -la ~/projects/{project}"
```

| Tình huống | Workspace |
|------------|-----------|
| Web app, API, backend | Container |
| Mobile app, native build, GPU | Device (SSH) |
| User không specify | Container |

## Bước 2: Planning

1. **What** — Break down subtasks
2. **Where** — Files/modules affected
3. **How** — Approach, check conventions
4. **Impact** — What could break?

```bash
cat ~/.openclaw/projects/<repo>/.claude/instructions.md 2>/dev/null
cat ~/.openclaw/projects/<repo>/CLAUDE.md 2>/dev/null
```

Trình bày: **acceptance criteria + plan** → chờ approval 1 lần.
💡 Task nhỏ: gộp Bước 1-2 thành 1 message.

## Bước 3: Create Feature Branch

> ⚠️ **Biến không share giữa exec sessions.** Re-detect mỗi lần.

```bash
cd ~/.openclaw/projects/<repo>

# === Environment Setup (copy vào đầu mỗi exec session) ===
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
if [ -z "$DEFAULT_BRANCH" ]; then
  DEFAULT_BRANCH=$(git branch -r 2>/dev/null | grep -E 'origin/(main|master)' | head -1 | sed 's|.*origin/||')
  DEFAULT_BRANCH=${DEFAULT_BRANCH:-main}
fi
if [ -f package.json ]; then
  if [ -f pnpm-lock.yaml ]; then PM="pnpm"
  elif [ -f yarn.lock ]; then PM="yarn"
  elif [ -f bun.lockb ]; then PM="bun"
  else PM="npm"; fi
fi
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519"
# ===================================================================

git stash --include-untracked 2>/dev/null || true
git checkout $DEFAULT_BRANCH && git pull origin $DEFAULT_BRANCH
[ -n "$PM" ] && $PM install
git checkout -b <branch-type>/<short-description> 2>/dev/null \
  || git checkout <branch-type>/<short-description>
```

Branch types: `feat/`, `fix/`, `refactor/`, `chore/`, `docs/`, `perf/`, `test/`

## Bước 4: Code với Claude CLI

**⚡ Hot Reload First:** Nếu app hỗ trợ hot reload → ưu tiên dev server.

**Quy tắc:**
- Claude CLI **chỉ edit files, KHÔNG commit**
- Luôn thêm `"DO NOT git commit or push."` vào cuối prompt
- Respect `.claude/instructions.md`

### 4.1 Spawn Claude Code CLI

**Container (root):**
```bash
cd ~/.openclaw/projects/<repo>
claude --dangerously-skip-permissions --output-format json -p "
<task description>
DO NOT git commit or push.
"
```

**Non-root fallback:**
```bash
su - coder -c "
export ANTHROPIC_API_KEY='$ANTHROPIC_API_KEY'
cd <workdir>
claude --permission-mode bypassPermissions --output-format json -p 'task'
"
```

**Background (task > 2 phút) — OpenClaw tool calls:**
```
exec(background:true, command:"claude --dangerously-skip-permissions --output-format json -p 'task'")
process(action:poll, sessionId:xxx, timeout:60000)
```

**Long prompts → write to file:**
```bash
cat > /tmp/prompt.md << 'PROMPT'
Your long prompt here...
PROMPT
cat /tmp/prompt.md | claude --dangerously-skip-permissions --output-format json -p -
```

### 4.2 Prompt Strategy

**High-level prompts, KHÔNG micromanage.** Cung cấp: Goal, Constraints, Edge cases, Safety.

**Coding rules (luôn inject):** Đọc section "Tóm tắt" cuối [references/coding-rules.md](references/coding-rules.md), append vào cuối prompt. 9 defensive programming rules bắt buộc.

**2-Phase cho complex tasks:**
```
Phase 1 (Plan): "Analyze + plan. Output: {steps, questions}"
Phase 2 (Implement): "Implement. [answers]" → resume via session_id
```

### 4.3 Timeout & Retry (BẮT BUỘC)

| Task type | Timeout |
|-----------|---------|
| Quick | 120s |
| Medium | 300s |
| Large | 600s |

**Max 3 attempts.** Fail → BÁO USER (Hard Rule #2). Task > 10 files → LUÔN split.

### 4.4 Parse Result

```json
{ "type": "result", "result": "...", "session_id": "uuid", "is_error": false, "total_cost_usd": 0.05 }
```

### 4.5 Monitoring (BẮT BUỘC cho background spawns)

1. Spawn → báo user ETA
2. Poll mỗi 30-60s → report progress
3. > 5 phút → update user. > 10 phút → kill, báo user, đề xuất split
4. Done → báo kết quả + files changed

### 4.6 Code trên Device (SSH)

```bash
# Recommended: clone container → code → push → device pull
# Direct: chạy CLI trên device (nếu có Claude CLI)
ssh $SSH_OPTS {user}@{ip} "cd ~/projects/{project} && claude --dangerously-skip-permissions --output-format json -p 'task'"
```

## Bước 5: Verification Pipeline

**BẮT BUỘC trước khi tạo PR.**

```bash
cd ~/.openclaw/projects/<repo>
# Re-detect environment (xem Bước 3)
```

### 5.1 Build Check
```bash
[ -n "$PM" ] && node -e "process.exit(require('./package.json').scripts?.build ? 0 : 1)" 2>/dev/null \
  && $PM run build 2>&1 | tail -20
# Python: python -m py_compile src/*.py | Go: go build ./... | Rust: cargo build
```

### 5.2 Type Check
```bash
[ -f tsconfig.json ] && npx tsc --noEmit 2>&1 | head -30
```

### 5.3 Lint + 5.4 Test
```bash
[ -n "$PM" ] && $PM run lint 2>&1 | head -30
[ -n "$PM" ] && $PM run test 2>&1 | tail -30
```

### 5.5 Security Scan (changed files only)
```bash
CHANGED=$(git diff $DEFAULT_BRANCH --name-only -- '*.ts' '*.tsx' '*.js' '*.jsx' '*.py' '*.go' '*.rs')
[ -n "$CHANGED" ] && echo "$CHANGED" | xargs -I{} grep -n "sk-\|api_key\|password\s*=\|secret\s*=" {} 2>/dev/null | head -10
```

### 5.6 Diff Review + 5.7 Acceptance Criteria
```bash
git diff $DEFAULT_BRANCH --stat && git status --short
```
Đối chiếu từng tiêu chí Bước 1 → PASS/FAIL.

### 5.8 Verification Report
```
VERIFICATION REPORT
====================
Build/Types/Lint/Tests/Security: [PASS/FAIL/SKIP]
Diff: [X files changed]
Criteria: [X/Y passed]
Overall: [READY / NOT READY] for PR
```
⚠️ NOT READY → FIX trước, chạy lại pipeline.

## Bước 6: Dev Preview (khi user cần manual test)

**Trigger:** User nói "test thử", "cho anh xem", "manual test", "review UI".

**Flow tự động — agent chạy hết, chỉ gửi link khi ready:**

### 6.1 Start Dev Server
```bash
cd ~/.openclaw/projects/<repo>
# Re-detect PM (xem Bước 3)

# Auto-detect port
PORT=$(node -e "
  try {
    const pkg = require('./package.json');
    const dev = pkg.scripts?.dev || '';
    const m = dev.match(/(?:--port|PORT=?|-p)\s*(\d+)/);
    console.log(m ? m[1] : '3000');
  } catch { console.log('3000'); }
" 2>/dev/null)

tmux kill-session -t dev 2>/dev/null || true
lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
tmux new-session -d -s dev "$PM run dev"
```

### 6.2 Wait Until Ready
```bash
for i in $(seq 1 30); do
  curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT | grep -qE "^(200|301|302|304)" && break
  [ $i -eq 30 ] && echo "❌ Dev server timeout" && exit 1
  sleep 1
done
```

### 6.3 Start Tunnel & Verify
```bash
pkill -f "cloudflared tunnel" 2>/dev/null || true
cloudflared tunnel --url http://localhost:$PORT &>/tmp/cloudflared.log &

TUNNEL_URL=""
for i in $(seq 1 15); do
  TUNNEL_URL=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" /tmp/cloudflared.log | head -1)
  [ -n "$TUNNEL_URL" ] && break
  sleep 1
done

# Verify
curl -s -o /dev/null -w "%{http_code}" "$TUNNEL_URL" | grep -qE "^(200|301|302|304)" && echo "✅ Ready"
```

### 6.4 Gửi Link
```
🔗 App ready for review:
- Local: http://localhost:<PORT>
- Public: <TUNNEL_URL>
Anh test xong báo em để cleanup nhé.
```
**KHÔNG cleanup cho đến khi user nói xong.**

### 6.5 Cleanup
```bash
pkill -f "cloudflared tunnel" 2>/dev/null || true
tmux kill-session -t dev 2>/dev/null || true
lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
```

## Bước 7: Commit & Push

```bash
cd ~/.openclaw/projects/<repo>
# Re-detect (xem Bước 3)

[ -n "$PM" ] && git diff $DEFAULT_BRANCH --name-only | grep -q "package.json" && $PM install
git add -A
git diff --cached --quiet || git commit -m "<type>(<scope>): <description>"
git push origin <branch-name>
```

Conventional Commits: `feat/fix/refactor/docs/chore/test/perf` — lowercase, imperative, ≤ 72 chars.

## Bước 8: Pull Request (nếu có `gh` CLI)

```bash
REPO=$(git remote get-url origin | sed 's|.*github.com[:/]||;s|\.git$||')
gh pr create --repo "$REPO" --title "<type>(<scope>): <description>" --assignee @me \
  --body "## Changes
- ...
## Verification Report
<từ Bước 5.8>" --base $DEFAULT_BRANCH
```

## Domain References (đọc khi cần, KHÔNG load mặc định)

| Reference | Khi nào đọc | Path |
|-----------|-------------|------|
| Coding Rules | **MỌI task code** — inject tóm tắt vào prompt | [references/coding-rules.md](references/coding-rules.md) |
| Tech Stack | User hỏi chọn framework/lib, hoặc cần chọn stack | [references/tech-stack.md](references/tech-stack.md) |
| Landing Page | Build landing page, marketing page | [references/landing-page.md](references/landing-page.md) |

## Bảo mật

- **KHÔNG** hardcode secrets, API keys, passwords
- **KHÔNG** commit `.env` files
- **KHÔNG** push to main trực tiếp (branch + PR)
- **Next.js: KHÔNG** dùng `NEXT_PUBLIC_` cho secrets (DB, tokens) — chỉ cho public config
- **HỎI user** trước khi deploy

## Platform-specific (SSH)

| Platform | Shell | Projects path |
|----------|-------|---------------|
| macOS | `zsh` | `/Users/{user}/projects/` |
| Windows | `powershell` | `C:\Users\{user}\projects\` |
| Linux | `bash` | `/home/{user}/projects/` |

## Troubleshooting

| Vấn đề | Giải pháp |
|---------|-----------|
| Claude CLI not found | `curl -fsSL https://claude.ai/install.sh \| bash` |
| `--dangerously-skip-permissions` blocked | Tạo user `coder`, dùng `--permission-mode bypassPermissions` |
| `git push` permission denied | Check SSH key / GitHub token |
| Device offline | Báo user bật máy + check network |
| Build fail | Đọc error → fix → retry |
| No `package.json` | Detect project type → adjust commands |

## Lessons Learned

| # | Lesson | Context |
|---|--------|---------|
| 1 | `--dangerously-skip-permissions` chỉ hoạt động root + CLI mới | Container default root |
| 2 | `--permission-mode bypassPermissions` blocked for root | Fallback: tạo user `coder` |
| 3 | Poll mỗi 30-60s — spawn rồi quên = bug | Hard Rule #3 |
| 4 | Quick tunnel URL random mỗi lần — OK cho single app | Multi-service cần inject URL |
