# Self-Improve — Developer Skill Learning Loop

Skill học từ thực tế: đọc data → tìm pattern → **thảo luận với user** → cải thiện skill khi được đồng ý.

## Core Principle

Skill này không cải tiến **code** — nó cải tiến **skill workflow**.
**Không tự apply bất kỳ thứ gì** — mọi thay đổi đều phải qua thảo luận và được user đồng ý.

```
[User yêu cầu]  ←── CHỈ bắt đầu khi được kích hoạt thủ công
      │
      ▼
[SCAN] — Thu thập signals từ dev history
      │
      ▼
[ANALYZE] — Tìm patterns + calibrate thresholds
      │
      ▼
[DISCUSS] — Trình bày findings, thảo luận
      │              │
      │         User quyết định:
      │         • Đồng ý → apply
      │         • Điều chỉnh → apply version đã chỉnh
      │         • Không đồng ý → discard, ghi lý do
      │         • Cần thêm data → defer
      ▼
[APPLY] — Chỉ apply những gì đã confirm
      │
      ▼
[PUSH] — Push updated skill → GitHub
```

**Nguyên tắc:**
- ⛔ KHÔNG tự kích hoạt
- ⛔ KHÔNG tự apply bất kỳ thay đổi nào
- ✅ Mọi proposal dựa trên data thực, có evidence
- ✅ Không xóa rule cũ — chỉ update hoặc thêm mới
- ✅ Mọi thay đổi ghi vào Lessons Learned + bump version

---

## Phase 1: SCAN — Thu Thập Signals

### Data Sources

```bash
# 1. Git history — PRs, commits, patterns
REPOS_DIR=~/projects
for repo in "$REPOS_DIR"/*/; do
  [ -d "$repo/.git" ] || continue
  echo "=== $(basename $repo) ==="
  # Recent PRs
  REPO_REMOTE=$(git -C "$repo" remote get-url origin 2>/dev/null | sed 's|.*github.com[:/]||;s|\.git$||')
  [ -n "$REPO_REMOTE" ] && gh pr list --repo "$REPO_REMOTE" --state merged --limit 20 --json number,title,createdAt,mergedAt
done

# 2. Claude CLI spawn history (nếu có logs)
find /tmp -name ".claude-done-*" -mtime -30 2>/dev/null
ls -la /tmp/claude-*.log 2>/dev/null

# 3. Memory files — dev-related entries
grep -l "developer\|coding\|Claude CLI\|spawn\|retry\|build\|PR" ~/. openclaw/workspace/memory/*.md 2>/dev/null

# 4. Skill's own Lessons Learned section
grep -A 50 "## Lessons Learned" <skill_dir>/SKILL.md
```

### Signals to Extract

**Workflow Signals (steps that work/fail)**
```
- Which steps get skipped most often? (Step 2, Step 3?)
- Verification pipeline — which checks catch real issues?
- PR review feedback patterns — same type of feedback recurring?
- Time from task start → PR merge — bottlenecks where?
```

**Claude CLI Signals (spawn effectiveness)**
```
- Retry rate — how often does attempt 1 fail?
- Common failure modes — timeout? token limit? wrong approach?
- Which prompt strategies work best?
- Model usage — sonnet vs opus, when does escalation help?
- Task size estimation accuracy — do timeouts match reality?
```

**Threshold Signals (defaults đúng hay sai)**
```
- Timeout defaults: Quick=120s, Medium=300s, Large=600s — đủ không?
- "Quick task" definition: 1-3 files — threshold hợp lý?
- Retry max 3 — có case nào cần nhiều hơn?
- Poll interval 30-60s — quá nhanh? quá chậm?
- "Im lặng > 3 phút = BUG" — realistic không?
```

**Gap Signals (cases chưa cover)**
```
- Loại task nào agent phải "tự nghĩ" vì skill không hướng dẫn?
- Error handling nào thiếu?
- Reference nào cần mà chưa có?
- Convention nào lặp lại mà chưa document?
```

---

## Phase 2: ANALYZE — Tìm Patterns

**Chỉ conclude khi có evidence từ ≥2 projects hoặc ≥3 data points.**

### Pattern Validation

```
Signal: "Claude CLI timeout 120s quá ngắn cho TypeScript projects"
Evidence:
  - Project A: 3/5 quick tasks timeout ở 120s, pass ở 180s
  - Project B: 2/3 quick tasks timeout ở 120s
  - Project C: 0/4 timeout (all <90s, nhưng project nhỏ)

Conclusion: CONFIRMED cho medium+ TypeScript projects
Confidence: Medium (2/3 projects)
Action: Đề xuất tăng Quick timeout → 180s cho TS projects
```

### Threshold Calibration

```markdown
| Threshold | Current | Observed | Suggestion |
|---|---|---|---|
| Quick timeout | 120s | 60% timeout cho TS | → 180s |
| Task split trigger | >10 files | Agent thường split ở 7-8 | → >8 files |
| Poll interval | 30-60s | 30s tốn tokens | → 45-90s |
```

