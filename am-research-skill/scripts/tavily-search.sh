#!/usr/bin/env bash
# Tavily Search API wrapper
# Usage: search.sh "<query>" [max_results] [search_depth]
# search_depth: "basic" (default) or "advanced"
# Requires: TAVILY_API_KEY in ~/.env or environment

set -euo pipefail

[ -f ~/.env ] && source ~/.env

QUERY="${1:?Usage: search.sh '<query>' [max_results] [search_depth]}"
MAX_RESULTS="${2:-5}"
SEARCH_DEPTH="${3:-basic}"

: "${TAVILY_API_KEY:?TAVILY_API_KEY not set}"

curl -s "https://api.tavily.com/search" \
  -H "Content-Type: application/json" \
  -d "{
    \"api_key\": \"${TAVILY_API_KEY}\",
    \"query\": $(printf '%s' "$QUERY" | jq -Rs .),
    \"max_results\": ${MAX_RESULTS},
    \"search_depth\": \"${SEARCH_DEPTH}\",
    \"include_answer\": true,
    \"include_raw_content\": false
  }" | jq '{
    answer: .answer,
    results: [.results[] | {title, url, content, score}]
  }'
