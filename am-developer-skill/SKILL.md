---
name: am-developer-skill
version: 2.3.0
author: khoidoan
description: >
  Developer workflow for ALL coding tasks: scout → plan → code → verify → PR.
  Handles feature, bug fix, refactor, test, deploy config via Claude CLI or self-code.
  Worktree-aware parallel sessions, verification pipeline, conventional commits.
  Use when: any coding task. Triggers: build, fix, refactor, test, deploy, init project, security audit.
  NOT for: edits under 3 lines (use edit), reading code (use read).
---

# Another Me Developer Skill

Developer workflow for ALL coding tasks — quick edits to complex multi-file features.

**Projects path:** Detect từ environment. Thường là `~/projects/<repo>` hoặc repo đã clone sẵn.
Nếu chưa có repo → `git clone` vào `~/projects/` trước khi bắt đầu.

## Permissions

**reads:** source code, git history, configs | **writes:** source files, branches, lock files, CLI logs, annotations
**external:** GitHub (`gh` — nếu có), Claude Code CLI, GitNexus (optional) | **destructive:** `git reset --soft`, `git stash`, branch delete
**requires_confirmation:** irreversible actions (DB prod, delete data, deploy prod)

> ⚠️ **Tool availability varies per agent.** Trước khi dùng tool nào, check: `command -v <tool> &>/dev/null`. Không có → skip bước đó hoặc dùng alternative.

## ⛔ Hard Rules (NEVER VIOLATE)

| # | Rule | Key Point |
|---|------|-----------|
| 1 | **Prefer Claude CLI** | Có Claude CLI → dùng nó (Step 5). Không có → agent tự code, nhưng vẫn follow process (plan → verify). Exception: edit < 3 dòng trivial |
| 2 | **MUST report failures** | 3 attempts fail → BÁO USER NGAY: lỗi gì, retry mấy lần, đề xuất hướng xử lý |
| 3 | **MUST monitor spawns** | Poll 30-60s. Spawn rồi quên = BUG |
| 4 | **MUST update progress** | Spawn → báo ETA. Done → báo kết quả. **Im lặng > 2 phút = BUG** |
| 5 | **MUST chunk tasks** | Mỗi spawn ~1-2 phút. Task lớn → chia subtasks. KHÔNG gom 1 prompt khổng lồ |
| 6 | **MUST challenge ambiguity** | Thiếu info hoặc risk chưa acknowledge → HỎI TRƯỚC, không tự đoán |
| 7 | **MUST verify, don't assume** | Medium+ → discuss approach trước (1b). Done → self-review (Step 6). Build pass ≠ done |

**#6 vs #7:** #6 = "thiếu info → hỏi", #7 = "có info → đừng skip process". Không chắc Quick/Medium → default Medium.

## When to Use & Task Routing

✅ Mọi task cần code: feature, bug fix, refactor, test, deploy config
❌ Skip: edit < 3 dòng trivial (`edit` tool), chỉ đọc code (`read`)

