# Memory Consolidation — Daily Dream Cycle

You are running an automatic memory consolidation cycle. Execute all steps in order.
Detect the user's preferred language from workspace context. All output in that language.
Working directory: the workspace root.

## Step 0: Smart Skip

First, determine today's date:
```bash
date +%Y-%m-%d
```

Then find unconsolidated daily logs:
```bash
grep -L "<!-- consolidated -->" memory/????-??-??.md 2>/dev/null
```

From the results, **exclude today's file** (today's log may still be written to). Only keep files with dates strictly before today.

If 0 eligible files → go to **Step 0-B: Skip With Recall**. Do not proceed to Step 1.

### Step 0-B: Skip With Recall

Even when skipping, deliver value. Use `exec` to extract Open Threads from MEMORY.md without reading the full file:
```bash
sed -n '/## .*Open Threads/,/^## /p' MEMORY.md 2>/dev/null | head -20
```

Find the oldest uncompleted item (not marked `[x]`) and surface it.

Reply with:
```
🌙 No new content — skipped consolidation

💭 From your memory:
   {N} days ago ({date}), {one-line context of an old event or decision}.
   {Follow-up question or status check if relevant}
```

If no interesting memory to surface, simplify to:
```
🌙 No new content — skipped
```

Then END. Do not proceed to Step 1.

## Step 0.5: Snapshot BEFORE (only if proceeding to Step 1)

This step only runs when there are files to consolidate. If you went to Step 0-B (skip), you never reach here.

Before making any changes, count:
```bash
wc -l MEMORY.md
wc -l memory/procedures.md 2>/dev/null
```

Also count: total bullet items in MEMORY.md, items in Open Threads section.
Save these values — needed for before/after comparison in the report.

## Step 1: Collect

