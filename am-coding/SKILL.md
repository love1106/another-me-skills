# Coding — Development Skill cho Another Me Agents

Skill cho phép agent code, review, fix bugs trên repo — local container hoặc trên user's device qua SSH.

## Khi nào dùng skill này

**Condition: effort cao HOẶC consequence cao.**

✅ **Dùng khi (effort cao):**
- > 3 files hoặc cross-module
- Cần đọc hiểu codebase trước khi code
- Cần plan trước khi code
- Multi-step tasks (DB + API + UI)

✅ **Dùng khi (consequence cao):**
- DB schema / migration
- Auth / security
- API contract
- Deploy config
- Shared libs

❌ **Không dùng khi effort thấp VÀ consequence thấp** → dùng `am-claude-code`

📌 **Không rõ → default dùng skill này** (safe choice)

## Prerequisites

### Claude CLI (trong container)
```bash
# Check
which claude && claude --version

# Nếu chưa có — báo admin setup Dockerfile
```

Claude CLI được pre-install trong Docker image. Nếu không có, agent vẫn code được bằng cách dùng `read`/`edit`/`write` tools trực tiếp.

### Git Auth (trong container)
Agent cần SSH key hoặc GitHub token để push code. Kiểm tra:
```bash
# SSH key
ls ~/.ssh/id_ed25519 2>/dev/null && echo "SSH key OK"

# GitHub CLI
gh auth status 2>/dev/null && echo "gh OK"

# Git config
git config user.name && git config user.email
```

Nếu thiếu → báo user liên hệ admin để setup.

## Bước 1: Xác định Workspace

**HỎI USER** nếu chưa rõ:

### Option A: Code trên container (mặc định)
- Repo clone vào `~/.openclaw/projects/` (persist qua volume mount)
- Phù hợp: web app, API, scripts, CLI tools
- Agent có full control: edit, build, test, push

```bash
WORKSPACE=~/.openclaw/projects
mkdir -p $WORKSPACE
cd $WORKSPACE
git clone <repo-url> <project-name>
cd <project-name>
```

### Option B: Code trên user's device (qua SSH)
- Dùng khi user cần native environment (iOS simulator, GPU, specific OS)
- Kết hợp với `my-devices` skill
- Kiểm tra device status trước:

```bash
cat ~/.openclaw/devices.json
# Verify device online
```

```bash
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519"

# Check project location trên device
ssh $SSH_OPTS {user}@{ip} "ls -la ~/projects/{project}"
```

### Quyết định workspace

| Tình huống | Workspace |
|------------|-----------|
| Web app, API, backend | Container (Option A) |
| Mobile app (iOS/Android) | Device (Option B) |
| User nói "trên máy tính" / "trên laptop" | Device (Option B) |
| User không specify | Container (Option A) |
| Cần build native binary | Device (Option B) |
| Cần GPU / specific hardware | Device (Option B) |

## Bước 2: Phân tích yêu cầu

Trước khi code, xác định rõ:

1. **Input** — Dữ liệu/điều kiện đầu vào
2. **Output mong đợi** — Kết quả cuối cùng
3. **Acceptance Criteria** — Tiêu chí "done"
4. **Nếu không rõ → hỏi user**

Đọc project conventions:
```bash
cat .claude/instructions.md 2>/dev/null
cat CLAUDE.md 2>/dev/null
cat README.md 2>/dev/null | head -50
```

**Task nhỏ/rõ ràng** (fix typo, đổi text, sửa CSS): skip phân tích, code luôn.
**Task phức tạp**: trình bày plan cho user → chờ confirm.

## Bước 3: Create Branch

```bash
# Detect default branch
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
DEFAULT_BRANCH=${DEFAULT_BRANCH:-main}

git checkout $DEFAULT_BRANCH
git pull origin $DEFAULT_BRANCH

# Create feature branch
git checkout -b <type>/<short-description>
```

Branch types: `feat/`, `fix/`, `refactor/`, `chore/`, `docs/`

**Trên device** (SSH):
```bash
ssh $SSH_OPTS {user}@{ip} "cd ~/projects/{project} && git checkout -b feat/my-feature"
```

## Bước 4: Code

### 4A: Dùng Claude CLI (recommended cho complex tasks)

Dùng `am-claude-code` skill để spawn Claude CLI. Xem chi tiết spawn method, env vars, parsing tại `am-claude-code/SKILL.md`.

**Quy tắc quan trọng:**
- Claude CLI **chỉ edit files, KHÔNG commit** → luôn thêm `"DO NOT git commit or push."` vào prompt
- Respect project conventions
- Git management ở Bước 6, không phải trong CLI

### 4B: Code trực tiếp (simple tasks)

Dùng `read`/`edit`/`write` tools của agent:
- `read` file để hiểu context
- `edit` để sửa code (surgical, exact match)
- `write` chỉ cho file mới

### 4C: Code trên device (SSH)

