---
name: am-developer-skill
version: 1.7.0
author: khoidoan
description: >
  Developer workflow for ALL coding tasks. Handles: Claude Code CLI with retry, planning,
  branching, verification, PR creation. Code on container or user's device via SSH.
  CLI error tracking with auto-log and retrospect analysis.
  Use when: init project, security audit, build feature, fix bug, refactor, code review, generate tests,
  write unit tests, TDD, viết tests, deploy config, self-improve dev skill, retrospect, hồi tưởng,
  review cli errors, xem lỗi cli, cli report, error report, analyze cli runs, phân tích lỗi.
  NOT for: reading code (use read), edits under 3 lines (use edit), ACP requests (use sessions_spawn).
---

# Another Me Developer Skill

Developer workflow cho MỌI coding tasks — từ quick edits đến complex multi-file features.

**Workspace mặc định:** `~/.openclaw/projects/<repo>` (container) hoặc user's device via SSH.

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

## When to Use

✅ **Dùng khi:** Bất kỳ task cần code — feature, bug fix, refactor, test, review, scaffolding
❌ **Không dùng khi:** Edit < 3 dòng trivial → `edit` tool. Chỉ đọc code → `read` tool.

### Task Size → Workflow

| Task size | Ví dụ | Workflow |
|-----------|-------|----------|
| **Quick** (1-3 files, isolated) | Fix CSS, update text, add test | Bước 1 gọn → Skip 2-3 → Bước 4 (annotations: `--limit 3` hoặc skip) → Bước 5 lite (Build + Diff + Criteria only). PR optional |
| **Medium** (3-10 files) | New component, refactor module | Full workflow, Bước 2 optional |
| **Large** (>10 files, cross-module) | New feature, migration | Full workflow bắt buộc |
| **Hotfix** (production emergency) | Critical bug in prod | Skip Bước 2-3 → Branch from latest tag → Bước 4 → Bước 5 lite → commit + push trực tiếp. Tạo issue **sau** khi fix |

## Workflow (follow strictly in order)

### Bước 0: Route by Task Type

Một số task có workflow riêng — check trước khi vào workflow chính:

| Task | Reference | Ghi chú |
|------|-----------|---------|
| Init project mới từ template | `references/init-project.md` | Xong → quay lại workflow này |
| Viết unit tests / TDD | `references/unit-testing.md` | TDD flow, spec-first, gap discovery |
| Security review / audit code | `references/security-review.md` | Script: `scripts/security-review.sh` |
| Self-improve / tự đánh giá skill | `references/self-improve.md` | Chỉ khi user yêu cầu |
| Retrospect / review CLI errors | `scripts/retrospect.py` | Xem Bước 0b |

Nếu không match → tiếp tục Bước 1.

### Bước 0b: CLI Retrospect (Error Tracking)

**Trigger keywords:** "retrospect", "hồi tưởng", "review cli errors", "xem lỗi cli", "cli report", "error report", "analyze cli runs", "phân tích lỗi"

```bash
# Full report (last 90 days)
python3 <skill_dir>/scripts/retrospect.py

# Filter by time or project
python3 <skill_dir>/scripts/retrospect.py --days 7
python3 <skill_dir>/scripts/retrospect.py --project <repo-name>
```

**Data files:**
- Active log: `~/.openclaw/workspace/memory/cli-runs.jsonl`
- Archives: `~/.openclaw/workspace/memory/cli-runs-archive/cli-runs-YYYY-QN.jsonl.gz`
- Auto-trim: entries >90 days archived on retrospect run.

### Bước 1: Phân tích yêu cầu & Xác định Workspace

**Bước này BẮT BUỘC — không được bỏ qua.**

#### 1.1 Phân tích Input/Output

1. **Input** — Dữ liệu/điều kiện đầu vào
2. **Output mong đợi** — Kết quả cuối cùng
3. **Acceptance Criteria** — Tiêu chí "done" cụ thể
4. **Reversibility:**
   - 🟢 Reversible (UI, refactor, test) → proceed
   - 🟡 Partial (DB migration, API contract) → ghi backup plan
   - 🔴 Irreversible (delete data, deploy prod) → BẮT BUỘC confirm user
