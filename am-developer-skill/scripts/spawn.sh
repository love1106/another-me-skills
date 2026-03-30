#!/bin/bash
# am-developer-skill — Claude Code CLI spawn wrapper
# Usage: spawn.sh <workdir> <model> <prompt> [session_id] [timeout_seconds]
# Outputs: JSON result from Claude Code CLI
# Exit 0 = success, 1 = error (including timeout at exit code 124)
#
# Prerequisites:
# - Claude CLI installed and accessible
# - If running as root: set CLAUDE_USER env var (bypassPermissions blocked for root)
# - ANTHROPIC_API_KEY and ANTHROPIC_BASE_URL env vars

WORKDIR="${1:-.}"
MODEL="${2:-sonnet}"
PROMPT="$3"
SESSION_ID="${4:-}"  # optional: resume session
TIMEOUT="${5:-240}"  # optional: timeout in seconds (default 240s = 4min)

# --- Auto-log on exit ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPAWN_START=$(date +%s)
_auto_log_cli_run() {
  local end_ts=$(date +%s)
  local duration=$(( end_ts - SPAWN_START ))
  local log_exit_code="${SPAWN_EXIT_CODE:-1}"
  local log_error_summary="${SPAWN_ERROR_SUMMARY:-}"
  local log_session_id="${SPAWN_SESSION_ID:-$SESSION_ID}"
  local log_cost="${SPAWN_COST:-0}"
  local project_name
  project_name=$(basename "$WORKDIR" 2>/dev/null || echo "unknown")
  local task_summary
  task_summary=$(echo "$PROMPT" | head -c 200)

  bash "${SCRIPT_DIR}/log-cli-run.sh" \
    --project "$project_name" \
    --task "$task_summary" \
    --model "$MODEL" \
    --exit-code "$log_exit_code" \
    --error-summary "$log_error_summary" \
    --duration "$duration" \
    --cost "$log_cost" \
    --session-id "$log_session_id" \
    2>/dev/null || true
}
trap '_auto_log_cli_run' EXIT

if [ -z "$PROMPT" ]; then
  echo '{"type":"error","is_error":true,"result":"Missing prompt argument"}'
  exit 1
fi

# Support file input: @/path/to/prompt.md or - (stdin)
if [[ "$PROMPT" == @* ]]; then
  PROMPT_FILE="${PROMPT#@}"
  if [ ! -f "$PROMPT_FILE" ]; then
    echo "{\"type\":\"error\",\"is_error\":true,\"result\":\"Prompt file not found: ${PROMPT_FILE}\"}"
    exit 1
  fi
  USE_FILE_INPUT="$PROMPT_FILE"
  PROMPT=""  # will pipe from file
elif [ "$PROMPT" = "-" ]; then
  # Read stdin to temp file
  PROMPT_TMP=$(mktemp /tmp/spawn-prompt-XXXXXX.md)
  cat > "$PROMPT_TMP"
  USE_FILE_INPUT="$PROMPT_TMP"
  PROMPT=""
else
  USE_FILE_INPUT=""
fi

# Env vars should be set by caller or inherited
API_KEY="${ANTHROPIC_API_KEY:-}"
BASE_URL="${ANTHROPIC_BASE_URL:-}"

if [ -z "$API_KEY" ]; then
  echo '{"type":"error","is_error":true,"result":"ANTHROPIC_API_KEY not set"}'
  exit 1
fi

# Determine execution mode: direct or su to another user
# Root can't run claude CLI with bypassPermissions — need CLAUDE_USER
RUN_AS_USER=""
if [ "$(id -u)" = "0" ]; then
  CLAUDE_USER="${CLAUDE_USER:-coder}"
  if id "$CLAUDE_USER" &>/dev/null; then
    RUN_AS_USER="$CLAUDE_USER"
  else
    echo "{\"type\":\"error\",\"is_error\":true,\"result\":\"Running as root but CLAUDE_USER='${CLAUDE_USER}' does not exist. Create user or set CLAUDE_USER env var.\"}"
    exit 1
  fi
fi

# Find claude binary
if [ -n "$RUN_AS_USER" ]; then
  CLAUDE_BIN=$(su - "$RUN_AS_USER" -s /bin/bash -c "which claude 2>/dev/null" || echo "/usr/local/bin/claude")
  if [ -z "$CLAUDE_BIN" ] || ! su - "$RUN_AS_USER" -s /bin/bash -c "[ -x '$CLAUDE_BIN' ]" 2>/dev/null; then
    echo '{"type":"error","is_error":true,"result":"claude CLI not found for user '"$RUN_AS_USER"'"}'
    exit 1
  fi
else
  CLAUDE_BIN=$(which claude 2>/dev/null || echo "/usr/local/bin/claude")
  if [ ! -x "$CLAUDE_BIN" ]; then
    echo '{"type":"error","is_error":true,"result":"claude CLI not found"}'
    exit 1
  fi
fi

# Ensure target user can access workdir (only when su-ing)
if [ -n "$RUN_AS_USER" ] && [ -d "$WORKDIR" ]; then
  setfacl -R -m u:${RUN_AS_USER}:rwX "$WORKDIR" 2>/dev/null \
    || chmod -R o+rwX "$WORKDIR" 2>/dev/null \
    || true
