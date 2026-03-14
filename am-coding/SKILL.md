---
name: am-coding
description: "Developer workflow cho mọi coding tasks — spawn Claude Code CLI, planning, branching, verification, PR. Hỗ trợ code trên container hoặc user's device qua SSH."
---

# Coding — Development Skill cho Another Me Agents

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

Trước khi chạy workflow, verify:

```bash
# Claude CLI
which claude && claude --version || echo "❌ Claude CLI chưa install"

# Git
git --version && git config user.name && git config user.email || echo "❌ Git chưa config"

# GitHub CLI (cần cho PR)
which gh && gh auth status 2>/dev/null || echo "⚠️ gh CLI chưa setup (PR sẽ không tạo được)"

# Env vars
[ -n "$ANTHROPIC_API_KEY" ] && echo "✅ API key set" || echo "❌ ANTHROPIC_API_KEY chưa set"
```

**Nếu Claude CLI không available:** Agent vẫn code được bằng `read`/`edit`/`write` tools trực tiếp. Hard Rule #1 chỉ áp dụng khi CLI available. Báo user rằng đang code trực tiếp vì CLI chưa install.

## Khi nào dùng

✅ **Dùng khi:**
- Bất kỳ task nào cần code: feature mới, bug fix, refactor, test, review
- Multi-file hoặc cross-module
- DB schema, auth, API contract, deploy config (consequence cao)
- Generate tests, scaffolding, boilerplate

❌ **Không dùng khi:**
- Edit < 3 dòng trivial (typo, config value) → dùng `edit` tool trực tiếp
- Chỉ đọc code → dùng `read` tool

📌 **Không rõ → default dùng skill này** (safe choice)

### Task Size → Workflow

| Task size | Ví dụ | Workflow |
|-----------|-------|----------|
| **Quick** (1-3 files, isolated) | Fix CSS, update text, add test | Bước 1 gọn → Skip Bước 2-3 → Bước 4 → Bước 5 nhẹ (chỉ 5.1 Build + 5.6 Diff + 5.7 Criteria). PR optional |
| **Medium** (3-10 files) | New component, refactor module | Full workflow |
| **Large** (>10 files, cross-module) | New feature, migration | Full workflow bắt buộc |

## Bước 1: Phân tích yêu cầu & Xác định Workspace

### 1.1 Phân tích Input/Output (BẮT BUỘC)

1. **Input** — Dữ liệu/điều kiện đầu vào là gì?
2. **Output mong đợi** — Kết quả cuối cùng phải như thế nào?
3. **Acceptance Criteria** — Liệt kê cụ thể các tiêu chí "done"
4. **Nếu ambiguous → hỏi.** Nếu suy luận được → ghi assumption và tiến hành.

> ⏩ Không chờ approval ở bước này — trình bày cùng plan ở Bước 2 để user confirm 1 lần duy nhất.

### 1.2 Xác định Workspace

**HỎI USER** nếu chưa rõ:

#### Option A: Code trên container (mặc định)
- Repo clone vào `~/.openclaw/projects/`
- Agent có full control: edit, build, test, push

```bash
WORKSPACE=~/.openclaw/projects
mkdir -p $WORKSPACE
cd $WORKSPACE

# Clone (chỉ skip nếu repo đã tồn tại)
if [ ! -d "<project-name>" ]; then
  git clone <repo-url> <project-name>
fi
cd <project-name>
```

#### Option B: Code trên user's device (qua SSH)
- Dùng khi user cần native environment (iOS simulator, GPU, specific OS)
- Kết hợp với `am-devices` skill
- Kiểm tra device status trước

```bash
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519"
ssh $SSH_OPTS {user}@{ip} "ls -la ~/projects/{project}"
```

| Tình huống | Workspace |
|------------|-----------|
| Web app, API, backend | Container (Option A) |
| Mobile app (iOS/Android) | Device (Option B) |
| User nói "trên máy tính" / "trên laptop" | Device (Option B) |
| User không specify | Container (Option A) |
| Cần build native binary / GPU | Device (Option B) |

## Bước 2: Planning

Analyze:
1. **What** — Break down into subtasks
2. **Where** — Files/modules affected
3. **How** — Approach/pattern, check project conventions
4. **Impact** — What could break? Testing needed?

```bash
# Chạy sau khi đã xác định workspace (Bước 1.2)
cat ~/.openclaw/projects/<repo>/.claude/instructions.md 2>/dev/null
cat ~/.openclaw/projects/<repo>/CLAUDE.md 2>/dev/null
```

Trình bày cho user: **acceptance criteria (Bước 1) + plan** → chờ approval 1 lần duy nhất.

💡 **Task nhỏ/rõ ràng**: gộp Bước 1-2 thành 1 message ngắn gọn.

## Bước 3: Create Feature Branch

