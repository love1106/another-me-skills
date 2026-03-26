# Verification Pipeline

**BẮT BUỘC trước khi tạo PR.**

Agent chạy verification trực tiếp qua exec sau khi Claude CLI hoàn thành. Nếu có FAIL → gọi lại Claude CLI để fix → chạy lại pipeline từ đầu.

## Modes

| Mode | Khi nào | Steps |
|------|---------|-------|
| **Full** | Medium/Large tasks | 6.1 → 6.2 → 6.3 → 6.4 → 6.4b → 6.5 → 6.6 → 6.7 → 6.8 |
| **Lite** | Quick tasks, hotfix | 6.1 (Build) → 6.6 (Diff) → 6.7 (Criteria) → 6.8 (Report) |
| **Full + Smoke** | Multi-service / API tasks | Full + 6.5b (Smoke Test) |

Lite mode skip type check, lint, tests, security scan — dùng khi thay đổi nhỏ, isolated, low-risk.

```bash
# Dùng WORKDIR từ Step 4 (KHÔNG hardcode repo path)
WORKDIR=$(cat /tmp/openclaw-workdir-$$.txt 2>/dev/null || echo ~/projects/<repo>)
cd "$WORKDIR"
source <skill_dir>/scripts/detect-env.sh
```

## 6.1 Build Check (compile only — không start server, không conflict dev server đang chạy)
```bash
# SKIP nếu project không có build script
node -e "process.exit(require('./package.json').scripts?.build ? 0 : 1)" 2>/dev/null \
  && $PM run build 2>&1 | tail -20
```
→ PHẢI pass. Fail → fix trước. Không có build script → SKIP.

## 6.2 Type Check (SKIP nếu không có TypeScript)
```bash
[ -f tsconfig.json ] && npx tsc --noEmit 2>&1 | head -30
```
→ 0 errors = PASS. Không có tsconfig.json → SKIP.

## 6.3 Lint Check
```bash
node -e "process.exit(require('./package.json').scripts?.lint ? 0 : 1)" 2>/dev/null \
  && $PM run lint 2>&1 | head -30
```
→ 0 errors = PASS (warnings chấp nhận). Không có lint script → SKIP.

## 6.4 Test Suite (SKIP nếu project chưa có tests)
```bash
node -e "process.exit(require('./package.json').scripts?.test ? 0 : 1)" 2>/dev/null \
  && $PM run test 2>&1 | tail -30
```
→ Ghi lại: X passed, Y failed, Z% coverage. Không có test script → SKIP.

## 6.5 Security Quick Scan (chỉ scan files đã thay đổi)

```bash
# Lấy danh sách files changed + new files (untracked) so với default branch
CHANGED=$(git diff $DEFAULT_BRANCH --name-only -- '*.ts' '*.tsx' '*.js' '*.jsx')
UNTRACKED=$(git ls-files --others --exclude-standard -- '*.ts' '*.tsx' '*.js' '*.jsx')
ALL_CHANGED=$(printf "%s\n%s" "$CHANGED" "$UNTRACKED" | sort -u | grep -v '^$')

if [ -n "$ALL_CHANGED" ]; then
  # Secrets check (dùng -I{} để handle filenames với spaces)
  echo "$ALL_CHANGED" | xargs -I{} grep -n "sk-\|api_key\|password\s*=\|secret\s*=" {} 2>/dev/null | head -10

  # Console.log check
  echo "$ALL_CHANGED" | xargs -I{} grep -n "console\.log" {} 2>/dev/null | head -10
else
  echo "No JS/TS files changed — security scan SKIP"
fi
```

Checklist (review thủ công trên changed files):
- [ ] **Secrets:** Không hardcode API keys, tokens, passwords
- [ ] **Console.log:** Không còn debug logs thừa
- [ ] **Error exposure:** Error messages không leak stack trace ra client
- [ ] **Input validation:** User input được validate
- [ ] **SQL/Query injection:** Dùng parameterized queries hoặc ORM
- [ ] **Auth check:** Endpoint sensitive có kiểm tra auth

## 6.5b Smoke Test (optional — multi-service / API tasks)

**Khi nào:** Task đụng API endpoints, DB operations, hoặc cross-service calls.
**Skip khi:** Pure frontend/CSS, docs, config-only changes.

```bash
# 1. API endpoint smoke — verify endpoints changed/added
# Adapt URL + method per task
curl -s -o /dev/null -w "%{http_code}" http://localhost:<port>/health
curl -s http://localhost:<port>/v1/<endpoint> | head -20

# 2. DB constraint check — nếu task thêm/sửa schema
# Verify insert/update không bị constraint violation
curl -s -X POST http://localhost:<port>/v1/<endpoint> \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}' | head -10

# 3. Cross-service call — nếu service A gọi service B
# Verify service B đang chạy + response OK
curl -s http://localhost:<serviceB_port>/health
```

**Checklist:**
- [ ] New/changed API endpoints return expected status codes
- [ ] DB operations (insert/update/delete) không bị constraint errors
- [ ] Cross-service calls succeed (không 503, timeout, auth failure)
- [ ] Error responses có format đúng (không leak stack trace)

→ FAIL bất kỳ check → fix trước khi PR. Ghi kết quả vào report (6.8).

## 6.6 Diff Review
```bash
git diff $DEFAULT_BRANCH --stat
git status --short
```
→ Review:
- File nào thay đổi ngoài ý muốn?
- Còn file nào unstaged/untracked cần commit?
- Thay đổi nào có thể break tính năng khác?

## 6.7 Acceptance Criteria Check

Đối chiếu từng tiêu chí ở Step 1. Mỗi tiêu chí ghi rõ PASS/FAIL + verification method đã dùng.
Nếu Step 1 đánh dấu 🔴 Irreversible → xác nhận user đã approve trước khi tiến hành.

## 6.8 Verification Report

Tổng hợp kết quả:

```
VERIFICATION REPORT
====================
Build:      [PASS/FAIL]
Types:      [PASS/FAIL/SKIP] (X errors)
Lint:       [PASS/FAIL] (X errors, Y warnings)
Tests:      [PASS/FAIL/SKIP] (X passed, Y failed, Z% coverage)
Security:   [PASS/FAIL] (X issues)
Diff:       [X files changed]
Criteria:   [X/Y passed]

Overall:    [READY / NOT READY] for PR
```

⚠️ **NOT READY → FIX hết rồi chạy lại pipeline. KHÔNG tạo PR khi còn FAIL.**

💡 **Gửi report cho user confirm trước khi tạo PR.**
