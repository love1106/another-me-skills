---
name: am-developer-skill
version: 1.9.0
author: khoidoan
description: >
  Developer workflow for ALL coding tasks. Handles: init project, security review, self-improve,
  Claude Code CLI with retry, planning, GitHub tracking, branching, verification, PR creation.
  CLI error tracking with auto-log and retrospect analysis.
  Use when: init project, security audit, build feature, fix bug, refactor, code review, generate tests,
  write unit tests, TDD, viết tests, deploy config, self-improve dev skill, retrospect, hồi tưởng,
  review cli errors, xem lỗi cli, cli report, error report, analyze cli runs, phân tích lỗi,
  code intelligence, index codebase, analyze architecture, blast radius.
  NOT for: reading code (use read), edits under 3 lines (use edit), ACP requests (use sessions_spawn).
---

# Another Me Developer Skill

Developer workflow for ALL coding tasks — quick edits to complex multi-file features.

**Projects path:** `~/projects/<repo>` (`~` = actual home dir, e.g. `/root` hoặc `/home/coder`)

## Permissions

- **reads:** source code, git history, project config files, `.claude/instructions.md`
- **writes:** source code files, git branches, lock files, CLI run logs (`memory/cli-runs.jsonl`), annotations (`memory/am-developer-skill-annotations/`)
- **external:** GitHub API (issues, PRs, projects via `gh` CLI), Claude Code CLI (spawns sub-process), GitNexus MCP (local), Cloudflare tunnel (dev preview)
- **destructive:** `git reset --soft` (squash commits), `git stash` (stashes uncommitted changes), branch deletion after merge
- **requires_confirmation:** irreversible actions (DB prod, delete data, deploy prod — flagged in Step 1 Reversibility check)

## ⛔ Hard Rules (NEVER VIOLATE)

1. **NEVER self-code when Claude Code CLI is available.**
   Agent là orchestrator, KHÔNG PHẢI coder.
   Mọi task cần code → spawn Claude CLI (Step 5).
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
   Ví dụ: Task đụng DB prod mà user chưa mention backup → flag risk trước.

## When to Use

**Dùng cho MỌI task cần viết/sửa code qua Claude Code CLI.**

✅ **Dùng khi:**
- Bất kỳ task nào cần code: feature mới, bug fix, refactor, test, review
- Multi-file hoặc cross-module
- DB schema, auth, API contract, deploy config (consequence cao)
- Generate tests, scaffolding, boilerplate

❌ **Không dùng khi:**
- Edit < 3 dòng trivial (typo, config value) → dùng `edit` tool trực tiếp
- Chỉ đọc code → dùng `read` tool
- Thread-bound ACP request → dùng `sessions_spawn`

### Task Size → Workflow

| Task size | Ví dụ | GitNexus (0c) | Workflow |
|-----------|-------|---------------|----------|
| **Quick** (1-3 files, isolated) | Fix CSS, update text, add test | Skip | Step 1 gọn → Skip Step 2-4 → Step 5 (annotations: `--limit 3` hoặc skip) → Step 6 lite (Build + Diff + Criteria only). Skip 5.10 nếu trivial visual change. PR optional — commit thẳng nếu user cho phép |
| **Medium** (3-10 files) | New component, refactor module | Recommended | Full workflow, Step 2 optional |
| **Large** (>10 files, cross-module) | New feature, migration | **Bắt buộc** | Full workflow bắt buộc |
| **Hotfix** (production emergency) | Critical bug in prod | Optional (nếu cần blast radius) | Skip Step 2-3 → Branch from latest release/tag → Step 5 → Step 6 lite → commit + push trực tiếp (hoặc fast-track PR). Tạo issue **sau** khi fix |

## Workflow (follow strictly in order)

### Step 0: Route by Task Type

Một số task có workflow riêng — check trước khi vào workflow chính:

| Task | Reference | Ghi chú |
|------|-----------|---------|
| Init project mới từ template | `references/init-project.md` | Xong → quay lại workflow này cho dev tiếp |
| Viết unit tests / TDD | `references/unit-testing.md` | TDD flow, spec-first, gap discovery |
| Security review / audit code | `references/security-review.md` | Script: `scripts/security-review.sh` |
| Self-improve / tự đánh giá skill | `references/self-improve.md` | Chỉ khi user yêu cầu, KHÔNG tự trigger |
| Retrospect / review CLI errors | `scripts/retrospect.py` | Xem bên dưới: Step 0b |

Nếu không match → tiếp tục Step 1 bên dưới.

### Step 0b: CLI Retrospect (Error Tracking)

**Trigger keywords:** "retrospect", "hồi tưởng", "review cli errors", "xem lỗi cli", "cli report", "error report", "analyze cli runs", "phân tích lỗi"

