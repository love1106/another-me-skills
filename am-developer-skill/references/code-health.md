# Code Health — Codebase Audit & Tech Debt Discovery

Scan codebase → phát hiện tech debt, complexity, gaps → trình bày findings → tạo issues (user confirm).

**Trigger:** "code health", "tech debt", "audit codebase", "tình hình code", "source code status", "what needs fixing", "cần fix gì"

## Workflow

### Phase 1: Setup

```bash
cd ~/projects/<repo>
REPO_REMOTE=$(git remote get-url origin 2>/dev/null | sed 's|.*github.com[:/]||;s|\.git$||')

# Detect stack
[ -f package.json ] && STACK="node" && PM=$([ -f bun.lockb ] && echo "bun" || echo "npm")
[ -f requirements.txt ] || [ -f pyproject.toml ] && STACK="python"
[ -f go.mod ] && STACK="go"

# Detect source directory (không hardcode path)
SRC_DIR=""
for dir in src app lib pkg; do
  [ -d "$dir" ] && SRC_DIR="$dir" && break
done
[ -z "$SRC_DIR" ] && SRC_DIR="."  # fallback: root
echo "Source dir: $SRC_DIR"
```

### Phase 2: Scan (6 categories)

#### 2.1 Test Coverage
```bash
# Count test files
TEST_COUNT=$(find . -name "*.test.*" -o -name "*.spec.*" | grep -v node_modules | wc -l)

# Count source files (endpoints, services, utils)
SRC_COUNT=$(find "$SRC_DIR"/ -name "*.ts" -o -name "*.py" | grep -v node_modules | wc -l)

# Ratio
echo "Test files: $TEST_COUNT / Source files: $SRC_COUNT"

# Coverage report (nếu có)
[ -f coverage/coverage-summary.json ] && cat coverage/coverage-summary.json | head -20

# Endpoints without tests — detect framework-appropriate patterns
# Express/Hono/Fastify: app.get, app.post, router.get, .route(), .on()
# Python: @app.get, @router.post
grep -rn "app\.\(get\|post\|put\|delete\|patch\|use\|route\)\|router\.\(get\|post\|put\|delete\|route\)\|\.on(" --include="*.ts" --include="*.js" "$SRC_DIR"/ -l 2>/dev/null | while read f; do
  BASENAME=$(basename "$f" .ts)
  find . -name "${BASENAME}.test.*" -o -name "${BASENAME}.spec.*" | grep -q . || echo "⚠️ No test: $f"
done
```

**Score:**
- 🟢 5/5: > 60% files have tests
- 🟡 3/5: 20-60% files have tests
- 🔴 1/5: < 20% files have tests

#### 2.2 Type Safety (TypeScript/Python)
```bash
# any types
grep -rn "\bany\b" --include="*.ts" "$SRC_DIR"/ | grep -v "node_modules\|\.d\.ts\|test\|spec" | wc -l

# @ts-ignore / @ts-nocheck
grep -rn "@ts-ignore\|@ts-nocheck" --include="*.ts" "$SRC_DIR"/ | wc -l

# Python: no type hints
grep -rn "def " --include="*.py" "$SRC_DIR"/ | grep -v "->.*:" | wc -l
```

**Score:**
- 🟢 5/5: < 5 `any` types, 0 `@ts-ignore`
- 🟡 3/5: 5-20 `any` types
- 🔴 1/5: > 20 `any` types or `@ts-nocheck` on files

#### 2.3 Code Complexity
```bash
# Large files (> 400 lines)
find "$SRC_DIR"/ -name "*.ts" -o -name "*.py" | grep -v node_modules | xargs wc -l 2>/dev/null | sort -rn | awk '$1 > 400 {print}'

# Long functions (rough: count lines between function declarations)
# Agent: read top 5 largest files, identify functions > 50 lines

# Deeply nested code (> 4 levels)
grep -rn "^\s\{16,\}" --include="*.ts" --include="*.py" "$SRC_DIR"/ | wc -l
```

**Score:**
- 🟢 5/5: 0 files > 400 lines, no deep nesting
- 🟡 3/5: 1-3 files > 400 lines
- 🔴 1/5: > 3 files > 400 lines or functions > 100 lines

#### 2.4 Dependencies
```bash
# Outdated packages
[ "$STACK" = "node" ] && $PM outdated 2>/dev/null | head -20

# Security vulns
[ "$STACK" = "node" ] && npm audit --json 2>/dev/null | head -30

# Unused dependencies (Node) — only if depcheck already installed (skip auto-install, slow)
command -v depcheck >/dev/null 2>&1 && depcheck --json 2>/dev/null | head -30 || echo "ℹ️ depcheck not installed — skip unused deps check"

# Python
[ "$STACK" = "python" ] && pip list --outdated 2>/dev/null | head -20
```

**Score:**
- 🟢 5/5: All up to date, 0 vulns, 0 unused
- 🟡 3/5: < 5 outdated, 0-1 medium vuln
- 🔴 1/5: > 5 outdated or any high/critical vuln

#### 2.5 Dead Code
```bash
# Unused exports — sample top 30 exports, check import count
# (full scan on large repos is slow — sample is sufficient for health check)
grep -rn "^export " --include="*.ts" "$SRC_DIR" | head -30 | while read line; do
  FILE=$(echo "$line" | cut -d: -f1)
  EXPORT_NAME=$(echo "$line" | grep -oP 'export\s+(const|function|class|type|interface)\s+\K\w+')
  [ -z "$EXPORT_NAME" ] && continue
  IMPORT_COUNT=$(grep -rn "$EXPORT_NAME" --include="*.ts" "$SRC_DIR" | grep -v "$FILE" | wc -l)
  [ "$IMPORT_COUNT" -eq 0 ] && echo "⚠️ Unused export: $EXPORT_NAME in $FILE"
done 2>/dev/null | head -20

# Nếu có depcheck (Node): npx depcheck --json (faster, more accurate)
```

