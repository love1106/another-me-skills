# Unit Testing Reference

## Core Philosophy

**Tests tồn tại để TÌM LỖI, không phải để confirm code đúng.**

Nếu viết xong chạy pass 100% ngay → tự hỏi: tests đã đủ aggressive chưa?

## TDD Flow (BẮT BUỘC)

Viết test TRƯỚC implementation. Flow:

```
1. Đọc requirement/spec/contract → KHÔNG đọc implementation
2. Viết tests từ góc nhìn người dùng function
3. Chạy tests → PHẢI có tests FAIL (Red)
4. Implement code → tests pass (Green)
5. Refactor → tests vẫn pass
```

**Khi viết tests cho code ĐÃ CÓ:**
```
1. Đọc requirement/spec/contract → KHÔNG đọc implementation trước
2. Viết tests dựa trên requirement
3. Chạy tests → nếu có FAIL:
   a. KHÔNG vội sửa test cho match implementation
   b. So sánh: requirement nói gì vs implementation làm gì
   c. Nếu khác nhau → ĐÂY LÀ GAP → xem section "Gap Discovery" bên dưới
4. Sau khi resolve gaps → bổ sung edge case tests
```

## Spec-First Testing

### Đọc gì TRƯỚC khi viết test:
- README, docs, API contract, type signatures
- Function/method signatures + JSDoc/docstring
- Interface definitions, OpenAPI spec
- PR description, issue description, acceptance criteria

### KHÔNG đọc trước:
- Implementation code (function body)
- Existing tests (đọc SAU khi viết xong tests mới, để so sánh coverage)

### Tại sao?
Đọc implementation trước → vô thức viết test follow code path → confirmation bias.
Test chỉ cover happy path mà dev nghĩ tới, bỏ qua edge cases dev không nghĩ tới.

## Gap Discovery (QUAN TRỌNG)

Khi tests fail trên code đã có, có 3 khả năng:

| Khả năng | Dấu hiệu | Action |
|----------|-----------|--------|
| **Bug thật** | Requirement rõ ràng, code sai | Report bug, fix code |
| **Requirement outdated** | Code đã evolve, requirement chưa update | **PHẢI discuss với user** — không tự quyết |
| **Test sai** | Test hiểu sai requirement | Fix test |

### ⚠️ KHÔNG BAO GIỜ tự assume requirement đúng hay sai

Khi phát hiện gap giữa requirement và behavior hiện tại:
1. **Dừng lại** — không tự sửa test hay code
2. **Báo user** rõ ràng:
   - Requirement nói: X
   - Code hiện tại làm: Y  
   - Existing tests expect: Z (nếu có)
3. **Hỏi:** "Requirement hay implementation đúng trong context hiện tại?"
4. **User quyết định** → cập nhật test/code/requirement tương ứng

Lý do: requirement có thể đã thay đổi ngầm qua discussions, Slack, meetings mà docs chưa update.
Agent không có context đó — chỉ user mới biết intent thật sự.

## Test Design: Góc nhìn người dùng function

### Input Categories (PHẢI cover)

| Category | Ví dụ | Mục đích |
|----------|-------|----------|
| **Happy path** | Valid input, expected flow | Baseline |
| **Edge cases** | Empty string, empty array, null, undefined, 0 | Boundary behavior |
| **Boundary values** | Min, max, off-by-one, INT_MAX, float precision | Overflow/underflow |
| **Invalid input** | Wrong type, negative where positive expected, NaN | Error handling |
| **State-dependent** | Already exhausted → deduct again, closed → reopen | State machine coverage |

### Ví dụ: `deductFromBalance(accountId, amount)`

```
Requirement: "Trừ amount từ balance. Nếu balance < amount → reject. Nếu balance = 0 → return exhausted."

Tests NÊN viết (từ requirement, chưa đọc code):
✅ Deduct thành công khi balance đủ
✅ Reject khi balance < amount (balance=50, amount=100)
✅ Return exhausted khi balance = 0
✅ amount = 0 → hành vi gì? (Requirement không nói → HỎI)
✅ amount âm → hành vi gì? (Requirement không nói → HỎI hoặc expect error)
✅ accountId không tồn tại → error handling
✅ Concurrent deducts → race condition (2 request cùng lúc, balance chỉ đủ 1)
✅ Deduct exact balance (balance=100, amount=100) → 0 hay exhausted?
✅ Precision: balance=0.1, amount=0.1 → floating point issues?

Tests KHÔNG NÊN viết (confirmation bias):
❌ Test internal helper function mà user không gọi trực tiếp
❌ Test implementation detail (dùng Redis hay memory cache)
❌ Copy logic từ implementation vào test assertion
```

## Prompt Template cho Claude CLI

Khi delegate viết tests qua Claude CLI, dùng prompt structure:

```
Write unit tests for [module/function].

REQUIREMENT:
[paste requirement/spec — KHÔNG paste implementation]

RULES:
- TDD approach: write tests FIRST based on requirement only
- DO NOT read the implementation before writing tests
- Focus on finding bugs, not confirming correctness
- Cover: happy path, edge cases, boundary values, invalid input, state transitions
- Each test should have a clear name describing the expected behavior
- If requirement is ambiguous about a case → add a TODO test with a question
- DO NOT git commit or push

TEST STRUCTURE:
- describe("<FunctionName>", () => { ... })
- Group by: happy path → edge cases → error handling → state transitions
- Use descriptive test names: "should reject when balance insufficient"
- One assertion per behavior (prefer multiple small tests over fewer large ones)
```

**Khi viết tests cho code đã có, thêm vào prompt:**
```
IMPORTANT — GAP DISCOVERY:
After writing tests from requirement, run them against existing code.
If any test FAILS:
- Do NOT fix the test to match implementation
- Do NOT fix the implementation
- Instead, report the gap:
  - What the requirement says
  - What the code actually does
  - What existing tests expect (if any)
  - Let ME decide which is correct
```

## Anti-Patterns (TRÁNH)

| Anti-pattern | Tại sao sai | Thay bằng |
|-------------|------------|-----------|
| Đọc implementation → viết test match code | Confirmation bias, miss bugs | Đọc spec → viết test → chạy |
| `expect(result).toBe(result)` | Tautology, test nothing | Assert expected VALUE from requirement |
| Mock everything | Test mock, không test real behavior | Mock boundaries only (DB, API, network) |
| Test private/internal methods | Coupling to implementation | Test public API/contract |
| 100% line coverage as goal | False confidence, miss logic bugs | Cover behavior categories above |
| Copy implementation logic into test | If code wrong, test wrong too | Derive expected values independently |
| Ignore flaky tests | Hide real issues | Fix or quarantine immediately |

## Coverage Strategy

- **Không set hard threshold** — coverage là signal, không phải goal
- **Ưu tiên:** Critical paths > edge cases > happy paths (happy path thường đã tested qua dev)
- **Đo bằng:** behavior coverage (đã test đủ categories chưa), không chỉ line coverage
- **New code:** mọi function mới PHẢI có tests (TDD flow)
- **Existing code:** viết tests khi touch (boy scout rule), không cần retroactive full coverage
