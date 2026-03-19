# Error Taxonomy — Claude CLI Error Types

Classification guide for `--error-type` parameter in `log-cli-run.sh`.

## Error Types

| Type | Khi nào dùng | Ví dụ |
|------|-------------|-------|
| `permission` | User/file permission issues | coder can't access workdir, setfacl fails |
| `timeout` | CLI exceeded timeout | Task too large, model too slow |
| `smart_quotes` | Output contains Unicode curly quotes | `''` → JS syntax error |
| `env` | Environment/setup issue | Missing API key, wrong base URL, deps not installed |
| `context_limit` | Token/context window exceeded | Prompt + codebase too large |
| `model_error` | Model refused, rate limit, API error | 429, 500, content policy block |
| `syntax` | Generated code has syntax errors | Missing imports, wrong language syntax |
| `cli_crash` | Claude CLI itself crashed | Non-JSON output, segfault, OOM |
| `wrong_approach` | Code works but wrong approach/pattern | Doesn't follow project conventions |
| `partial` | Partially completed | Some files done, others not |
| `unknown` | Can't classify | Fallback — try to investigate further |

## Classification Rules

1. **Be specific** — prefer `permission` over `unknown`
2. **Root cause** — if timeout because context_limit, use `context_limit`
3. **Multiple issues** — use the PRIMARY cause that triggered the failure
4. **Success runs** — leave `error_type` empty string

## Common Patterns & Known Fixes

| Pattern | Fix |
|---------|-----|
| `permission` recurring on same project | Check spawn.sh setfacl, or project has root-owned files |
| `smart_quotes` after any run | Add sed post-processing in spawn.sh |
| `timeout` on specific task type | Split into smaller chunks, use 2-phase approach |
| `context_limit` on large repos | Use .claudeignore, or scope prompt to specific dirs |
| `cli_crash` with OOM | Reduce concurrent processes, check system memory |