Chạy retrospect report từ logged CLI runs:

```bash
# Full report (last 90 days)
python3 <skill_dir>/scripts/retrospect.py

# Filter by time
python3 <skill_dir>/scripts/retrospect.py --days 7     # last week
python3 <skill_dir>/scripts/retrospect.py --days 30    # last month

# Filter by project
python3 <skill_dir>/scripts/retrospect.py --project another-me-workspace

# Include archived data
python3 <skill_dir>/scripts/retrospect.py --all

# Only trim (no report)
python3 <skill_dir>/scripts/retrospect.py --trim-only
```

**Output:** Summary table with success/fail rates, error type breakdown, per-project stats, repeated patterns, and improvement suggestions.

**After retrospect:** Review suggestions → update Lessons Learned table (below) and/or spawn.sh if patterns warrant fixes.

**Data files:**
- Active log: `~/.openclaw/workspace/memory/cli-runs.jsonl`
- Archives: `~/.openclaw/workspace/memory/cli-runs-archive/cli-runs-YYYY-QN.jsonl.gz`
- Auto-trim: entries >90 days archived on retrospect run. Also triggers if file >5MB.

### Step 0c: GitNexus Code Intelligence (Pre-Task Context)

**Khi nào dùng:** Sau Step 1 (đã hiểu task), trước Step 3 (planning) — cho task Medium/Large trên repo đã index.
**Bỏ qua:** Quick tasks, repo chưa index, task không cần architectural context.

```bash
# 0. Check GitNexus có sẵn không — nếu chưa install → skip toàn bộ Step 0c
command -v gitnexus >/dev/null 2>&1 || { echo "GitNexus not installed, skipping code intelligence. See references/gitnexus-setup.md"; exit 0; }

BRIDGE="<skill_dir>/scripts/git-nexus-mcp-bridge.js"

# 1. Check repo đã index chưa + staleness
STATUS=$(gitnexus status 2>/dev/null)
# Nếu chưa index → gitnexus analyze --skills (lần đầu)
# Nếu stale (>24h hoặc status warns) → gitnexus analyze (incremental re-index, ~2-5s)

# 2. Query context liên quan đến task → save to temp file cho Step 5.2
GN_CONTEXT="/tmp/gitnexus-context-$$.md"
echo "## GitNexus Context" > "$GN_CONTEXT"

echo "### Query Results" >> "$GN_CONTEXT"
node $BRIDGE query '{"query":"<task-related search>"}' --repo <repo-name> >> "$GN_CONTEXT" 2>/dev/null

# 3. Check blast radius nếu task sửa existing code
echo "### Impact Analysis" >> "$GN_CONTEXT"
node $BRIDGE impact '{"target":"<function/class cần sửa>"}' --repo <repo-name> >> "$GN_CONTEXT" 2>/dev/null

# 4. Inject vào Claude CLI prompt (Step 5.2): cat $GN_CONTEXT >> prompt
# ⚠️ Mỗi bridge call spawn MCP server mới (~1-2s). Chỉ chạy queries thật sự cần.
# Thường đủ: 1x query + 1x impact. Không cần gọi hết 7 tools.
```

**Workflow integration:**
- Step 1 (phân tích) → dùng `query` + `context` để hiểu module
- Step 3 (planning) → dùng `impact` để xác định scope chính xác
- Step 5.2 (prompt) → inject kết quả vào prompt → Claude Code làm đúng từ lần đầu
- Post-commit → `gitnexus analyze` tự re-index qua PostToolUse hook (Claude Code)

**Setup lần đầu:** Xem `references/gitnexus-setup.md`

### Step 1: Phân tích yêu cầu & Xác định Input/Output

**Bước này BẮT BUỘC — không được bỏ qua.**

Trước khi lên plan hay viết code, phải xác định rõ:

1. **Input** — Dữ liệu/điều kiện đầu vào là gì? (API data, user action, props...)
2. **Output mong đợi** — Kết quả cuối cùng phải như thế nào? (UI, behavior, data format...)
3. **Acceptance Criteria** — Liệt kê cụ thể các tiêu chí "done":
   - [ ] Tiêu chí 1
   - [ ] Tiêu chí 2
   - [ ] Edge cases cần xử lý
4. **Reversibility** — Task có thể revert không?
   - 🟢 Reversible (UI, refactor, test) → proceed bình thường
   - 🟡 Partial (DB migration, API contract change) → ghi backup plan
   - 🔴 Irreversible (delete data, deploy prod, external API call) → BẮT BUỘC confirm user trước khi execute
5. **Verification method** cho mỗi criterion:
   - Build pass/fail, test result, curl check, browser verify, v.v.
   - Criterion mà chỉ "looks good" / "feels right" → KHÔNG hợp lệ, phải cụ thể hơn hoặc hỏi user
