---
name: am-developer-skill
version: 2.0.0
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

**reads:** source code, git history, configs | **writes:** source files, branches, lock files, CLI logs, annotations
**external:** GitHub (`gh`), Claude Code CLI, GitNexus, Cloudflare tunnel | **destructive:** `git reset --soft`, `git stash`, branch delete
**requires_confirmation:** irreversible actions (DB prod, delete data, deploy prod)

## ⛔ Hard Rules (NEVER VIOLATE)

| # | Rule | Key Point |
|---|------|-----------|
| 1 | **NEVER self-code** | Agent = orchestrator. Mọi code → Claude CLI (Step 5). Exception: edit < 3 dòng trivial |
| 2 | **MUST report failures** | 3 attempts fail → BÁO USER NGAY: lỗi gì, retry mấy lần, đề xuất hướng xử lý |
| 3 | **MUST monitor spawns** | Poll 30-60s. Spawn rồi quên = BUG |
| 4 | **MUST update progress** | Spawn → báo ETA. Done → báo kết quả. **Im lặng > 2 phút = BUG** |
| 5 | **MUST chunk tasks** | Mỗi spawn ~1-2 phút. Task lớn → chia subtasks. KHÔNG gom 1 prompt khổng lồ |
| 6 | **MUST challenge ambiguity** | Thiếu info hoặc risk chưa acknowledge → HỎI TRƯỚC, không tự đoán |
| 7 | **MUST verify, don't assume** | Medium+ → discuss approach trước (1b). Done → self-review (Step 6). Build pass ≠ done |

**#6 vs #7:** #6 = "thiếu info → hỏi", #7 = "có info → đừng skip process". Không chắc Quick/Medium → default Medium.

## When to Use

✅ Mọi task cần code qua Claude CLI: feature, bug fix, refactor, test, review, deploy config
❌ Skip: edit < 3 dòng trivial (`edit` tool), chỉ đọc code (`read`), ACP requests (`sessions_spawn`)

### Task Size → Workflow

