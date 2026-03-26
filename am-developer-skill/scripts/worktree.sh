#!/bin/bash
# hc-developer-skill — Git Worktree Manager
# Manages worktrees + lockfiles to prevent session overlap on same repo.
#
# Usage:
#   worktree.sh acquire <repo_path> <branch_name>   → prints WORKDIR path (repo root or new worktree)
#   worktree.sh release <repo_path> <branch_name>   → releases lock, optionally removes worktree
#   worktree.sh status  <repo_path>                  → shows lock status + active worktrees
#   worktree.sh cleanup <repo_path>                  → removes merged/stale worktrees
#
# Lock mechanism:
#   <repo>/.git/openclaw-session.lock — contains session info (PID, timestamp, branch)
#   If lock exists + process alive → repo busy → create worktree
#   If lock exists + process dead → stale lock → reclaim
#
# Worktree naming:
#   <repo>--<branch-name>/   (sibling to repo dir)
#   e.g. ~/projects/my-app--feat-auth/

set -euo pipefail

ACTION="${1:-}"
REPO_PATH="${2:-}"
BRANCH_NAME="${3:-}"

# Resolve repo path
REPO_PATH=$(realpath "$REPO_PATH" 2>/dev/null || echo "$REPO_PATH")

# ─── Helpers ───

