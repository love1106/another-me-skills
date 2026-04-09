---
name: am-memory-consolidation
version: 1.1.0
author: khoidoan
description: >
  Cognitive memory consolidation for AI agents — daily "dream cycles" that scan
  daily logs, extract knowledge, consolidate into structured long-term memory, archive
  outdated entries, and generate per-project context summaries.
  Use when: "consolidate memory", "dream", "memory maintenance", "archive old memories",
  "setup memory consolidation", "memory status".
  NOT for: reading/searching memory (use memory_search), writing daily logs (agent does
  this naturally during sessions).
---

# Memory Consolidation

Agent "sleeps" every night — scans daily logs, extracts key knowledge, consolidates into
structured long-term memory, archives old entries, detects stale threads, and generates
per-project context summaries.

Inspired by how the human brain consolidates memories during sleep: replay, filter, store,
forget, wake up lighter.

> **Note:** OpenClaw has a built-in `memory-core` dreaming feature (signal-based, promotes
> frequently-recalled snippets). This skill is complementary — it handles structured daily log
> consolidation, project summaries, and growth control. Both can run together without conflict.

## Setup

Run once when installing the skill. Say **"Set up memory consolidation"**.

### Step 1: Create Memory Files

Create these files if they don't exist (use templates from `references/templates.md`):

```bash
mkdir -p memory/projects
```

- `memory/archive.md` — compressed old entries
- `memory/procedures.md` — workflows, deploy commands, tool configs
- `memory/dream-log.md` — consolidation report history (append-only)

### Step 2: Update AGENTS.md

Add these rules to the agent's AGENTS.md:

```markdown
## Memory — Daily Log Rule

After every session with decisions, tasks, or important info → write to memory/YYYY-MM-DD.md.
Applies to ALL sessions: DM, group chat, cron. Group chats are project contexts —
losing group memory = losing project context. No exceptions.

### Daily Log Format

Tag each entry block with its source context:
- Group sessions: ## [group-name] Topic
- DM sessions: ## [DM] Topic
- Cron/automated: ## [cron] Topic

### Session Startup — Context Loading

- DM session: load MEMORY.md (full context)
- Group session: load memory/projects/<project>.md (project-specific context)
- If project summary doesn't exist yet: fall back to MEMORY.md
```

### Step 3: Create Cron Job

```json
{
  "name": "am-memory-consolidation",
  "schedule": { "kind": "cron", "expr": "0 4 * * *", "tz": "<USER_TIMEZONE>" },
  "payload": {
    "kind": "agentTurn",
    "message": "Run memory consolidation.\n\nRead skills/am-memory-consolidation/references/consolidation-prompt.md and follow every step strictly.",
    "timeoutSeconds": 0
  },
  "sessionTarget": "isolated",
  "delivery": { "mode": "announce" }
}
```

Replace `<USER_TIMEZONE>` with the agent owner's IANA timezone (e.g., `Asia/Ho_Chi_Minh`, `America/New_York`). The goal is 4AM local time.

### Step 4: Run First Consolidation

Read `references/first-run-prompt.md` and follow every step. This scans ALL existing daily
logs, restructures MEMORY.md, creates procedures.md, generates project summaries, and
produces a before/after report.

## Manual Triggers

| Command | What happens |
|---------|-------------|
| "Consolidate memory" / "Dream now" | Run full consolidation in current session |
| "Archive old memories" | Run only Archive (forgetting) + Growth Check |
| "Memory status" | Report: MEMORY.md line count, entries, last consolidation date, project summaries status |

## How It Works

Each night, the cron job creates an isolated session. The agent reads
`references/consolidation-prompt.md` and executes these steps:

1. **Smart Skip** — check for unconsolidated daily logs. None → surface an old memory recall + skip
2. **Collect** — read daily logs, extract decisions, facts, progress, lessons
3. **Consolidate** — merge into MEMORY.md (facts/decisions) or procedures.md (workflows)
4. **Archive** — entries >90 days + unreferenced → compress to archive.md
5. **Stale Detection** — Open Threads >14 days without mention → flag
6. **Growth Check** — MEMORY.md line count caps (daily); deep clean on Sundays
7. **Project Summaries** — generate/update memory/projects/<name>.md for each project
8. **Log** — append report to memory/dream-log.md
9. **Report** — send summary to user's chat with before/after deltas; weekly summary on Sundays

## Content Routing

| Content type | Destination |
|-------------|-------------|
| Decisions, facts, architecture, project status, people, strategy | `MEMORY.md` |
| Deploy commands, coding rules, tool configs, workflow steps | `memory/procedures.md` |
| Compressed old entries | `memory/archive.md` |
| Per-project derived summaries | `memory/projects/<name>.md` |

## Safety Rules

1. **Never delete daily logs within 6 months** — only mark with `<!-- consolidated -->`. After 6 months + consolidated → deletion allowed during weekly growth control
2. **Never remove ⚠️ PERMANENT, 📌 PIN, or 🔴 entries** — protected from archival
3. **Backup before big changes** — if MEMORY.md changes >30%, save `.bak` copy first
4. **Scope** — only read/write within `memory/` directory, `MEMORY.md`, and `AGENTS.md` (during setup)
5. **Project summaries are derived** — MEMORY.md is source of truth, project files are regenerated each cycle. If the user has manually added content to project files beyond what MEMORY.md contains, that content will be lost on next consolidation. Users who want persistent project-specific notes should add them to MEMORY.md instead
6. **Isolated session** — cron runs in isolated context. MEMORY.md and procedures.md are NOT auto-loaded — the consolidation prompt reads them explicitly. This also means no race condition with the user's active session

## Growth Control

### Daily (every run)
- MEMORY.md > 300 lines → warning in report
- MEMORY.md > 400 lines → forced prune: reduce archive threshold (90d → 60d → 30d) until < 300

### Weekly (Sundays only)
- `procedures.md`: entries unreferenced > 90 days → archive
- Daily logs > 6 months + consolidated → delete originals
- `archive.md` > 500 lines → rotate to `memory/archive-YYYY.md`

## Reference Files

| File | Purpose |
|------|---------|
| `references/consolidation-prompt.md` | Daily cron prompt — the "dream cycle" instructions |
| `references/first-run-prompt.md` | First-time setup — scan all logs, restructure, generate summaries |
| `references/templates.md` | File templates: archive.md, procedures.md, dream-log.md, project summary |

## Permissions

- **reads:** MEMORY.md, memory/*.md, memory/projects/*.md, AGENTS.md
- **writes:** MEMORY.md, memory/archive.md, memory/procedures.md, memory/projects/*.md, memory/dream-log.md, AGENTS.md (setup only)
- **external:** cron job (isolated session)
- **destructive:** daily log deletion (only >6 months + consolidated, weekly)
