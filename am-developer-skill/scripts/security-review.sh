#!/usr/bin/env bash
# Claude Code Security Review — local repo scanner
# Adapted from https://github.com/anthropics/claude-code-security-review
#
# Usage:
#   bash security-review.sh <repo_path> [output_json] [base_branch] [head_branch]
#
# Examples:
#   bash security-review.sh /root/projects/my-api
#   bash security-review.sh /root/projects/my-api /tmp/results.json
#   bash security-review.sh /root/projects/my-api /tmp/results.json main feat/new-feature

set -euo pipefail

REPO_PATH="${1:-.}"
OUTPUT_FILE="${2:-/tmp/security-review-$(date +%Y%m%d-%H%M%S).json}"
BASE_BRANCH="${3:-}"
HEAD_BRANCH="${4:-}"

CLAUDE_MODEL="${CLAUDE_MODEL:-claude-sonnet-4-6}"
CLAUDE_TIMEOUT="${CLAUDE_TIMEOUT:-600}"
EXCLUDE_DIRS="${EXCLUDE_DIRS:-node_modules,dist,.git,.next,__pycache__,coverage}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Validate
if [ ! -d "$REPO_PATH" ]; then
  echo "❌ Directory not found: $REPO_PATH" >&2
  exit 1
fi

if ! command -v claude &>/dev/null; then
  echo "❌ claude CLI not found. Install: npm install -g @anthropic-ai/claude-code" >&2
  exit 1
fi

REPO_PATH="$(cd "$REPO_PATH" && pwd)"
echo "🔒 Security Review: $REPO_PATH" >&2
echo "📋 Model: $CLAUDE_MODEL | Timeout: ${CLAUDE_TIMEOUT}s" >&2
echo "📁 Output: $OUTPUT_FILE" >&2

# Build file list or diff
if [ -n "$BASE_BRANCH" ] && [ -n "$HEAD_BRANCH" ]; then
  echo "🔀 Diff mode: $BASE_BRANCH → $HEAD_BRANCH" >&2
  DIFF_CONTENT=$(cd "$REPO_PATH" && git diff "$BASE_BRANCH...$HEAD_BRANCH" -- . ':!node_modules' ':!dist' ':!.git' 2>/dev/null || echo "")
  FILES_CHANGED=$(cd "$REPO_PATH" && git diff --name-only "$BASE_BRANCH...$HEAD_BRANCH" 2>/dev/null | head -100 || echo "")
  
  if [ -z "$DIFF_CONTENT" ]; then
    echo "⚠️  No diff found, falling back to full scan" >&2
    DIFF_CONTENT=""
  fi
else
  DIFF_CONTENT=""
  FILES_CHANGED=""
fi

# Build exclude pattern for find
IFS=',' read -ra EXCL_ARRAY <<< "$EXCLUDE_DIRS"
FIND_EXCLUDES=""
for dir in "${EXCL_ARRAY[@]}"; do
  FIND_EXCLUDES="$FIND_EXCLUDES -path '*/$dir' -prune -o"
done

# Get file tree (limited)
FILE_TREE=$(cd "$REPO_PATH" && eval "find . $FIND_EXCLUDES -type f -name '*.ts' -o -name '*.js' -o -name '*.py' -o -name '*.go' -o -name '*.rs' -o -name '*.java' -o -name '*.rb' -o -name '*.php' -o -name '*.sql' -o -name '*.toml' -o -name '*.yml' -o -name '*.yaml' -o -name '*.json' -o -name '*.env*'" 2>/dev/null | grep -v node_modules | grep -v dist | grep -v .git/ | sort | head -200)

# Build prompt
DIFF_SECTION=""
if [ -n "$DIFF_CONTENT" ]; then
  DIFF_SECTION="
