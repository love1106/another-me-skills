---
name: am-create-skill
description: >
  Create, analyze, or improve OpenClaw skills with orchestrator pattern support.
  Use when: creating new skills, analyzing/auditing existing skills, improving/refactoring
  skills, restructuring into orchestrator pattern, reviewing skill quality.
  Triggers: "create skill", "tạo skill", "analyze skill", "đánh giá skill",
  "audit skill", "check quality", "review skill", "improve skill", "cải tiến skill",
  "refactor skill", "tidy up skill", "clean up skill", "nâng cấp skill".
  NOT for: non-skill tasks, editing code/config files.
---

# Skill Manager

Unified skill for the full skill lifecycle: **Create → Analyze → Improve**.

## Mode Detection

| Mode | User Intent | Keywords |
|---|---|---|
| **Create** | Skill chưa tồn tại, cần tạo mới | "create", "tạo", "build", "make" |
| **Analyze** | Skill đã có, muốn đánh giá quality (không sửa) | "analyze", "đánh giá", "audit", "check quality" |
| **Improve** | Skill đã có, muốn cải thiện/sửa/refactor | "improve", "cải tiến", "refactor", "nâng cấp", "fix", "tidy up", "review skill" |

**Ambiguous?** → Hỏi user: "Muốn đánh giá trước hay sửa luôn?"

**Existence check:** Trước khi vào mode, kiểm tra skill đã tồn tại chưa:
- **Create + skill đã có** → Hỏi: "Skill đã tồn tại, muốn improve hay overwrite?"
- **Analyze/Improve + skill chưa có** → Hỏi: "Skill chưa tồn tại, muốn tạo mới không?" → chuyển Create

---

## Mode 1: Create

Tạo skill mới từ đầu.

### Step 1: Assess Complexity

**Quick check:** Nếu skill hiển nhiên đơn giản (one-shot, no risk, no coordination, 1 concern) → skip scoring, chọn Pattern 1 trực tiếp.

**Nếu không rõ:** Score 9 dimensions theo `references/architecture-patterns.md` → Complexity Assessment.

```
1. Score 9 dimensions (D1-D9)
2. Calculate total → determine level (L1-L4)
3. Choose pattern (Simple / Reference-Heavy / Orchestrator)
4. Document score in SKILL.md (nếu L2+)
```

### Step 2: Create Structure

**L1-L2 (Simple/Moderate):**
```bash
mkdir -p skills/{name}/{scripts,references}
```

**L3-L4 (Complex/Critical):** Orchestrator pattern — xem templates trong `references/architecture-patterns.md`.

### Step 3: Write Content

1. **YAML frontmatter** — name (kebab-case) + description (<1024 chars, có What/When/Triggers/NOT for)
2. **SKILL.md body** — workflow steps, checklists. Giữ < 5,000 words.
3. **References** — chi tiết nặng tách sang `references/`
4. **Scripts** — validation scripts nếu cần

Naming convention:
- Skill name: `am-{domain}` hoặc `am-{domain}-{phase}` (cho sub-skills)
- kebab-case, không chứa "claude"/"anthropic"

5. **Permissions Declaration** (bắt buộc nếu D7≥3 hoặc D9≥2)
```markdown
## Permissions
- reads: [files, git history, API data...]
- writes: [workspace files, DB, config...]
- external: [GitHub API, web fetch, messaging...]
- destructive: [none | list specific destructive actions]
- requires_confirmation: [actions cần user confirm trước khi execute]
```
Quan trọng cho Skills Market — user cần biết skill access gì trước khi install.

Nếu orchestrator:
- Shared rules → `references/shared-rules.md`
- Sub-skills → self-contained, reference ngược orchestrator
- Routing table rõ ràng

### Step 4: Validate

Chạy **Anthropic Quality Checklist** (`references/anthropic-skill-guidelines.md`):

```
- [ ] SKILL.md < 5,000 words?
- [ ] Description < 1,024 chars, có What + When + Triggers + NOT for?
- [ ] Name kebab-case, không chứa "claude"/"anthropic"?
- [ ] Progressive disclosure: frontmatter → body → references?
- [ ] Scripts cho validation thay vì chỉ language instructions?
```

**Delegation Safety** (từ Intelligent AI Delegation framework):
```
- [ ] Skill define verification method cho output? (test, build, screenshot, curl...)
- [ ] Destructive/irreversible actions (D7≥3) có confirmation step?
- [ ] Permissions declared nếu D7≥3 hoặc D9≥2?
- [ ] High-context skills (D9≥3) có privacy guardrails?
- [ ] Output verifiability thấp (D8≥3) có human review step?
```

