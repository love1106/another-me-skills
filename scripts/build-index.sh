#!/bin/bash
# Auto-generate index.json from all skill.json files
set -e
cd "$(dirname "$0")/.."

echo "["
first=true
for f in */skill.json; do
  [ -f "$f" ] || continue
  if [ "$first" = true ]; then
    first=false
  else
    echo ","
  fi
  cat "$f"
done
echo "]"
