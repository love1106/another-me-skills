---
name: am-planner-code-task
version: 1.6.1
author: khoidoan
description: >
  Plan and break down CODING tasks — features, bug fixes, refactors, API changes,
  DB migrations, UI implementation. Analyzes codebase, clarifies requirements,
  defines acceptance criteria, test strategy, and implementation steps.
  Default output: GitHub issue (or markdown if gh unavailable). Supports Jira, Monday, Trello.
  Triggers: "tạo coding task", "plan task code", "lên task dev", "break down feature",
  "phân tích yêu cầu code", "create issue", "tạo issue", "plan feature implementation",
  "task planning cho code", "cần code gì", "update issue", "sửa issue", "plan this",
  "what needs to be done", "scope this out", "break this down".
  NOT for: non-coding tasks (marketing, content, design, ops), executing code
  (use am-developer-skill), project ideation, general planning, simple questions.
---

# Code Task Planner

Turn vague requirements into actionable, well-structured development tasks.

## Permissions

**reads:** source code, git history, existing issues, conversation context
**writes:** GitHub issues (create/edit)
**external:** GitHub API via `gh` CLI (if available), GitNexus MCP (optional)
**destructive:** none
**requires_confirmation:** always preview before create/edit issue

> ⚠️ **Tool availability varies per agent.** Check `command -v <tool> &>/dev/null` before using `gh`, `gitnexus`, etc. Missing → skip or use alternative.

## When to Use

- User describes a feature/fix/change in broad terms
- Need to clarify scope before coding
- Breaking epic into implementable tasks
- Creating or updating issues with proper AC and test strategy

## Mode Detection

| Mode | Intent | Keywords |
|------|--------|----------|
| **Create** | New task from scratch | "tạo task", "create issue", "plan feature" |
| **Update** | Revise existing issue | "update issue #X", "sửa issue", "thêm vào task" |
| **Split** | Break epic into sub-tasks | "tách task", "break down", "chia nhỏ" |

## Quick Mode (Task size S)

**When:** Task is clearly simple — add field, CRUD endpoint, CSS fix, rename, config change.

**Quick check — ALL must be true:**
- Estimate < 2 hours
- ≤ 3 files affected
- No DB migration
- No breaking changes
- Risk 🟢 Low

→ **Quick flow:**
1. **Step 0.5** — conversation context (skip Step 0 Challenge)
2. **Step 1** — understand & clarify (manual discovery only, skip GitNexus). Skip questions if enough context.
3. **Step 3** — compact AC (3-5 items), skip category grouping
4. **Step 4** — list files affected + 1-line approach each. No sub-steps.
5. **Step 5** — E2E checklist only (3-5 items). Skip unit test table.
6. **Step 6** — preview (mandatory)
7. **Step 7** — create (includes duplicate check)

**Skip entirely:** Step 2 (Impact Analysis).

**If task turns out more complex** (DB migration, multi-service, risk > Low):
1. Stop Quick flow, tell user: "Task phức tạp hơn expected ({reason}), chuyển full flow."
2. Keep findings gathered so far (Step 0-1 context carries over).
3. Continue from **Step 2** (Impact Analysis) — don't restart from Step 0.

---

## Full Workflow

### Step 0: Challenge Scope (gstack-inspired)

**Purpose:** Challenge assumptions before planning. Avoid building the wrong thing.

**Auto-skip when:**
- Task is bug fix, typo, config change, rename
- User says "skip challenge" or "plan luôn"
- Quick Mode (size S)
- Update/Split mode (task already planned)

**Trigger when (BOTH required):**
1. Keyword present: "feature", "tính năng mới", "build", "tạo mới", "redesign", "rewrite"
2. AND effort estimate ≥ M size (or unclear size — vague scope)

If keyword present but task is clearly small (add 1 field, 1 simple endpoint) → skip.

**3 Forcing Questions:**

