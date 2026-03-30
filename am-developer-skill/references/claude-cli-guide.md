# Claude CLI Guide — Detailed Reference

Chi tiết cho Step 5 (Code with Claude CLI). SKILL.md giữ summary, file này chứa full instructions.

## 5.1 Spawn Claude Code CLI

**Option A: spawn.sh wrapper (recommended)**
```bash
export ANTHROPIC_API_KEY="$KEY"
export ANTHROPIC_BASE_URL="$URL"  # optional, for proxy

bash <skill_dir>/scripts/spawn.sh <WORKDIR> <MODEL> "YOUR PROMPT"
# With session resume:
bash <skill_dir>/scripts/spawn.sh <WORKDIR> <MODEL> "continue..." <SESSION_UUID>
# With custom timeout (default 180s):
bash <skill_dir>/scripts/spawn.sh <WORKDIR> <MODEL> "YOUR PROMPT" "" 120
```
`<skill_dir>` = directory containing SKILL.md (e.g. the skill's own directory)

**Timeout:** Default 180s. Exit code 124 = timed out → task quá lớn, cần chia nhỏ (Hard Rule #5).

Returns JSON: `{ result, session_id, is_error, total_cost_usd, usage }`

**Option B: Direct CLI**
```bash
CLAUDE_USER="${CLAUDE_USER:-coder}"
su - "$CLAUDE_USER" -s /bin/bash -c "
  export ANTHROPIC_API_KEY='${ANTHROPIC_API_KEY}'
  export ANTHROPIC_BASE_URL='${ANTHROPIC_BASE_URL}'
  cd <WORKDIR>
  claude --permission-mode bypassPermissions --output-format json -p 'task'
"
```

**Background mode (cho subtask cần async — ví dụ build/test chạy lâu):**
```bash
exec background:true command:"bash <skill_dir>/scripts/spawn.sh <WORKDIR> sonnet 'task'"
# Monitor (BẮT BUỘC — xem Hard Rule #3):
process action:poll sessionId:xxx timeout:60000
process action:log sessionId:xxx
```
⚠️ Mỗi subtask nên hoàn thành trong ~1-2 phút (Hard Rule #5). Nếu cần background mode, subtask có thể quá lớn → xem xét chia nhỏ thêm.

**Long prompts hoặc prompts có special chars (backticks, $, quotes) → dùng file input:**
```bash
write /tmp/prompt.md "prompt content with $vars, `backticks`, and \"quotes\""
bash <skill_dir>/scripts/spawn.sh <WORKDIR> <MODEL> @/tmp/prompt.md
# Hoặc pipe stdin:
cat /tmp/prompt.md | bash <skill_dir>/scripts/spawn.sh <WORKDIR> <MODEL> -
```
⚠️ Inline prompts qua spawn.sh chỉ escape single quotes. Nếu prompt chứa `$`, `` ` ``, `"` → **luôn dùng `@file` hoặc `-` stdin**.

## 5.2 Prompt Strategy

**High-level prompts, KHÔNG micromanage.** Claude Code tự explore codebase.

Chỉ cung cấp:
- **Goal**: cần làm gì
- **Constraints**: giữ gì, không đụng gì, pattern nào follow
- **Edge cases**: nếu X → làm Y
- **Safety**: "If unsure → choose the safer option"
- **Cuối prompt luôn thêm:** `"DO NOT git commit or push."`
- **Coding rules (luôn inject):** Đọc section "Tóm tắt" cuối [coding-rules.md](coding-rules.md), append vào cuối prompt. Đây là 8 defensive programming rules bắt buộc.
- **Unit testing rules (inject khi task cần tests):** Đọc [unit-testing.md](unit-testing.md), inject TDD flow + Gap Discovery rules vào prompt.
- **GitNexus context (inject khi có):** Nếu Step 0c đã chạy, append kết quả vào prompt. Truncate: chỉ inject top 10 results + summary. Nếu bridge timeout → skip.
- **Annotations (inject khi có):** Trước khi spawn, inject relevant gotchas:
  ```bash
  ANN_IDS="/tmp/ann-ids-$$.txt"
  ANNOTATIONS=$(bash <skill_dir>/scripts/annotate.sh inject \
    --project <repo-name> --scope <module> --limit 5 2>"$ANN_IDS")
  [ -n "$ANNOTATIONS" ] && PROMPT="${PROMPT}\n\n${ANNOTATIONS}"
  ```
  **Token budget:** Quick tasks `--limit 3`, Medium `--limit 5`, Large `--limit 7`.
  IDs output to stderr → `$ANN_IDS` cho 5.9 hit bumping.

❌ Wrong: list mọi file, mọi dòng cần sửa, copy-paste code context
✅ Right: mô tả goal + constraints, để Claude Code tự đọc code và implement

💡 **Project conventions:** Claude Code tự đọc `.claude/instructions.md` nếu file tồn tại. Chỉ nhắc: `"Follow project conventions in .claude/instructions.md if it exists."`

**2-Phase cho complex subtasks:**
```
Phase 1 (Plan): "Analyze + plan this subtask. Output JSON: {steps, questions, assumptions}"
  → parse result → có questions? → trả lời → Phase 2
Phase 2 (Implement): "Implement the plan. [answers if any]"
  → Resume session via session_id from Phase 1
```

## 5.3 Timeout & Retry (BẮT BUỘC)

| Task type | Timeout | Ví dụ |
|-----------|---------|-------|
| Quick | 120s | review, explain, 1-2 files |
| Medium | 180s | 3-5 files, refactor |
| Large | 300s | >5 files — nhưng ĐÃ chia subtask nhỏ (Hard Rule #5) |

⚠️ **Nếu ước lượng task > 2 phút → PHẢI chia subtask trước khi spawn (Hard Rule #5).**

**Retry flow (max 3 attempts) — Adaptive:**
```
Attempt 1: full prompt, standard timeout
  ↓ fail → DIAGNOSE root cause:

  ┌─ Token/context limit?  → Split task thành chunks nhỏ hơn
  ├─ Wrong approach?       → Thay đổi prompt strategy
  ├─ Environment issue?    → Fix env trước, retry cùng prompt
  ├─ Model limitation?     → Escalate model (sonnet → opus)
  └─ Timeout?              → Chia subtask nhỏ hơn, KHÔNG tăng timeout

Attempt 2: strategy KHÁC so với attempt 1
  ↓ fail → diagnose lại

Attempt 3: last resort — minimal prompt, split nhỏ nhất, hoặc escalate model
  ↓ fail
→ BÁO USER NGAY (Hard Rule #2).
```

⚠️ **Mỗi attempt PHẢI khác strategy** — retry cùng cách = lãng phí.

## 5.4 Parse Result

```json
{
  "type": "result",
  "subtype": "success",
  "result": "The response text",
  "session_id": "uuid-to-resume",
  "is_error": false,
  "total_cost_usd": 0.05,
  "usage": { "input_tokens": 1000, "output_tokens": 500 }
}
```

- `is_error: true` → retry (xem 5.3)
- `session_id` → lưu để resume multi-turn
- CLI crash / non-JSON output → retry once, vẫn fail → báo user

## 5.5 Available Models
- `sonnet` — default cho hầu hết tasks
- `opus` — chỉ cho deep reasoning (complex review, architecture)

## 5.6 Environment

| Var | Required | Default | Description |
|-----|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | ✅ | — | API key |
| `ANTHROPIC_BASE_URL` | ❌ | api.anthropic.com | Proxy URL |
| `CLAUDE_USER` | ❌ | `coder` | Non-root user |

**Tại sao cần user `coder`?**
Claude Code CLI block `--permission-mode bypassPermissions` khi chạy root.
`spawn.sh` tự động `su - coder` và **tự chmod workdir** nếu thiếu permission.

**First-time setup checklist (1 lần duy nhất):**
1. `npm install -g @anthropic-ai/claude-code` + verify `claude --version`
2. `useradd -m -s /bin/bash coder` (hoặc set `CLAUDE_USER`)
3. Set env vars: `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL` (optional)
4. Install LSP servers: `npm install -g typescript-language-server typescript pyright`
5. Enable experimental features — tạo `/home/coder/.claude/settings.json`:
   ```json
   { "env": { "ENABLE_LSP_TOOL": "1", "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }
   ```
6. Install `acl` package: `apt install acl` (cho setfacl permission handling)

## 5.7 Monitoring Checklist (BẮT BUỘC cho background spawns)

1. **Spawn xong → báo user:** "Đang chạy Claude Code cho [task], ETA ~X phút"
2. **Poll loop:**
   ```
   process action:poll sessionId:xxx timeout:60000
   ```
   - Running + > 2 phút → báo user
   - Done → parse result → báo user kết quả + files changed
   - Fail → retry hoặc báo user
3. **Partial success:** Parse result → resume session cho files còn lại
4. **Auto-notify (recommended):**
   ```
   When completely finished, create a file: touch /tmp/.claude-done-<task-id>
   ```
   ⚠️ Không dùng `openclaw` CLI trong prompt — user `coder` có thể không có trong PATH.

## 5.8 Log CLI Run (BẮT BUỘC — auto sau mỗi spawn)

```bash
bash <skill_dir>/scripts/log-cli-run.sh \
  --project "<repo-name>" \
  --task "<task description>" \
  --model "<model>" \
  --exit-code <exit_code> \
  --error-type "<type>"  \
  --error-summary "<short description>" \
  --duration <seconds> \
  --cost "<cost_usd from result>" \
  --attempt <N> \
  --retry-strategy "<strategy used>" \
  --resolved <true|false> \
  --resolution "<how resolved>" \
  --session-id "<session_id from result>"
```

- **Success:** `--exit-code 0`, skip error fields
- **Error:** classify per `error-taxonomy.md`
- **Retry:** log EACH attempt separately
- **Subtask pattern:** log 1 lần cho cả task sau subtask cuối cùng
- Log KHÔNG block workflow

## 5.9 Capture Learnings (Auto-Annotate)

**Sau mỗi task hoàn thành**, 3 actions (non-blocking):

1. **Retry gotchas** — nếu retry > 1:
   ```bash
   bash <skill_dir>/scripts/annotate.sh add --project "<repo>" --scope "<module>" \
     --text "<what went wrong + fix>" --tags "<tags>" --source "auto-retry"
   ```

2. **Bump hits** — nếu Step 5 đã inject annotations:
   ```bash
   IDS=$(grep "^INJECTED_IDS:" "$ANN_IDS" 2>/dev/null | sed 's/INJECTED_IDS://')
   for id in $(echo "$IDS" | tr ',' ' '); do
     bash <skill_dir>/scripts/annotate.sh hit --project "<repo>" --id "$id"
   done
   ```

3. **Ask for discoveries** (optional, medium/large) — resume session:
   *"List non-obvious gotchas you discovered. One line each, concise."*
   Session expired → skip. Parse → `annotate.sh add --source auto-discovery`

**Auto-dedup** (>80% word overlap → skip). Text truncated at 500 chars.
**Promote:** `hits > 10` → add to `.claude/instructions.md`.
**Monorepo:** 1 file per repo, `--scope` per service.

## Subtask Execution Pattern (Hard Rule #5)

Mọi task Medium/Large → chia subtasks trước khi spawn:

**Subtask template:**
```
Subtask N: <tên ngắn gọn>
  Goal: <1 dòng>
  Files: <files dự kiến>
  ETA: ~1-2 phút
  Verify: <build pass / test pass / UI check>
```

**Execution loop (FOREGROUND preferred):**
```
SESSION_ID=""

Loop:
  1. Spawn subtask (foreground, timeout 120s)
     - First: spawn mới
     - Subsequent: resume session_id
  2. Parse result → save session_id
  3. Report: "✅ Subtask 1/3 done: <summary>"
  4. Fail → retry (max 3, xem 5.3)
  5. Pass → spawn next subtask
  6. Repeat
  7. SAU TẤT CẢ → Verification Pipeline (Step 6)
```

💡 Foreground > Background cho subtask ngắn.
💡 Session expired? Spawn mới (~5-10s overhead).