> ⚠️ **Biến không share giữa exec sessions.** Mỗi block bash dưới đây là 1 session riêng. Phải re-detect `DEFAULT_BRANCH`, `PM`, `SSH_OPTS` mỗi lần chạy lệnh mới.

```bash
cd ~/.openclaw/projects/<repo>

# === Environment Setup (copy block này vào đầu mỗi exec session) ===
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
if [ -z "$DEFAULT_BRANCH" ]; then
  DEFAULT_BRANCH=$(git branch -r 2>/dev/null | grep -E 'origin/(main|master)' | head -1 | sed 's|.*origin/||')
  DEFAULT_BRANCH=${DEFAULT_BRANCH:-main}
fi

# Detect package manager (SKIP cho non-Node.js projects)
if [ -f package.json ]; then
  if [ -f pnpm-lock.yaml ]; then PM="pnpm"
  elif [ -f yarn.lock ]; then PM="yarn"
  elif [ -f bun.lockb ]; then PM="bun"
  else PM="npm"; fi
fi

# SSH (chỉ khi code trên device)
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519"
# ===================================================================

# Stash uncommitted changes
git stash --include-untracked 2>/dev/null || true

git checkout $DEFAULT_BRANCH
git pull origin $DEFAULT_BRANCH

# Install deps (Node.js only)
[ -n "$PM" ] && $PM install

# Create branch (nếu đã tồn tại → checkout)
git checkout -b <branch-type>/<short-description> 2>/dev/null \
  || git checkout <branch-type>/<short-description>
```

Branch types: `feat/`, `fix/`, `refactor/`, `chore/`, `docs/`, `perf/`, `test/`

**Trên device (SSH):**
```bash
ssh $SSH_OPTS {user}@{ip} "cd ~/projects/{project} && git checkout -b feat/my-feature"
```

## Bước 4: Code với Claude CLI

**⚡ Hot Reload First:** Nếu app hỗ trợ hot reload (Next.js, Vite...), ưu tiên dev server + hot reload.

**Quy tắc:**
- Claude CLI **chỉ edit files, KHÔNG commit** — luôn thêm `"DO NOT git commit or push."` vào prompt
- Respect `.claude/instructions.md` và project conventions
- Git management ở Bước 6

### 4.1 Spawn Claude Code CLI

**Container (root):**
```bash
cd ~/.openclaw/projects/<repo>
claude --dangerously-skip-permissions --output-format json -p "
<task description>
DO NOT git commit or push.
"
```

**Container (non-root fallback):**
```bash
su - coder -c "
export ANTHROPIC_API_KEY='$ANTHROPIC_API_KEY'
export ANTHROPIC_BASE_URL='$ANTHROPIC_BASE_URL'
cd <workdir>
claude --permission-mode bypassPermissions --output-format json -p 'task'
"
```

**Resume session:**
```bash
claude --dangerously-skip-permissions --output-format json --resume <session_id> -p "continue..."
```

**Background mode (task > 2 phút) — dùng OpenClaw tool calls, KHÔNG phải shell:**
```
# Spawn background (OpenClaw exec tool)
exec(background:true, command:"claude --dangerously-skip-permissions --output-format json -p 'task'")

# Monitor (BẮT BUỘC — Hard Rule #3, OpenClaw process tool):
process(action:poll, sessionId:xxx, timeout:60000)
process(action:log, sessionId:xxx)
```

**Long prompts (>500 chars hoặc special chars) → write to file:**
```bash
cat > /tmp/prompt.md << 'PROMPT'
Your long prompt here...
PROMPT
cat /tmp/prompt.md | claude --dangerously-skip-permissions --output-format json -p -
```

### 4.2 Prompt Strategy

**High-level prompts, KHÔNG micromanage.** Claude Code tự explore codebase.

Chỉ cung cấp:
- **Goal**: cần làm gì
- **Constraints**: giữ gì, không đụng gì, pattern nào follow
- **Edge cases**: nếu X → làm Y
- **Safety**: "If unsure → choose the safer option"
- **Cuối prompt:** `"DO NOT git commit or push."`

**2-Phase cho complex tasks:**
```
Phase 1 (Plan): "Analyze + plan this task. Output JSON: {steps, questions, assumptions}"
  → parse → có questions? → trả lời
Phase 2 (Implement): "Implement the plan. [answers if any]"
  → Resume session via session_id from Phase 1
```

### 4.3 Timeout & Retry (BẮT BUỘC)

| Task type | Timeout | Ví dụ |
|-----------|---------|-------|
| Quick | 120s | review, explain, 1-2 files |
| Medium | 300s | 3-5 files, refactor |
| Large | 600s | >5 files, multi-module |