1. **Demand** — "Who needs this now? Is there real signal (user feedback, data, blocker) or just assumption?"
   - If assumption only → flag in issue: "⚠️ Assumption-driven, demand not validated"
   - If real signal → record evidence in issue context

2. **Narrowest Wedge** — "What's the smallest version we can ship that still delivers value?"
   - Compare: user request vs narrowest wedge
   - If different → present both options

3. **Risk** — "What's the most dangerous assumption in this plan? What if it's wrong?"
   - Example: "Assumes users understand dual wallet" → if wrong → wasted effort
   - Record top risk in issue "## Decision Context"

**Scope Mode (ask after 3 questions):**

| Mode | When | Agent action |
|---|---|---|
| **Expand** | User wants to explore more | Surface opportunities, recommend enthusiastically |
| **Selective Expand** | User wants baseline + cherry-pick | Show additions one by one |
| **Hold Scope** | User is clear, wants to plan now | Skip expansion, maximum rigor on current scope |
| **Reduce** | User wants to ship fast | Find minimum viable version, cut non-essential |

Default: **Hold Scope** (don't ask if user is already clear).
Only ask scope mode when questions reveal unclear scope or tension between ambition vs effort.

**Output:** "Decision Context" section in issue:
```markdown
## Decision Context
- **Demand:** {signal or assumption}
- **Narrowest Wedge:** {smallest shippable version}
- **Top Risk:** {most dangerous assumption}
- **Scope Mode:** {chosen mode}
```

**Question budget:** Step 0 uses max 3 questions. Step 1 has max 2 remaining. Total ≤ 5 questions before planning.

→ Continue to Step 0.5 (Gather Conversation Context)

---

### Step 0.5: Gather Conversation Context

Before anything, extract from the current conversation:
- What user already described about the feature/change
- Decisions already made (don't re-ask)
- Code snippets or files already discussed
- Platform preference if mentioned

This saves clarifying questions and avoids re-asking.

### Step 1: Understand & Clarify

**Goal:** Get enough context to plan accurately.

**1. Read the request** — what does the user actually want?

**2. Identify target project** — if workspace has multiple repos:
- Check conversation context for project name/path
- Check `git remote get-url origin` in cwd (if in a repo)
- If ambiguous → ask: "Task này cho project nào?"
- `cd` into correct project root before exploring

**3. Gather codebase context:**

**Option A: GitNexus (preferred for Medium/Large tasks)**
```bash
# Check availability
command -v gitnexus &>/dev/null || { echo "GitNexus not available, using manual discovery"; }

gitnexus status
gitnexus analyze  # incremental re-index if stale

# Bridge script (bundled with this skill)
# Resolve skill_dir dynamically — works regardless of install path
SKILL_DIR="$(dirname "$(readlink -f "$(find ~/.openclaw -path '*/am-planner-code-task/SKILL.md' 2>/dev/null | head -1)")" 2>/dev/null)"
BRIDGE="$SKILL_DIR/scripts/git-nexus-mcp-bridge.js"

# Query related modules
node $BRIDGE query '{"query":"<feature keyword>"}' --repo <repo>

# Blast radius
node $BRIDGE impact '{"target":"<function/module to change>"}' --repo <repo>
```
→ If `gitnexus` not installed → skip to Option B.

**Option B: Manual discovery (fallback)**
```bash
# Detect primary project language (first match wins — monorepo safe)
LANG_EXT=""
[ -z "$LANG_EXT" ] && ls tsconfig.json package.json 2>/dev/null && LANG_EXT="ts"
[ -z "$LANG_EXT" ] && ls go.mod 2>/dev/null && LANG_EXT="go"
[ -z "$LANG_EXT" ] && ls pyproject.toml setup.py requirements.txt 2>/dev/null && LANG_EXT="py"
[ -z "$LANG_EXT" ] && ls Cargo.toml 2>/dev/null && LANG_EXT="rs"
[ -z "$LANG_EXT" ] && ls *.java pom.xml build.gradle 2>/dev/null && LANG_EXT="java"
: ${LANG_EXT:="ts"}  # fallback TypeScript

# Find project structure
find . -name "*.$LANG_EXT" -not -path "*/node_modules/*" -not -path "*/.venv/*" -not -path "*/target/*" -not -path "*/vendor/*" | head -30

# Find DB schema / migrations
find . \( -name "schema.*" -o -name "*.schema.*" -o -name "*.entity.*" -o -name "models.py" \) -not -path "*/node_modules/*" | head -10
find . -type d -name "migrations" -not -path "*/node_modules/*"

# Find related code
grep -rn "{keyword}" --include="*.$LANG_EXT" -l | head -10

# Find existing tests
find . \( -name "*.test.*" -o -name "*.spec.*" -o -name "*_test.*" -o -name "test_*.$LANG_EXT" \) -not -path "*/node_modules/*" | head -10
```
Don't hardcode paths — discover them.

**4. Identify gaps** — ask only what code can't answer:
- Scope: "Feature X includes Y and Z, correct?"
- Business logic: "How should case A be handled?"
- Priority: "All at once or phased?"

**Rules:**
- Read source code BEFORE asking — self-answer as much as possible
- Max 3-5 questions, batched in one message (if Step 0 Challenge ran → max 2 questions here, total ≤ 5)
- Use conversation context (Step 0.5) — don't re-ask known info
- If enough context → skip questions, confirm understanding and proceed

### Step 2: Analyze Impact & Risk

**Goal:** Understand what the task affects and what risks exist.

1. **Files affected** — list specific files/modules that will change (use GitNexus `impact` if available)
2. **Services affected** — workers, containers, proxies, external services
3. **Dependencies** — external APIs, DB, queues, caches
4. **Breaking changes** — backward compatible? migration needed?
5. **Risk level:**

| Level | Criteria | Examples |
|-------|----------|----------|
| 🟢 Low | UI, add field, simple CRUD, no migration | Add column, new page, CSS fix |
| 🟡 Medium | Logic change, DB migration, multi-file | New API endpoint + UI + migration |
| 🔴 High | Billing, auth, data migration, breaking API | Payment flow, schema redesign |

6. **Non-functional concerns** (check if relevant):
   - **Performance:** Large data sets? Pagination? Timeout risk?
   - **Security:** New input → sanitize? Auth changes? Data exposure?
   - **Data integrity:** Concurrent writes? Race conditions? Rollback plan?
   - Skip if clearly not applicable (pure UI, no data).

### Step 3: Define Expected Result & Acceptance Criteria

**Goal:** Describe clearly what "done" looks like.

**Expected Result:** 1-3 sentences, user-facing outcome.

**Acceptance Criteria (AC):**
- Checklist format `- [ ]`
- Each AC must be **testable** — verify yes/no, not vague
- Group by category (API / UI / Integration) if > 5 items
- Cover: happy path + error cases + edge cases

**Examples:**
- ❌ Bad: "System works correctly"
- ✅ Good API: "POST /v1/admin/pricing returns 201 with created record"
- ✅ Good UI: "Click 'Add Model' → modal opens with empty form, all fields required"
- ✅ Good Edge: "Create pricing with duplicate model+date → returns 409 conflict"

### Step 4: Steps to Implement

**Goal:** Break down into steps a developer can follow without asking more questions.

Each step:
- **What:** Specific action
- **Where:** File/module
- **Effort:** S / M / L (see sizing guide in `references/issue-templates.md`)

**Always include if applicable:**
- **Migration step** — if DB changes needed (separate step, run before code)
- **Deploy step** — how to deploy each affected service
- **Verify step** — how to verify the change works after deploy

**Rules:**
- Order by dependency
- Each step independently verifiable
- If 1 step > L → split into sub-steps or separate issue

### Step 5: Test Strategy

**Goal:** Define tests appropriate to scope AND size. Don't over-engineer.

**Task size = total estimate from Step 4** (S < 2h, M = 2-8h, L = 1-3d, XL > 3d — see `references/issue-templates.md`).

**Test depth by task size:**

| Size | Test Depth |
|------|-----------|
| **S** (Quick Mode) | E2E checklist only (3-5 items). Skip unit test table. |
| **M** | Unit tests (table format) + E2E checklist |
| **L/XL** | Unit + Integration + E2E + Migration rollback (if applicable) |

**Test scope by affected area:**

| Scope | Required Tests |
|-------|---------------|
| API only | Unit tests (required for M+) |
| UI only | E2E checklist |
| API + UI | Unit + E2E |
| Multi-service | Unit + Integration + E2E |
| DB migration | Unit + Migration rollback test |

**Unit Tests (M+ only):**
- List test cases: `{name}: {input} → {expected}`
- Cover: success, validation error, auth (401/403), edge cases
- Guideline: 5-8 cases for CRUD, 8-15 for complex logic

**E2E Checklist (all sizes):**
- `- [ ] {user action} → {expected result}`

**Rules:**
- Size S → E2E checklist is sufficient, don't add unit test table
- Don't skip auth tests — every admin endpoint must test 401
- Don't write tests for config/constant changes

### Step 6: Preview & Confirm

**MANDATORY — do not skip.**

Before creating/editing issue:
1. Show full issue preview to user (formatted markdown)
2. Ask: "Review giúp em, có cần sửa gì không?" (or equivalent)
3. User confirms → create issue
4. User requests changes → revise → show preview again

Never create an issue without user confirmation.

### Step 7: Output — Create Task

**Pre-flight checks:**
```bash
# 1. Check gh availability + auth
GH_OK=false
command -v gh &>/dev/null && gh auth status &>/dev/null && GH_OK=true

# 2. Detect repo
REPO_URL=$(git remote get-url origin 2>/dev/null)
# Extract owner/repo from URL (HTTPS or SSH)
OWNER_REPO=$(echo "$REPO_URL" | sed -E 's#.*(github\.com[:/])##; s#\.git$##')
```
If not in a git repo → ask user. If `gh` not available → all output as formatted markdown for manual paste.

**Duplicate check (mandatory before creating):**
```bash
if $GH_OK; then
  gh issue list --repo "$OWNER_REPO" --search "{keywords}" --state open --limit 10
else
  echo "⚠️ gh unavailable — manual duplicate check: search '{keywords}' in repo issues"
fi
```
- Found similar → show user: "Similar issue exists: #{number} — {title}. Create new or update existing?"
- Not found → proceed with create
- No `gh` → remind user to check manually, then proceed

**Read template:** Load `references/issue-templates.md` for structure + labeling + sizing.
If Step 0 Challenge ran → include "Decision Context" section at top of issue body (before Mô tả). If Step 0 skipped → omit section.

**Platform routing:**

| User says | Platform | Action |
|-----------|----------|--------|
| "tạo issue" / default | GitHub | `gh issue create` (or markdown output if no `gh`) |
| "tạo task trên Jira" | Jira | Format Jira-compatible output |
| "tạo card Trello" | Trello | Format Trello card |
| "Monday" | Monday | Format Monday item |
| Other | Ask | Ask format preference |

Remember platform preference for session — don't re-ask.

**Create command (when `gh` available):**
```bash
# Write body to temp file (avoids shell escaping issues)
TMPFILE="${HOME}/.openclaw/.issue-body-$$.md"
cat > "$TMPFILE" << 'ISSUE_EOF'
{full body from template}
ISSUE_EOF
gh issue create --repo "$OWNER_REPO" \
  --title "{title}" \
  --label "{label1},{label2}" \
  --body-file "$TMPFILE"
rm -f "$TMPFILE"
# Optionally: --assignee @me --milestone "v1.0"
```

**When `gh` is not available:**
Output the full issue as formatted markdown with clear copy-paste instructions:
```
📋 Issue ready — paste into GitHub manually:
Title: {title}
Labels: {labels}
---
{full body}
```

**For Update mode:**
1. Fetch current issue (requires `gh`): `gh issue view {number} --json body,title,labels`
   - No `gh` → ask user to paste current issue body, or provide URL for `web_fetch`
2. **Parse sections** — split body by `## heading` markers
3. **Merge strategy:**
   - Section user mentioned → **replace** content
   - Section user did NOT mention → **keep** (append if user says "add")
   - New section → **insert** at canonical position:
     `Mô tả → Hiện trạng → Impact → AC → Steps → Test Strategy → Deploy → Notes → Estimate`
4. **Show diff preview** — display `[CHANGED]`, `[ADDED]`, `[KEPT]` per section
5. User confirm → write:
   ```bash
   # Write to workspace temp (avoids /tmp restrictions in some containers)
   TMPFILE="${HOME}/.openclaw/.issue-body-$$.md"
   cat > "$TMPFILE" << 'ISSUE_EOF'
   {merged body}
   ISSUE_EOF
   gh issue edit {number} --body-file "$TMPFILE"
   rm -f "$TMPFILE"
   ```

**For Split mode:**
1. **Analyze epic** — read existing issue (if any), understand full scope
2. **Identify sub-tasks** — group by concern (DB, API, UI, deploy), each self-contained
3. **Dependency ordering** — which task blocks which:
   - DB migration → before API
   - API → before UI
   - Draw dependency chain in parent issue
4. **Estimate rollup** — estimate each child → total for parent
5. **Create parent issue** (epic overview) first:
   - Summary of all sub-tasks + dependency graph + total estimate
6. **Create child issues** — each with full AC + steps
   - Link via "Parent: #X" + "Depends on: #Y" in Notes
   - Label: add `epic:{parent-number}`
7. **Preview all** — show parent + all children before creating
   - No `gh` → output all issues as numbered markdown blocks for manual creation

**Language:** Match repo language. Check existing issues or README for convention. Default: language user is speaking.

## Handoff to Developer

After issue is created, the planner's job is done. To execute:

**If am-developer-skill is available:**
- User says "build this" / "implement #N" → am-developer-skill takes over
- The issue body IS the plan — developer skill reads it as input
- No need to re-plan; developer skill starts from Scout (Step 1a)

**If no developer skill:**
- Issue is self-contained — any developer can pick it up
- Steps + AC + test strategy provide complete implementation guide

**Do NOT:**
- Auto-trigger developer skill without user asking
- Start coding within the planner flow
- Modify the issue after handoff without going through Update mode

## Quality Checklist

Self-review BEFORE showing preview.

**All sizes (mandatory):**
- [ ] Title clear and descriptive (not generic)
- [ ] AC all testable (verify yes/no)
- [ ] Source code was read — no guessing
- [ ] Labels correct (see labeling strategy in references)
- [ ] Estimate realistic (see sizing guide)

**M+ only (skip for Quick Mode S):**
- [ ] Steps detailed enough — dev doesn't need to ask more
- [ ] Tests cover happy path + error cases
- [ ] Risk assessed, breaking changes noted
- [ ] Related issues linked (if any)

## Anti-patterns

❌ **Vague issue** — no AC, no steps, just "Implement feature X"
❌ **Skip reading code** — asking user what code does instead of grepping
❌ **Over-engineering** — 50 test cases for 1 CRUD, full impact analysis for a CSS fix
❌ **Ignore risk** — billing/auth change marked as 🟢 Low
❌ **Monolith issue** — 1 issue with 10 features → split
❌ **Skip preview** — creating issue without user confirmation
❌ **Wrong mode** — Quick Mode for DB migration, Full flow for adding 1 field

## References

| File | Content |
|------|---------|
| `references/issue-templates.md` | Issue template + labeling + sizing guide |
| `references/gitnexus-setup.md` | GitNexus install, index, MCP bridge usage |
| `scripts/git-nexus-mcp-bridge.js` | MCP bridge script — call GitNexus tools directly |
