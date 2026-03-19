#!/bin/bash
# am-developer-skill — Claude Code CLI spawn wrapper
# Usage: spawn.sh <workdir> <model> <prompt> [session_id]
# Outputs: JSON result from Claude Code CLI
# Exit 0 = success, 1 = error
#
# Prerequisites:
# - A non-root user that can run claude CLI (bypassPermissions blocked for root)
#   Set CLAUDE_USER env var or defaults to "coder"
# - ANTHROPIC_API_KEY and ANTHROPIC_BASE_URL env vars

WORKDIR="${1:-.}"
MODEL="${2:-sonnet}"
PROMPT="$3"
SESSION_ID="${4:-}"  # optional: resume session
# Auto-detect non-root user: $CLAUDE_USER → coder → first non-system user → current user
if [ -n "$CLAUDE_USER" ]; then
  : # use env var
elif id "coder" &>/dev/null; then
  CLAUDE_USER="coder"
else
  # Find first non-system user (UID >= 1000)
  CLAUDE_USER=$(awk -F: '$3 >= 1000 && $3 < 65534 { print $1; exit }' /etc/passwd 2>/dev/null || echo "")
  if [ -z "$CLAUDE_USER" ]; then
    CLAUDE_USER=$(whoami)
  fi
fi

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

# Verify user exists
if ! id "$CLAUDE_USER" &>/dev/null; then
  echo "{\"type\":\"error\",\"is_error\":true,\"result\":\"User ${CLAUDE_USER} does not exist. Set CLAUDE_USER env var or create: useradd -m -s /bin/bash coder\"}"
  exit 1
fi

# If running as root and CLAUDE_USER is also root, warn and use acceptEdits
RUN_AS_ROOT=false
if [ "$CLAUDE_USER" = "root" ] || [ "$(id -u "$CLAUDE_USER")" = "0" ]; then
  RUN_AS_ROOT=true
fi

# Find claude binary
CLAUDE_BIN=$(which claude 2>/dev/null || echo "/usr/local/bin/claude")
if [ ! -x "$CLAUDE_BIN" ]; then
  echo '{"type":"error","is_error":true,"result":"claude CLI not found"}'
  exit 1
fi

# Ensure coder user can access and write to workdir
if [ -d "$WORKDIR" ]; then
  setfacl -R -m u:${CLAUDE_USER}:rwX "$WORKDIR" 2>/dev/null \
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

# Build CLI args — use acceptEdits if running as root (bypassPermissions blocked for root)
PERM_MODE="bypassPermissions"
if [ "$RUN_AS_ROOT" = true ]; then
  PERM_MODE="acceptEdits"
fi

if [ -n "$SESSION_ID" ]; then
  ESC_SESSION=$(escape_sq "$SESSION_ID")
  CLI_ARGS="--resume '${ESC_SESSION}' --permission-mode ${PERM_MODE} --output-format json --model '${ESC_MODEL}' -p"
else
  CLI_ARGS="--permission-mode ${PERM_MODE} --output-format json --model '${ESC_MODEL}' -p"
fi

# Determine if we need su (skip if CLAUDE_USER is current user)
CURRENT_USER=$(whoami)
USE_SU=true
if [ "$CLAUDE_USER" = "$CURRENT_USER" ]; then
  USE_SU=false
fi

# Helper: run command as CLAUDE_USER (or directly if same user)
run_as_user() {
  local CMD="$1"
  if [ "$USE_SU" = true ]; then
    su - "$CLAUDE_USER" -s /bin/bash -c "$CMD" 2>&1
  else
    bash -c "$CMD" 2>&1
  fi
}

# Run Claude CLI
if [ -n "$USE_FILE_INPUT" ]; then
  # Pipe from file — safe for prompts with special chars ($, backticks, quotes)
  chmod o+r "$USE_FILE_INPUT" 2>/dev/null || true
  OUTPUT=$(run_as_user "
    export ANTHROPIC_API_KEY='${ESC_API_KEY}'
    export ANTHROPIC_BASE_URL='${ESC_BASE_URL}'
    cd '${ESC_WORKDIR}' || { echo '{\"type\":\"error\",\"is_error\":true,\"result\":\"Cannot cd to workdir: ${ESC_WORKDIR}\"}'; exit 1; }
    cat '$(escape_sq "$USE_FILE_INPUT")' | ${CLAUDE_BIN} ${CLI_ARGS} -
  ")
  # Cleanup temp file if we created one
  [[ "$USE_FILE_INPUT" == /tmp/spawn-prompt-* ]] && rm -f "$USE_FILE_INPUT"
else
  OUTPUT=$(run_as_user "
    export ANTHROPIC_API_KEY='${ESC_API_KEY}'
    export ANTHROPIC_BASE_URL='${ESC_BASE_URL}'
    cd '${ESC_WORKDIR}' || { echo '{\"type\":\"error\",\"is_error\":true,\"result\":\"Cannot cd to workdir: ${ESC_WORKDIR}\"}'; exit 1; }
    ${CLAUDE_BIN} ${CLI_ARGS} '${ESC_PROMPT}'
  ")
fi

EXIT_CODE=$?

# If su/claude failed and output is not JSON, wrap in error JSON
if [ $EXIT_CODE -ne 0 ] && ! echo "$OUTPUT" | head -1 | grep -q '^{'; then
  echo "{\"type\":\"error\",\"is_error\":true,\"result\":\"CLI exited with code ${EXIT_CODE}: $(echo "$OUTPUT" | head -3 | tr '\n' ' ' | sed 's/"/\\"/g')\"}"
  exit 1
fi

echo "$OUTPUT"
exit $EXIT_CODE