**Retry flow (max 3 attempts):**
```
Attempt 1: full prompt, standard timeout
  ↓ timeout/fail
Attempt 2: simplified prompt OR split task, tăng timeout
  ↓ timeout/fail  
Attempt 3: minimal prompt, max timeout
  ↓ fail
→ BÁO USER NGAY (Hard Rule #2). Đề xuất hướng xử lý. KHÔNG tự code.
```

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
  "total_cost_usd": 0.05
}
```

- `is_error: true` → retry (xem 4.3)
- `session_id` → lưu để resume multi-turn
- CLI crash / non-JSON output → retry once, vẫn fail → báo user

### 4.5 Available Models
- `sonnet` — default cho hầu hết tasks
- `opus` — deep reasoning (complex review, architecture)

### 4.6 Monitoring Checklist (BẮT BUỘC cho background spawns)

1. **Spawn xong → báo user:** "Đang chạy Claude Code cho [task], ETA ~X phút"
2. **Poll loop:**
   ```
   process action:poll sessionId:xxx timeout:60000
   ```
   - Running + > 5 phút → báo user "Vẫn đang chạy, đã X phút"
   - Done → parse result → báo user kết quả + files changed
   - Fail → retry (xem 4.3) hoặc báo user nếu hết retry
3. **Partial success:** Parse result → xác định files đã sửa vs chưa → resume session cho phần còn lại
4. **Max wait:** Nếu task chạy > 10 phút → kill process, báo user, đề xuất split task nhỏ hơn

### 4.7 Code trên Device (SSH)

```bash
# Option 1: Clone về container → code → push → device pull (recommended)
# Option 2: Chạy CLI trên device (nếu device có Claude CLI)
ssh $SSH_OPTS {user}@{ip} "cd ~/projects/{project} && claude --dangerously-skip-permissions --output-format json -p 'task'"

# Option 3: Agent edit trực tiếp qua SSH (simple tasks only)
ssh $SSH_OPTS {user}@{ip} "cd ~/projects/{project} && sed -i 's/old/new/' src/app.ts"
```

## Bước 5: Verification Pipeline

**BẮT BUỘC trước khi tạo PR.** Agent chạy verification sau khi Claude CLI hoàn thành.

```bash
cd ~/.openclaw/projects/<repo>

# Re-detect environment (xem Environment Setup ở Bước 3)
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
```

> **Non-Node.js projects:** Adjust verify commands cho Python (`pytest`, `mypy`), Go (`go build`, `go test`), Rust (`cargo build`, `cargo test`), v.v.

### 5.1 Build Check
```bash
# Node.js
[ -n "$PM" ] && node -e "process.exit(require('./package.json').scripts?.build ? 0 : 1)" 2>/dev/null \
  && $PM run build 2>&1 | tail -20

# Python: python -m py_compile src/*.py
# Go: go build ./...
# Rust: cargo build
```

### 5.2 Type Check (SKIP nếu không có TypeScript)
```bash
[ -f tsconfig.json ] && npx tsc --noEmit 2>&1 | head -30
```

### 5.3 Lint Check
```bash
# Node.js
[ -n "$PM" ] && node -e "process.exit(require('./package.json').scripts?.lint ? 0 : 1)" 2>/dev/null \
  && $PM run lint 2>&1 | head -30

# Python: ruff check . || flake8 .
# Go: golangci-lint run
```

### 5.4 Test Suite (SKIP nếu chưa có tests)
```bash
# Node.js
[ -n "$PM" ] && node -e "process.exit(require('./package.json').scripts?.test ? 0 : 1)" 2>/dev/null \
  && $PM run test 2>&1 | tail -30

# Python: pytest
# Go: go test ./...
# Rust: cargo test
```

### 5.5 Security Quick Scan (chỉ files đã thay đổi)
```bash
# Scan tất cả source files đã thay đổi (JS/TS/Python/Go/...)
CHANGED=$(git diff $DEFAULT_BRANCH --name-only -- '*.ts' '*.tsx' '*.js' '*.jsx' '*.py' '*.go' '*.rs')
UNTRACKED=$(git ls-files --others --exclude-standard -- '*.ts' '*.tsx' '*.js' '*.jsx' '*.py' '*.go' '*.rs')
ALL_CHANGED=$(printf "%s\n%s" "$CHANGED" "$UNTRACKED" | sort -u | grep -v '^$')

if [ -n "$ALL_CHANGED" ]; then
  echo "$ALL_CHANGED" | xargs -I{} grep -n "sk-\|api_key\|password\s*=\|secret\s*=" {} 2>/dev/null | head -10
  echo "$ALL_CHANGED" | xargs -I{} grep -n "console\.log" {} 2>/dev/null | head -10