**Không chắc Quick/Medium → default Medium (Hard Rule #7).**

| Size | Scout | Flow |
|------|-------|------|
| **Quick** (≤3 files, isolated, no logic change) | locate only | `[1a] → 1 → 4 → 5 → 6 lite → 8` |
| **Medium** (3-10 files, logic change) | full 5 bước | `1a → 1+1b → 2-3 → 4 → 5 → [5.10] → 6 full → 8` |
| **Large** (>10 files, cross-module) | full 5 bước | `1a → 1+1b → 2-3+issue → 4 → 5 → [5.10] → 6 full → 8` |
| **Hotfix** (prod emergency) | reproduce+locate | `1a → 1 → 4(tag) → 5 → 6 lite → push → [9]` |
| **Greenfield** (100% new) | skip | `1+1b → 2-3 → 4 → 5 → [5.10] → 6 → 8` |

`[brackets]` = optional. Mọi flow kết thúc bằng Step 8b (release lock).

## Workflow (follow strictly in order)

### Step 0: Route & Tools

**Special task types** — đọc reference tương ứng trước khi vào workflow:
Init project → `references/init-project.md` | Unit tests/TDD → `references/unit-testing.md` | Security review → `references/security-review.md` | Self-improve → `references/self-improve.md`

**Optional tools** (dùng trong Scout nếu có):
- **Retrospect:** `python3 <skill_dir>/scripts/retrospect.py [--days 7]` — CLI error patterns
- **GitNexus:** `node <skill_dir>/scripts/git-nexus-mcp-bridge.js query/impact` — code search + blast radius

Không match special type → Step 1a (Scout).

### Step 1a: Scout — Investigate Before You Plan

**BẮT BUỘC cho bug fixes + tasks cần hiểu existing code.** Skip: greenfield, docs, config.

5 bước (Quick tasks chỉ cần 1-2):

1. **Reproduce** — verify bug, điều kiện trigger (curl, browser, logs)
2. **Locate** — grep keywords, `git log -10 -- <file>`, GitNexus query (nếu có)
3. **Root Cause** — đọc code, trace data flow. Ghi: "Bug ở file X, dòng Y, vì Z"
4. **Blast Radius** — ai gọi function này? grep callers, GitNexus impact
5. **Evidence** — log/stack trace, screenshot, commit hash (nếu regression)

**Output** (trình bày ở Step 1):
```
🔍 Scout: Reproduce [✅/❌] | Location [file:line] | Root cause [mô tả] | Blast radius [N callers] | Evidence [proof]
```

⚠️ Scout = đọc + trace. KHÔNG sửa code.

---

### Step 1: Phân tích yêu cầu (dựa trên Scout)

Dựa trên scout findings (Step 1a), xác định:

- [ ] **Input/Output** — đầu vào gì, kết quả mong đợi gì
- [ ] **Acceptance Criteria** — tiêu chí "done" cụ thể (bao gồm edge cases)
- [ ] **Reversibility** — 🟢 safe / 🟡 partial (ghi backup plan) / 🔴 irreversible (confirm user trước)
- [ ] **Verify method** — build/test/curl/browser cho mỗi criterion (không chấp nhận "looks good")
- [ ] **Ambiguous?** → hỏi (Hard Rule #6)

> Trình bày cùng Step 1b trong 1 message → chờ user approval 1 lần.

**Quick:** 1-2 dòng đủ. `Task: X | Criteria: Y | Verify: Z`. Skip 1b + 2-3.

---

### Step 1b: Solution Discussion (Medium/Large — Hard Rule #7)

Dựa trên scout evidence, đề xuất **2-3 approaches** (pros/cons/complexity/risk) + recommendation.
Trình bày cùng Step 1 trong 1 message → **chờ user chọn**, KHÔNG tự quyết.

Skip: Quick tasks, hotfix, approach hiển nhiên chỉ có 1.
Medium approach rõ ràng → gộp: analysis + 1 approach + "nếu OK em chạy luôn".

### Step 2-3: Planning

Chia subtasks nhỏ (~1-2 phút mỗi cái). Dùng scout findings cho accuracy:

```
Subtask N: <tên> | Files: <từ scout> | ETA: ~1-2 phút | Verify: <build/test>
```

Check conventions: `cat $WORKDIR/.claude/instructions.md 2>/dev/null`
**GitHub Issue** (Large only, cần `gh`): `gh issue create --repo "$REPO" --title "<task>" --assignee @me`
Quick tasks → skip, gộp Step 1-3 thành 1 message.

### Step 4: Setup & Create Feature Branch (Worktree-Aware)

`worktree.sh` tự decide: repo free → dùng trực tiếp, bận → tạo worktree sibling.

```bash
REPO_ROOT=~/projects/<repo>
BRANCH_NAME=<branch-type>/<short-description>   # feat/, fix/, refactor/, chore/, docs/, perf/, hotfix/

# Acquire workdir (returns repo root OR new worktree path)
WORKDIR=$(bash <skill_dir>/scripts/worktree.sh acquire "$REPO_ROOT" "$BRANCH_NAME")
cd "$WORKDIR"
source <skill_dir>/scripts/detect-env.sh

# Nếu repo gốc → checkout branch; worktree → branch đã set bởi script
[ "$WORKDIR" = "$REPO_ROOT" ] && {
  git rev-parse HEAD &>/dev/null && git checkout $DEFAULT_BRANCH && git pull origin $DEFAULT_BRANCH
  git checkout -b "$BRANCH_NAME" 2>/dev/null || git checkout "$BRANCH_NAME"
}

$PM install  # bắt buộc — worktree không share node_modules
echo "$WORKDIR" > /tmp/openclaw-workdir-$$.txt  # save cho Step 5, 6, 8
```

**Hotfix:** `worktree.sh acquire` + `git reset --hard $(git describe --tags --abbrev=0)`. Skip Step 2-3.
**Status:** `bash <skill_dir>/scripts/worktree.sh status ~/projects/<repo>`

### Step 5: Implement Code

**2 modes tuỳ môi trường:**

#### Mode A: Claude CLI available (`command -v claude &>/dev/null`)

Chi tiết: [references/claude-cli-guide.md](references/claude-cli-guide.md)

```bash
bash <skill_dir>/scripts/spawn.sh <WORKDIR> <MODEL> "YOUR PROMPT"
# Timeout default 180s. Exit 124 = timed out → chia nhỏ hơn
```

Inject vào prompt: scout findings → coding rules → annotations → `"DO NOT git commit or push."`

Sau spawn: parse `is_error` → retry max 3 → log (`scripts/log-cli-run.sh`) → report user.

#### Mode B: Self-code (Claude CLI không có)

Agent tự implement qua `read` + `edit`/`write` tools. **Vẫn follow toàn bộ process:**
- Đọc [references/coding-rules.md](references/coding-rules.md) trước khi code — 10 rules bắt buộc
- **Read before edit** — LUÔN đọc file trước khi sửa, hiểu context
- Chunk: mỗi lần edit 1-2 files → `$PM run build` verify → tiếp file sau
- **KHÔNG commit** — git managed ở Step 8
- Report progress cho user sau mỗi file/module
- Nếu task phức tạp (>5 files, cross-module logic) → **hỏi user** có muốn cài Claude CLI không

**Quy tắc chung (cả 2 modes):**
- Respect `.claude/instructions.md` và project conventions
- **⚡ Hot Reload First:** Nếu app hỗ trợ (Next.js, Vite...) → ưu tiên dev server + hot reload

### Step 5.10: Browser Verification (nếu có tool)

**Cho frontend/fullstack tasks.** Skip: backend-only, Quick tasks, hotfix, hoặc không có browser tool.

```bash
# PinchTab (nếu có)
command -v pinchtab &>/dev/null && {
  pgrep -f "pinchtab" || (pinchtab &>/tmp/pinchtab.log &); sleep 3
  pinchtab nav http://localhost:<port>/<path>
  pinchtab snap -i -c && pinchtab text
}
# Không có PinchTab → curl smoke test hoặc skip, note trong verification report
```

⚠️ UI không đúng → FIX trước, KHÔNG tiếp Step 6.

### Step 6: Verification Pipeline

**BẮT BUỘC trước khi tạo PR.** Chi tiết tại [references/verification-pipeline.md](references/verification-pipeline.md).

| Mode | Steps | Khi nào |
|------|-------|---------|
| **Full** | Build → Types → Lint → Tests → Security → **Self-Review** → Diff → Criteria → Report | Medium/Large tasks |
| **Full + Smoke** | Full + Smoke Test (API, DB, cross-service) | Multi-service / API tasks |
| **Lite** | Build → **Self-Review** → Diff → Criteria → Report | Quick tasks, hotfix |

#### Self-Review (Hard Rule #7 — BẮT BUỘC mọi task)

Sau build pass, TRƯỚC khi declare done:

1. **Scope drift** — `git diff $DEFAULT_BRANCH --name-only` vs Step 2-3 plan. File ngoài scope → revert hoặc justify
2. **Read diff** — `git diff --stat` + `git diff`, hiểu mọi thay đổi
3. **Acceptance criteria** — check từng cái ✅/❌ từ Step 1
4. **Verify logic** — trace data flow: "Input X → qua code → output đúng Y?" Không trace được → ❌
5. **Edge cases** — null/empty/error states xử lý chưa?
6. **Side effects** — có phá gì ngoài ý muốn?

⚠️ Build pass ≠ done. FAIL → fix → chạy lại pipeline. **KHÔNG tạo PR khi còn FAIL.**

### Step 7: Dev Preview (Optional)

**Trigger:** User yêu cầu xem trước. **Skip** nếu task nhỏ, backend-only, hoặc không có tunnel tool.

Nếu có `cloudflared` → [references/dev-preview.md](references/dev-preview.md). Không có → chạy dev server, báo user localhost URL.

### Step 8: Commit & PR

```bash
cd "$WORKDIR" && source <skill_dir>/scripts/detect-env.sh
git diff $DEFAULT_BRANCH --name-only | grep -q "package.json" && $PM install
git add -A

# Squash multiple commits into 1 conventional commit
AHEAD=$(git rev-list --count $DEFAULT_BRANCH..HEAD 2>/dev/null || echo 0)
[ "$AHEAD" -gt 1 ] && git reset --soft $DEFAULT_BRANCH
git diff --cached --quiet || git commit -m "<type>(<scope>): <description>"
git push origin <branch-name>
```

**PR:** `gh pr create` nếu có `gh`. Không có → báo user branch name + diff để tạo PR manual.
**Quick tasks:** commit thẳng vào branch nếu user cho phép, skip PR.

### Step 8b: Release Lock & PR Review Feedback

**Release (BẮT BUỘC sau PR created):**
```bash
bash <skill_dir>/scripts/worktree.sh release "$REPO_ROOT" "$BRANCH_NAME"
bash <skill_dir>/scripts/worktree.sh cleanup "$REPO_ROOT"  # optional, periodic
rm -f /tmp/openclaw-workdir-$$.txt
```
⚠️ Không cleanup worktree khi PR chưa merged — reviewer có thể request changes.

**PR Review Feedback:** Re-acquire → fix (Claude CLI) → verify (Step 6) → push → release.
```bash
WORKDIR=$(bash <skill_dir>/scripts/worktree.sh acquire "$REPO_ROOT" "$BRANCH_NAME")
cd "$WORKDIR"
# Fix → verify → commit → push → release
```

### Step 9: Post-Merge Deploy (Optional)

**Trigger:** User nói "deploy", "lên prod", hoặc PR merged + project có deploy flow.
**Skip:** User chưa yêu cầu, hoặc project là library/package.

| Type | Command |
|------|---------|
| CF Workers | `npx wrangler deploy` |
| Docker | `docker compose up -d --build` ([references/docker-rules.md](references/docker-rules.md)) |
| Multi-service | Dependency order ([references/multi-service-deploy.md](references/multi-service-deploy.md)) |
| CF Pages | Auto-deploy on push |

⚠️ Confirm user trước khi deploy prod (Reversibility 🟡/🔴).
💡 Deploy method: check `MEMORY.md`, project README, hoặc hỏi user → ghi annotation.

### Conventional Commits (BẮT BUỘC)

Chi tiết tại [references/conventions.md](references/conventions.md). Format: `<type>(<scope>): <description>` — types: feat, fix, docs, style, refactor, perf, test, chore.

## Lessons Learned (Recent)

Full history: [references/lessons-learned.md](references/lessons-learned.md)

| # | Lesson |
|---|--------|
| 1 | **Scout trước Plan** — đọc code thật trước khi đề xuất. Đoán mò = sai approach |
| 2 | **Scope drift** — self-review PHẢI check `git diff --name-only` vs plan. File ngoài scope → revert |
| 3 | **Chunk tasks** — 1 prompt lớn chạy 10 phút = user chờ mù. Chia ~1-2 phút, report sau mỗi cái |
| 4 | **Build pass ≠ done** — PHẢI self-review logic + trace data flow + check edge cases |
| 5 | **Tool check first** — `command -v` trước khi dùng. Crash vì thiếu tool = bug dễ tránh |

## References & Tools

**References** (đọc khi task match): [references/README.md](references/README.md)
Key: [coding-rules.md](references/coding-rules.md) (mọi task) | [claude-cli-guide.md](references/claude-cli-guide.md) | [verification-pipeline.md](references/verification-pipeline.md) | [conventions.md](references/conventions.md)

**Tools:** `git` (bắt buộc) | `claude` CLI (recommended, Mode B nếu không có) | `gh`, `cloudflared`, `pinchtab`, `gitnexus` (optional — skill tự detect + fallback)
