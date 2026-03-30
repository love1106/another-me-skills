---
name: am-developer-skill
version: 2.10.3
author: khoidoan
description: >
  Developer workflow for ALL coding tasks. Handles: init project, security review, self-improve,
  Claude Code CLI with retry, planning, GitHub tracking, branching, verification, PR creation.
  CLI error tracking with auto-log and retrospect analysis.
  Use when: init project, security audit, build feature, fix bug, refactor, code review, generate tests,
  write unit tests, TDD, viết tests, deploy config, self-improve dev skill, retrospect, hồi tưởng,
  review cli errors, xem lỗi cli, cli report, error report, analyze cli runs, phân tích lỗi,
  code intelligence, index codebase, analyze architecture, blast radius,
  code health, tech debt, audit codebase, tình hình code, what needs fixing.
  NOT for: reading code (use read), edits under 3 lines (use edit), ACP requests (use sessions_spawn).
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
| **Medium** (3-10 files, logic change) | full 5 bước | `1a → 1+1b → 2-3 → 4 → 5 → [5.10] → 6 full → 8 → 8b` |
| **Large** (>10 files, cross-module) | full 5 bước | `1a → 1+1b → 2-3+issue → 4 → 5 → [5.10] → 6 full → 8 → 8b → [9]` |
| **Hotfix** (prod emergency) | reproduce+locate | `1a → 1 → 4(tag) → 5 → 6 lite → push → 8b → 9` |
| **Greenfield** (100% new) | skip | `1+1b → 2-3 → 4 → 5 → [5.10] → 6 → 8 → 8b` |

`[brackets]` = optional. Mọi flow kết thúc bằng Step 8b (release lock).

## Workflow Cheat Sheet

```
⚠️ LUÔN check Step 0 trước — nếu match special task → đi theo reference riêng.

Quick:      [1a gọn] → 1 (gọn) ────────────→ 4 → 5 → 6 lite → 8 → 8b
Medium:     1a → 1+1b → 2-3 (plan) ──────→ 4 → 5 → [5.10] → 6 full → [7] → 8 → 8b → [9]
Large:      1a → 1+1b → 2-3 (plan+issue) → 4 → 5 → [5.10] → 6 full → [7] → 8 → 8b → [9]
Hotfix:     1a (quick) → 1 (gọn) ──────────→ 4 (from tag) → 5 → 6 lite → push → 8b → 9
Greenfield: Skip 1a → 1+1b → 2-3 → 4 → 5 → [5.10] → 6 → 8 → 8b
```

## Workflow (follow strictly in order)

### Step 0: Route by Task Type

Một số task có workflow riêng — check trước khi vào workflow chính:

| Task | Reference | Ghi chú |
|------|-----------|---------|
| Init project mới từ template | `references/init-project.md` | Xong → quay lại workflow này cho dev tiếp |
| Viết unit tests / TDD | `references/unit-testing.md` | TDD flow, spec-first, gap discovery |
| Security review / audit code | `references/security-review.md` | Script: `scripts/security-review.sh` |
| Code health / tech debt audit | `references/code-health.md` | Scan → report → tạo issues (user confirm) |
| Self-improve / tự đánh giá skill | `references/self-improve.md` | Chỉ khi user yêu cầu, KHÔNG tự trigger |
| Retrospect / review CLI errors | `scripts/retrospect.py` | Xem bên dưới: Step 0b |

Nếu không match → resolve project rồi tiếp Step 1a.

**Resolve project (trước Step 1a):**
1. Check conversation context — user đề cập repo/project nào?
2. Check cwd: `git remote get-url origin 2>/dev/null`
3. Nếu vẫn unclear → hỏi: "Task này cho project nào?"
4. `cd ~/projects/<repo>` trước khi bắt đầu Scout.

### Step 0b: CLI Retrospect (Error Tracking)

**Trigger:** "retrospect", "hồi tưởng", "review cli errors", "xem lỗi cli", "cli report"

```bash
python3 <skill_dir>/scripts/retrospect.py [--days 7] [--project <name>] [--all] [--trim-only]
```
Output: success/fail rates, error patterns, improvement suggestions. Review → update lessons learned.

### Step 0c: GitNexus Code Intelligence (Optional)

**Dùng trong Step 1a (Scout) bước 2+4** — nếu repo đã index và tool available.

```bash
command -v gitnexus >/dev/null 2>&1 || { echo "Skip — not installed"; }
BRIDGE="<skill_dir>/scripts/git-nexus-mcp-bridge.js"
node $BRIDGE query '{"query":"<search>"}' --repo <name>    # Scout bước 2: Locate
node $BRIDGE impact '{"target":"<function>"}' --repo <name> # Scout bước 4: Blast Radius
```

