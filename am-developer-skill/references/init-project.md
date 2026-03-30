# Init Project from Template

Tạo project mới từ template có sẵn trong `initial-template-workspace`.

## Template Repository

- **Repo:** Template repo configured per organization (check `TOOLS.md` or ask user)
- **Local cache:** `~/projects/initial-template-workspace`
- **Projects dir:** `~/projects/`

## Workflow

### Step 1: Hỏi Repo & Project Info

**Hỏi progressive — không dump hết câu hỏi cùng lúc.**

**Nhóm 1 — Repo:**
1. **GitHub repo link** — Repo đã tạo chưa?
   - Nếu có: dùng link đó
   - Nếu chưa: tạo mới, tên **bắt buộc** có postfix `-workspace` (vd: `myshop-workspace`)
   - Org: check `TOOLS.md` for default GitHub org

**Nhóm 2 — Project info (để match template):**
2. **Project name** — Tên project/thương hiệu (vd: "MyShop", "CafeXyz")
3. **Mô tả ngắn** — Project làm gì? (vd: "Website bán giày cho shop ABC")
4. **Loại project** — Hỏi để match template:
   - E-commerce frontend (bán hàng online)?
   - Admin/backoffice?
   - API backend?
   - Landing page?
   - Khác?

→ Sau khi match template xong, mới hỏi tiếp env vars (Nhóm 3 ở Step 5).

### Step 2: Match Template

```bash
# Clone nếu chưa có (shallow — repo có thể rất lớn với nhiều templates)
if [ ! -d ~/projects/initial-template-workspace ]; then
  git clone --depth 1 <TEMPLATE_REPO_URL> ~/projects/initial-template-workspace
fi
cd ~/projects/initial-template-workspace
git pull origin main

# Đọc INDEX.md — danh sách TẤT CẢ templates + use cases
cat INDEX.md
```

**Matching logic — đọc kỹ INDEX.md, so sánh với project info từ Step 1:**

1. Đọc hết mục `## <template-name>` trong INDEX.md
2. Với mỗi template, đối chiếu:
   - **Mục đích** có khớp loại project user cần?
   - **Use Cases** có cover scenario user mô tả?
   - **"Không phải dùng cho"** — loại bỏ template không phù hợp
   - **Stack** có match preference user?
3. Xếp hạng theo mức độ phù hợp

**Kết quả matching:**

| Trường hợp | Hành động |
|------------|-----------|
| 1 template match rõ ràng | Đề xuất + giải thích lý do |
| Nhiều template có thể match | Liệt kê top 2-3, so sánh pros/cons, hỏi user chọn |
| Không match template nào | Báo: không có template phù hợp. Hỏi: (a) tạo từ scratch — follow `references/tech-stack.md` để suggest stack, (b) dùng template gần nhất + customize, (c) đợi template mới |

**Báo user:**
- Template được chọn + **lý do cụ thể** (match điểm nào trong INDEX.md)
- Features included / không included
- **Hỏi confirm trước khi tiếp**

### Step 3: Setup GitHub Repo

**Nếu user đã có repo:**
```bash
cd ~/projects
git clone <repo-url> "$PROJECT_NAME"
```

Nếu repo đã có code → **warn user**, hỏi có muốn overwrite không.

**Nếu user chưa có repo:**
```bash
PROJECT_NAME="myshop-workspace"  # Must end with -workspace
ORG="${GITHUB_ORG:-$(grep -oP 'Org:\s*\K\S+' ~/.openclaw/workspace/TOOLS.md 2>/dev/null || echo 'my-org')}"

cd ~/projects
gh repo create "$ORG/$PROJECT_NAME" --private --clone --description "Project description"
cd "$PROJECT_NAME"
```

> Dùng `--clone` để tạo + clone 1 bước.

### Step 4: Copy Template

**Chỉ copy template đã match** — không copy toàn bộ repo template.

```bash
TEMPLATE="storims-fo"  # Template đã match ở Step 2

# Copy CHỈ folder template phù hợp (exclude .git, .env)
rsync -a \
  --exclude='.git' \
  --exclude='.env' \
  --exclude='.env.local' \
  ~/projects/initial-template-workspace/templates/$TEMPLATE/ \
  ~/projects/$PROJECT_NAME/

# Setup git config
cd ~/projects/$PROJECT_NAME
# Đọc TOOLS.md cho git user info, fallback to defaults
GIT_USER=$(grep -oP 'Username:\s*\K\S+' ~/.openclaw/workspace/TOOLS.md 2>/dev/null || echo "dinh_cp")
GIT_EMAIL=$(grep -oP 'Email:\s*\K\S+' ~/.openclaw/workspace/TOOLS.md 2>/dev/null || git config user.email || echo "user@example.com")
git config user.name "$GIT_USER"
git config user.email "$GIT_EMAIL"

# Verify .gitignore has .env
grep -q '^\.env$' .gitignore 2>/dev/null || echo '.env' >> .gitignore
```

> Dùng `rsync` thay `cp` — exclude `.git` an toàn, không overwrite repo.

### Step 5: Configure Environment

**Nhóm 3 — Hỏi env vars (chỉ khi template cần):**

Đọc `.env.example` để biết cần gì, hỏi user từng nhóm:

```bash
cp .env.example .env
```

- Nếu user chưa có production values → fill dummy values có ghi chú `# TODO: fill real value`
- **Quan trọng:** `.env` PHẢI nằm trong `.gitignore` — không commit secrets

### Step 6: Install & Verify

```bash
# Install dependencies
bun install

# Verify build (cần .env đã fill ở Step 5)
bun run build
```

- Build fail do missing env → kiểm tra `.env`, fill đủ rồi build lại
- Build fail do code error → debug, fix, báo user
- **Không push code broken** — build phải pass trước

### Step 7: Initial Commit & Push

```bash
git add -A
git commit -m "feat: init project from $TEMPLATE template"
git push origin main
```

**⚠️ RULE: Đây là lần DUY NHẤT được push trực tiếp main (initial commit). Sau đó mọi thay đổi phải qua PR.**

### Step 8: Report

Báo user:
- ✅ Project đã tạo tại `~/projects/$PROJECT_NAME`
- 📦 Template: `$TEMPLATE`
- 🔗 GitHub: `<repo-url>`
- 🐳 Docker: `docker build -t $PROJECT_NAME .`
- 🔧 Tiếp theo: dùng `am-developer-skill` để phát triển features

## Available Templates

Đọc `INDEX.md` trong template repo để biết templates hiện có. **Không hardcode** — luôn đọc file vì templates có thể thay đổi.

## Rules

- Tên repo **nên** có postfix `-workspace` — nếu user đã có repo không có postfix, warn nhưng không block
- Không commit secrets (`.env`, API keys)
- Initial commit là lần duy nhất push main trực tiếp
- Luôn verify build trước khi push
- Hỏi confirm ở mỗi bước quan trọng (chọn template, tạo repo, push)
- Luôn `git pull` template repo trước khi copy (lấy latest)

## Error Handling

- Template không match → suggest tạo từ scratch hoặc đợi template mới
- Build fail → debug trước, không push broken code
- Repo đã có code → warn user, hỏi có muốn overwrite không
- Thiếu env vars → hỏi user, dùng dummy values có `# TODO` nếu chưa có production values
- Template repo outdated → pull trước khi copy
