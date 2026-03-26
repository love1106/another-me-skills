#!/bin/bash
# Detect project environment: DEFAULT_BRANCH + PM (package manager)
# Usage: source detect-env.sh (from project root)

DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
if [ -z "$DEFAULT_BRANCH" ]; then
  DEFAULT_BRANCH=$(git branch -r 2>/dev/null | grep -E 'origin/(main|master)' | head -1 | sed 's|.*origin/||')
  DEFAULT_BRANCH=${DEFAULT_BRANCH:-main}
fi

if [ -f pnpm-lock.yaml ]; then PM="pnpm"
elif [ -f yarn.lock ]; then PM="yarn"
elif [ -f bun.lockb ]; then PM="bun"
else PM="npm"; fi

export DEFAULT_BRANCH PM