⚠️ **Khi không chắc Quick hay Medium → LUÔN coi là Medium (Hard Rule #7).**
Quick chỉ áp dụng khi **TẤT CẢ** điều kiện thỏa: ≤3 files, isolated (không cross-module), không side effects, không thay đổi logic/behavior.

| Task size | Ví dụ | Scout (1a) | GitNexus (0c) | Workflow |
|-----------|-------|------------|---------------|----------|
| **Quick** (1-3 files, isolated) | Fix typo, update text, change color | Gọn (locate only) | Skip | Step 1 gọn → Skip 2-3 → Step 4 → 5 → 6 lite → 8. PR optional |
| **Medium** (3-10 files, logic change) | Bug fix, refactor module, new endpoint | **Full 5 bước** | Recommended | Full workflow (1a → 1 → 1b → 3 → 4 → 5 → 6 → 8) |
| **Large** (>10 files, cross-module) | New feature, migration | **Full 5 bước** | **Bắt buộc** | Full workflow bắt buộc |
| **Hotfix** (production emergency) | Critical bug in prod | Quick (reproduce + locate) | Optional | Skip 1b + 2-3 → Branch from tag → 5 → 6 lite → push |
| **Greenfield** (code mới 100%) | New project, new module from scratch | **Skip** | Optional | Skip 1a → 1 → 1b → 3 → 4 → 5 → 6 → 8 |

## Workflow Cheat Sheet

```
Quick:      [1a gọn] → 1 (gọn) ────────────→ 4 → 5 → 6 lite → 8 → 8b
Medium:     1a → 1+1b → 2-3 (plan) ──────→ 4 → 5 → [5.10] → 6 full → [7] → 8 → 8b → [9]
Large:      1a → 1+1b → 2-3 (plan+issue) → 4 → 5 → [5.10] → 6 full → [7] → 8 → 8b → [9]
Hotfix:     1a (quick) → 1 (gọn) ──────────→ 4 (from tag) → 5 → 6 lite → push → 8b → 9
Greenfield: Skip 1a → 1+1b → 2-3 → 4 → 5 → [5.10] → 6 → 8 → 8b

[brackets] = optional/trigger-based
```

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

Nếu không match → tiếp tục Step 1a (Scout) bên dưới.

### Step 0b: CLI Retrospect (Error Tracking)

**Trigger:** "retrospect", "hồi tưởng", "review cli errors", "xem lỗi cli", "cli report"

```bash
python3 <skill_dir>/scripts/retrospect.py [--days 7] [--project <name>] [--all] [--trim-only]
```
Output: success/fail rates, error patterns, improvement suggestions. Review → update lessons learned.

### Step 0c: GitNexus Code Intelligence

**Dùng trong Step 1a (Scout) bước 2+4** — nếu repo đã index. Không cần step riêng.

```bash
command -v gitnexus >/dev/null 2>&1 || { echo "Skip — not installed"; }
BRIDGE="<skill_dir>/scripts/git-nexus-mcp-bridge.js"
node $BRIDGE query '{"query":"<search>"}' --repo <name>    # Scout bước 2: Locate
node $BRIDGE impact '{"target":"<function>"}' --repo <name> # Scout bước 4: Blast Radius
```

Chi tiết: [references/gitnexus-setup.md](references/gitnexus-setup.md)

### Step 1a: Scout — Investigate Before You Plan

**BẮT BUỘC cho bug fixes và tasks cần hiểu existing code.** Skip cho: greenfield features (code mới hoàn toàn), docs, config changes.

**Mục đích:** Hiểu root cause từ CODE THẬT trước khi đề xuất solution. Không đoán.

**5 bước scout:**

1. **Reproduce** — Verify bug có thật không, điều kiện trigger
   ```bash
   # Chạy app, test endpoint, check logs
   curl -s http://localhost:3000/api/... | jq .
   # Hoặc browser: pinchtab nav → reproduce steps → screenshot
   ```

2. **Locate** — Tìm code liên quan
   ```bash
   # Grep keywords từ error message / feature name
   cd "$WORKDIR"
   grep -rn "functionName\|errorMessage\|routePath" src/ --include="*.ts" --include="*.tsx" | head -20
   # Git log: ai sửa gần nhất, commit nào introduce bug
   git log --oneline -10 -- src/path/to/suspected/file.ts
   # GitNexus (nếu có): query + impact
   ```

3. **Root Cause** — Đọc code, trace data flow
   ```bash
   # Đọc file suspect → trace từ entry point → tìm chỗ logic sai
   # Ghi rõ: "Bug ở file X, dòng Y, vì Z"
   ```

4. **Blast Radius** — Fix chỗ này ảnh hưởng gì
   ```bash
   # Ai gọi function/component này?
   grep -rn "importedFunction\|<Component" src/ --include="*.ts" --include="*.tsx" | head -20
   # GitNexus impact (nếu có)
   ```

5. **Evidence** — Thu thập proof
   - Error log / stack trace
   - Screenshot reproduce
   - Test case trigger bug
   - Commit introduce bug (nếu regression)

**Output scout** (trình bày cho user ở Step 1):
```
🔍 Scout findings:
- Reproduce: [có/không reproduce, điều kiện]
- Location: [file:line]
- Root cause: [mô tả cụ thể]
- Blast radius: [N callers, M components affected]
- Evidence: [log snippet / screenshot / commit hash]
```

**Quick tasks:** Scout gọn — chỉ cần locate + đọc nhanh, 1-2 phút. Không cần full 5 bước.

**⚠️ Scout ≠ Fix.** Scout chỉ đọc + trace. KHÔNG sửa code ở bước này.

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

### Step 1b: Solution Discussion (BẮT BUỘC cho Medium/Large — Hard Rule #7)

**Mục đích:** Đề xuất solution dựa trên **evidence từ scout** (Step 1a), không phải giả định.

Trình bày cho user **trong cùng 1 message** với Step 1 analysis + scout findings:

1. **2-3 Solution Approaches** — mỗi cái nêu rõ:
   - Mô tả ngắn (1-2 dòng)
   - Pros / Cons
   - Complexity estimate (low/medium/high)
   - Risk level

2. **Recommendation** — em đề xuất approach nào + lý do

3. **Chờ user chọn** — KHÔNG tự quyết. User có thể chọn, modify, hoặc đề xuất approach khác.

**Skip khi:**
- Quick tasks (thật sự trivial — xem bảng Task Size)
- Hotfix (thời gian critical)
- Task có 1 approach duy nhất hiển nhiên (ví dụ: "update text X thành Y")

> Sau khi user approve approach → tiến sang Step 3 (plan subtasks chi tiết — KHÔNG hỏi approval lần 2).

💡 **Medium tasks với approach rõ ràng:** Gộp Step 1 + 1b thành 1 message: analysis + 1 recommended approach + "nếu OK em chạy luôn". Vẫn chờ user approve, nhưng gọn hơn.

### Step 2-3: Planning & Issue Tracking

**Approval đã có ở Step 1b.** Bước này detail subtasks từ approach đã chọn.

Chia subtasks **nhỏ, ~1-2 phút CLI time mỗi cái.** Dùng scout findings (files, blast radius) cho accuracy:

```
Subtask N: <tên>
  Goal: <1 dòng>
  Files: <từ scout Step 1a>
  ETA: ~1-2 phút
  Verify: <build/test/UI>
```

Check project conventions: `cat $WORKDIR/.claude/instructions.md 2>/dev/null`

Nếu approach cần thay đổi đáng kể → quay lại hỏi user.

**GitHub Issue (Large tasks only):**
```bash
REPO=$(git remote get-url origin | sed 's|.*github.com[:/]||;s|\.git$||')
ISSUE_URL=$(gh issue create --repo "$REPO" --title "<task>" --body "<criteria>" --assignee @me)
```

💡 Quick tasks: skip issue + gộp Step 1-3 thành 1 message ngắn.

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

### Step 5: Code with Claude CLI

**Chi tiết đầy đủ:** [references/claude-cli-guide.md](references/claude-cli-guide.md) — spawn, prompt strategy, timeout/retry, parse result, environment, monitoring, logging, annotations.

**⚡ Hot Reload First:** Nếu application hỗ trợ hot reload (Next.js, Expo, Vite...), luôn ưu tiên dev server + hot reload.

**Quy tắc cốt lõi:**
- Claude CLI **chỉ edit files, KHÔNG commit** — git managed ở Step 8
- Respect `.claude/instructions.md` và project conventions
- Mỗi subtask ~1-2 phút (Hard Rule #5). Task lớn → chia subtasks trước khi spawn
- **Inject vào prompt** (theo thứ tự):
  1. **Scout findings** (Step 1a) — root cause, file:line, blast radius → Claude Code biết chính xác chỗ cần fix
  2. **Coding rules** ([references/coding-rules.md](references/coding-rules.md)) — 10 defensive programming rules
  3. **Annotations** (nếu có) — project-specific gotchas
  4. Cuối prompt: `"DO NOT git commit or push."`

**Quick spawn:**
```bash
bash <skill_dir>/scripts/spawn.sh <WORKDIR> <MODEL> "YOUR PROMPT"
# Resume: bash <skill_dir>/scripts/spawn.sh <WORKDIR> <MODEL> "continue..." <SESSION_UUID>
# Custom timeout (default 180s): bash <skill_dir>/scripts/spawn.sh <WORKDIR> <MODEL> "PROMPT" "" 120
```
⏱️ **Timeout:** Default 180s. Exit code 124 = timed out → chia subtask nhỏ hơn (Hard Rule #5).

**Sau mỗi spawn — BẮT BUỘC:**
1. Parse result → check `is_error` → retry nếu fail (max 3, mỗi lần khác strategy)
2. Log CLI run (`scripts/log-cli-run.sh`)
3. Report kết quả cho user
4. Capture learnings (`scripts/annotate.sh`) nếu có retry/discoveries

📖 **Đọc full reference** khi cần: retry strategy chi tiết, env setup, session resume, prompt injection checklist (annotations, GitNexus, unit testing rules).

### Step 5.10: Browser Verification (PinchTab)

**BẮT BUỘC cho frontend/fullstack tasks.** Skip: backend-only, trivial Quick tasks, hotfix.

```bash
pgrep -f "pinchtab" || (pinchtab &>/tmp/pinchtab.log &); sleep 3
pinchtab nav http://localhost:<port>/<path>
pinchtab snap -i -c && pinchtab text
pinchtab screenshot -o /tmp/verify-<feature>.png  # evidence cho PR
```

⚠️ UI không đúng → FIX trước (gọi lại Claude CLI), KHÔNG tiếp Step 6.
Chi tiết: [references/browser-verify.md](references/browser-verify.md)

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

### Step 7: Dev Preview (Cloudflare Tunnel)

**Trigger:** User nói "test thử", "cho anh xem", "manual test", "review UI", hoặc yêu cầu link preview.
**Bỏ qua** nếu task nhỏ, backend-only, hoặc user mở localhost trực tiếp được.

Chi tiết tại `references/dev-preview.md`. Flow: start dev server → wait ready → start tunnel → gửi link → giữ alive → cleanup khi user xong.

### Step 8: Create Pull Request & Cleanup Worktree

```bash
# Dùng WORKDIR từ Step 4
WORKDIR=$(cat /tmp/openclaw-workdir-$$.txt 2>/dev/null || echo ~/projects/<repo>)
cd "$WORKDIR"
source <skill_dir>/scripts/detect-env.sh

# Sync deps nếu package.json changed
git diff $DEFAULT_BRANCH --name-only | grep -q "package.json" && $PM install

# Stage + squash into 1 conventional commit
git add -A
AHEAD=$(git rev-list --count $DEFAULT_BRANCH..HEAD 2>/dev/null || echo 0)
if [ "$AHEAD" -gt 1 ]; then
  git reset --soft $DEFAULT_BRANCH
  git commit -m "<type>(<scope>): <description>"
elif [ "$AHEAD" -eq 1 ]; then
  git commit --amend -m "<type>(<scope>): <description>" 2>/dev/null || true
else
  git diff --cached --quiet || git commit -m "<type>(<scope>): <description>"
fi
git push origin <branch-name>

# Quick tasks: commit-only path (skip PR nếu user cho phép)
# Standard path: tạo PR
REPO=$(git remote get-url origin | sed 's|.*github.com[:/]||;s|\.git$||')
gh pr create --repo "$REPO" \
  --title "<type>(<scope>): <description>" --assignee @me \
  --body "## Changes\n- ...\n\n## Verification Report\n<Step 6.8>\n\nCloses #<N>" \
  --base $DEFAULT_BRANCH
```

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

Full history: [references/lessons-learned.md](references/lessons-learned.md) (16 entries)

| # | Lesson | Date |
|---|--------|------|
| 14 | **spawn.sh cần timeout** — default 180s, exit 124 = timed out. Chia task nhỏ hơn, không tăng timeout | 2026-03-25 |
| 15 | **Scope drift = silent bug** — Claude CLI sửa file ngoài scope. Self-review check `git diff --name-only` vs plan | 2026-03-25 |
| 16 | **Deploy = separate step** — Step 9 detect + chạy deploy method. Confirm user trước prod | 2026-03-25 |
| 17 | **Scout trước Plan** — discuss approach chưa đọc code = đoán mò. Step 1a bắt buộc: reproduce → locate → root cause → blast radius → evidence. Solution dựa trên code thật | 2026-03-25 |

## Domain References

**Đọc khi task match, KHÔNG load mặc định.** Full index: [references/README.md](references/README.md)

Key references (đọc thường xuyên nhất):
- **Coding Rules** → [references/coding-rules.md](references/coding-rules.md) — inject vào MỌI Claude CLI prompt
- **Claude CLI Guide** → [references/claude-cli-guide.md](references/claude-cli-guide.md) — retry, env, session resume
- **Verification Pipeline** → [references/verification-pipeline.md](references/verification-pipeline.md) — Step 6 detail
- **Docker Rules** → [references/docker-rules.md](references/docker-rules.md) — deploy, compose, container

## Quick Reference

Conventions, conflict resolution, module system → [references/conventions.md](references/conventions.md)

## Tools Required

- `claude` CLI (v2.1.63+) — coding agent (xem setup tại Step 5.6)
- `gh` CLI — GitHub operations
- `cloudflared` — dev preview tunnels
- `git` — version control
- `typescript-language-server`, `pyright` — LSP servers cho code navigation (recommended)
- `gitnexus` — code intelligence engine, MCP tools cho codebase awareness (recommended, xem `references/gitnexus-setup.md`)
