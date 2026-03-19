#!/bin/bash
# hc-developer-skill — Manage per-project annotations (learning loop)
#
# Usage:
#   annotate.sh add    --project <name> [--scope <module>] --text <note> [--tags <t1,t2>]
#   annotate.sh list   --project <name> [--scope <module>] [--tags <t1,t2>] [--limit N]
#   annotate.sh search --project <name> --query <text> [--limit N]
#   annotate.sh hit    --project <name> --id <ann-id>         # bump hit counter
#   annotate.sh remove --project <name> --id <ann-id>
#   annotate.sh archive --project <name> [--before <YYYY-MM-DD>] [--min-age-days N]
#   annotate.sh inject --project <name> [--scope <module>] [--tags <t1,t2>] [--query <text>] [--limit N]
#                      # Output formatted block to stdout, IDs to stderr (INJECTED_IDS:id1,id2,...)
#   annotate.sh stats  [--project <name>]                     # summary stats
#
# Annotations stored in: ~/.openclaw/workspace/memory/hc-developer-skill-annotations/<project>.jsonl
#
# Entry format (JSONL):
# {
#   "id": "ann-<timestamp>",
#   "project": "<name>",
#   "scope": "<module/area>",
#   "text": "<the annotation>",
#   "tags": ["tag1", "tag2"],
#   "source": "manual|auto-retry|auto-discovery|retrospect",
#   "created": "2026-03-19",
#   "last_hit": "2026-03-19",
#   "hits": 0,
#   "archived": false
# }

set -euo pipefail

ANNOTATIONS_DIR="${HOME}/.openclaw/workspace/memory/hc-developer-skill-annotations"
mkdir -p "$ANNOTATIONS_DIR"

# --- Helpers ---

json_escape() {
  printf '%s' "$1" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()), end="")'
}

get_file() {
  echo "${ANNOTATIONS_DIR}/${1}.jsonl"
}

gen_id() {
  echo "ann-$(date +%s)-$((RANDOM % 1000))"
}

today() {
  date -u +"%Y-%m-%d"
}

# --- Commands ---

cmd_add() {
  local project="" scope="" text="" tags="" source="manual"

  while [[ $# -gt 0 ]]; do
    case $1 in
      --project) project="$2"; shift 2 ;;
      --scope) scope="$2"; shift 2 ;;
      --text) text="$2"; shift 2 ;;
      --tags) tags="$2"; shift 2 ;;
      --source) source="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$project" || -z "$text" ]]; then
    echo "ERROR: --project and --text required" >&2
    exit 1
  fi

  # Truncate text to 500 chars max — annotations must be concise
  if [[ ${#text} -gt 500 ]]; then
    text="${text:0:497}..."
  fi

  local file
  file=$(get_file "$project")

  # Dedup: skip if very similar annotation exists (>80% word overlap)
  if [[ -f "$file" ]]; then
    local is_dup
    is_dup=$(_PY_TEXT="$text" _PY_FILE="$file" python3 << 'PYEOF'
import json, os

new_words = set(os.environ['_PY_TEXT'].lower().split())
filepath = os.environ['_PY_FILE']
if not new_words:
    print("no")
    exit()

for line in open(filepath):
    line = line.strip()
    if not line: continue
    try:
        entry = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        continue
    if entry.get('archived', False): continue
    existing_words = set(entry.get('text', '').lower().split())
    if not existing_words: continue
    overlap = len(new_words & existing_words)
    similarity = overlap / max(len(new_words), len(existing_words))
    if similarity >= 0.8:
        print("dup:" + entry.get('id', ''))
        exit()
print("no")
PYEOF
)
    if [[ "$is_dup" == dup:* ]]; then
      echo "DUPLICATE (similar to ${is_dup#dup:})" >&2
      echo "${is_dup#dup:}"
      return 0
    fi
  fi

  local id
  id=$(gen_id)
  local today_str
  today_str=$(today)

  # Convert comma-separated tags to JSON array
  local tags_json="[]"
  if [[ -n "$tags" ]]; then
    tags_json=$(echo "$tags" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip().split(",")))')
  fi

  cat >> "$file" <<EOF
{"id":"${id}","project":$(json_escape "$project"),"scope":$(json_escape "$scope"),"text":$(json_escape "$text"),"tags":${tags_json},"source":"${source}","created":"${today_str}","last_hit":"${today_str}","hits":0,"archived":false}
EOF

  echo "${id}"
}

cmd_list() {
  local project="" scope="" tags="" limit=20

  while [[ $# -gt 0 ]]; do
    case $1 in
      --project) project="$2"; shift 2 ;;
      --scope) scope="$2"; shift 2 ;;
      --tags) tags="$2"; shift 2 ;;
      --limit) limit="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$project" ]]; then
    echo "ERROR: --project required" >&2
    exit 1
  fi

  local file
  file=$(get_file "$project")
  [[ ! -f "$file" ]] && exit 0

  _PY_SCOPE="$scope" _PY_TAGS="$tags" _PY_LIMIT="$limit" _PY_FILE="$file" python3 << 'PYEOF'
