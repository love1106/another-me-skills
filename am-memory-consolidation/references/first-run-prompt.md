# First Dream — Initial Memory Consolidation

Run this ONCE immediately after installing the skill.
Detect the user's preferred language from workspace context. All output in that language.
Working directory: the workspace root.

## Phase 1: Snapshot BEFORE

Count and record these numbers BEFORE making any changes:

```bash
MEMORY_LINES=$(wc -l < MEMORY.md 2>/dev/null || echo 0)
PROCEDURES_LINES=$(wc -l < memory/procedures.md 2>/dev/null || echo 0)
DAILY_LOGS=$(ls memory/????-??-??.md 2>/dev/null | wc -l)
UNCONSOLIDATED=$(grep -L "<!-- consolidated -->" memory/????-??-??.md 2>/dev/null | wc -l)
PROJECT_SUMMARIES=$(ls memory/projects/*.md 2>/dev/null | wc -l)
```

Also count items in MEMORY.md sections: Key Decisions, Lessons Learned, Open Threads, Projects.
Save all values — needed for before/after comparison.

Create `memory/dream-log.md` if it doesn't exist (use template from `references/templates.md`).

If DAILY_LOGS == 0 AND MEMORY_LINES < 10 → this is a fresh instance. Skip to Phase 6.

## Phase 2: Restructure MEMORY.md

Read current MEMORY.md. Separate content into two categories:

**Stays in MEMORY.md** (what happened / what is):
- Decisions, facts, architecture descriptions, project status
- People, team info, contacts
- Strategy, goals, milestones
- Open threads, pending items

**Moves to procedures.md** (how to do):
- Deploy commands, start sequences
- Coding rules, conventions
- Tool configs, environment setup
- Workflow steps, checklists

For each entry staying in MEMORY.md, add a date comment `<!-- YYYY-MM-DD -->` where the date can be inferred from daily logs or context. If date is unknown, use `<!-- undated -->`.

Restructure the Projects section with explicit per-project subsections:

```markdown
## 🏗️ Projects

### [Project Name 1]
<!-- All facts, decisions, architecture, status for this project -->

### [Project Name 2]
<!-- All facts, decisions, architecture, status for this project -->
```

Use existing Group Chat → Repo Mapping if available to identify projects.

**Safety:** Save `MEMORY.md.bak` before any restructuring.

## Phase 3: Create procedures.md

Write extracted procedural content to `memory/procedures.md` using the template from `references/templates.md`.

Organize into sections: Deploy Commands, Coding Rules, Tool Configs, Communication Preferences.

## Phase 4: Consolidate Daily Logs

Read ALL unconsolidated daily logs (excluding today's).

For each file:
1. Extract decisions, facts, progress, lessons, todos
2. Note `## [group-name]` tags for project routing
3. Compare with MEMORY.md — **strong semantic dedup**: content may already exist in different wording from manual curation. When in doubt, skip rather than duplicate.
4. New entries → append to correct section with `<!-- YYYY-MM-DD -->`
5. Updated entries → update in-place
6. Workflow content → procedures.md
7. Mark file with `<!-- consolidated -->` at end

Process files chronologically (oldest first).

If there are many files (>15), process in batches and report progress.

## Phase 5: Generate Project Summaries

For each project subsection under `## 🏗️ Projects` in MEMORY.md:

1. Create `memory/projects/<project-name>.md` using template from `references/templates.md`
2. Extract: architecture, current status, recent decisions (last 30 days), active threads, key people
3. Target: 30-60 lines per summary
4. Project name → filename: kebab-case

## Phase 5.5: Log to dream-log.md

Append the first consolidation report to `memory/dream-log.md`:

```markdown
## 🧠 First Consolidation — YYYY-MM-DD

**Scanned:** N files | **New:** N | **Updated:** N | **Moved to procedures:** N
**MEMORY.md:** N → N lines | **procedures.md:** 0 → N lines | **Project summaries:** N

### Changes
- [New] brief description of each new entry
- [Moved] brief description of content moved to procedures.md
```

## Phase 6: Snapshot AFTER + Report

Count the same metrics again after all changes.

Compose the First Dream Report (this is your final reply):

```
🧠 First Memory Consolidation Complete!

📦 Memory assets:
   • N daily logs (earliest → latest, spanning N days)
   • N lines of long-term memory (MEMORY.md)
   • N lines of procedures (procedures.md)
   • N project summaries generated

🔍 Scan results:
   • Extracted N new entries from N unconsolidated logs
   • Updated N existing entries
   • Moved N procedural entries to procedures.md

📊 Before → After:
   MEMORY.md:      N → N lines
   procedures.md:  N → N lines
   Key decisions:  N → N
   Lessons learned: N → N
   Open threads:   N → N
   Project summaries: N → N

✅ Setup complete:
   • memory/archive.md — ready
   • memory/procedures.md — N entries
   • memory/projects/ — N project summaries
   • Cron job — daily consolidation active
   • AGENTS.md — updated with memory rules

💬 Daily consolidation starts tonight. You'll receive a report each morning.
```

For fresh instances (Phase 6 direct):
```
🧠 Memory Consolidation Initialized!

✅ Memory architecture ready:
   • MEMORY.md — long-term knowledge
   • memory/procedures.md — workflows & patterns
   • memory/archive.md — compressed old entries
   • memory/projects/ — per-project summaries

🌱 Starting from zero — and that's fine.
   Every conversation will be captured in daily logs.
   Each night, I'll consolidate them into structured memory.

⏰ Daily consolidation scheduled.
   First real report after a few days of use.
```

## Safety Rules

- Save MEMORY.md.bak before restructuring
- Never delete daily log originals — only mark `<!-- consolidated -->`
- Never remove ⚠️ PERMANENT, 📌 PIN, or 🔴 entries
- Strong semantic dedup — do not duplicate existing manually curated content
- Process chronologically to maintain consistency