fi
```

Checklist:
- [ ] Không hardcode API keys, tokens, passwords
- [ ] Không còn debug logs thừa
- [ ] Error messages không leak stack trace ra client
- [ ] User input được validate

### 5.6 Diff Review
```bash
git diff $DEFAULT_BRANCH --stat
git status --short
```

### 5.7 Acceptance Criteria Check

Đối chiếu từng tiêu chí ở Bước 1. Mỗi tiêu chí ghi rõ PASS/FAIL.

### 5.8 Verification Report

```
VERIFICATION REPORT
====================
Build:      [PASS/FAIL/SKIP]
Types:      [PASS/FAIL/SKIP]
Lint:       [PASS/FAIL/SKIP]
Tests:      [PASS/FAIL/SKIP]
Security:   [PASS/FAIL]
Diff:       [X files changed]
Criteria:   [X/Y passed]

Overall:    [READY / NOT READY] for PR
```

⚠️ **NOT READY → FIX hết rồi chạy lại pipeline. KHÔNG tạo PR khi còn FAIL.**

## Bước 6: Commit & Push

```bash
cd ~/.openclaw/projects/<repo>

# Re-detect (xem Environment Setup ở Bước 3)
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

# Update lock file nếu package.json changed (Node.js only)
if [ -n "$PM" ] && git diff $DEFAULT_BRANCH --name-only | grep -q "package.json"; then
  $PM install
fi

# Stage & commit (conventional format)
git add -A
git diff --cached --quiet || git commit -m "<type>(<scope>): <description>"
git push origin <branch-name>
```

### Conventional Commits

| Type | Khi nào |
|------|---------|
| `feat` | Feature mới |
| `fix` | Sửa bug |
| `refactor` | Refactor |
| `docs` | Docs |
| `chore` | Config, deps |
| `test` | Tests |
| `perf` | Performance |

Format: `<type>[optional scope]: <description>` — lowercase, imperative mood, ≤ 72 chars.

**Trên device (SSH):**
```bash
ssh $SSH_OPTS {user}@{ip} "cd ~/projects/{project} && git add -A && git commit -m 'feat: my feature' && git push origin feat/my-feature"
```

## Bước 7: Pull Request (nếu có GitHub + `gh` CLI)

**SKIP nếu `gh` CLI không available** — commit đã push ở Bước 6, user tạo PR thủ công.

```bash
REPO=$(git remote get-url origin | sed 's|.*github.com[:/]||;s|\.git$||')

gh pr create \
  --repo "$REPO" \
  --title "<type>(<scope>): <description>" \
  --assignee @me \
  --body "## Changes
- <change 1>
- <change 2>

## Verification Report
<report từ Bước 5.8>

## Testing
- <how to test>" \
  --base $DEFAULT_BRANCH
```

### Handling PR Review Feedback

```bash
# Fix theo feedback — spawn Claude CLI (Bước 4)
# Chạy lại verification (Bước 5)
git add -A
git diff --cached --quiet || git commit -m "fix: address PR review feedback"
git push origin <feature-branch>
```

## Deploy/Preview (khi user yêu cầu)

Agent **KHÔNG tự deploy** trừ khi user yêu cầu rõ ràng.

```bash
# Dev server trên container
$PM run dev &

# Dev server trên device
ssh $SSH_OPTS {user}@{ip} "cd ~/projects/{project} && npm run dev &"
```

## Bảo mật

- **KHÔNG** hardcode secrets, API keys, passwords trong code
- **KHÔNG** commit `.env` files
- **KHÔNG** push to main/master trực tiếp (dùng branch + PR)
- **HỎI user** trước khi chạy deploy commands
- Review diff trước khi commit

## Platform-specific (SSH trên device)

| Platform | Shell | Projects path |
|----------|-------|---------------|
| macOS | `zsh` | `/Users/{user}/projects/` |
| Windows | `powershell` | `C:\Users\{user}\projects\` |
| Linux | `bash` | `/home/{user}/projects/` |

## Troubleshooting

| Vấn đề | Giải pháp |
|---------|-----------|
| `git push` permission denied | Kiểm tra SSH key / GitHub token |
| Claude CLI not found | `curl -fsSL https://claude.ai/install.sh \| bash` |
| Device offline | Báo user bật máy + check network |
| Build fail | Đọc error → fix → retry |
| SSH timeout | Check device status |
| `--dangerously-skip-permissions` blocked | Tạo user `coder`, dùng `--permission-mode bypassPermissions` |
| No `package.json` | Detect project type (Python? Go? Rust?) và adjust |

## Lessons Learned

| # | Lesson | Context |
|---|--------|---------|
| 1 | `--dangerously-skip-permissions` chỉ hoạt động với root + CLI version mới | Container default chạy root |
| 2 | `--permission-mode bypassPermissions` blocked for root | Fallback: tạo user `coder` |
| 3 | Poll mỗi 30-60s cho background spawn — spawn rồi quên = bug | Hard Rule #3 |