Chi tiết: [references/gitnexus-setup.md](references/gitnexus-setup.md)

### Pre-flight Check (chạy 1 lần đầu session, skip nếu đã check)

```bash
command -v git >/dev/null 2>&1 || echo "❌ git not found"
command -v gh >/dev/null 2>&1 || echo "⚠️ gh not found — PR creation sẽ fail"
command -v claude >/dev/null 2>&1 || echo "⚠️ claude CLI not found — Step 5 sẽ dùng Mode B (self-code)"
```

Nếu `git` missing → BLOCKED. Nếu `gh` hoặc `claude` missing → warn, tiếp nếu task không cần.

### Step 1a: Scout — Investigate Before You Plan

**BẮT BUỘC cho bug fixes và tasks cần hiểu existing code.** Skip cho: greenfield features (code mới hoàn toàn), docs, config changes.

**Mục đích:** Hiểu root cause từ CODE THẬT trước khi đề xuất solution. Không đoán.

**5 bước scout:**

1. **Reproduce** — Verify bug có thật không, điều kiện trigger
   ```bash
   curl -s http://localhost:3000/api/... | jq .
   ```

2. **Locate** — Tìm code liên quan
   ```bash
   cd "$WORKDIR"
   grep -rn "functionName\|errorMessage" src/ --include="*.ts" --include="*.tsx" | head -20
   git log --oneline -10 -- src/path/to/suspected/file.ts
   ```

3. **Root Cause** — Đọc code, trace data flow. Ghi: "Bug ở file X, dòng Y, vì Z"

4. **Blast Radius** — Fix chỗ này ảnh hưởng gì
   ```bash
   grep -rn "importedFunction\|<Component" src/ --include="*.ts" --include="*.tsx" | head -20
   ```

5. **Evidence** — Log/stack trace, screenshot, commit hash (nếu regression)

**Output scout** (trình bày cho user ở Step 1):
```
🔍 Scout: Reproduce [✅/❌] | Location [file:line] | Root cause [mô tả] | Blast radius [N callers] | Evidence [proof]
```

**Quick tasks:** Scout gọn — chỉ locate + đọc nhanh. Không cần full 5 bước.

**⚠️ Scout ≠ Fix.** Scout chỉ đọc + trace. KHÔNG sửa code ở bước này.

**Iron Law:** Không có fix nào được phép trước khi có investigation. Document hypothesis TRƯỚC khi attempt fix:
```
Hypothesis: {mô tả nguyên nhân suspected}
Evidence: {data từ scout}
Fix approach: {plan cụ thể nếu hypothesis đúng}
```
Nếu 3 fix attempts thất bại → STOP, re-investigate (hypothesis sai?), escalate (dùng BLOCKED status).

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

# Install deps (stack-aware)
[ -f package.json ] && $PM install
[ -f requirements.txt ] && pip install -r requirements.txt 2>/dev/null
[ -f go.mod ] && go mod download 2>/dev/null
echo "$WORKDIR" > /tmp/openclaw-workdir-$$.txt  # save cho Step 5, 6, 8
```

**Hotfix:** `worktree.sh acquire` + reset to stable point:
```bash
TAG=$(git describe --tags --abbrev=0 2>/dev/null)
if [ -n "$TAG" ]; then
  git reset --hard "$TAG"
else
  git reset --hard "origin/$DEFAULT_BRANCH"