import json, os

scope = os.environ.get('_PY_SCOPE', '')
tags = set(os.environ['_PY_TAGS'].split(',')) if os.environ.get('_PY_TAGS') else set()
limit = int(os.environ.get('_PY_LIMIT', '20'))
filepath = os.environ['_PY_FILE']

results = []
for line in open(filepath):
    line = line.strip()
    if not line:
        continue
    try:
        entry = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        continue
    if entry.get('archived', False):
        continue
    if scope and entry.get('scope', '') != scope:
        continue
    if tags and not tags.intersection(set(entry.get('tags', []))):
        continue
    results.append(entry)

results.sort(key=lambda x: (x.get('hits', 0), x.get('created', '')), reverse=True)

for entry in results[:limit]:
    print(json.dumps(entry))
PYEOF
}

cmd_search() {
  local project="" query="" limit=10

  while [[ $# -gt 0 ]]; do
    case $1 in
      --project) project="$2"; shift 2 ;;
      --query) query="$2"; shift 2 ;;
      --limit) limit="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$project" || -z "$query" ]]; then
    echo "ERROR: --project and --query required" >&2
    exit 1
  fi

  local file
  file=$(get_file "$project")
  [[ ! -f "$file" ]] && exit 0

  _PY_QUERY="$query" _PY_LIMIT="$limit" _PY_FILE="$file" python3 << 'PYEOF'
import json, os

query_terms = os.environ['_PY_QUERY'].lower().split()
limit = int(os.environ.get('_PY_LIMIT', '10'))
filepath = os.environ['_PY_FILE']

results = []
for line in open(filepath):
    line = line.strip()
    if not line:
        continue
    try:
        entry = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        continue
    if entry.get('archived', False):
        continue
    searchable = (entry.get('text', '') + ' ' + entry.get('scope', '') + ' ' + ' '.join(entry.get('tags', []))).lower()
    score = sum(1 for t in query_terms if t in searchable)
    if score > 0:
        results.append((score, entry))

results.sort(key=lambda x: (x[0], x[1].get('hits', 0)), reverse=True)

for score, entry in results[:limit]:
    print(json.dumps(entry))
PYEOF
}

cmd_hit() {
  local project="" id=""

  while [[ $# -gt 0 ]]; do
    case $1 in
      --project) project="$2"; shift 2 ;;
      --id) id="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$project" || -z "$id" ]]; then
    echo "ERROR: --project and --id required" >&2
    exit 1
  fi

  local file
  file=$(get_file "$project")
  [[ ! -f "$file" ]] && exit 0

  local today_str
  today_str=$(today)

  _PY_ID="$id" _PY_TODAY="$today_str" _PY_FILE="$file" python3 << 'PYEOF'
import json, os

target_id = os.environ['_PY_ID']
today_str = os.environ['_PY_TODAY']
filepath = os.environ['_PY_FILE']

lines = []
found = False
for line in open(filepath):
    line = line.strip()
    if not line:
        continue
    try:
        entry = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        continue
    if entry['id'] == target_id:
        entry['hits'] = entry.get('hits', 0) + 1
        entry['last_hit'] = today_str
        found = True
    lines.append(json.dumps(entry, ensure_ascii=False))

