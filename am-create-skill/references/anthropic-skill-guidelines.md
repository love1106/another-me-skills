# Anthropic Skill Guidelines

Source: "The Complete Guide to Building Skills for Claude" (Anthropic, 2025)

## 3 Design Principles

### 1. Progressive Disclosure (3 tầng)
```
Layer 1: YAML Frontmatter — LUÔN load (name, description)
Layer 2: SKILL.md body — load khi skill relevant
Layer 3: references/, scripts/ — load KHI CẦN trong workflow
```
→ Giảm token consumption. Chỉ load chi tiết khi thật sự cần.

### 2. Composability
- Skill phải hoạt động tốt cùng skills khác
- Không conflict naming, không assume exclusive access
- Shared resources phải documented

### 3. Portability
- Skill nên chạy được trên: Claude.ai, Claude Code, API
- Tránh hard-dependency vào platform-specific features
- Fallback paths cho khi tool không available

## YAML Frontmatter Rules

```yaml
---
name: kebab-case-name          # BẮT BUỘC
description: >                 # BẮT BUỘC, <1024 chars
  What it does + When to use + Trigger phrases
license: MIT                   # optional
metadata:
  author: Company
  version: 1.0.0
---
```

**Cấm:**
- XML tags `< >` trong frontmatter
- Tên chứa "claude" hoặc "anthropic"
- Description > 1024 chars

**Description phải có:**
- **What**: skill làm gì
- **When**: khi nào dùng (conditions)
- **Trigger phrases**: từ khóa cụ thể để match (VD: "create skill", "audit skill", "review UX")
- **NOT for**: khi nào KHÔNG dùng

## Size Limits

| Component | Limit |
|-----------|-------|
| SKILL.md body | < 5,000 words |
| Description | < 1,024 chars |
| References | Không limit, nhưng mỗi file nên focused |

→ Nếu SKILL.md > 5,000 words → tách chi tiết sang `references/`

## 3 Loại Skill

| Loại | Dùng khi | Ví dụ |
|------|----------|-------|
| **Document/Asset Creation** | Tạo output nhất quán | frontend-design, docx, pptx |
| **Workflow Automation** | Quy trình nhiều bước | skill-creator, developer-skill |
| **MCP Enhancement** | Tăng sức mạnh cho MCP tool | sentry-code-review |

## 5 Patterns

1. **Sequential Workflow** — multi-step theo thứ tự (A→B→C)
2. **Multi-MCP Coordination** — phối hợp nhiều service/tools
3. **Iterative Refinement** — cải thiện output qua vòng lặp
4. **Context-aware Tool Selection** — chọn tool theo context
5. **Domain-specific Intelligence** — nhúng domain knowledge vào instructions

## Testing 3 Tầng

### Tier 1: Triggering
- Skill có load đúng khi task match không?
- Description triggers đúng scenarios?
- Không false-positive (load khi không cần)?

### Tier 2: Functional
- Output có đúng format/quality không?
- Edge cases handled?
- Error paths có fallback?

### Tier 3: Performance
- So sánh kết quả có skill vs không skill
- Token consumption hợp lý?
- Thời gian execution chấp nhận được?

## Quality Checklist

Dùng checklist này khi tạo mới hoặc review skill:

```
STRUCTURE:
- [ ] SKILL.md < 5,000 words?
- [ ] Chi tiết nặng đã tách sang references/?
- [ ] Progressive disclosure: 3 layers rõ ràng?

FRONTMATTER:
- [ ] name: kebab-case, không chứa "claude"/"anthropic"?
- [ ] description: < 1024 chars?
- [ ] description có: What + When + Trigger phrases + NOT for?

COMPOSABILITY:
- [ ] Không conflict với skills khác?
- [ ] Shared resources documented?
- [ ] Có thể dùng alongside skills khác?

ROBUSTNESS:
- [ ] Scripts cho validation (không chỉ language instructions)?
- [ ] Error handling / fallback paths?
- [ ] Edge cases documented?

DELEGATION SAFETY (ref: Intelligent AI Delegation, arXiv:2602.11865):
- [ ] Output verification method defined? (test, build, screenshot, curl...)
- [ ] Destructive/irreversible actions có confirmation step?
- [ ] Permissions declared? (reads/writes/external/destructive/requires_confirmation)
- [ ] High-context skills có privacy guardrails?
- [ ] Low-verifiability output có human review step?

TESTING:
- [ ] Triggering: match đúng scenarios?
- [ ] Functional: output đúng?
- [ ] Performance: token consumption hợp lý?
```

## Tips

- Dùng **scripts cho validation** thay vì dựa hoàn toàn vào language instructions
- Không quá **20-50 skills** enable cùng lúc (token pressure)
- Description là yếu tố **quan trọng nhất** cho triggering — đầu tư viết kỹ
- Mỗi skill nên có **1 concern chính** — không multipurpose
