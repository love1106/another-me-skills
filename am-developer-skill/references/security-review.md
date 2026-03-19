# Security Review (Claude Code)

AI-powered security audit using Claude Code CLI. Analyzes code for vulnerabilities with false-positive filtering.

## Prerequisites

- `claude` CLI installed and configured
- `ANTHROPIC_API_KEY` set in environment
- Python 3.10+ with `anthropic` package (for Claude API filtering, optional)

## Usage

### Full Repo Scan

```bash
# Scan entire repo
bash scripts/security-review.sh /path/to/repo

# Scan with custom output
bash scripts/security-review.sh /path/to/repo /tmp/results.json

# Scan specific subdirectory
bash scripts/security-review.sh /path/to/repo/src
```

### PR/Branch Diff Scan

```bash
# Scan only changes between branches
bash scripts/security-review.sh /path/to/repo /tmp/results.json main feature-branch
```

### Options (env vars)

| Var | Default | Description |
|-----|---------|-------------|
| `CLAUDE_MODEL` | `claude-sonnet-4-6` | Claude model to use |
| `CLAUDE_TIMEOUT` | `600` | Timeout in seconds |
| `EXCLUDE_DIRS` | `node_modules,dist,.git` | Comma-separated dirs to skip |

## Output

JSON file with findings:

```json
{
  "findings": [
    {
      "file": "src/routes/auth.ts",
      "line": 42,
      "severity": "HIGH",
      "category": "auth_bypass",
      "description": "JWT validation can be bypassed...",
      "exploit_scenario": "Attacker could...",
      "recommendation": "Add proper validation...",
      "confidence": 0.92
    }
  ],
  "analysis_summary": {
    "files_reviewed": 15,
    "high_severity": 1,
    "medium_severity": 2,
    "low_severity": 0
  }
}
```

## Workflow

1. Run `security-review.sh` on target repo
2. Script generates security prompt → sends to Claude Code CLI
3. Claude analyzes codebase, returns structured findings
4. Hard exclusion rules filter obvious false positives (DOS, rate limiting, etc.)
5. Results saved as JSON
6. Review findings and recommend fixes

## Severity Guide

- **HIGH**: Directly exploitable — RCE, data breach, auth bypass
- **MEDIUM**: Exploitable with conditions — needs specific setup
- **LOW**: Defense-in-depth issues

## What Gets Excluded Automatically

- DOS/resource exhaustion
- Rate limiting recommendations
- Memory safety in non-C/C++ code
- Open redirects
- Secrets on disk (managed separately)
- Resource leaks
