#!/usr/bin/env python3
"""
am-developer-skill — CLI Retrospect Tool
Parse cli-runs.jsonl, aggregate errors, generate report, auto-trim old entries.

Usage:
  retrospect.py [--days N] [--project NAME] [--all] [--trim-only]

Options:
  --days N       Filter last N days (default: 90)
  --project NAME Filter by project name
  --all          Include archived data
  --trim-only    Only trim old entries, no report
"""

import json
import sys
import os
import gzip
import shutil
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict
from pathlib import Path

# Paths
WORKSPACE = Path.home() / ".openclaw" / "workspace"
LOG_FILE = WORKSPACE / "memory" / "cli-runs.jsonl"
ARCHIVE_DIR = WORKSPACE / "memory" / "cli-runs-archive"

# Config
RETENTION_DAYS = 90
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def parse_args():
    args = {"days": RETENTION_DAYS, "project": None, "all": False, "trim_only": False}
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        if argv[i] == "--days" and i + 1 < len(argv):
            args["days"] = int(argv[i + 1])
            i += 2
        elif argv[i] == "--project" and i + 1 < len(argv):
            args["project"] = argv[i + 1]
            i += 2
        elif argv[i] == "--all":
            args["all"] = True
            i += 1
        elif argv[i] == "--trim-only":
            args["trim_only"] = True
            i += 1
        else:
            i += 1
    return args


def load_jsonl(filepath):
    """Load entries from a JSONL file (plain or gzipped)."""
    entries = []
    if not filepath.exists():
        return entries

    opener = gzip.open if str(filepath).endswith(".gz") else open
    try:
        with opener(filepath, "rt", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except (OSError, EOFError):
        pass
    return entries


def load_all_entries(include_archive=False):
    """Load entries from active log and optionally archives."""
    entries = load_jsonl(LOG_FILE)

    if include_archive and ARCHIVE_DIR.exists():
        for archive_file in sorted(ARCHIVE_DIR.glob("*.jsonl*")):
            entries.extend(load_jsonl(archive_file))

    return entries


def trim_and_archive():
    """Trim entries older than RETENTION_DAYS, archive them by quarter."""
    if not LOG_FILE.exists():
        return 0

    entries = load_jsonl(LOG_FILE)
    if not entries:
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)
    keep = []
    archive = []

    for entry in entries:
        try:
            ts = datetime.fromisoformat(entry["ts"].replace("Z", "+00:00"))
            if ts >= cutoff:
                keep.append(entry)
            else:
                archive.append(entry)
        except (KeyError, ValueError):
            keep.append(entry)  # Keep unparseable entries

    if not archive:
        # Also check file size — if over limit, archive oldest 50%
        file_size = LOG_FILE.stat().st_size
        if file_size > MAX_FILE_SIZE and len(keep) > 10:
            mid = len(keep) // 2
            archive = keep[:mid]
            keep = keep[mid:]
        else:
            return 0

    # Group archived entries by quarter
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    by_quarter = defaultdict(list)
    for entry in archive:
        try:
            ts = datetime.fromisoformat(entry["ts"].replace("Z", "+00:00"))
            quarter = f"Q{(ts.month - 1) // 3 + 1}"
            key = f"cli-runs-{ts.year}-{quarter}"
        except (KeyError, ValueError):
            key = "cli-runs-unknown"
        by_quarter[key].append(entry)

    for key, items in by_quarter.items():
        archive_path = ARCHIVE_DIR / f"{key}.jsonl.gz"

        # Append to existing archive if present
        existing = load_jsonl(archive_path) if archive_path.exists() else []
        existing.extend(items)

        with gzip.open(archive_path, "wt", encoding="utf-8") as f:
            for item in existing:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    # Rewrite active log with kept entries only
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        for entry in keep:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return len(archive)