```bash
# Edit file trên device
ssh $SSH_OPTS {user}@{ip} "cat ~/projects/{project}/src/app.ts"

# Tạo patch local → apply trên device
cat > /tmp/fix.patch << 'EOF'
--- a/src/app.ts
+++ b/src/app.ts
@@ -10,3 +10,3 @@
-  console.log("old")
+  console.log("new")
EOF
scp $SCP_OPTS /tmp/fix.patch {user}@{ip}:/tmp/
ssh $SSH_OPTS {user}@{ip} "cd ~/projects/{project} && git apply /tmp/fix.patch"
```

Hoặc đơn giản hơn — dùng `sed`:
```bash
ssh $SSH_OPTS {user}@{ip} "cd ~/projects/{project} && sed -i 's/old text/new text/' src/app.ts"
```

## Bước 5: Verify

### 5.1 Build Check
```bash
# Detect package manager
if [ -f pnpm-lock.yaml ]; then PM="pnpm"
elif [ -f yarn.lock ]; then PM="yarn"
elif [ -f bun.lockb ]; then PM="bun"
else PM="npm"; fi

$PM run build 2>&1 | tail -20
```

### 5.2 Type Check (TypeScript)
```bash
[ -f tsconfig.json ] && npx tsc --noEmit 2>&1 | head -30
```

### 5.3 Lint
```bash
$PM run lint 2>&1 | head -30
```

### 5.4 Test
```bash
$PM run test 2>&1 | tail -20
```

### 5.5 Screenshot Verify (nếu có UI + device linked)

Kết hợp `my-devices` skill:
```bash
# Chụp screenshot device
ssh $SSH_OPTS {user}@{ip} "screencapture -x /tmp/am-screenshot.png"  # Mac
scp $SCP_OPTS {user}@{ip}:/tmp/am-screenshot.png /tmp/am-screenshot.png
# Phân tích bằng vision model
```

### 5.6 Quick Security Check
```bash
# Scan changed files
git diff $DEFAULT_BRANCH --name-only -- '*.ts' '*.tsx' '*.js' '*.jsx' | \
  xargs grep -n "sk-\|api_key\|password\s*=\|secret\s*=" 2>/dev/null | head -10
```

**Verify FAIL → fix trước, không tiếp tục.**

## Bước 6: Commit & Push

```bash
git add -A
git status

# Conventional commit
git commit -m "<type>(<scope>): <description>"

git push origin <branch-name>
```

### Conventional Commits

| Type | Khi nào |
|------|---------|
| `feat` | Feature mới |
| `fix` | Sửa bug |
| `refactor` | Refactor |
| `docs` | Docs |
| `chore` | Config, deps |
| `test` | Tests |

### Trên device (SSH):
```bash
ssh $SSH_OPTS {user}@{ip} "cd ~/projects/{project} && git add -A && git commit -m 'feat: my feature' && git push origin feat/my-feature"
```

## Bước 7: Pull Request (nếu có GitHub)

```bash
REPO=$(git remote get-url origin | sed 's|.*github.com[:/]||;s|\.git$||')

gh pr create \
  --repo "$REPO" \
  --title "<type>(<scope>): <description>" \
  --body "## Changes
- <change 1>
- <change 2>

## Testing
- <how to test>" \
  --base $DEFAULT_BRANCH
```

Gửi PR link cho user.

## Deploy/Preview (khi user yêu cầu)

Agent **KHÔNG tự deploy** trừ khi user yêu cầu rõ ràng.

### Dev server trên container
```bash
$PM run dev &
# Expose qua tunnel nếu cần share
```

### Dev server trên device
```bash
ssh $SSH_OPTS {user}@{ip} "cd ~/projects/{project} && npm run dev &"
# User truy cập localhost trên device
```

### Deploy options
- Vercel: `npx vercel --prod`
- Cloudflare Pages: `npx wrangler pages deploy`
- Docker: `docker build && docker run`
- Tùy project — đọc README/docs trước

## Bảo mật

- **KHÔNG** hardcode secrets, API keys, passwords trong code
- **KHÔNG** commit `.env` files
- **KHÔNG** push to main/master trực tiếp (dùng branch + PR)
- **HỎI user** trước khi chạy deploy commands
- Review diff trước khi commit — đảm bảo không có sensitive data

## Platform-specific (SSH coding trên device)

### macOS
- Shell: `zsh`
- Paths: `/Users/{user}/projects/`
- Build tools: `xcode-select --install`
- iOS: `xcodebuild`, Simulator

### Windows
- Shell: `cmd.exe` hoặc `powershell`
- Paths: `C:\Users\{user}\projects\`
- Dùng PowerShell cho complex commands: `powershell -Command '...'`

### Linux
- Shell: `bash`
- Paths: `/home/{user}/projects/` hoặc `/root/projects/`

## Troubleshooting

| Vấn đề | Giải pháp |
|---------|-----------|
| `git push` permission denied | Kiểm tra SSH key / GitHub token |
| Claude CLI not found | Báo admin setup Dockerfile |
| Device offline | Báo user bật máy + check network |
| Build fail | Đọc error → fix → retry |
| SSH timeout | Check device status trong `devices.json` |
| No `package.json` | Detect project type (Python? Go? Rust?) và adjust commands |
