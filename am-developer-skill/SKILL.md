---
name: am-developer-skill
description: "Developer workflow cho mọi coding tasks — spawn Claude Code CLI, planning, branching, verification, dev preview, PR. Code trên container hoặc user's device qua SSH. Use when: build feature, fix bug, refactor code, create PR, code review, generate tests, add API endpoint, update component, database migration, deploy config. NOT for: reading code (use read tool), simple edits under 3 lines (use edit tool directly), or thread-bound ACP harness requests (use sessions_spawn)."
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

5. **MUST challenge ambiguous or high-risk tasks.**
   Nếu task mơ hồ, thiếu context, hoặc có risk cao mà user chưa acknowledge → HỎI TRƯỚC.
   KHÔNG tự suy đoán scope/approach rồi chạy.
   Ví dụ: "Refactor auth module" mà không nói rõ scope → hỏi scope.
   Ví dụ: Task đụng DB prod mà user chưa mention backup → flag risk.

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
| **Quick** (1-3 files) | Fix CSS, update text | Bước 1 gọn → Skip 2-3 → Bước 4 → Bước 5 nhẹ (5.1 Build + 5.6 Diff + 5.7 Criteria). PR optional |
| **Medium** (3-10 files) | New component, refactor | Full workflow |
| **Large** (>10 files) | New feature, migration | Full workflow bắt buộc |

## Bước 1: Phân tích yêu cầu & Xác định Workspace

### 1.1 Phân tích Input/Output (BẮT BUỘC)

1. **Input** — Dữ liệu/điều kiện đầu vào
2. **Output mong đợi** — Kết quả cuối cùng
3. **Acceptance Criteria** — Tiêu chí "done" cụ thể:
   - [ ] Tiêu chí 1
   - [ ] Tiêu chí 2
   - [ ] Edge cases cần xử lý
4. **Reversibility** — Task có thể revert không?
   - 🟢 Reversible (UI, refactor, test) → proceed bình thường
   - 🟡 Partial (DB migration, API contract) → ghi backup plan
   - 🔴 Irreversible (delete data, deploy prod) → BẮT BUỘC confirm user
5. **Verification method** cho mỗi criterion (build, test, curl, browser...)
   - Criterion mà chỉ "looks good" → KHÔNG hợp lệ, phải cụ thể