5. **Verification method** cho mỗi criterion (build, test, curl, browser...)
6. **Ambiguous → hỏi** (Hard Rule #5). Suy luận được → ghi assumption, tiến hành.

> ⏩ Trình bày cùng plan ở Bước 2 → user confirm 1 lần duy nhất.

#### 1.2 Xác định Workspace

| Tình huống | Workspace |
|------------|-----------|
| Web app, API, backend | Container (`~/.openclaw/projects/`) |
| Mobile app, native build, GPU | Device via SSH (kết hợp `am-devices` skill) |
| User không specify | Container |

**Container:**
```bash
WORKSPACE=~/.openclaw/projects
mkdir -p $WORKSPACE && cd $WORKSPACE
[ ! -d "<project-name>" ] && git clone <repo-url> <project-name>
cd <project-name>
```

**Device (SSH):**
```bash
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519"
ssh $SSH_OPTS {user}@{ip} "ls -la ~/projects/{project}"
```

### Bước 2: Planning

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

### Bước 3: Setup & Create Feature Branch

> ⚠️ **Biến không share giữa exec sessions.** Re-detect mỗi lần.

```bash
cd ~/.openclaw/projects/<repo>

# === Environment Setup (copy vào đầu mỗi exec session) ===
source <skill_dir>/scripts/detect-env.sh
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519"
# ===================================================================

git stash --include-untracked 2>/dev/null || true
git checkout $DEFAULT_BRANCH && git pull origin $DEFAULT_BRANCH
[ -n "$PM" ] && $PM install

git checkout -b <branch-type>/<short-description> 2>/dev/null \
  || git checkout <branch-type>/<short-description>
```

Branch types: `feat/`, `fix/`, `refactor/`, `chore/`, `docs/`, `perf/`, `test/`, `hotfix/`

**Hotfix flow:**
```bash
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo $DEFAULT_BRANCH)
git checkout -b hotfix/<description> $LATEST_TAG
```

### Bước 4: Code với Claude CLI

**⚡ Hot Reload First:** Nếu app hỗ trợ hot reload → ưu tiên dev server.

**Quy tắc:**
- Claude CLI **chỉ edit files, KHÔNG commit** — git managed ở Bước 7
- Respect `.claude/instructions.md` và project conventions

#### 4.1 Spawn Claude Code CLI

**Container (root — mặc định):**
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

**Background (task > 2 phút):**
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

#### 4.2 Prompt Strategy

**High-level prompts, KHÔNG micromanage.** Claude Code tự explore codebase.

Chỉ cung cấp:
- **Goal**: cần làm gì
- **Constraints**: giữ gì, không đụng gì, pattern nào follow
- **Edge cases**: nếu X → làm Y
- **Safety**: "If unsure → choose the safer option"
- **Cuối prompt luôn thêm:** `"DO NOT git commit or push."`
- **Coding rules (luôn inject):** Đọc section "Tóm tắt" cuối [references/coding-rules.md](references/coding-rules.md), append vào cuối prompt. Defensive programming rules bắt buộc.
- **Unit testing rules (inject khi task cần tests):** Đọc [references/unit-testing.md](references/unit-testing.md), inject TDD flow + Gap Discovery rules vào prompt. Key: spec-first, KHÔNG đọc implementation trước, phát hiện gap → báo user quyết định.
- **Annotations (inject khi có):** Trước khi spawn, inject relevant gotchas:
  ```bash
  ANNOTATIONS=$(bash <skill_dir>/scripts/annotate.sh inject \
    --project <repo-name> --scope <module> --limit 5 2>/tmp/ann-ids.txt)
  
  # Fallback: no filter, nhưng LUÔN set --limit
  ANNOTATIONS=$(bash <skill_dir>/scripts/annotate.sh inject \
    --project <repo-name> --limit 5 2>/tmp/ann-ids.txt)
  
  [ -n "$ANNOTATIONS" ] && PROMPT="${PROMPT}\n\n${ANNOTATIONS}"
  ```
  **Token budget:** Quick tasks `--limit 3`, Medium `--limit 5`, Large `--limit 7`.

❌ Wrong: list mọi file, mọi dòng cần sửa, copy-paste code context
✅ Right: mô tả goal + constraints, để Claude Code tự đọc code và implement

💡 **Project conventions:** Claude Code tự đọc `.claude/instructions.md` nếu có.

**2-Phase cho complex tasks:**
```
Phase 1 (Plan): "Analyze + plan this task. Output JSON: {steps, questions, assumptions}"
  → parse result → có questions? → trả lời → Phase 2
Phase 2 (Implement): "Implement the plan. [answers if any]"
  → Resume session via session_id from Phase 1
```

#### 4.3 Timeout & Retry (BẮT BUỘC)

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
  ├─ Wrong approach?       → Thay đổi prompt strategy
  ├─ Environment issue?    → Fix env trước, retry cùng prompt
  ├─ Model limitation?     → Escalate model (sonnet → opus)
  └─ Timeout?              → Tăng timeout + simplify prompt

Attempt 2: strategy KHÁC (dựa trên diagnosis)
Attempt 3: last resort — minimal prompt, max timeout, hoặc split nhỏ nhất
  ↓ fail → BÁO USER NGAY (Hard Rule #2)
```

⚠️ **Mỗi attempt PHẢI khác strategy** — retry cùng cách = lãng phí.

**Task > 10 files → LUÔN split:**
- Call 1: Tạo files mới (lib, utils, hooks)
- Call 2: Update files hiện có (pages, components)
- Call 3: Cleanup (xóa file cũ, verify build)

#### 4.4 Parse Result

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

#### 4.5 Available Models
- `sonnet` — default cho hầu hết tasks
- `opus` — chỉ cho deep reasoning (complex review, architecture)

#### 4.6 Monitoring (BẮT BUỘC cho background spawns)

1. **Spawn xong → báo user:** "Đang chạy Claude Code cho [task], ETA ~X phút"
2. **Poll loop:**
   ```
   process action:poll sessionId:xxx timeout:60000
   ```
   - Running + > 5 phút → báo user "Vẫn đang chạy, đã X phút"
   - Done → parse result → báo user kết quả + files changed
   - Fail → retry (xem 4.3) hoặc báo user nếu đã hết retry
3. **Partial success:** Resume session (`session_id`) với prompt focus files còn lại
4. **> 10 phút → kill, báo user, đề xuất split**

#### 4.7 Code trên Device (SSH)

```bash
# Direct: chạy CLI trên device (nếu có Claude CLI)
ssh $SSH_OPTS {user}@{ip} "cd ~/projects/{project} && claude --dangerously-skip-permissions --output-format json -p 'task'"
```

#### 4.8 Log CLI Run (BẮT BUỘC — auto sau mỗi spawn)

Sau khi parse result (4.4), **LUÔN** log kết quả:

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
- Log KHÔNG block workflow — nếu log script fail, tiếp tục bình thường

#### 4.9 Capture Learnings (Auto-Annotate)

**Sau mỗi task hoàn thành**, 3 actions (non-blocking):

1. **Retry gotchas** — nếu task cần retry > 1:
   ```bash
   bash <skill_dir>/scripts/annotate.sh add --project "<repo>" --scope "<module>" \
     --text "<what went wrong + fix>" --tags "<tags>" --source "auto-retry"
   ```

2. **Bump hits** — nếu Bước 4.2 đã inject annotations:
   ```bash
   IDS=$(grep "^INJECTED_IDS:" /tmp/ann-ids.txt 2>/dev/null | sed 's/INJECTED_IDS://')
   for id in $(echo "$IDS" | tr ',' ' '); do
     bash <skill_dir>/scripts/annotate.sh hit --project "<repo>" --id "$id"
   done
   ```

3. **Ask for discoveries** (optional, medium/large tasks only) — nếu có `session_id`:
   Resume session hỏi: *"List non-obvious gotchas you discovered. One line each, concise."*
   Parse → `annotate.sh add --source auto-discovery`

### Bước 4.10: Browser Verification (nếu có PinchTab)

**BẮT BUỘC cho frontend/fullstack tasks.** Skip nếu: backend-only, PinchTab không available, trivial CSS.

```bash
pgrep -f "pinchtab" || (pinchtab &>/tmp/pinchtab.log &)
sleep 3
pinchtab nav http://localhost:<port>/<path>
pinchtab snap -i -c
pinchtab text
pinchtab screenshot -o /tmp/verify-<feature>.png
```

⚠️ **UI không đúng → FIX trước (gọi lại Claude CLI), KHÔNG tiếp tục Bước 5.**

### Bước 5: Verification Pipeline

**BẮT BUỘC trước khi tạo PR.** Chi tiết tại [references/verification-pipeline.md](references/verification-pipeline.md).

| Mode | Steps | Khi nào |
|------|-------|---------|
| **Full** | Build → Types → Lint → Tests → Security → Diff → Criteria → Report | Medium/Large tasks |
| **Full + Smoke** | Full + Smoke Test (API, DB, cross-service) | Multi-service / API tasks |
| **Lite** | Build → Diff → Criteria → Report | Quick tasks, hotfix |

Nếu có FAIL → gọi lại Claude CLI để fix → chạy lại pipeline từ đầu.
**NOT READY → FIX hết. KHÔNG tạo PR khi còn FAIL.**

### Bước 6: Dev Preview (Cloudflare Tunnel)

**Trigger:** User nói "test thử", "cho anh xem", "manual test", "review UI".
**Bỏ qua** nếu task nhỏ, backend-only, hoặc user mở localhost trực tiếp được.

Chi tiết tại `references/dev-preview.md`. Flow: start dev server → wait ready → start tunnel → gửi link → giữ alive → cleanup khi user xong.

### Bước 7: Commit & Push

```bash
cd ~/.openclaw/projects/<repo>
source <skill_dir>/scripts/detect-env.sh

[ -n "$PM" ] && git diff $DEFAULT_BRANCH --name-only | grep -q "package.json" && $PM install

git status && git diff --stat
git add -A

# Count commits ahead of default branch
AHEAD=$(git rev-list --count $DEFAULT_BRANCH..HEAD 2>/dev/null || echo 0)

if [ "$AHEAD" -gt 1 ]; then
  # Multiple commits from Claude CLI → squash into 1 clean conventional commit
  git reset --soft $DEFAULT_BRANCH
  git commit -m "<type>(<scope>): <description>"
elif [ "$AHEAD" -eq 1 ]; then
  git commit --amend -m "<type>(<scope>): <description>" --no-edit 2>/dev/null || true
else
  git diff --cached --quiet || git commit -m "<type>(<scope>): <description>"
fi
git push origin <branch-name>
```

### Conventional Commits (BẮT BUỘC)

Format: `<type>[optional scope]: <description>`

| Type | Khi nào |
|------|---------|
| `feat` | Feature mới |
| `fix` | Sửa bug |
| `docs` | Chỉ docs |
| `style` | Format (không đổi logic) |
| `refactor` | Refactor |
| `perf` | Performance |
| `test` | Thêm/sửa test |
| `chore` | Build, CI, deps |

Quy tắc: lowercase, imperative mood, ≤ 72 chars, không chấm cuối.

### Bước 8: Pull Request (nếu có `gh` CLI)

```bash
REPO=$(git remote get-url origin | sed 's|.*github.com[:/]||;s|\.git$||')

gh pr create --repo "$REPO" \
  --title "<type>(<scope>): <description>" \
  --assignee @me \
  --body "## Changes
- <change 1>
- <change 2>

## Verification Report
<nhúng report từ Bước 5>

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
git add -A
git diff --cached --quiet || git commit -m "fix: address PR review feedback"
git push origin <feature-branch>
```

## Lessons Learned

| # | Lesson | Context |
|---|--------|---------|
| 1 | `--dangerously-skip-permissions` chỉ hoạt động root + CLI mới | Container default root |
| 2 | `--permission-mode bypassPermissions` blocked for root | Fallback: tạo user `coder` |
| 3 | Poll mỗi 30-60s — spawn rồi quên = bug | Hard Rule #3 |
| 4 | Quick tunnel URL random mỗi lần — OK cho single app | Multi-service cần inject URL |
| 5 | Mỗi retry PHẢI khác strategy — retry cùng cách = lãng phí | Adaptive retry |
| 6 | Task > 10 files → LUÔN split thành multiple calls | Tránh timeout + token limit |
| 7 | **Multi-commit squash** — Claude CLI có thể tạo nhiều commits. `git reset --soft` + re-commit | Bước 7 squash flow |
| 8 | **Task size gates everything** — Quick/Medium/Large/Hotfix quyết định workflow depth | Không one-size-fits-all |
| 9 | **Annotations need guardrails** — auto-dedup (≥80% overlap), text truncate 500 chars | Không dump stack traces |
| 10 | **Claude CLI smart quotes** — CLI dùng `''` (U+2018/2019) trong JS → syntax error. Detect + replace | another-me gotcha |
| 11 | **CF Worker→Worker fetch 503** — CF Worker gọi CF Worker bằng URL → 503. Dùng Service Bindings | another-me middleware |
| 12 | **FK delete order matters** — Xóa record có FK phải xóa child tables trước → parent last | Agent stuck deleting |

## Domain References (đọc khi cần, KHÔNG load mặc định)

| Reference | Khi nào đọc | Path |
|-----------|-------------|------|
| Unit Testing | Task viết tests, TDD, hoặc Claude CLI cần viết tests | [references/unit-testing.md](references/unit-testing.md) |
| Coding Rules | **MỌI task code** — inject tóm tắt vào prompt | [references/coding-rules.md](references/coding-rules.md) |
| Tech Stack | Chọn framework/lib cho project mới | [references/tech-stack.md](references/tech-stack.md) |
| Landing Page | Build landing page, marketing page | [references/landing-page.md](references/landing-page.md) |
| Conventions | Check project conventions | [references/conventions.md](references/conventions.md) |
| Tunnel Setup | Setup Cloudflare tunnel mới | [references/tunnel-setup.md](references/tunnel-setup.md) |
| Docker Rules | Docker deploy, docker-compose, container management | [references/docker-rules.md](references/docker-rules.md) |
| Multi-Service Deploy | Deploy project ≥3 services, rollback strategy | [references/multi-service-deploy.md](references/multi-service-deploy.md) |
| Init Project | Khởi tạo project mới từ template (Bước 0) | [references/init-project.md](references/init-project.md) |
| Browser Verify | Verify UI frontend qua PinchTab (Bước 4.10) | [references/browser-verify.md](references/browser-verify.md) |
| Security Review | Security audit codebase (Bước 0) | [references/security-review.md](references/security-review.md) |
| Dev Preview | Dev preview qua Cloudflare tunnel (Bước 6) | [references/dev-preview.md](references/dev-preview.md) |
| Self-Improve | Skill tự đánh giá/cải tiến (Bước 0) | [references/self-improve.md](references/self-improve.md) |
| Error Taxonomy | Phân loại error types cho CLI logging (Bước 4.8) | [references/error-taxonomy.md](references/error-taxonomy.md) |
| Verification Pipeline | Full verification pipeline chi tiết (Bước 5) | [references/verification-pipeline.md](references/verification-pipeline.md) |

## Platform-specific (SSH — via am-devices)

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

## Quick Reference

### Conflict Resolution
1. Read — understand both sides
2. Prioritize default branch — code đã reviewed
3. Ask if unsure — never silently delete someone else's code
4. Use Claude CLI for complex conflicts
5. Never force push to default branch

### Module System
Follow project's existing module system. Prefer ESM cho new projects.

## Tools Required

- `claude` CLI (v2.1.63+) — coding agent
- `gh` CLI — GitHub operations (optional, cho PR)
- `cloudflared` — dev preview tunnels (optional)
- `git` — version control