DIFF CONTENT (changes to review):
\`\`\`
$DIFF_CONTENT
\`\`\`

Focus your review on the changed code above.
"
fi

FILES_SECTION=""
if [ -n "$FILES_CHANGED" ]; then
  FILES_SECTION="
FILES CHANGED:
$FILES_CHANGED
"
fi

PROMPT="You are a senior security engineer conducting a security review of this codebase.

REPOSITORY: $REPO_PATH

FILE TREE:
$FILE_TREE
${FILES_SECTION}${DIFF_SECTION}
OBJECTIVE:
Perform a security-focused code review to identify HIGH-CONFIDENCE security vulnerabilities with real exploitation potential. Focus ONLY on security implications.

CRITICAL INSTRUCTIONS:
1. MINIMIZE FALSE POSITIVES: Only flag issues where you're >80% confident of actual exploitability
2. AVOID NOISE: Skip theoretical issues, style concerns, or low-impact findings
3. FOCUS ON IMPACT: Prioritize vulnerabilities leading to unauthorized access, data breaches, or system compromise

SECURITY CATEGORIES TO EXAMINE:

**Input Validation**: SQL injection, command injection, XXE, template injection, path traversal
**Auth & Authorization**: Auth bypass, privilege escalation, session flaws, JWT vulnerabilities
**Crypto & Secrets**: Hardcoded secrets, weak crypto, improper key management
**Injection & Code Exec**: RCE via deserialization, eval injection, XSS
**Data Exposure**: Sensitive data logging, PII handling, API data leakage
**Configuration**: CORS misconfiguration, debug info exposure, insecure defaults

EXCLUSIONS — DO NOT REPORT:
- DOS/resource exhaustion
- Rate limiting concerns
- Secrets stored on disk
- Memory safety in non-C/C++ code
- Input validation on non-security-critical fields without proven impact
- Open redirects
- Generic best practice recommendations without specific exploit path

ANALYSIS:
1. Read and understand the codebase structure
2. Examine each source file for security implications
3. Trace data flow from user inputs to sensitive operations
4. Identify injection points and unsafe patterns

OUTPUT FORMAT — You MUST output ONLY this JSON (no markdown, no explanation):

{
  \"findings\": [
    {
      \"file\": \"path/to/file.ts\",
      \"line\": 42,
      \"severity\": \"HIGH\",
      \"category\": \"sql_injection\",
      \"description\": \"User input passed to SQL query without parameterization\",
      \"exploit_scenario\": \"Attacker could extract database contents via...\",
      \"recommendation\": \"Use parameterized queries\",
      \"confidence\": 0.95
    }
  ],
  \"analysis_summary\": {
    \"files_reviewed\": 15,
    \"high_severity\": 1,
    \"medium_severity\": 2,
    \"low_severity\": 0,
    \"review_completed\": true
  }
}

Begin your analysis now. Use file tools to read source files. Your final reply must contain ONLY the JSON."

echo "🚀 Running Claude Code security audit..." >&2

# Run claude with --output-format json, pipe prompt via stdin
CLAUDE_OUTPUT=$(echo "$PROMPT" | claude \
  --output-format json \
  --model "$CLAUDE_MODEL" \
  --max-turns 30 \
  2>/dev/null) || {
  echo "❌ Claude Code execution failed" >&2
  exit 1
}

# Extract result from Claude Code JSON wrapper
RESULT=$(echo "$CLAUDE_OUTPUT" | python3 -c "
import sys, json

try:
    data = json.load(sys.stdin)
    
    # Claude Code wraps output: {type: 'result', result: '...'}
    if isinstance(data, dict) and 'result' in data:
        result_text = data['result']
        # Try to parse the result as JSON
        try:
            parsed = json.loads(result_text)
            if 'findings' in parsed:
                print(json.dumps(parsed, indent=2))
                sys.exit(0)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from text
        import re
        json_match = re.search(r'\{[\s\S]*\"findings\"[\s\S]*\}', result_text)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                print(json.dumps(parsed, indent=2))
                sys.exit(0)
            except json.JSONDecodeError:
                pass
    
    # If data itself has findings
    if isinstance(data, dict) and 'findings' in data:
        print(json.dumps(data, indent=2))
        sys.exit(0)
    
    # Fallback
    print(json.dumps({'findings': [], 'analysis_summary': {'error': 'Could not parse findings', 'raw_type': str(type(data))}, 'raw_output': str(data)[:500]}, indent=2))
except Exception as e:
    print(json.dumps({'findings': [], 'analysis_summary': {'error': str(e)}}, indent=2))
" 2>/dev/null)

# Apply hard exclusion filters
FILTERED=$(echo "$RESULT" | python3 -c "
import sys, json, re

EXCLUDE_PATTERNS = [
    (r'\b(denial of service|dos attack|resource exhaustion)\b', 'DOS finding'),
    (r'\b(missing|lack of|no)\s+rate\s+limit', 'Rate limiting'),
    (r'\b(resource|memory|file)\s+leak', 'Resource leak'),
    (r'\b(open redirect|unvalidated redirect)\b', 'Open redirect'),
    (r'\b(buffer overflow|stack overflow|use.?after.?free)\b', 'Memory safety'),
]

try:
    data = json.load(sys.stdin)
    findings = data.get('findings', [])
    kept = []
    excluded = 0
    
    for f in findings:
        desc = (f.get('description', '') + ' ' + f.get('category', '')).lower()
        skip = False
        for pattern, reason in EXCLUDE_PATTERNS:
            if re.search(pattern, desc, re.IGNORECASE):
                skip = True
                excluded += 1
                break
        
        # Skip .md files
        if f.get('file', '').endswith('.md'):
            skip = True
            excluded += 1
        
        if not skip:
            kept.append(f)
    
    data['findings'] = kept
    if 'filtering' not in data:
        data['filtering'] = {}
    data['filtering']['excluded_count'] = excluded
    data['filtering']['kept_count'] = len(kept)
    
    print(json.dumps(data, indent=2))
except Exception as e:
    print(json.dumps({'error': str(e)}, indent=2))
" 2>/dev/null)

# Save results
echo "$FILTERED" > "$OUTPUT_FILE"

# Summary
FINDINGS_COUNT=$(echo "$FILTERED" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('findings',[])))" 2>/dev/null || echo "0")
HIGH_COUNT=$(echo "$FILTERED" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len([f for f in d.get('findings',[]) if f.get('severity','').upper()=='HIGH']))" 2>/dev/null || echo "0")
MEDIUM_COUNT=$(echo "$FILTERED" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len([f for f in d.get('findings',[]) if f.get('severity','').upper()=='MEDIUM']))" 2>/dev/null || echo "0")

echo "" >&2
echo "✅ Security review complete!" >&2
echo "📊 Findings: $FINDINGS_COUNT total ($HIGH_COUNT HIGH, $MEDIUM_COUNT MEDIUM)" >&2
echo "📁 Results: $OUTPUT_FILE" >&2

# Exit with error if high severity found
if [ "$HIGH_COUNT" -gt 0 ]; then
  exit 1
fi
exit 0