Nếu orchestrator, thêm:
```
- [ ] Orchestrator < 150 lines?
- [ ] Sub-skills self-contained?
- [ ] No duplicated rules?
- [ ] Routing clear?
```

### Step 5: Review & Finalize

Dùng review methodology từ `references/review-methodology.md`:
- Round 1: Logic & Consistency
- Round 2: Adversarial (bắt buộc)

→ Fix issues → commit.

---

## Mode 2: Analyze

Đánh giá quality của skill hiện có. **Chỉ report, không sửa.**

### Step 1: Read & Understand

Đọc toàn bộ skill: SKILL.md + references/ + scripts/

### Step 2: Score Complexity

Score 9 dimensions (D1-D9) → xác định level hiện tại. So sánh với pattern đang dùng — có match không?

Chú ý 3 dimensions:
- **D7 Reversibility** — skill có hành động irreversible? → cần confirmation gates
- **D8 Verifiability** — output verify tự động được? → thấp thì cần human review step
- **D9 Contextuality** — cần sensitive context? → cần permission declaration

### Step 3: Run Quality Checks

**Anthropic Standards** (`references/anthropic-skill-guidelines.md`):
- Size limits (SKILL.md < 5K words, description < 1024 chars)
- Progressive disclosure
- Composability
- Trigger accuracy

**Architecture fit:**
- Pattern đang dùng có phù hợp complexity level không?
- Nếu orchestrator: sub-skills self-contained? routing clear?

**Workflow simulation:**
- Trace 1-2 scenarios thực tế
- Identify gaps, ambiguities, edge cases

### Step 4: Report

Output dạng bảng:

```
## Kết quả phân tích: {skill-name}

**Complexity Score:** {score}/64 → Level {L1-L4}
**Pattern hiện tại:** {pattern} — {phù hợp / cần nâng cấp}

### Findings

| # | Mức | Category | Issue |
|---|---|---|---|
| 1 | 🔴 | Logic | ... |
| 2 | 🟡 | Completeness | ... |
| 3 | 🟢 | Style | ... |

### Đề xuất
- [ ] ...
```

**Không tự sửa.** User quyết định: fix ngay (→ chuyển Improve mode) hay để sau.

---

## Mode 3: Improve

Cải thiện skill hiện có qua multi-round review.

### Phase 0: Xác định mục tiêu

1. **Skill nào?** — Đọc SKILL.md hiện tại
2. **Vì sao improve?**
   - Bug/lỗi logic
   - Gap — thiếu step/edge case
   - Outdated — tool/framework đã thay đổi
   - User feedback
   - Benchmark — nâng chất lượng theo chuẩn mới
3. **Mức độ:**
   - **Patch** — sửa nhỏ, 1-2 chỗ → simplified flow (fix trực tiếp + 1 round adversarial)
   - **Improve** — bổ sung/cải thiện nhiều phần → full flow (Phase 2-4)
   - **Refactor** — đại tu cấu trúc → full flow (Phase 2-4)

→ Trình bày mục tiêu cho user confirm.

### Phase 1: Nghiên cứu (OPTIONAL)

**Chỉ khi** muốn benchmark hoặc user cung cấp nguồn tham khảo. Skip nếu improve từ bug/feedback.

1. Search GitHub repos, docs liên quan
2. Phân loại: 🔴 Nên làm | 🟡 Xem xét | 🟢 Nice to have | ❌ Không cần
3. Plan cụ thể → user approve

### Phase 2: Implement

**Patch:** Fix trực tiếp → commit → chạy 1 round adversarial → Phase 4.

**Improve/Refactor:** Đọc toàn bộ skill → xác định chỗ sửa → trình bày plan → user approve → implement
- Atomic commits sau mỗi thay đổi
- Không refactor "tiện tay"
- Check downstream: skill khác reference đến skill này không?

### Phase 3: Multi-Round Review

**Đọc chi tiết:** `references/review-methodology.md`

Tóm tắt:
1. Mỗi round chọn 1 góc khác nhau (Logic → Completeness → Simulation → ... → Adversarial)
2. Đọc toàn bộ + simulate scenario thật
3. Findings → user approve → fix → commit
4. **Dừng khi:** Adversarial round ≤ 1 issue 🟢

### Phase 4: Finalize

1. **Review** final state
2. **Commit** — clear message
3. **Ghi bài học** — pattern lỗi lặp lại → update skill này

---

## References

| File | Nội dung |
|---|---|
| `references/anthropic-skill-guidelines.md` | Anthropic quality standards + checklist |
| `references/architecture-patterns.md` | 3 patterns + complexity scoring + orchestrator templates |
| `references/review-methodology.md` | Multi-round review process, góc review, anti-patterns |