### Gap Prioritization

```markdown
| Gap | Impact (1-5) | Frequency | Ease to Fix | Priority |
|---|---|---|---|---|
| Monorepo handling | 4 | 3 projects | Medium | 🔴 High |
| Docker compose dev | 3 | 2 projects | Easy | 🟡 Medium |
| DB migration rollback | 2 | 1 project | Hard | 🟢 Low |
```

---

## Phase 3: DISCUSS — Thảo Luận

**Bước quan trọng nhất. Không skip.**

### Present Findings — Retro Dashboard (gstack /retro inspired)

Mỗi lần self-improve, generate retro dashboard TRƯỚC findings:

```
📊 Developer Skill Retro — {date range}

### Shipping Stats
| Project | PRs | Commits | +Lines | -Lines | Median PR Time |
|---------|-----|---------|--------|--------|----------------|
| {repo}  | {n} | {n}     | {n}    | {n}    | {n} min        |

### Test Health
| Project | Tests Before | Tests After | Coverage Δ |
|---------|-------------|-------------|------------|
| {repo}  | {n}         | {n}         | {+/-n%}    |

### CLI Health (from retrospect.py)
| Total Runs | Success | Fail | Avg Duration | Top Errors |
|-----------|---------|------|-------------|------------|
| {n}       | {n}     | {n}  | {n}s        | {list}     |

### 🔥 Shipping Streak: {N} consecutive days with merged PR
```

**Data collection:**
```bash
# Shipping stats — iterate all repos
for repo in ~/projects/*/; do
  [ -d "$repo/.git" ] || continue
  REMOTE=$(git -C "$repo" remote get-url origin 2>/dev/null | sed 's|.*github.com[:/]||;s|\.git$||')
  [ -z "$REMOTE" ] && continue
  echo "=== $(basename $repo) ==="
  gh pr list --repo "$REMOTE" --state merged --limit 50 --json number,additions,deletions,createdAt,mergedAt
  git -C "$repo" log --oneline --since="7 days ago" | wc -l
done

# Test health — check test count changes
git diff main --stat -- "*.test.*" "*.spec.*"

# CLI health — from retrospect.py
python3 <skill_dir>/scripts/retrospect.py --days 7 --all --json 2>/dev/null
```

**Trend tracking:** Save retro output to `memory/retro-{YYYY-MM-DD}.md`. Future retros compare week-over-week.

Sau dashboard, present findings:

```
📊 Skill Analysis

✅ Confirmed working (nên hardcode):
1. {finding + evidence}
2. ...

⚠️ Thresholds cần calibrate:
1. {metric}: skill nói {X}, thực tế {Y} — đề xuất {Z}
2. ...

🕳️ Gaps phát hiện:
1. {gap} — xảy ra {N lần} ở {project(s)}
2. ...

💡 Reference mới đề xuất:
1. {tên} — evidence: {data}

Anh muốn đi qua từng item?
```

### Per-item Decision

Mỗi item, user quyết định:
- ✅ Đồng ý → apply
- ✏️ Điều chỉnh → apply version đã chỉnh
- ⏸️ Cần thêm data → defer
- ❌ Không đồng ý → discard, ghi lý do

---

## Phase 4: APPLY — Update Skill Files

**Chỉ sau khi user confirm.**

### Rules

1. Dùng `edit` tool — **KHÔNG dùng `write`** trên existing files
2. `read` file trước → xác định đoạn cần sửa → `edit` chính xác
3. Update version trong frontmatter (patch/minor/major tùy scope)
4. Update Lessons Learned table trong SKILL.md
5. Báo user mỗi change: "✅ Applied: {description}"

### Version Bump Guide

- **Patch** (1.0.0 → 1.0.1): threshold tweak, minor wording
- **Minor** (1.0.0 → 1.1.0): new reference, new step, new pattern
- **Major** (1.0.0 → 2.0.0): flow restructure, breaking change

---

## Phase 5: PUSH — GitHub Sync

Push updated skill to the skills repo. Commit message:

```
feat(self-improve): developer skill update from {YYYY-MM} data

- {N} proposals applied
- Files updated: {list}
- See Lessons Learned table for details
```

---

## What Can Be Improved

| Area | Examples |
|---|---|
| Timeouts | Quick/Medium/Large defaults |
| Retry strategy | Max attempts, escalation triggers |
| Task sizing | File count thresholds, split triggers |
| Prompt strategy | Template improvements, 2-phase patterns |
| Verification pipeline | Which checks to add/remove/reorder |
| References | New reference files, update existing |
| Conventions | New patterns discovered across projects |
| Hard Rules | Clarify edge cases (not relax rules) |

## What CANNOT Be Improved

- Hard Rules — chỉ clarify, KHÔNG relax
- Security practices — KHÔNG loosen
- `edit` > `write` rule — bất di bất dịch
- User approval gates — KHÔNG bypass
