# am-claude-code — Claude Code CLI (Quick Tasks)

Spawn Claude Code CLI cho task nhỏ, nhanh. Agent craft prompt → spawn CLI → parse JSON → report.

## Khi nào dùng

**Condition: effort thấp VÀ consequence thấp.**

✅ **Dùng khi:**
- Review / explain code
- Generate unit tests
- Quick edit 1-3 files (UI text, styling, comments)
- Check syntax, type errors
- Small refactor trong 1 file
- Generate boilerplate / scaffolding

❌ **KHÔNG dùng (chuyển sang am-coding) khi:**
- Effort cao: > 3 files, cross-module, cần planning
- Consequence cao: DB schema, auth/security, API contract, deploy config, billing, shared libs
- Không rõ → **default am-coding** (safe choice)

⚠️ **Escalation:** Bắt đầu am-claude-code nhưng phát hiện phức tạp hơn → **dừng, chuyển am-coding**.

## Architecture
```
Agent → spawn CLI → Claude Code → JSON result → Agent parse & report
```

## Spawn Claude CLI

### Container environment
Agent chạy trong Docker container. Claude CLI đã pre-install.

```bash
# Check CLI available
which claude && claude --version
```

### Env vars (đã có sẵn trong container)
- `ANTHROPIC_API_KEY` — set bởi orchestrator
- `ANTHROPIC_BASE_URL` — set bởi orchestrator (optional, for proxy)

### Spawn command

```bash
# Quick task
claude --dangerously-skip-permissions --output-format json -p "
<task description>
DO NOT git commit or push.
"

# Với model cụ thể
claude --dangerously-skip-permissions --output-format json --model sonnet -p "task"

# Resume session
claude --dangerously-skip-permissions --output-format json --resume <session_id> -p "continue..."
```

> **Note:** Container chạy root → dùng `--dangerously-skip-permissions` (không cần `su - coder`). Flag này chỉ hoạt động khi Claude CLI version hỗ trợ. Nếu bị block → fallback dùng `--permission-mode bypassPermissions` với non-root user.

### Fallback: non-root user
Nếu `--dangerously-skip-permissions` bị block:
```bash
# Tạo user nếu chưa có
useradd -m -s /bin/bash coder 2>/dev/null || true

su - coder -c "
export ANTHROPIC_API_KEY='$ANTHROPIC_API_KEY'
export ANTHROPIC_BASE_URL='$ANTHROPIC_BASE_URL'
cd <workdir>
claude --permission-mode bypassPermissions --output-format json -p 'task'
"
```

## Parsing Result

```json
{
  "type": "result",
  "subtype": "success",
  "result": "The actual text response",
  "session_id": "uuid-to-resume",
  "total_cost_usd": 0.05,
  "is_error": false
}
```

Key fields:
- `result` — response text
- `session_id` — save for multi-turn
- `is_error` — check failures
- `total_cost_usd` — track spending

## Prompt Strategy

**High-level prompts. KHÔNG micromanage.**

Claude Code đủ thông minh để explore codebase. Agent chỉ cung cấp:
- **Goal**: cần làm gì
- **Constraints**: giữ gì, không đụng gì
- **Safety**: "If unsure → chọn option an toàn hơn"

### 2-Phase cho task phức tạp hơn
```
Phase 1 (Plan): "Analyze + plan. Output: {steps, questions}"
  → parse → có questions? → answer
Phase 2 (Implement): "Implement. [answers]"
  → resume session via session_id
```

## Timeout & Retry

| Task type | Timeout | Examples |
|-----------|---------|----------|
| Quick | 120s | review, explain, 1-2 files |
| Medium | 300s | 3-5 files, refactor |
| Large | 600s | >5 files → cân nhắc dùng am-coding |

### Retry flow:
```
Attempt 1: full prompt, standard timeout
  ↓ fail
Attempt 2: simplified prompt, increased timeout
  ↓ fail
Attempt 3: minimal prompt, max timeout
  ↓ fail
→ Report failure, suggest am-coding
```

**Max retries: 2** (total 3 attempts)

### Long prompts (>500 chars → write to file):
```bash
cat > /tmp/prompt.md << 'PROMPT'
Your long prompt here...
PROMPT
cat /tmp/prompt.md | claude --dangerously-skip-permissions --output-format json -p -
```

## Coding trên Device (SSH)

Khi cần code trên user's device thay vì container:

```bash
# Clone repo về container, code ở đây, push
# Hoặc SSH vào device + chạy Claude CLI trên device (nếu device có CLI)

SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519"
ssh $SSH_OPTS {user}@{ip} "cd ~/projects/{project} && claude --dangerously-skip-permissions --output-format json -p 'task'"
```

> Hầu hết trường hợp: clone về container → code → push → device pull. Chỉ SSH chạy CLI trên device khi cần native environment.

## Available Models
- `sonnet` — default cho quick tasks
- `opus` — deep reasoning, complex review

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `claude: not found` | `curl -fsSL https://claude.ai/install.sh \| bash` |
| `bypassPermissions blocked for root` | Dùng `--dangerously-skip-permissions` hoặc tạo user `coder` |
| JSON parse error | Check stderr, có thể auth error |
| Timeout | Tăng timeout hoặc split task |
| API key invalid | Check `ANTHROPIC_API_KEY` env var |
