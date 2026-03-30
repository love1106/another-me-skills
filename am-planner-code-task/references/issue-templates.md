# Issue Templates

## GitHub Issue (Default)

```markdown
## Decision Context
- **Demand:** {signal thật hoặc assumption — ghi evidence nếu có}
- **Narrowest Wedge:** {phiên bản nhỏ nhất ship được}
- **Top Risk:** {giả định nguy hiểm nhất}
- **Scope Mode:** {Expand / Selective Expand / Hold Scope / Reduce}

> ℹ️ Section này chỉ xuất hiện khi Step 0 Challenge được chạy (feature mới, M+ size). Xóa nếu không applicable.

## Mô tả
{1-3 câu context + expected result}

## Hiện trạng
{Trạng thái hiện tại — code/feature đang làm gì, thiếu gì}

## Impact Analysis
- **Files affected:** {list files/dirs}
- **Services affected:** {list services, workers, containers}
- **Dependencies:** {external APIs, DB, queues}
- **Risk level:** 🟢 Low / 🟡 Medium / 🔴 High
- **Breaking changes:** {none / list cụ thể}

## Acceptance Criteria

### API
- [ ] {endpoint + behavior expected}

### UI
- [ ] {user action → expected result}

### Integration
- [ ] {cross-service behavior}

## Steps to Implement

### Step 1: {title}
**File:** `path/to/file`
**Effort:** S
{mô tả approach}

### Step 2: {title}
**File:** `path/to/file`
**Effort:** M
{mô tả approach}

## Test Strategy

### Unit Tests (`path/to/test.ts`)
| Test Case | Input | Expected |
|-----------|-------|----------|
| {name} | {input} | {output} |

### Integration Tests
- {flow}: {expected behavior}

### E2E Checklist
- [ ] {user flow → expected result}

## Notes
- {edge cases, warnings, related issues, migration notes}
- Related: #{issue_number} (nếu có)

## Estimate
{total: S/M/L} — breakdown theo steps ở trên
```

## Jira Format

Khi user yêu cầu Jira, convert structure trên sang Jira fields:
- **Summary** = Issue title
- **Description** = Mô tả + Hiện trạng
- **Acceptance Criteria** = custom field hoặc trong Description
- **Story Points** = map từ Estimate (S=1-2, M=3-5, L=8-13)
- **Labels** = risk level, type
- **Subtasks** = Steps to Implement (mỗi step = 1 subtask)

Output: formatted text user có thể paste vào Jira, hoặc dùng Jira CLI nếu available.

## Trello Format

- **Card Title** = Issue title
- **Description** = Mô tả + AC + Steps
- **Checklist "AC"** = Acceptance Criteria items
- **Checklist "Steps"** = Implementation steps
- **Labels** = risk level (Green/Yellow/Red)

## Monday Format

- **Item Name** = Issue title
- **Status** = "Planning"
- **Notes** = Full issue body
- **Subitems** = Steps to Implement

## Labeling Strategy

| Label | Khi nào |
|-------|---------|
| `feature` | Tính năng mới |
| `bug` | Fix lỗi |
| `enhancement` | Cải thiện existing feature |
| `refactor` | Code restructure, no behavior change |
| `risk:high` | Risk level 🔴 |
| `risk:medium` | Risk level 🟡 |
| `breaking` | Có breaking changes |
| `needs-migration` | Cần DB migration |

## Effort Sizing Guide

| Size | Meaning | Time Estimate | Examples |
|------|---------|---------------|----------|
| **S** | Trivial | < 2 hours | Add field, CRUD endpoint, UI tweak |
| **M** | Moderate | 2-8 hours | New page, multi-file logic, DB migration |
| **L** | Large | 1-3 days | New service, complex flow, multi-service |
| **XL** | Epic | > 3 days | Should be broken into smaller tasks |