with open(filepath, 'w') as f:
    f.write('\n'.join(lines) + '\n')

print('HIT' if found else 'NOT_FOUND')
PYEOF
}

cmd_remove() {
  local project="" id=""

  while [[ $# -gt 0 ]]; do
    case $1 in
      --project) project="$2"; shift 2 ;;
      --id) id="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$project" || -z "$id" ]]; then
    echo "ERROR: --project and --id required" >&2
    exit 1
  fi

  local file
  file=$(get_file "$project")
  [[ ! -f "$file" ]] && exit 0

  _PY_ID="$id" _PY_FILE="$file" python3 << 'PYEOF'
import json, os

target_id = os.environ['_PY_ID']
filepath = os.environ['_PY_FILE']

lines = []
removed = False
for line in open(filepath):
    line = line.strip()
    if not line:
        continue
    try:
        entry = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        continue
    if entry['id'] == target_id:
        removed = True
        continue
    lines.append(json.dumps(entry, ensure_ascii=False))

with open(filepath, 'w') as f:
    if lines:
        f.write('\n'.join(lines) + '\n')

print('REMOVED' if removed else 'NOT_FOUND')
PYEOF
}

cmd_archive() {
  local project="" before="" min_age_days=180

  while [[ $# -gt 0 ]]; do
    case $1 in
      --project) project="$2"; shift 2 ;;
      --before) before="$2"; shift 2 ;;
      --min-age-days) min_age_days="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$project" ]]; then
    echo "ERROR: --project required" >&2
    exit 1
  fi

  local file
  file=$(get_file "$project")
  [[ ! -f "$file" ]] && exit 0

  _PY_BEFORE="$before" _PY_MIN_AGE="$min_age_days" _PY_FILE="$file" python3 << 'PYEOF'
import json, os
from datetime import datetime, timedelta

before = os.environ.get('_PY_BEFORE') or None
min_age_days = int(os.environ.get('_PY_MIN_AGE', '180'))
filepath = os.environ['_PY_FILE']
cutoff = before or (datetime.utcnow() - timedelta(days=min_age_days)).strftime('%Y-%m-%d')

lines = []
archived_count = 0
for line in open(filepath):
    line = line.strip()
    if not line:
        continue
    try:
        entry = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        continue
    if not entry.get('archived', False):
        last_hit = entry.get('last_hit', entry.get('created', '9999-99-99'))
        if last_hit < cutoff:
            entry['archived'] = True
            archived_count += 1
    lines.append(json.dumps(entry, ensure_ascii=False))

with open(filepath, 'w') as f:
    f.write('\n'.join(lines) + '\n')

print(f'Archived {archived_count} annotations (cutoff: {cutoff})')
PYEOF
}

cmd_inject() {
  local project="" scope="" tags="" query="" limit=5

  while [[ $# -gt 0 ]]; do
    case $1 in
      --project) project="$2"; shift 2 ;;
      --scope) scope="$2"; shift 2 ;;
      --tags) tags="$2"; shift 2 ;;
      --query) query="$2"; shift 2 ;;
      --limit) limit="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  if [[ -z "$project" ]]; then
    echo "ERROR: --project required" >&2
    exit 1
  fi

  local file
  file=$(get_file "$project")
  [[ ! -f "$file" ]] && { exit 0; }

  _PY_SCOPE="$scope" _PY_TAGS="$tags" _PY_QUERY="$query" _PY_LIMIT="$limit" _PY_FILE="$file" python3 << 'PYEOF'
import json, os, sys

scope = os.environ.get('_PY_SCOPE', '')
tags = set(os.environ['_PY_TAGS'].split(',')) if os.environ.get('_PY_TAGS') else set()
query_terms = os.environ['_PY_QUERY'].lower().split() if os.environ.get('_PY_QUERY') else []
limit = int(os.environ.get('_PY_LIMIT', '10'))
filepath = os.environ['_PY_FILE']

