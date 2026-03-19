#!/bin/bash
# am-developer-skill — Log Claude CLI run result to JSONL
# Usage: log-cli-run.sh [options]
#   --project <name>       Project/repo name
#   --task <description>   Task description
#   --model <model>        Model used (sonnet/opus)
#   --exit-code <N>        CLI exit code
#   --error-type <type>    Error classification (see error-taxonomy.md)
#   --error-summary <text> Short error description
#   --duration <seconds>   Run duration in seconds
#   --cost <usd>           Cost in USD (from CLI output)
#   --attempt <N>          Retry attempt number (1-based)
#   --retry-strategy <text> Strategy used for this attempt
#   --resolved <bool>      Whether error was resolved
#   --resolution <text>    How it was resolved
#   --session-id <uuid>    Claude CLI session ID
#
# Output: Appends 1 JSON line to ~/.openclaw/workspace/memory/cli-runs.jsonl

LOG_FILE="${HOME}/.openclaw/workspace/memory/cli-runs.jsonl"

# Defaults
PROJECT=""
TASK=""
MODEL="sonnet"
EXIT_CODE=0
ERROR_TYPE=""
ERROR_SUMMARY=""
DURATION=0
COST="0"
ATTEMPT=1
RETRY_STRATEGY=""
RESOLVED="true"
RESOLUTION=""
SESSION_ID=""

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --project) PROJECT="$2"; shift 2 ;;
    --task) TASK="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --exit-code) EXIT_CODE="$2"; shift 2 ;;
    --error-type) ERROR_TYPE="$2"; shift 2 ;;
    --error-summary) ERROR_SUMMARY="$2"; shift 2 ;;
    --duration) DURATION="$2"; shift 2 ;;
    --cost) COST="$2"; shift 2 ;;
    --attempt) ATTEMPT="$2"; shift 2 ;;
    --retry-strategy) RETRY_STRATEGY="$2"; shift 2 ;;
    --resolved) RESOLVED="$2"; shift 2 ;;
    --resolution) RESOLUTION="$2"; shift 2 ;;
    --session-id) SESSION_ID="$2"; shift 2 ;;
    *) shift ;;
  esac
done

# Determine is_error
IS_ERROR="false"
if [ "$EXIT_CODE" -ne 0 ] 2>/dev/null; then
  IS_ERROR="true"
fi

# Timestamp in ISO 8601 with timezone
TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Escape strings for JSON (handle quotes and newlines)
json_escape() {
  printf '%s' "$1" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()), end="")'
}

# Build JSON line
cat >> "$LOG_FILE" <<EOF
{"ts":"${TS}","project":$(json_escape "$PROJECT"),"task":$(json_escape "$TASK"),"model":"${MODEL}","exit_code":${EXIT_CODE},"is_error":${IS_ERROR},"error_type":$(json_escape "$ERROR_TYPE"),"error_summary":$(json_escape "$ERROR_SUMMARY"),"attempt":${ATTEMPT},"retry_strategy":$(json_escape "$RETRY_STRATEGY"),"resolved":${RESOLVED},"resolution":$(json_escape "$RESOLUTION"),"duration_s":${DURATION},"cost_usd":${COST},"session_id":$(json_escape "$SESSION_ID")}
EOF

echo "Logged CLI run → ${LOG_FILE}"
