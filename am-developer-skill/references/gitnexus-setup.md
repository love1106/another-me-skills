# GitNexus Setup & Integration

Code intelligence engine — indexes codebase into knowledge graph, exposed via MCP tools.

## Install (1 lần)

```bash
# 1. Install GitNexus globally
npm install -g gitnexus

# 2. Config MCP cho Claude Code CLI (global, auto-detect)
gitnexus setup
# Hoặc manual:
claude mcp add gitnexus -- npx -y gitnexus@latest mcp

# 3. Verify
gitnexus --version
```

## Index Repo

```bash
cd ~/projects/<repo>

# Index lần đầu (full, có thể mất vài phút cho repo lớn)
gitnexus analyze --skills

# Check status (last indexed time, staleness)
gitnexus status

# Re-index (incremental, nhanh ~2-5s cho changes nhỏ)
gitnexus analyze

# Force full re-index
gitnexus analyze --force

# List all indexed repos
gitnexus list
```

`--skills` generates repo-specific skill files in `.claude/skills/generated/` — chỉ cần chạy lần đầu hoặc khi architecture thay đổi lớn.

## MCP Bridge (OpenClaw trực tiếp)

Script: `scripts/git-nexus-mcp-bridge.js` — gọi GitNexus MCP tools không cần MCP client.

```bash
BRIDGE="<skill_dir>/scripts/git-nexus-mcp-bridge.js"

# List indexed repos
node $BRIDGE list_repos

# Search codebase (hybrid: BM25 + semantic)
node $BRIDGE query '{"query":"auth handler"}' --repo another-me

# 360° symbol view (callers, callees, community, dead code status)
node $BRIDGE context '{"name":"UserService"}' --repo another-me

# Blast radius analysis (what breaks if I change this?)
node $BRIDGE impact '{"target":"validate"}' --repo another-me

# Git diff → affected symbols (uncommitted changes)
node $BRIDGE detect_changes --repo another-me

# Multi-file rename plan
node $BRIDGE rename '{"old":"oldName","new":"newName"}' --repo another-me

# Raw Cypher query
node $BRIDGE cypher '{"query":"MATCH (n:Function) RETURN n.name LIMIT 10"}' --repo another-me
```

## When to Use What

| Scenario | Tool | Command |
|----------|------|---------|
| Em (Hip) cần hiểu architecture trước khi giao task | MCP Bridge | `node $BRIDGE query/context/impact` |
| Em cần check blast radius trước khi delegate | MCP Bridge | `node $BRIDGE impact '{"symbol":"X"}'` |
| Claude Code đang code, cần navigate/debug | Claude Code MCP | Tự động qua MCP (đã setup) |
| Check index có stale không | CLI | `gitnexus status` |
| Re-index sau changes lớn | CLI | `gitnexus analyze` |

## Auto-Generated Files

Sau `gitnexus analyze`, repo sẽ có:
- `.claude/skills/` — built-in skills (exploring, debugging, impact, refactoring)
- `.claude/skills/generated/` — repo-specific skills (from `--skills`)
- `AGENTS.md` / `CLAUDE.md` — context files cho agent
- `.gitnexus/` — index data (LadybugDB)

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `gitnexus: command not found` | `npm install -g gitnexus` |
| MCP bridge timeout | Tăng `--timeout 30000`, hoặc check `gitnexus status` |
| Index stale | `gitnexus analyze` (incremental) |
| Index corrupted | `gitnexus clean && gitnexus analyze --skills` |
| Claude Code không dùng MCP tools | `gitnexus setup` lại, hoặc `claude mcp list` verify |

## License Note

GitNexus dùng Polyform Noncommercial License. Dùng internal/dev workflow = OK.
Không ship GitNexus binary/code cho end user.