results = []
for line in open(filepath):
    line = line.strip()
    if not line:
        continue
    try:
        entry = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        continue
    if entry.get('archived', False):
        continue

    # Score: scope match (3pts) + tag overlap (1pt each) + query match (2pts each) + hits (0.1pt each)
    score = 0
    if scope and entry.get('scope', '') == scope:
        score += 3
    if tags:
        overlap = tags.intersection(set(entry.get('tags', [])))
        score += len(overlap)
    if query_terms:
        searchable = (entry.get('text', '') + ' ' + entry.get('scope', '') + ' ' + ' '.join(entry.get('tags', []))).lower()
        matched = sum(1 for t in query_terms if t in searchable)
        score += matched * 2
    score += entry.get('hits', 0) * 0.1

    # Include if any relevance, or if no filters (show all)
    has_filter = bool(scope or tags or query_terms)
    if score > 0 or not has_filter:
        results.append((score, entry))

results.sort(key=lambda x: x[0], reverse=True)
top = results[:limit]

if not top:
    sys.exit(0)

# Compact output — minimal tokens, max signal
# Format: "GOTCHAS:\n- text [scope]" (no header bloat, no tags in output)
print('GOTCHAS:')
for _, entry in top:
    scope_tag = f' [{entry["scope"]}]' if entry.get('scope') else ''
    print(f'- {entry["text"]}{scope_tag}')

# Output injected IDs to stderr for hit tracking
ids = [e["id"] for _, e in top if "id" in e]
if ids:
    sys.stderr.write("INJECTED_IDS:" + ",".join(ids) + "\n")
PYEOF
}

cmd_stats() {
  local project=""

  while [[ $# -gt 0 ]]; do
    case $1 in
      --project) project="$2"; shift 2 ;;
      *) shift ;;
    esac
  done

  _PY_DIR="$ANNOTATIONS_DIR" _PY_PROJECT="$project" python3 << 'PYEOF'
import json, os, glob

annotations_dir = os.environ['_PY_DIR']
project_filter = os.environ.get('_PY_PROJECT', '')

files = glob.glob(os.path.join(annotations_dir, '*.jsonl'))
if project_filter:
    files = [f for f in files if os.path.basename(f) == project_filter + '.jsonl']

total = 0
active = 0
archived = 0
total_hits = 0
by_project = {}

for f in sorted(files):
    pname = os.path.basename(f).replace('.jsonl', '')
    p_active = 0
    p_archived = 0
    p_hits = 0
    for line in open(f):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        total += 1
        if entry.get('archived', False):
            archived += 1
            p_archived += 1
        else:
            active += 1
            p_active += 1
            p_hits += entry.get('hits', 0)
            total_hits += entry.get('hits', 0)
    by_project[pname] = {'active': p_active, 'archived': p_archived, 'hits': p_hits}

print('ANNOTATION STATS')
print('================')
print(f'Total: {total} ({active} active, {archived} archived)')
print(f'Total hits: {total_hits}')
print()
if by_project:
    print(f'{"Project":<30} {"Active":>7} {"Archived":>9} {"Hits":>6}')
    print('-' * 55)
    for p, s in sorted(by_project.items()):
        print(f'{p:<30} {s["active"]:>7} {s["archived"]:>9} {s["hits"]:>6}')
else:
    print('No annotations yet.')
PYEOF
}

# --- Main ---

ACTION="${1:-help}"
shift || true

case "$ACTION" in
  add)     cmd_add "$@" ;;
  list)    cmd_list "$@" ;;
  search)  cmd_search "$@" ;;
  hit)     cmd_hit "$@" ;;
  remove)  cmd_remove "$@" ;;
  archive) cmd_archive "$@" ;;
  inject)  cmd_inject "$@" ;;
  stats)   cmd_stats "$@" ;;
  help|*)
    echo "Usage: annotate.sh <command> [options]"
    echo ""
    echo "Commands:"
    echo "  add      Add annotation (--project, --text required)"
    echo "  list     List annotations (--project required)"
    echo "  search   Search annotations (--project, --query required)"
    echo "  hit      Bump hit counter (--project, --id required)"
    echo "  remove   Remove annotation (--project, --id required)"
    echo "  archive  Archive old annotations (--project required)"
    echo "  inject   Output formatted block for Claude CLI prompt (--project required)"
    echo "  stats    Show annotation stats (--project optional)"
    ;;
esac
