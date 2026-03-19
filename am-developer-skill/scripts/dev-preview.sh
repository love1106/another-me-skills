#!/bin/bash
# Start a Cloudflare tunnel for dev preview
# Usage: ./dev-preview.sh <port> [project-dir]

PORT=${1:-3000}
PROJECT_DIR=${2:-$(pwd)}

echo "🚀 Starting dev preview tunnel on port $PORT..."
echo "📁 Project: $PROJECT_DIR"

# Start cloudflare tunnel in background
cloudflared tunnel --url http://localhost:$PORT 2>&1 | while read line; do
  # Extract and display the tunnel URL
  if echo "$line" | grep -q "trycloudflare.com"; then
    URL=$(echo "$line" | grep -oP 'https://[a-z0-9-]+\.trycloudflare\.com')
    if [ -n "$URL" ]; then
      echo ""
      echo "✅ Preview ready: $URL"
      echo ""
    fi
  fi
  echo "$line"
done