**Score:**
- 🟢 5/5: 0-2 unused exports
- 🟡 3/5: 3-10 unused exports
- 🔴 1/5: > 10 unused exports

#### 2.6 Debt Markers
```bash
# TODO/FIXME/HACK/XXX count
grep -rn "TODO\|FIXME\|HACK\|XXX" --include="*.ts" --include="*.py" --include="*.js" "$SRC_DIR"/ | grep -v node_modules > /tmp/debt-markers.txt
wc -l /tmp/debt-markers.txt

# Stale TODOs — use git blame (batch, much faster than per-line git log)
while IFS= read -r line; do
  FILE=$(echo "$line" | cut -d: -f1)
  LINE_NUM=$(echo "$line" | cut -d: -f2)
  BLAME=$(git blame -L "$LINE_NUM,$LINE_NUM" "$FILE" 2>/dev/null | head -1)
  echo "$BLAME | $(echo "$line" | cut -d: -f3-)"
done < /tmp/debt-markers.txt 2>/dev/null | head -20
# Filter: lines with date > 30 days ago = stale
```

**Score:**
- 🟢 5/5: < 5 markers, 0 stale
- 🟡 3/5: 5-15 markers
- 🔴 1/5: > 15 markers or > 5 stale (> 30 days)

### Phase 3: Report

Trình bày cho user:

```
📊 Code Health — {project-name}
Date: {date} | Stack: {stack} | Files: {N} | Lines: {N}

| Category        | Score | Key Finding                      |
|-----------------|-------|----------------------------------|
| Test Coverage   | {emoji} {n}/5 | {summary}                 |
| Type Safety     | {emoji} {n}/5 | {summary}                 |
| Code Complexity | {emoji} {n}/5 | {summary}                 |
| Dependencies    | {emoji} {n}/5 | {summary}                 |
| Dead Code       | {emoji} {n}/5 | {summary}                 |
| Debt Markers    | {emoji} {n}/5 | {summary}                 |
| **OVERALL**     | **{emoji} {total}/30** |                  |

TOP ITEMS (ranked by severity × ease-to-fix)
# | Sev | Item                              | Effort | Files
1 | 🔴  | {description}                     | S/M/L  | {n files}
2 | 🔴  | {description}                     | S/M/L  | {n files}
...
```

### Phase 4: Create Issues (user confirm)

Sau report, hỏi:

> "Tạo GitHub issues cho items nào? (all / chọn số: 1,3,5 / skip)"

**Default: tạo trên GitHub** (`gh issue create --repo {repo}`).

Mỗi issue:
- **Title:** `tech-debt: {item description}`
- **Labels:** `tech-debt` + severity label
- **Body:** Context từ scan (file locations, code snippets, current state), Acceptance Criteria, Effort estimate
- **Format:** Theo am-planner-code-task issue template (nếu available, đọc `references/issue-templates.md` từ planner skill)

```bash
# Create issue
gh issue create --repo "$REPO_REMOTE" \
  --title "tech-debt: {title}" \
  --label "tech-debt" \
  --body "## Mô tả
{finding description + evidence}

## Acceptance Criteria
- [ ] {criteria}

## Effort: {S/M/L}
## Files: {list}"
```

**KHÔNG auto-create.** Luôn show preview + wait confirm.

### Phase 5: Save Report (optional)

```bash
mkdir -p .code-health
```

Save JSON report:
```json
{
  "date": "2026-03-30",
  "project": "{repo-name}",
  "maturity": "early|growing|mature",
  "commits": 142,
  "stack": "node",
  "src_dir": "src",
  "files": 85,
  "lines": 12400,
  "scores": {
    "test_coverage": 2,
    "type_safety": 3,
    "complexity": 3,
    "dependencies": 4,
    "dead_code": 4,
    "debt_markers": 2,
    "overall": 18
  },
  "findings": [
    {
      "rank": 1,
      "severity": "red",
      "description": "Missing tests billing endpoints",
      "effort": "M",
      "files": 5,
      "issue_created": "#42"
    }
  ],
  "trend": {
    "prior_date": "2026-03-23",
    "prior_overall": 15,
    "delta": 3,
    "direction": "improving"
  }
}
```

File: `.code-health/{date}.json`. So sánh với most recent prior report → trend: improving / degrading / stable.

## Scoring Guide

**Project maturity context** (detect tự động, ghi trong report):
```bash
FIRST_COMMIT=$(git log --reverse --format="%ai" | head -1)
TOTAL_COMMITS=$(git rev-list --count HEAD)
# < 50 commits hoặc < 30 ngày = Early stage
# 50-500 commits = Growing
# > 500 commits = Mature
```

| Overall Score | Early Stage | Growing | Mature |
|---|---|---|---|
| 25-30 | 🟢 Great start | 🟢 Healthy | 🟢 Healthy |
| 15-24 | 🟡 Normal — debt accumulates as you build | 🟡 Plan debt sprint | 🟡 Needs attention |
| < 15 | 🟡 Expected if < 2 weeks old | 🔴 Debt growing fast | 🔴 Critical |

Ghi maturity trong report header: `Maturity: Early / Growing / Mature ({N} commits, {age})`

## Rules

- **Read-only scan** — KHÔNG sửa code, chỉ report
- **Evidence-based** — mỗi finding phải có file:line reference
- **Practical scoring** — 5-point scale, không over-complicate
- **User decides** — agent report, user chọn items tạo issue
- **Skip categories không relevant** — Python project skip Type Safety (TS), Go project skip npm deps