fi
```
Skip Step 2-3.
**Status:** `bash <skill_dir>/scripts/worktree.sh status ~/projects/<repo>`

### Step 5: Implement Code

**2 modes tuỳ môi trường:**

#### Mode A: Claude CLI available (`command -v claude &>/dev/null`)

Chi tiết: [references/claude-cli-guide.md](references/claude-cli-guide.md)

```bash
bash <skill_dir>/scripts/spawn.sh <WORKDIR> <MODEL> "YOUR PROMPT"
# Resume: bash <skill_dir>/scripts/spawn.sh <WORKDIR> <MODEL> "continue..." <SESSION_UUID>
# Custom timeout (default 240s): bash <skill_dir>/scripts/spawn.sh <WORKDIR> <MODEL> "PROMPT" "" 120
```
⏱️ **Timeout:** Default 240s. Exit code 124 = timed out → chia subtask nhỏ hơn (Hard Rule #5).

**Inject vào prompt** (theo thứ tự):
1. **Scout findings** (Step 1a) — root cause, file:line, blast radius
2. **Coding rules** ([references/coding-rules.md](references/coding-rules.md)) — 10 defensive programming rules
3. **Annotations** (nếu có) — project-specific gotchas
4. Cuối prompt: `"DO NOT git commit or push."`

Sau spawn: parse `is_error` → retry max 3 (mỗi lần khác strategy) → log (`scripts/log-cli-run.sh`) → report user.

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

**A. Structural Review (mọi task):**
1. **Scope drift** — `git diff $DEFAULT_BRANCH --name-only` vs Step 2-3 plan. File ngoài scope → revert hoặc justify
2. **Read diff** — `git diff --stat` + `git diff`, hiểu mọi thay đổi
3. **Acceptance criteria** — check từng cái ✅/❌ từ Step 1
4. **Verify logic** — trace data flow: "Input X → qua code → output đúng Y?" Không trace được → ❌
5. **Edge cases** — null/empty/error states xử lý chưa?
6. **Side effects** — có phá gì ngoài ý muốn?

**B. Safety Checklist (Medium+ tasks):**
```
- [ ] SQL: parameterized queries? migration có rollback?
- [ ] Auth: new endpoints có auth check? existing auth không bị bypass?
- [ ] Side effects: conditional logic khác nhau prod/dev? (env checks, feature flags)
- [ ] Error handling: new error paths có user-facing message? Không leak stack trace?
- [ ] Completeness: tất cả TODO/FIXME resolved? Không có stub/placeholder?
- [ ] Secrets: không hardcode API key, token, password trong code?
```
Quick tasks: skip Safety Checklist. Chỉ chạy Structural Review.

⚠️ Build pass ≠ done. FAIL → fix → chạy lại pipeline. **KHÔNG tạo PR khi còn FAIL.**

#### Completion Status Protocol (báo kết quả cho user)

Sau verification pipeline, report status bằng 1 trong 4 format:

| Status | Khi nào | Format |
|---|---|---|
| **DONE** | Mọi step pass, evidence đầy đủ | `✅ DONE: {mô tả} — PR: {link}` |
| **DONE_WITH_CONCERNS** | Pass nhưng có issues cần flag | `⚠️ DONE_WITH_CONCERNS: {mô tả} — Concerns: {list}` |
| **BLOCKED** | Không thể tiếp tục | `🚫 BLOCKED: {lý do} — Tried: {gì đã thử} — Need: {cần gì}` |
| **NEEDS_CONTEXT** | Thiếu info để tiếp | `❓ NEEDS_CONTEXT: {cần gì cụ thể}` |

**Rule:** Sau 3 retry thất bại (Hard Rule #2) → BẮT BUỘC dùng BLOCKED format.

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

### Conventional Commits (BẮT BUỘC)

Chi tiết tại [references/conventions.md](references/conventions.md). Format: `<type>(<scope>): <description>` — types: feat, fix, docs, style, refactor, perf, test, chore.

## Lessons Learned (Recent)

Full history: [references/lessons-learned.md](references/lessons-learned.md)

| # | Lesson | Date |
|---|--------|------|
| 14 | **spawn.sh cần timeout** — default 240s, exit 124 = timed out. Chia task nhỏ hơn, không tăng timeout | 2026-03-25 |
| 15 | **Scope drift = silent bug** — Claude CLI sửa file ngoài scope. Self-review check `git diff --name-only` vs plan | 2026-03-25 |
| 16 | **Deploy = separate step** — Step 9 detect + chạy deploy method. Confirm user trước prod | 2026-03-25 |
| 17 | **Scout trước Plan** — discuss approach chưa đọc code = đoán mò. Step 1a bắt buộc | 2026-03-25 |
| 18 | **Auto-log > Manual-log** — Hook vào spawn.sh exit trap. Manual log = luôn bị skip | 2026-03-29 |
| 19 | **Timeout 240s cho TS projects** — 180s quá ngắn cho TypeScript projects trung bình | 2026-03-29 |
| 20 | **Safety Checklist catches real bugs** — SQL injection, missing auth, env-conditional logic = top 3 issues | 2026-03-29 |
| 21 | **Completion Protocol > free-form** — DONE/BLOCKED/NEEDS_CONTEXT format giúp user scan nhanh | 2026-03-29 |

## References & Tools

**References** (đọc khi task match): [references/README.md](references/README.md)
Key: [coding-rules.md](references/coding-rules.md) (mọi task) | [claude-cli-guide.md](references/claude-cli-guide.md) | [verification-pipeline.md](references/verification-pipeline.md) | [conventions.md](references/conventions.md)

**Tools:** `git` (bắt buộc) | `claude` CLI (recommended, Mode B nếu không có) | `gh`, `cloudflared`, `pinchtab`, `gitnexus` (optional — skill tự detect + fallback)