6. **Nếu ambiguous → hỏi** (Hard Rule #5). Nếu có thể suy luận hợp lý → ghi assumption và tiến hành.

> ⏩ **Không chờ approval ở Step 1** — kết quả phân tích sẽ trình bày cùng plan ở Step 3 để user confirm 1 lần duy nhất.

### Step 2: Create GitHub Project Task

Sau khi đã hiểu rõ yêu cầu (Step 1), tạo GitHub Issue để tracking:

```bash
# Detect owner/repo from git remote
REPO=$(git -C ~/projects/<repo> remote get-url origin | sed 's|.*github.com[:/]||;s|\.git$||')

# Capture issue number for Step 8 PR body (Closes #N)
ISSUE_URL=$(gh issue create --repo "$REPO" \
  --title "<task>" \
  --body "<description + acceptance criteria từ Step 1>" \
  --assignee @me 2>&1)
ISSUE_NUM=$(echo "$ISSUE_URL" | grep -oP '/issues/\K\d+' || echo "")
```

Nếu project dùng GitHub Projects, thêm issue vào board:
```bash
OWNER=$(echo "$REPO" | cut -d/ -f1)
gh project list --owner "$OWNER"

# Add existing issue to project
gh project item-add <PROJECT_NUMBER> --owner "$OWNER" --url <issue-url>
```

### Step 3: Planning

Before writing any code, create a plan. Analyze:

1. **What** — What needs to be done? Break down into subtasks.
2. **Where** — Which files/modules are affected? (Nếu đã chạy Step 0c → dùng GitNexus `query`/`context` results)
3. **How** — What approach/pattern to use? Check project conventions first.
4. **Impact** — What could break? What needs testing? (Nếu đã chạy Step 0c → dùng GitNexus `impact` results cho blast radius chính xác)

Read project-specific conventions:
```bash
cat ~/projects/<repo>/.claude/instructions.md 2>/dev/null
cat ~/projects/<repo>/CLAUDE.md 2>/dev/null
cat ~/projects/<repo>/CODING.md 2>/dev/null
```

Trình bày cho user: **acceptance criteria (Step 1) + GitNexus context nếu có (Step 0c) + plan (Step 3)** cùng lúc → chờ approval 1 lần duy nhất.

💡 **Task nhỏ/rõ ràng** (fix bug cụ thể, sửa CSS, update config): có thể gộp Step 1–3 thành 1 message ngắn gọn.

### Step 4: Setup & Create Feature Branch

```bash
cd ~/projects/<repo>   # resolve ~ = actual home dir (e.g. /root, /home/coder)

# Detect environment (re-run mỗi exec session vì không share state)
source <skill_dir>/scripts/detect-env.sh

# Stash uncommitted changes nếu có (tránh checkout fail)
# Fresh repo (chưa có commits) → skip stash + checkout
if git rev-parse HEAD &>/dev/null; then
  git stash --include-untracked 2>/dev/null || true
  git checkout $DEFAULT_BRANCH
  git pull origin $DEFAULT_BRANCH
fi

# Install dependencies (đảm bảo sync sau pull)
$PM install || { echo "⚠️ Dependency install failed — check registry/lock file"; }

# Tạo branch (nếu đã tồn tại → checkout, không tạo mới)
git checkout -b <branch-type>/<short-description> 2>/dev/null \
  || git checkout <branch-type>/<short-description>
```

Branch naming (match commit type):
- `feat/<name>` — new features
- `fix/<name>` — bug fixes
- `refactor/<name>` — refactoring
- `chore/<name>` — maintenance
- `docs/<name>` — documentation
- `perf/<name>` — performance
- `hotfix/<name>` — production emergency fixes

**Hotfix flow (production emergency):**
```bash
# Branch from latest tag/release instead of main
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo $DEFAULT_BRANCH)
git checkout -b hotfix/<description> $LATEST_TAG

# After fix: push + fast-track PR (hoặc merge trực tiếp nếu user cho phép)
# Then cherry-pick to main if needed:
# git checkout main && git cherry-pick <hotfix-commit>
```
Skip Step 2-3 cho hotfix — tạo issue **sau** khi deploy fix.

### Step 5: Code with Claude CLI

**⚡ Hot Reload First:** Nếu application hỗ trợ hot reload (Next.js, Expo, Vite...), luôn ưu tiên dùng dev server + hot reload để xác thực kết quả ngay sau mỗi thay đổi.

**Quy tắc:**
- Claude CLI **chỉ edit files, KHÔNG commit** — git managed ở Step 8 (xem prompt rule trong 5.2)
- Respect `.claude/instructions.md` và project conventions

#### 5.1 Spawn Claude Code CLI

**Option A: spawn.sh wrapper (recommended)**
```bash
export ANTHROPIC_API_KEY="$KEY"
export ANTHROPIC_BASE_URL="$URL"  # optional, for proxy

bash <skill_dir>/scripts/spawn.sh <WORKDIR> <MODEL> "YOUR PROMPT"
# With session resume:
bash <skill_dir>/scripts/spawn.sh <WORKDIR> <MODEL> "continue..." <SESSION_UUID>
```
`<skill_dir>` = directory containing this SKILL.md (e.g. `~/.openclaw/workspace/skills/am-developer-skill/`)

Returns JSON: `{ result, session_id, is_error, total_cost_usd, usage }`

**Option B: Direct CLI**
```bash
CLAUDE_USER="${CLAUDE_USER:-coder}"
su - "$CLAUDE_USER" -s /bin/bash -c "
  export ANTHROPIC_API_KEY='${ANTHROPIC_API_KEY}'
  export ANTHROPIC_BASE_URL='${ANTHROPIC_BASE_URL}'
  cd <WORKDIR>
  claude --permission-mode bypassPermissions --output-format json -p 'task'
"
```

**Background mode (cho task > 2 phút):**
```bash
exec background:true command:"bash <skill_dir>/scripts/spawn.sh <WORKDIR> sonnet 'task'"
# Monitor (BẮT BUỘC — xem Hard Rule #3):
process action:poll sessionId:xxx timeout:60000
process action:log sessionId:xxx
```

**Long prompts hoặc prompts có special chars (backticks, $, quotes) → dùng file input:**
```bash
write /tmp/prompt.md "prompt content with $vars, `backticks`, and \"quotes\""
bash <skill_dir>/scripts/spawn.sh <WORKDIR> <MODEL> @/tmp/prompt.md
# Hoặc pipe stdin:
cat /tmp/prompt.md | bash <skill_dir>/scripts/spawn.sh <WORKDIR> <MODEL> -
```
⚠️ Inline prompts qua spawn.sh chỉ escape single quotes. Nếu prompt chứa `$`, `` ` ``, `"` → **luôn dùng `@file` hoặc `-` stdin**.

#### 5.2 Prompt Strategy

**High-level prompts, KHÔNG micromanage.** Claude Code tự explore codebase.

Chỉ cung cấp:
- **Goal**: cần làm gì
- **Constraints**: giữ gì, không đụng gì, pattern nào follow
- **Edge cases**: nếu X → làm Y
- **Safety**: "If unsure → choose the safer option"
- **Cuối prompt luôn thêm:** `"DO NOT git commit or push."`
- **Coding rules (luôn inject):** Đọc section "Tóm tắt" cuối [references/coding-rules.md](references/coding-rules.md), append vào cuối prompt. Đây là 8 defensive programming rules bắt buộc.
- **Unit testing rules (inject khi task cần tests):** Đọc [references/unit-testing.md](references/unit-testing.md), inject TDD flow + Gap Discovery rules vào prompt. Key: spec-first, KHÔNG đọc implementation trước, phát hiện gap → báo user quyết định.
- **GitNexus context (inject khi có):** Nếu Step 0c đã chạy, append kết quả vào prompt: `"Architectural context: [query results]. Blast radius: [impact results]. Affected symbols: [list]."` Truncate: chỉ inject top 10 results + summary, không dump toàn bộ output. Nếu bridge timeout → skip, ghi note "GitNexus unavailable".
- **Annotations (inject khi có):** Trước khi spawn, inject relevant gotchas:
  ```bash
  # Filter by scope (best) hoặc query (fuzzy match task)
  ANN_IDS="/tmp/ann-ids-$$.txt"
  ANNOTATIONS=$(bash <skill_dir>/scripts/annotate.sh inject \
    --project <repo-name> --scope <module> --limit 5 2>"$ANN_IDS")
  
  # Fallback: no filter, nhưng LUÔN set --limit
  ANNOTATIONS=$(bash <skill_dir>/scripts/annotate.sh inject \
    --project <repo-name> --limit 5 2>"$ANN_IDS")
  
  # Append (chỉ khi có output)
  [ -n "$ANNOTATIONS" ] && PROMPT="${PROMPT}\n\n${ANNOTATIONS}"
  ```
  **Token budget:** Quick tasks `--limit 3`, Medium `--limit 5`, Large `--limit 7`. Mỗi annotation ~15-25 tokens.
  IDs output to stderr → `$ANN_IDS` cho Step 5.9 hit bumping.

❌ Wrong: list mọi file, mọi dòng cần sửa, copy-paste code context
✅ Right: mô tả goal + constraints, để Claude Code tự đọc code và implement

💡 **Project conventions:** Claude Code tự đọc `.claude/instructions.md` nếu file tồn tại trong workdir. Không cần copy nội dung vào prompt — chỉ nhắc: `"Follow project conventions in .claude/instructions.md if it exists."`

**2-Phase cho complex tasks:**
```
Phase 1 (Plan): "Analyze + plan this task. Output JSON: {steps, questions, assumptions}"
  → parse result → có questions? → trả lời → Phase 2
Phase 2 (Implement): "Implement the plan. [answers if any]"
  → Resume session via session_id from Phase 1
```

#### 5.3 Timeout & Retry (BẮT BUỘC)

| Task type | Timeout | Ví dụ |
|-----------|---------|-------|
| Quick | 120s | review, explain, 1-2 files |
| Medium | 300s | 3-5 files, refactor |
| Large | 600s | >5 files, multi-module |

**Retry flow (max 3 attempts) — Adaptive:**
```
Attempt 1: full prompt, standard timeout
  ↓ fail → DIAGNOSE root cause:

  ┌─ Token/context limit?  → Split task thành chunks nhỏ hơn
  ├─ Wrong approach?       → Thay đổi prompt strategy (ví dụ: chuyển sang 2-phase plan→implement)
  ├─ Environment issue?    → Fix env trước (deps, permissions, config), retry cùng prompt
  ├─ Model limitation?     → Escalate model (sonnet → opus)
  └─ Timeout?              → Tăng timeout + simplify prompt

Attempt 2: strategy KHÁC so với attempt 1 (dựa trên diagnosis)
  ↓ fail → diagnose lại, chọn strategy chưa thử

Attempt 3: last resort — minimal prompt, max timeout, hoặc split nhỏ nhất có thể
  ↓ fail
→ BÁO USER NGAY (Hard Rule #2). Kèm: lỗi gì, đã thử gì, đề xuất hướng xử lý. KHÔNG tự code.
```

⚠️ **Mỗi attempt PHẢI khác strategy** — retry cùng cách = lãng phí. Ghi lại diagnosis mỗi attempt.

**Task > 10 files → LUÔN split:**
- Call 1: Tạo files mới (lib, utils, hooks)
- Call 2: Update files hiện có (pages, components)
- Call 3: Cleanup (xóa file cũ, verify build)

#### 5.4 Parse Result

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

- `is_error: true` → retry (xem 5.3)
- `session_id` → lưu để resume multi-turn
- CLI crash / non-JSON output → retry once, vẫn fail → báo user

#### 5.5 Available Models
- `sonnet` — default cho hầu hết tasks
- `opus` — chỉ cho deep reasoning (complex review, architecture)

#### 5.6 Environment

| Var | Required | Default | Description |
|-----|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | — | API key |
| `ANTHROPIC_BASE_URL` | ❌ | api.anthropic.com | Proxy URL |
| `CLAUDE_USER` | ❌ | `coder` | Non-root user (xem bên dưới) |

**Tại sao cần user `coder`?**
Claude Code CLI block `--permission-mode bypassPermissions` khi chạy root.
`spawn.sh` tự động `su - coder` và **tự chmod workdir** nếu thiếu permission.
Agent không cần lo permission — `spawn.sh` handle hết.

**First-time setup checklist (1 lần duy nhất):**
1. `npm install -g @anthropic-ai/claude-code` + verify `claude --version`
2. `useradd -m -s /bin/bash coder` (hoặc set `CLAUDE_USER` nếu dùng user khác)
3. Set env vars: `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL` (optional)
4. Install LSP servers: `npm install -g typescript-language-server typescript pyright`
5. Enable experimental features — tạo `/home/coder/.claude/settings.json`:
   ```json
   { "env": { "ENABLE_LSP_TOOL": "1", "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }
   ```
6. Install `acl` package nếu chưa có: `apt install acl` (cho setfacl permission handling)

#### 5.7 Monitoring Checklist (BẮT BUỘC cho background spawns)

1. **Spawn xong → báo user:** "Đang chạy Claude Code cho [task], ETA ~X phút"
2. **Poll loop:**
   ```
   process action:poll sessionId:xxx timeout:60000
   ```
   - Running + > 5 phút → báo user "Vẫn đang chạy, đã X phút"
   - Done → parse result → báo user kết quả + files changed
   - Fail → retry (xem 5.3) hoặc báo user nếu đã hết retry
3. **Partial success:**
   - Parse result text → xác định files nào đã sửa, files nào chưa
   - Resume session (`session_id`) với prompt chỉ focus files còn lại
4. **Auto-notify (recommended — append vào cuối prompt):**
   ```
   When completely finished, create a file: touch /tmp/.claude-done-<task-id>
   ```
   → `<task-id>` = branch name hoặc short hash. Agent poll `test -f /tmp/.claude-done-<task-id>` để detect completion.
   
   ⚠️ Không dùng `openclaw` CLI trong prompt — user `coder` có thể không có trong PATH.

#### 5.8 Log CLI Run (BẮT BUỘC — auto sau mỗi spawn)

Sau khi parse result (5.4), **LUÔN** log kết quả:

```bash
bash <skill_dir>/scripts/log-cli-run.sh \
  --project "<repo-name>" \
  --task "<task description>" \
  --model "<model>" \
  --exit-code <exit_code> \
  --error-type "<type>"  \
  --error-summary "<short description>" \
  --duration <seconds> \
  --cost "<cost_usd from result>" \
  --attempt <N> \
  --retry-strategy "<strategy used>" \
  --resolved <true|false> \
  --resolution "<how resolved>" \
  --session-id "<session_id from result>"
```

- **Success:** `--exit-code 0`, skip `--error-type/--error-summary/--retry-strategy`
- **Error:** classify `--error-type` per `references/error-taxonomy.md`
- **Retry:** log EACH attempt separately with incrementing `--attempt`
- Log KHÔNG block workflow — nếu log script fail, tiếp tục bình thường

#### 5.9 Capture Learnings (Auto-Annotate)

**Sau mỗi task hoàn thành**, 3 actions (tất cả non-blocking — skip nếu fail):

1. **Retry gotchas** — nếu task cần retry > 1, ghi root cause:
   ```bash
   bash <skill_dir>/scripts/annotate.sh add --project "<repo>" --scope "<module>" \
     --text "<what went wrong + fix>" --tags "<tags>" --source "auto-retry"
   ```

2. **Bump hits** — nếu Step 5.2 đã inject annotations:
   ```bash
   IDS=$(grep "^INJECTED_IDS:" "$ANN_IDS" 2>/dev/null | sed 's/INJECTED_IDS://')
   for id in $(echo "$IDS" | tr ',' ' '); do
     bash <skill_dir>/scripts/annotate.sh hit --project "<repo>" --id "$id"
   done
   ```

3. **Ask for discoveries** (optional, medium/large tasks only) — nếu có `session_id`:
   Resume session hỏi: *"List non-obvious gotchas you discovered. One line each, concise."*
   Session expired → skip. Parse → `annotate.sh add --source auto-discovery`

**Annotations auto-dedup** (>80% word overlap → skip). Text auto-truncated tại 500 chars.
**Promote:** `hits > 10` → xem xét thêm vào `.claude/instructions.md` (dùng `annotate.sh stats` để check).

**Monorepo:** 1 file per repo, `--scope` per service (`orchestrator`, `billing`, `api`...), `--query` cho cross-service.

### Step 5.10: Browser Verification (PinchTab)

**BẮT BUỘC cho frontend/fullstack tasks.** Exceptions:
- Task chỉ backend/API → skip
- Quick tasks (trivial CSS, text change, config) → skip nếu build pass
- Hotfix → skip nếu build pass + user đã confirm behavior

**Trước khi verify:** đảm bảo dev server đang chạy (xem `references/dev-preview.md` section 1-2 cho startup flow).

Sau khi dev server ready, verify UI trên browser thật. Chi tiết đầy đủ tại `references/browser-verify.md`.

```bash
# Start PinchTab (nếu chưa chạy)
pgrep -f "pinchtab" || (pinchtab &>/tmp/pinchtab.log &)
sleep 3

# Navigate & verify
pinchtab nav http://localhost:<port>/<path>
pinchtab snap -i -c
pinchtab text

# Test interactions
pinchtab click e5
pinchtab type e3 "test@example.com"
pinchtab eval "document.querySelector('form').submit()"

# Screenshot làm evidence cho PR
pinchtab screenshot -o /tmp/verify-<feature>.png
```

⚠️ **UI không đúng → FIX trước (gọi lại Claude CLI), KHÔNG tiếp tục Step 6.**

💡 **Giữ dev server chạy** — dùng tiếp cho Step 7 (Dev Preview). Build check ở Step 6.1 chỉ compile, không start server nên không conflict port.

### Step 6: Verification Pipeline

**BẮT BUỘC trước khi tạo PR.** Chi tiết tại [references/verification-pipeline.md](references/verification-pipeline.md).

| Mode | Steps | Khi nào |
|------|-------|---------|
| **Full** | Build → Types → Lint → Tests → Security → Diff → Criteria → Report | Medium/Large tasks |
| **Full + Smoke** | Full + Smoke Test (API, DB, cross-service) | Multi-service / API tasks |
| **Lite** | Build → Diff → Criteria → Report | Quick tasks, hotfix |

Nếu có FAIL → gọi lại Claude CLI để fix → chạy lại pipeline từ đầu.
**NOT READY → FIX hết. KHÔNG tạo PR khi còn FAIL.**

### Step 7: Dev Preview (Cloudflare Tunnel)

**Trigger:** User nói "test thử", "cho anh xem", "manual test", "review UI", hoặc yêu cầu link preview.
**Bỏ qua** nếu task nhỏ, backend-only, hoặc user mở localhost trực tiếp được.

Chi tiết tại `references/dev-preview.md`. Flow: start dev server → wait ready → start tunnel → gửi link → giữ alive → cleanup khi user xong.

### Step 8: Create Pull Request

```bash
cd ~/projects/<repo>
source <skill_dir>/scripts/detect-env.sh

# Nếu Claude CLI thêm package mới → đảm bảo lock file updated
if git diff $DEFAULT_BRANCH --name-only | grep -q "package.json"; then
  $PM install
fi

# Review changes trước khi commit
git status
git diff --stat

# Stage & commit (resilient — hoạt động cả khi Claude CLI đã commit hoặc chưa)
git add -A

# Count commits ahead of default branch
AHEAD=$(git rev-list --count $DEFAULT_BRANCH..HEAD 2>/dev/null || echo 0)

if [ "$AHEAD" -gt 1 ]; then
  # Multiple commits from Claude CLI → squash into 1 clean conventional commit
  git reset --soft $DEFAULT_BRANCH
  git commit -m "<type>(<scope>): <description>"
elif [ "$AHEAD" -eq 1 ]; then
  # Single commit → amend with conventional message if needed
  git commit --amend -m "<type>(<scope>): <description>" 2>/dev/null || true
else
  # No commits yet → create new
  git diff --cached --quiet || git commit -m "<type>(<scope>): <description>"
fi
git push origin <branch-name>

# === Quick tasks: commit-only path (nếu user cho phép skip PR) ===
# git checkout $DEFAULT_BRANCH
# git merge <branch-name>
# git push origin $DEFAULT_BRANCH
# git branch -d <branch-name>
# → Done, không cần PR. Chỉ dùng khi: Quick task + user explicitly OK.

# === Standard path: tạo PR ===
# Detect repo from git remote
REPO=$(git remote get-url origin | sed 's|.*github.com[:/]||;s|\.git$||')

# Tạo PR — nhúng verification report vào body, assign luôn
gh pr create \
  --repo "$REPO" \
  --title "<type>(<scope>): <description>" \
  --assignee @me \
  --body "## Changes
- <change 1>
- <change 2>

## Task
- Closes #<issue-number> (if applicable)

## Verification Report
<nhúng report từ Step 6.8>

## Testing
- <how to test>" \
  --base $DEFAULT_BRANCH
```

### Handling PR Review Feedback

Khi reviewer request changes:

```bash
cd ~/projects/<repo>
git checkout <feature-branch>

# Fix theo feedback — spawn Claude CLI (xem Step 5, nhớ "DO NOT git commit" rule)

# Chạy lại verification pipeline (Step 6)
# Sau khi PASS:
git add -A
git diff --cached --quiet || git commit -m "fix: address PR review feedback"
git push origin <feature-branch>
```

→ PR tự update. Reply vào review comments giải thích đã fix gì.

### Conventional Commits (BẮT BUỘC)

Chi tiết tại [references/conventions.md](references/conventions.md). Format: `<type>(<scope>): <description>` — types: feat, fix, docs, style, refactor, perf, test, chore.

## Lessons Learned

**Skill-level** learnings — cách dùng skill, workflow insights, tool quirks.
Khác với **annotations** (project-level gotchas lưu trong `memory/am-developer-skill-annotations/<project>.jsonl`).

- **Lessons Learned** = "spawn.sh cần setfacl" (áp dụng mọi project)
- **Annotations** = "Orchestrator phải docker compose up --build" (project-specific)

| # | Lesson | Context |
|---|--------|---------|
| 1 | **`spawn.sh` cần setfacl/chmod workdir** — user `coder` không access được dir owned by root | Test task 2026-03-14: files tạo sai chỗ (`/tmp/src/` thay vì workdir) |
| 2 | **`--permission-mode bypassPermissions` blocked for root** — phải dùng `su - coder` | Claude Code CLI restriction |
| 3 | **`--permission-mode acceptEdits`** là alternative khi không dùng được `bypassPermissions` — nhưng sẽ hỏi confirm cho commands | Fallback option, chưa cần |
| 4 | **Per-project annotations = learning loop** — gotchas persist qua sessions, auto-inject vào prompt. Dùng `annotate.sh inject` (Step 5.2) + `annotate.sh add` (Step 5.9) | Inspired by Context Hub (andrewyng). 2026-03-19 |
| 5 | **Python heredoc + positional args = broken** — `python3 << 'EOF' "$arg"` treats arg as filename. Dùng env vars: `_PY_VAR="$val" python3 << 'EOF'` | annotate.sh refactor. 2026-03-19 |
| 6 | **JSONL must be fault-tolerant** — 1 corrupted line crashes toàn bộ command. Luôn wrap `json.loads()` trong try/except | annotate.sh round 2. 2026-03-19 |
| 7 | **Multi-commit squash** — Claude CLI có thể tạo nhiều commits. `git reset --soft` + re-commit thay vì amend (chỉ fix commit cuối) | Step 8 fix. 2026-03-19 |
| 8 | **Task size gates everything** — Quick/Medium/Large/Hotfix quyết định workflow depth. Quick = skip annotations heavy inject, skip browser verify trivial, skip verification full. Không one-size-fits-all | Simulation round 3. 2026-03-19 |
| 9 | **Annotations need guardrails** — auto-dedup (≥80% word overlap), text truncate 500 chars, size limits. Không để agent dump stack traces làm annotation | Adversarial round 4. 2026-03-19 |
| 10 | **Claude CLI smart quotes** — CLI đôi khi dùng `''` (U+2018/2019) trong JS strings → syntax error. Detect + sed/python replace sau mỗi spawn nếu output có JS/TS files | another-me star-office-ui. 2026-03-17 |

## Domain References (đọc khi cần, KHÔNG load mặc định)

Reference files cung cấp domain knowledge cho các loại task cụ thể. **Chỉ đọc khi task match**, không load sẵn để tiết kiệm token.

| Reference | Khi nào đọc | Path |
|-----------|-------------|------|
| Unit Testing | Task viết tests, TDD, hoặc Claude CLI cần viết tests kèm feature | [references/unit-testing.md](references/unit-testing.md) |
| Coding Rules | **MỌI task code** — inject tóm tắt vào Claude CLI prompt | [references/coding-rules.md](references/coding-rules.md) |
| Tech Stack | User hỏi chọn framework/lib, hoặc agent cần chọn stack cho project mới | [references/tech-stack.md](references/tech-stack.md) |
| Landing Page | User yêu cầu build landing page, marketing page, product page | [references/landing-page.md](references/landing-page.md) |
| Conventions | Cần check project conventions | [references/conventions.md](references/conventions.md) |
| Tunnel Setup | Cần setup Cloudflare tunnel mới | [references/tunnel-setup.md](references/tunnel-setup.md) |
| Docker Rules | Task liên quan Docker: deploy, docker-compose, container management | [references/docker-rules.md](references/docker-rules.md) |
| Multi-Service Deploy | Deploy project có ≥3 services interdependent, rollback strategy | [references/multi-service-deploy.md](references/multi-service-deploy.md) |
| Init Project | Khởi tạo project mới từ template (Step 0) | [references/init-project.md](references/init-project.md) |
| Browser Verify | Verify UI frontend qua PinchTab (Step 5.10) | [references/browser-verify.md](references/browser-verify.md) |
| Security Review | Security audit codebase (Step 0) | [references/security-review.md](references/security-review.md) |
| Dev Preview | Dev preview qua Cloudflare tunnel (Step 7) | [references/dev-preview.md](references/dev-preview.md) |
| Self-Improve | Skill tự đánh giá/cải tiến từ dev history (Step 0) | [references/self-improve.md](references/self-improve.md) |
| Error Taxonomy | Phân loại error types cho CLI logging (Step 5.8) | [references/error-taxonomy.md](references/error-taxonomy.md) |
| Verification Pipeline | Full verification pipeline chi tiết (Step 6) | [references/verification-pipeline.md](references/verification-pipeline.md) |
| GitNexus Setup | Install, index, MCP bridge usage, troubleshooting (Step 0c) | [references/gitnexus-setup.md](references/gitnexus-setup.md) |

**Cách dùng:**
1. Detect task type từ yêu cầu user
2. Đọc reference file tương ứng (nếu có)
3. Inject nội dung relevant vào prompt cho Claude CLI (Step 5)

> 💡 Thêm reference mới: tạo file trong `references/`, update bảng trên.

## Quick Reference

Conventions, conflict resolution, module system → [references/conventions.md](references/conventions.md)

## Tools Required

- `claude` CLI (v2.1.63+) — coding agent (xem setup tại Step 5.6)
- `gh` CLI — GitHub operations
- `cloudflared` — dev preview tunnels
- `git` — version control
- `typescript-language-server`, `pyright` — LSP servers cho code navigation (recommended)
- `gitnexus` — code intelligence engine, MCP tools cho codebase awareness (recommended, xem `references/gitnexus-setup.md`)