def generate_report(entries, args):
    """Generate retrospect report from entries."""
    if not entries:
        print("No CLI runs found.")
        return

    # Filter by date
    cutoff = datetime.now(timezone.utc) - timedelta(days=args["days"])
    filtered = []
    for entry in entries:
        try:
            ts = datetime.fromisoformat(entry["ts"].replace("Z", "+00:00"))
            if ts >= cutoff:
                if args["project"] is None or entry.get("project", "") == args["project"]:
                    filtered.append(entry)
        except (KeyError, ValueError):
            continue

    if not filtered:
        print(f"No CLI runs in last {args['days']} days"
              + (f" for project '{args['project']}'" if args["project"] else "")
              + ".")
        return

    # Aggregate stats
    total = len(filtered)
    errors = [e for e in filtered if e.get("is_error", False)]
    successes = total - len(errors)
    retries = [e for e in filtered if e.get("attempt", 1) > 1]
    total_cost = sum(float(e.get("cost_usd", 0)) for e in filtered)
    total_duration = sum(int(e.get("duration_s", 0)) for e in filtered)

    # Error type breakdown
    error_types = Counter(e.get("error_type", "unknown") for e in errors if e.get("error_type"))
    
    # Project breakdown
    projects = Counter(e.get("project", "unknown") for e in filtered)

    # Model breakdown
    models = Counter(e.get("model", "unknown") for e in filtered)

    # Unresolved errors
    unresolved = [e for e in errors if not e.get("resolved", True)]

    # Repeated errors (same error_type + project combo > 2 times)
    error_combos = Counter(
        (e.get("error_type", "unknown"), e.get("project", "unknown"))
        for e in errors
    )
    repeated = {k: v for k, v in error_combos.items() if v >= 3}

    # Print report
    period = f"last {args['days']} days"
    project_filter = f" | project: {args['project']}" if args["project"] else ""

    print(f"""
CLI RETROSPECT ({period}{project_filter})
{'=' * 50}
Total runs:      {total}
Success:         {successes} ({successes * 100 // total}%)
Failed:          {len(errors)} ({len(errors) * 100 // total}%)
Retry attempts:  {len(retries)}
Total cost:      ${total_cost:.2f}
Total time:      {total_duration // 60}m {total_duration % 60}s

ERROR BREAKDOWN
{'-' * 30}""")

    if error_types:
        for err_type, count in error_types.most_common():
            print(f"  {err_type:<20} {count}x")
    else:
        print("  (none)")

    print(f"""
BY PROJECT
{'-' * 30}""")
    for proj, count in projects.most_common():
        proj_errors = sum(1 for e in errors if e.get("project") == proj)
        print(f"  {proj:<30} {count} runs, {proj_errors} errors")

    print(f"""
BY MODEL
{'-' * 30}""")
    for model, count in models.most_common():
        model_cost = sum(float(e.get("cost_usd", 0)) for e in filtered if e.get("model") == model)
        print(f"  {model:<15} {count} runs, ${model_cost:.2f}")

    if unresolved:
        print(f"""
⚠️  UNRESOLVED ERRORS ({len(unresolved)})
{'-' * 30}""")
        for e in unresolved[:10]:
            print(f"  [{e.get('ts', '?')[:10]}] {e.get('project', '?')} — {e.get('error_summary', 'no summary')}")

    if repeated:
        print(f"""
🔴 REPEATED PATTERNS (≥3 occurrences)
{'-' * 30}""")
        for (err_type, proj), count in sorted(repeated.items(), key=lambda x: -x[1]):
            print(f"  {err_type} in {proj}: {count}x → SUGGEST: add fix to spawn.sh or Lessons Learned")

    # Suggestions
    suggestions = []
    if error_types.get("permission", 0) >= 3:
        suggestions.append("permission errors recurring → review spawn.sh setfacl logic")
    if error_types.get("timeout", 0) >= 3:
        suggestions.append("timeout errors recurring → default to task splitting for large tasks")
    if error_types.get("smart_quotes", 0) >= 2:
        suggestions.append("smart quotes still appearing → add post-processing step in spawn.sh")
    if len(retries) / max(total, 1) > 0.3:
        suggestions.append(f"retry rate {len(retries)*100//total}% is high → review prompt strategy")
    if total_cost > 10:
        suggestions.append(f"total cost ${total_cost:.2f} — consider using sonnet more, opus less")

    if suggestions:
        print(f"""
💡 SUGGESTIONS
{'-' * 30}""")
        for s in suggestions:
            print(f"  → {s}")

    print()


def annotation_report():
    """Scan annotations: flag high-hit for promotion, stale for archiving."""
    ann_dir = WORKSPACE / "memory" / "am-developer-skill-annotations"
    if not ann_dir.exists():
        return

    files = list(ann_dir.glob("*.jsonl"))
    if not files:
        return

    total = 0
    active = 0
    high_hit = []  # hits > 10 → suggest promote
    stale = []     # last_hit > 180 days ago → suggest archive
    cutoff = (datetime.now(timezone.utc) - timedelta(days=180)).strftime("%Y-%m-%d")

    for f in sorted(files):
        project = f.stem
        for line in f.read_text().strip().split("\n"):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("archived", False):
                continue
            total += 1
            active += 1
            hits = entry.get("hits", 0)
            last_hit = entry.get("last_hit", entry.get("created", "9999-99-99"))
            if hits > 10:
                high_hit.append((project, entry))
            if last_hit < cutoff:
                stale.append((project, entry))

    print(f"""
📝 ANNOTATIONS ({active} active across {len(files)} project(s))
{'-' * 30}""")

    if high_hit:
        print(f"\n  🏆 HIGH-HIT (>{10} hits) → consider promoting to .claude/instructions.md:")
        for proj, e in high_hit:
            print(f"    [{proj}] {e['text'][:80]}  (hits: {e.get('hits', 0)})")

    if stale:
        print(f"\n  🕸️  STALE (no hit in 180+ days) → consider archiving:")
        for proj, e in stale:
            print(f"    [{proj}] {e['text'][:80]}  (last: {e.get('last_hit', '?')})")
        print(f"\n    Run: annotate.sh archive --project <name> --min-age-days 180")

    if not high_hit and not stale:
        print("  All annotations healthy — no action needed.")

    print()


def main():
    args = parse_args()

    # Always try trim
    archived_count = trim_and_archive()
    if archived_count > 0:
        print(f"📦 Archived {archived_count} old entries")

    if args["trim_only"]:
        return

    # Load entries
    entries = load_all_entries(include_archive=args["all"])

    # Generate report
    generate_report(entries, args)

    # Annotation report
    annotation_report()


if __name__ == "__main__":
    main()