6. **Ambiguous → hỏi** (Hard Rule #5). Suy luận được → ghi assumption, tiến hành.

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

Trình bày: **acceptance criteria (Bước 1) + plan (Bước 2)** → chờ approval 1 lần.
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

**Long prompts hoặc prompts có special chars ($, backticks, quotes) → write to file:**
```bash
cat > /tmp/prompt.md << 'PROMPT'
Your long prompt here...
PROMPT
cat /tmp/prompt.md | claude --dangerously-skip-permissions --output-format json -p -
```
⚠️ Inline prompts chỉ escape single quotes. Nếu prompt chứa `$`, `` ` ``, `"` → **luôn dùng file**.

### 4.2 Prompt Strategy

**High-level prompts, KHÔNG micromanage.** Claude Code tự explore codebase.

Chỉ cung cấp:
- **Goal**: cần làm gì
- **Constraints**: giữ gì, không đụng gì, pattern nào follow
- **Edge cases**: nếu X → làm Y
- **Safety**: "If unsure → choose the safer option"
- **Cuối prompt luôn thêm:** `"DO NOT git commit or push."`
- **Coding rules (luôn inject):** Đọc section "Tóm tắt" cuối [references/coding-rules.md](references/coding-rules.md), append vào cuối prompt. 9 defensive programming rules bắt buộc.

❌ Wrong: list mọi file, mọi dòng cần sửa, copy-paste code context
✅ Right: mô tả goal + constraints, để Claude Code tự đọc code và implement

💡 **Project conventions:** Claude Code tự đọc `.claude/instructions.md` nếu có. Không cần copy vào prompt — chỉ nhắc: `"Follow project conventions in .claude/instructions.md if it exists."`

**2-Phase cho complex tasks:**
```
Phase 1 (Plan): "Analyze + plan this task. Output JSON: {steps, questions, assumptions}"
  → parse result → có questions? → trả lời → Phase 2
Phase 2 (Implement): "Implement the plan. [answers if any]"
  → Resume session via session_id from Phase 1
```

### 4.3 Timeout & Retry (BẮT BUỘC)

| Task type | Timeout | Ví dụ |
|-----------|---------|-------|
| Quick | 120s | review, explain, 1-2 files |
| Medium | 300s | 3-5 files, refactor |
| Large | 600s | >5 files, multi-module |

**Retry flow (max 3 attempts) — Adaptive:**
```
Attempt 1: full prompt, standard timeout
  ↓ fail → DIAGNOSE root cause:

  ┌─ Token/context limit?  → Split task nhỏ hơn
  ├─ Wrong approach?       → Thay đổi prompt strategy (chuyển sang 2-phase)
  ├─ Environment issue?    → Fix env trước, retry cùng prompt
  ├─ Model limitation?     → Escalate model (sonnet → opus)
  └─ Timeout?              → Tăng timeout + simplify prompt

Attempt 2: strategy KHÁC so với attempt 1 (dựa trên diagnosis)
  ↓ fail → diagnose lại, chọn strategy chưa thử

Attempt 3: last resort — minimal prompt, max timeout, hoặc split nhỏ nhất
  ↓ fail
→ BÁO USER NGAY (Hard Rule #2). Kèm: lỗi gì, đã thử gì, đề xuất hướng.
```

⚠️ **Mỗi attempt PHẢI khác strategy** — retry cùng cách = lãng phí. Ghi lại diagnosis mỗi attempt.

**Task > 10 files → LUÔN split:**
- Call 1: Tạo files mới (lib, utils, hooks)
- Call 2: Update files hiện có (pages, components)
- Call 3: Cleanup (xóa file cũ, verify build)

### 4.4 Parse Result

```json
{
  "type": "result",
  "subtype": "success",
  "result": "The response text",
  "session_id": "uuid-to-resume",
  "is_error": false,
  "total_cost_usd": 0.05,
  "usage": { "input_tokens": 1000, "output_tokens": 500 }
}
```

- `is_error: true` → retry (xem 4.3)
- `session_id` → lưu để resume multi-turn
- CLI crash / non-JSON → retry once, vẫn fail → báo user

### 4.5 Available Models
- `sonnet` — default cho hầu hết tasks
- `opus` — chỉ cho deep reasoning (complex review, architecture)

### 4.6 Monitoring (BẮT BUỘC cho background spawns)

1. **Spawn xong → báo user:** "Đang chạy Claude Code cho [task], ETA ~X phút"
2. **Poll loop:**
   ```
   process action:poll sessionId:xxx timeout:60000
   ```
   - Running + > 5 phút → báo user "Vẫn đang chạy, đã X phút"
   - Done → parse result → báo user kết quả + files changed
   - Fail → retry (xem 4.3) hoặc báo user nếu đã hết retry
3. **Partial success:**
   - Parse result → xác định files đã sửa vs chưa
   - Resume session (`session_id`) với prompt focus files còn lại
4. **> 10 phút → kill, báo user, đề xuất split**

### 4.7 Code trên Device (SSH)

```bash
# Recommended: clone container → code → push → device pull
# Direct: chạy CLI trên device (nếu có Claude CLI)
ssh $SSH_OPTS {user}@{ip} "cd ~/projects/{project} && claude --dangerously-skip-permissions --output-format json -p 'task'"
```

## Bước 5: Verification Pipeline

**BẮT BUỘC trước khi tạo PR.**

Agent chạy verification trực tiếp qua exec sau khi Claude CLI hoàn thành. Nếu có FAIL → gọi lại Claude CLI để fix → chạy lại pipeline từ đầu.

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
→ PHẢI pass. Fail → fix trước. Không có build script → SKIP.

### 5.2 Type Check (SKIP nếu không có TypeScript)
```bash
[ -f tsconfig.json ] && npx tsc --noEmit 2>&1 | head -30
```

### 5.3 Lint Check
```bash
[ -n "$PM" ] && node -e "process.exit(require('./package.json').scripts?.lint ? 0 : 1)" 2>/dev/null \
  && $PM run lint 2>&1 | head -30
```

### 5.4 Test Suite (SKIP nếu chưa có tests)
```bash
[ -n "$PM" ] && node -e "process.exit(require('./package.json').scripts?.test ? 0 : 1)" 2>/dev/null \
  && $PM run test 2>&1 | tail -30
```

### 5.5 Security Quick Scan (changed files only)
```bash
CHANGED=$(git diff $DEFAULT_BRANCH --name-only -- '*.ts' '*.tsx' '*.js' '*.jsx' '*.py' '*.go' '*.rs')
UNTRACKED=$(git ls-files --others --exclude-standard -- '*.ts' '*.tsx' '*.js' '*.jsx' '*.py' '*.go' '*.rs')
ALL_CHANGED=$(printf "%s\n%s" "$CHANGED" "$UNTRACKED" | sort -u | grep -v '^$')

if [ -n "$ALL_CHANGED" ]; then
  # Secrets check
  echo "$ALL_CHANGED" | xargs -I{} grep -n "sk-\|api_key\|password\s*=\|secret\s*=" {} 2>/dev/null | head -10
  # Console.log check
  echo "$ALL_CHANGED" | xargs -I{} grep -n "console\.log" {} 2>/dev/null | head -10
fi
```

Security checklist (review thủ công trên changed files):
- [ ] Không hardcode API keys, tokens, passwords
- [ ] Không còn debug logs thừa
- [ ] Error messages không leak stack trace ra client
- [ ] User input được validate
- [ ] Dùng parameterized queries hoặc ORM
- [ ] Endpoint sensitive có kiểm tra auth

### 5.6 Diff Review
```bash
git diff $DEFAULT_BRANCH --stat
git status --short
```

### 5.7 Acceptance Criteria Check
Đối chiếu từng tiêu chí ở Bước 1. Mỗi tiêu chí ghi rõ PASS/FAIL + verification method đã dùng.

### 5.8 Verification Report

```
VERIFICATION REPORT
====================
Build:      [PASS/FAIL]
Types:      [PASS/FAIL/SKIP]
Lint:       [PASS/FAIL]
Tests:      [PASS/FAIL/SKIP]
Security:   [PASS/FAIL]
Diff:       [X files changed]
Criteria:   [X/Y passed]

Overall:    [READY / NOT READY] for PR
```

⚠️ **NOT READY → FIX hết rồi chạy lại pipeline. KHÔNG tạo PR khi còn FAIL.**
💡 **Gửi report cho user confirm trước khi tạo PR.**

## Bước 6: Dev Preview (khi user cần manual test)

**Trigger:** User nói "test thử", "cho anh xem", "manual test", "review UI".
**Bỏ qua** nếu task nhỏ, backend-only, hoặc user mở localhost trực tiếp được.

**Flow tự động — agent chạy hết, chỉ gửi link khi ready:**

### 6.1 Start Dev Server
```bash
cd ~/.openclaw/projects/<repo>
# Re-detect PM (xem Bước 3)

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

git status && git diff --stat

git add -A
git diff --cached --quiet || git commit -m "<type>(<scope>): <description>"
git push origin <branch-name>
```

### Conventional Commits (BẮT BUỘC)

Format: `<type>[optional scope]: <description>`

| Type | Khi nào dùng |
|------|-------------|
| `feat` | Feature mới |
| `fix` | Sửa bug |
| `docs` | Chỉ docs |
| `style` | Format (không đổi logic) |
| `refactor` | Refactor |
| `perf` | Performance |
| `test` | Thêm/sửa test |
| `chore` | Build, CI, deps |

Quy tắc: lowercase, imperative mood, ≤ 72 chars, không chấm cuối.

## Bước 8: Pull Request (nếu có `gh` CLI)

```bash
REPO=$(git remote get-url origin | sed 's|.*github.com[:/]||;s|\.git$||')

gh pr create --repo "$REPO" \
  --title "<type>(<scope>): <description>" \
  --assignee @me \
  --body "## Changes
- <change 1>
- <change 2>

## Verification Report
<nhúng report từ Bước 5.8>

## Testing
- <how to test>" \
  --base $DEFAULT_BRANCH
```

### Handling PR Review Feedback

```bash
cd ~/.openclaw/projects/<repo>
git checkout <feature-branch>

# Fix theo feedback — spawn Claude CLI (Bước 4)
# Chạy lại verification pipeline (Bước 5)
# Sau khi PASS:
git add -A
git diff --cached --quiet || git commit -m "fix: address PR review feedback"
git push origin <feature-branch>
```
→ PR tự update. Reply vào review comments giải thích đã fix gì.

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
- **Next.js: KHÔNG** dùng `NEXT_PUBLIC_` cho secrets — chỉ cho public config
- **HỎI user** trước khi deploy

## Platform-specific (SSH)

| Platform | Shell | Projects path |
|----------|-------|---------------|
| macOS | `zsh` | `/Users/{user}/projects/` |
| Windows | `powershell` | `C:\Users\{user}\projects\` |
| Linux | `bash` | `/home/{user}/projects/` |

## Quick Reference

### Conflict Resolution
1. Read — understand both sides
2. Prioritize default branch — code đã reviewed, adapt your code
3. Ask if unsure — never silently delete someone else's code
4. Use Claude CLI for complex conflicts
5. Never force push to default branch

### Module System
Follow project's existing module system. Prefer ESM cho new projects.

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
| 5 | Mỗi retry PHẢI khác strategy — retry cùng cách = lãng phí | Adaptive retry |
| 6 | Task > 10 files → LUÔN split thành multiple calls | Tránh timeout + token limit |

## Tools Required

- `claude` CLI — coding agent
- `gh` CLI — GitHub operations (optional, cho PR)
- `cloudflared` — dev preview tunnels (optional)
- `git` — version control