get_lock_file() {
  local repo="$1"
  # Support both regular repos and worktrees
  # --git-common-dir returns relative path → resolve to absolute
  local git_dir
  git_dir=$(cd "$repo" && git rev-parse --git-common-dir 2>/dev/null || echo ".git")
  # Make absolute if relative
  if [[ "$git_dir" != /* ]]; then
    git_dir="${repo}/${git_dir}"
  fi
  echo "${git_dir}/openclaw-session.lock"
}

is_lock_alive() {
  local lock_file="$1"
  if [ ! -f "$lock_file" ]; then
    return 1  # no lock
  fi
  local lock_pid
  # Match only ^pid= (not ppid=) to get exactly 1 value
  lock_pid=$(grep -oP '^pid=\K\d+' "$lock_file" 2>/dev/null | head -1 || echo "")
  if [ -z "$lock_pid" ]; then
    return 1  # malformed lock
  fi
  # Check if the process (or its parent shell) is still running
  if kill -0 "$lock_pid" 2>/dev/null; then
    return 0  # alive
  fi
  return 1  # dead
}

create_lock() {
  local lock_file="$1"
  local branch="$2"
  cat > "$lock_file" << EOF
pid=$$
ppid=$PPID
branch=${branch}
timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF
}

remove_lock() {
  local lock_file="$1"
  rm -f "$lock_file"
}

worktree_path_for_branch() {
  local repo="$1"
  local branch="$2"
  # Sanitize branch name: feat/my-thing → feat-my-thing
  local safe_branch
  safe_branch=$(echo "$branch" | tr '/' '-')
  # Place worktree as sibling: ~/projects/repo--branch/
  echo "${repo}--${safe_branch}"
}

# Check if branch already has a worktree
branch_has_worktree() {
  local repo="$1"
  local branch="$2"
  git -C "$repo" worktree list --porcelain 2>/dev/null | grep -q "branch refs/heads/${branch}$"
}

# ─── Actions ───

cmd_acquire() {
  if [ -z "$REPO_PATH" ] || [ -z "$BRANCH_NAME" ]; then
    echo "ERROR: Usage: worktree.sh acquire <repo_path> <branch_name>" >&2
    exit 1
  fi

  if [ ! -d "$REPO_PATH/.git" ] && [ ! -f "$REPO_PATH/.git" ]; then
    echo "ERROR: Not a git repo: $REPO_PATH" >&2
    exit 1
  fi

  local lock_file
  lock_file=$(get_lock_file "$REPO_PATH")

  # Case 1: No lock or stale lock → use repo directly
  if ! is_lock_alive "$lock_file"; then
    # Reclaim stale lock if exists
    [ -f "$lock_file" ] && remove_lock "$lock_file"

    # Check for uncommitted changes
    local dirty
    dirty=$(git -C "$REPO_PATH" status --porcelain 2>/dev/null | head -1)
    if [ -n "$dirty" ]; then
      echo "WARN: Repo has uncommitted changes, stashing..." >&2
      git -C "$REPO_PATH" stash --include-untracked 2>/dev/null || true
    fi

    create_lock "$lock_file" "$BRANCH_NAME"
    echo "$REPO_PATH"
    return 0
  fi

  # Case 2: Lock alive → need worktree
  local lock_branch
  lock_branch=$(grep -oP 'branch=\K.*' "$lock_file" 2>/dev/null || echo "unknown")
  echo "INFO: Repo locked by branch '${lock_branch}', creating worktree..." >&2

  # Check if branch already has a worktree somewhere
  if branch_has_worktree "$REPO_PATH" "$BRANCH_NAME"; then
    local wt_path
    wt_path=$(git -C "$REPO_PATH" worktree list --porcelain 2>/dev/null \
      | grep -B2 "branch refs/heads/${BRANCH_NAME}$" \
      | grep "^worktree " | sed 's/^worktree //')
    if [ -n "$wt_path" ] && [ -d "$wt_path" ]; then
      local wt_lock
      wt_lock=$(get_lock_file "$wt_path")
      if ! is_lock_alive "$wt_lock"; then
        [ -f "$wt_lock" ] && remove_lock "$wt_lock"
        create_lock "$wt_lock" "$BRANCH_NAME"
        echo "$wt_path"
        return 0
      fi
      echo "ERROR: Branch '${BRANCH_NAME}' worktree also locked" >&2
      exit 1
    fi
  fi

  # Create new worktree
  local wt_path
  wt_path=$(worktree_path_for_branch "$REPO_PATH" "$BRANCH_NAME")

  # Fetch latest before creating worktree
  git -C "$REPO_PATH" fetch origin 2>/dev/null || true

  # Determine base: default branch
  local default_branch
  default_branch=$(git -C "$REPO_PATH" symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
  if [ -z "$default_branch" ]; then
    default_branch=$(git -C "$REPO_PATH" branch -r 2>/dev/null | grep -E 'origin/(main|master)' | head -1 | sed 's|.*origin/||' | xargs)
    default_branch=${default_branch:-main}
  fi

  if git -C "$REPO_PATH" show-ref --verify --quiet "refs/heads/${BRANCH_NAME}" 2>/dev/null; then
    # Branch exists locally → create worktree from it
    git -C "$REPO_PATH" worktree add "$wt_path" "$BRANCH_NAME" 2>/dev/null
  else
    # New branch → create from default branch
    git -C "$REPO_PATH" worktree add -b "$BRANCH_NAME" "$wt_path" "origin/${default_branch}" 2>/dev/null
  fi

  if [ $? -ne 0 ] || [ ! -d "$wt_path" ]; then
    echo "ERROR: Failed to create worktree at $wt_path" >&2
    exit 1
  fi

  # Lock the worktree
  local wt_lock
  wt_lock=$(get_lock_file "$wt_path")
  create_lock "$wt_lock" "$BRANCH_NAME"

  echo "$wt_path"
}

cmd_release() {
  if [ -z "$REPO_PATH" ] || [ -z "$BRANCH_NAME" ]; then
    echo "ERROR: Usage: worktree.sh release <repo_path> <branch_name>" >&2
    exit 1
  fi

  # Find the workdir for this branch (could be repo itself or a worktree)
  local lock_file
  lock_file=$(get_lock_file "$REPO_PATH")

  # Check if the main repo holds this branch
  if [ -f "$lock_file" ]; then
    local lock_branch
    lock_branch=$(grep -oP 'branch=\K.*' "$lock_file" 2>/dev/null || echo "")
    if [ "$lock_branch" = "$BRANCH_NAME" ]; then
      remove_lock "$lock_file"
      echo "Released lock on $REPO_PATH (branch: $BRANCH_NAME)"
      return 0
    fi
  fi

  # Check worktrees
  local wt_path
  wt_path=$(worktree_path_for_branch "$REPO_PATH" "$BRANCH_NAME")
  if [ -d "$wt_path" ]; then
    local wt_lock
    wt_lock=$(get_lock_file "$wt_path")
    remove_lock "$wt_lock"
    echo "Released lock on worktree $wt_path (branch: $BRANCH_NAME)"
    return 0
  fi

  echo "WARN: No lock found for branch '$BRANCH_NAME'" >&2
}

cmd_status() {
  if [ -z "$REPO_PATH" ]; then
    echo "ERROR: Usage: worktree.sh status <repo_path>" >&2
    exit 1
  fi

  echo "=== Repo: $REPO_PATH ==="

  # Main repo lock
  local lock_file
  lock_file=$(get_lock_file "$REPO_PATH")
  if [ -f "$lock_file" ]; then
    if is_lock_alive "$lock_file"; then
      echo "  Main repo: LOCKED ($(cat "$lock_file" | tr '\n' ', '))"
    else
      echo "  Main repo: STALE LOCK (process dead)"
    fi
  else
    echo "  Main repo: FREE"
  fi

  # Worktrees
  echo ""
  echo "  Worktrees:"
  git -C "$REPO_PATH" worktree list 2>/dev/null | while read -r line; do
    local wt_dir
    wt_dir=$(echo "$line" | awk '{print $1}')
    if [ "$wt_dir" = "$REPO_PATH" ]; then
      continue  # skip main
    fi
    local wt_lock
    wt_lock="${wt_dir}/.git/openclaw-session.lock"
    # For linked worktrees, .git is a file pointing to gitdir
    if [ -f "$wt_dir/.git" ]; then
      local gitdir
      gitdir=$(cat "$wt_dir/.git" | sed 's/gitdir: //')
      wt_lock="${gitdir}/openclaw-session.lock"
    fi
    if [ -f "$wt_lock" ] && is_lock_alive "$wt_lock"; then
      echo "    $line — LOCKED"
    else
      echo "    $line — FREE"
    fi
  done
}

cmd_cleanup() {
  if [ -z "$REPO_PATH" ]; then
    echo "ERROR: Usage: worktree.sh cleanup <repo_path>" >&2
    exit 1
  fi

  local cleaned=0

  # Find sibling worktree directories
  local repo_base
  repo_base=$(basename "$REPO_PATH")
  local repo_parent
  repo_parent=$(dirname "$REPO_PATH")

  for wt_dir in "${repo_parent}/${repo_base}--"*/; do
    [ -d "$wt_dir" ] || continue
    wt_dir="${wt_dir%/}"  # remove trailing slash

    # Skip if locked and alive
    local wt_lock
    wt_lock=$(get_lock_file "$wt_dir" 2>/dev/null || echo "")
    if [ -n "$wt_lock" ] && is_lock_alive "$wt_lock"; then
      echo "SKIP: $wt_dir (locked, in use)"
      continue
    fi

    # Check if branch was merged
    local wt_branch
    wt_branch=$(git -C "$wt_dir" branch --show-current 2>/dev/null || echo "")
    
    echo "Removing worktree: $wt_dir (branch: $wt_branch)"
    git -C "$REPO_PATH" worktree remove "$wt_dir" --force 2>/dev/null || rm -rf "$wt_dir"
    cleaned=$((cleaned + 1))
  done

  echo "Cleaned up $cleaned worktree(s)"
  
  # Prune stale worktree references
  git -C "$REPO_PATH" worktree prune 2>/dev/null || true
}

# ─── Main ───

case "$ACTION" in
  acquire)  cmd_acquire ;;
  release)  cmd_release ;;
  status)   cmd_status ;;
  cleanup)  cmd_cleanup ;;
  *)
    echo "Usage: worktree.sh <acquire|release|status|cleanup> <repo_path> [branch_name]" >&2
    exit 1
    ;;
esac