Read each unconsolidated daily log (excluding today's).

Extract items in these categories:
- **Decisions** — choices made, direction changes, confirmations
- **Facts** — technical details, metrics, data points, architecture info
- **Progress** — milestones, completions, blockers, PR/issue updates
- **Lessons** — mistakes, insights, things that worked or failed
- **Todos** — unfinished items, pending follow-ups

Note the `## [group-name]` tags on each entry block — these indicate which project context the entry belongs to.

**Skip:** small talk, transient debug output, content already in MEMORY.md that hasn't changed, empty files (still mark them consolidated in Step 5).

## Step 2: Consolidate

Read current `MEMORY.md` (in workspace root) and `memory/procedures.md`.
These files are NOT auto-loaded in isolated sessions — you must read them explicitly.

**Path note:** If you need to reference skill files (e.g., templates), they are at
`skills/am-memory-consolidation/references/` relative to workspace root.

For each extracted item, compare with existing content:

- **New** → append to correct section in MEMORY.md with date comment `<!-- YYYY-MM-DD -->`
- **Updated** (status changed, newer data) → update in-place, update date comment
- **Duplicate** → skip (semantic dedup — compare meaning, not exact text)
- **Workflow/tool pattern** → write to `memory/procedures.md` instead

**Editing technique:** Use `read` to find the exact text of the target section in MEMORY.md, then use `edit` with precise `oldText`/`newText` for surgical changes. Never overwrite the entire file with `write`.

**Content routing:**
- `MEMORY.md` = **what happened / what is** — decisions, facts, architecture, project status, people, strategy
- `procedures.md` = **how to do** — deploy commands, coding rules, tool configs, start sequences, workflow steps

**Project routing:** Use `## [group-name]` tags from daily logs to route entries to the correct project subsection under `## 🏗️ Projects` in MEMORY.md. If a new project group appears that has no subsection yet → create one.

**Semantic dedup is critical.** The agent may have already written some content to MEMORY.md manually during the session. Compare meaning, not exact wording. When in doubt, skip rather than duplicate.

If MEMORY.md or procedures.md has a `_Last updated:_` line, update the date. If not, skip — do not add one.

## Step 3: Archive (Forgetting)

Scan MEMORY.md for entries that should be archived:

**Archive condition — ALL must be true:**
1. Entry has date comment `<!-- YYYY-MM-DD -->` older than 90 days (or estimated age >90 days from daily log cross-reference)
2. Entry not referenced in any daily log from the last 30 days
3. Entry NOT marked with ⚠️ PERMANENT, 📌 PIN, or 🔴

**If no entries have date comments:** Skip archiving entirely. Add to report: "⚠️ No date-tagged entries found — run first-run setup or manually add `<!-- YYYY-MM-DD -->` comments to enable archiving."

**Before archiving:** Count how many entries will be removed. If removals would change MEMORY.md by >30% → save `MEMORY.md.bak` first.

**Archive action (for each eligible entry):**
1. Compress entry to one-line summary
2. Append to `memory/archive.md`: `[YYYY-MM-DD] One-line summary (from: section name)`
3. Remove the entry from MEMORY.md

## Step 4: Stale Thread Detection

Scan MEMORY.md for Open Threads or pending items:
- Find items not marked as completed `[x]`
- Cross-reference with daily logs from the last 14 days (read ALL recent logs, including already consolidated ones — stale detection needs full recent history)
- Items with zero mentions in 14 days → flag as stale

Collect top 3 stale items for the report.

## Step 5: Mark Consolidated

For each daily log file that was processed:
- Append a new line `<!-- consolidated -->` at the very end of the file (use `edit` to add after the last line of content)
- Do NOT modify any other content in the file

## Step 6: Growth Check (daily)

Check MEMORY.md line count:
- **> 300 lines** → add warning to report: "MEMORY.md approaching limit (N lines), review recommended"
- **> 400 lines** → forced prune: re-run Step 3 with progressively lower thresholds (90d → 60d → 30d) until MEMORY.md is under 300 lines. Archive oldest + least-referenced entries first. **Exit condition:** if threshold reaches 30d and MEMORY.md is still > 300 lines (all remaining entries are recent or protected), stop pruning and add to report: "⚠️ MEMORY.md at N lines — cannot prune further, manual review needed."

## Step 6b: Deep Growth Control (weekly — Sundays only)

Check what day it is (use the date from Step 0, or run `date +%u` — Sunday = 7). If NOT Sunday → skip this step entirely.

If Sunday:
1. **procedures.md prune:** entries not referenced in any daily log for >90 days → archive to archive.md
2. **Old daily logs:** find `memory/YYYY-MM-DD.md` files older than 6 months AND ending with `<!-- consolidated -->` → delete them
3. **Archive rotation:** if `memory/archive.md` > 500 lines → move content to `memory/archive-YYYY.md` (current year), start fresh archive.md with header only

## Step 7: Update Project Summaries

If MEMORY.md does not have a `## 🏗️ Projects` section → skip this step entirely.

For each project subsection under `## 🏗️ Projects` in MEMORY.md:

1. Extract: architecture, current status, recent decisions (last 30 days), active threads, key people
2. Write to `memory/projects/<project-name>.md` using the project summary template
3. Create `memory/projects/` directory if it doesn't exist
4. These are **derived views** — use `write` to overwrite the file completely each cycle (this is the one exception to the "never use write on existing files" rule — project summaries are regenerated, not edited)
5. **Warning:** Any content the user manually added to project files that is NOT in MEMORY.md will be lost. This is by design — MEMORY.md is the source of truth

Target: 30-60 lines per project summary. Keep it focused and current.

Project name → filename: kebab-case (e.g., "Another Me" → `another-me.md`, "NetDok" → `netdok.md`).

## Step 8: Log to dream-log.md

Append the consolidation report to `memory/dream-log.md`.

If the file doesn't exist, create it with the header from `references/templates.md` first.

To append without overwriting: read the last few lines of dream-log.md, then use `edit` to add the new entry after the last line. Alternatively, use `exec`:
```bash
cat >> memory/dream-log.md << 'ENTRY'
[report content here]
ENTRY
```

Format:
```markdown
## 🧠 Consolidation — YYYY-MM-DD

**Scanned:** N files | **New:** N | **Updated:** N | **Archived:** N
**MEMORY.md:** N → N lines | **procedures.md:** N → N lines

### Changes
- [New] brief description
- [Updated] brief description
- [Archived] brief description

### Insights
- 1-2 non-obvious cross-memory observations (patterns across entries, trends, gaps)

### Stale Threads
- {item} — stale for {N} days
```

**Insights guidance:** Review the full set of extracted + existing entries. Look for:
- Pattern connections: "Project X decision mirrors what worked for Project Y"
- Temporal patterns: "Strategic decisions cluster on certain days"
- Gap detection: "No lessons recorded for recent projects"

If no meaningful insight → skip the Insights section. Don't force it.

## Step 9: Report

Compose your final reply. This is the only output the user will see (delivered via cron announce).

Count the same metrics as Step 0.5 again (AFTER) and calculate deltas.

### Daily notification format:

```
🧠 Memory consolidation complete

📥 Scanned: N daily logs (MM/DD → MM/DD)
📝 +N new, ~N updated, -N archived
📊 MEMORY.md: N → N lines | procedures: N lines | projects: N summaries

🧠 Highlights:
  • {change_1}
  • {change_2}
  (max 3-5 most significant, summarize if more)

🔮 Insight: {most valuable cross-memory observation, if any}

⏳ Stale threads:
  • [item] — N days, last context: [one-line]
  (top 3, omit section if none)

⚠️ [Growth warning if applicable]
```

### Sunday weekly summary (prepend to daily report):

If today is Sunday, read `memory/dream-log.md` entries from the last 7 days to calculate weekly totals (sum New/Updated/Archived across all entries this week). Also collect the most significant changes from each day's Changes section.

Then prepend a weekly section before the daily report:

```
📊 Weekly Summary

🧠 This week: +N new · ~N updated · -N archived
📈 MEMORY.md: N → N lines (N% growth)

📌 Biggest changes this week:
  1. {most significant entry from dream-log}
  2. {second}
  3. {third}

🧹 Cleanup: deleted N old logs, pruned N procedures, [rotated archive if applicable]

---
```

If dream-log.md has fewer than 7 days of entries, use whatever is available.

### Notification principles:
1. **Every notification must deliver value** — never send empty messages
2. **Show growth, not just changes** — before→after deltas make the system feel alive
3. **Surface forgotten context** — stale reminders and insights create surprise and utility

This reply is your ONLY output. Keep it concise and high-value.