fi

# Escape single quotes for safe injection into su -c '...'
escape_sq() { printf '%s' "$1" | sed "s/'/'\\\\''/g"; }

ESC_API_KEY=$(escape_sq "$API_KEY")
ESC_BASE_URL=$(escape_sq "$BASE_URL")
ESC_WORKDIR=$(escape_sq "$WORKDIR")
ESC_PROMPT=$(escape_sq "$PROMPT")
ESC_MODEL=$(escape_sq "$MODEL")

# Build CLI args
if [ -n "$SESSION_ID" ]; then
  ESC_SESSION=$(escape_sq "$SESSION_ID")
  CLI_ARGS="--resume '${ESC_SESSION}' --permission-mode bypassPermissions --output-format json --model '${ESC_MODEL}' -p"
else
  CLI_ARGS="--permission-mode bypassPermissions --output-format json --model '${ESC_MODEL}' -p"
fi

# Timeout wrapper
TIMEOUT_CMD=""
if command -v timeout &>/dev/null && [ "$TIMEOUT" -gt 0 ] 2>/dev/null; then
  TIMEOUT_CMD="timeout --signal=TERM --kill-after=10 ${TIMEOUT}"
fi

# Execute — either direct or via su
run_claude() {
  local input_source="$1"  # "file", "prompt", or empty
  
  if [ -n "$RUN_AS_USER" ]; then
    # Running as root → su to target user
    if [ "$input_source" = "file" ]; then
      chmod o+r "$USE_FILE_INPUT" 2>/dev/null || true
      $TIMEOUT_CMD su - "$RUN_AS_USER" -s /bin/bash -c "
        export ANTHROPIC_API_KEY='${ESC_API_KEY}'
        export ANTHROPIC_BASE_URL='${ESC_BASE_URL}'
        cd '${ESC_WORKDIR}' || { echo '{\"type\":\"error\",\"is_error\":true,\"result\":\"Cannot cd to workdir\"}'; exit 1; }
        cat '$(escape_sq "$USE_FILE_INPUT")' | ${CLAUDE_BIN} ${CLI_ARGS} -
      " 2>&1
    else
      $TIMEOUT_CMD su - "$RUN_AS_USER" -s /bin/bash -c "
        export ANTHROPIC_API_KEY='${ESC_API_KEY}'
        export ANTHROPIC_BASE_URL='${ESC_BASE_URL}'
        cd '${ESC_WORKDIR}' || { echo '{\"type\":\"error\",\"is_error\":true,\"result\":\"Cannot cd to workdir\"}'; exit 1; }
        ${CLAUDE_BIN} ${CLI_ARGS} '${ESC_PROMPT}'
      " 2>&1
    fi
  else
    # Running as non-root → direct execution
    export ANTHROPIC_API_KEY="$API_KEY"
    export ANTHROPIC_BASE_URL="$BASE_URL"
    cd "$WORKDIR" || { echo '{"type":"error","is_error":true,"result":"Cannot cd to workdir"}'; exit 1; }
    if [ "$input_source" = "file" ]; then
      $TIMEOUT_CMD cat "$USE_FILE_INPUT" | $CLAUDE_BIN $CLI_ARGS - 2>&1
    else
      $TIMEOUT_CMD $CLAUDE_BIN $CLI_ARGS "$PROMPT" 2>&1
    fi
  fi
}

if [ -n "$USE_FILE_INPUT" ]; then
  OUTPUT=$(run_claude "file")
  [[ "$USE_FILE_INPUT" == /tmp/spawn-prompt-* ]] && rm -f "$USE_FILE_INPUT"
else
  OUTPUT=$(run_claude "prompt")
fi

EXIT_CODE=$?

# Capture data for auto-log trap
SPAWN_EXIT_CODE=$EXIT_CODE

# Try to extract session_id and cost from JSON output
if echo "$OUTPUT" | tail -1 | grep -q '^{'; then
  SPAWN_SESSION_ID=$(echo "$OUTPUT" | tail -1 | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null || true)
  SPAWN_COST=$(echo "$OUTPUT" | tail -1 | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('cost_usd', d.get('total_cost_usd', 0)))" 2>/dev/null || true)
fi

# Detect timeout (exit code 124 from timeout command)
if [ $EXIT_CODE -eq 124 ]; then
  SPAWN_ERROR_SUMMARY="CLI timed out after ${TIMEOUT}s"
  echo "{\"type\":\"error\",\"is_error\":true,\"result\":\"CLI timed out after ${TIMEOUT}s. Task may be too large — consider splitting into smaller subtasks (Hard Rule #5).\"}"
  exit 1
fi

# If su/claude failed and output is not JSON, wrap in error JSON
if [ $EXIT_CODE -ne 0 ] && ! echo "$OUTPUT" | head -1 | grep -q '^{'; then
  SPAWN_ERROR_SUMMARY="CLI exited with code ${EXIT_CODE}"
  echo "{\"type\":\"error\",\"is_error\":true,\"result\":\"CLI exited with code ${EXIT_CODE}: $(echo "$OUTPUT" | head -3 | tr '\n' ' ' | sed 's/"/\\"/g')\"}"
  exit 1
fi

echo "$OUTPUT"
exit $EXIT_CODE
