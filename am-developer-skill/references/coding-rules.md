# Coding Rules — Defensive Programming

Rules bắt buộc khi viết code. Inject vào prompt cho Claude CLI.

## 1. Null/Undefined Check

**LUÔN dùng optional chaining + nullish coalescing.** Không bao giờ assume property tồn tại.

```typescript
// ❌ Crash nếu user hoặc address null
const city = user.address.city;

// ✅ Safe
const city = user?.address?.city ?? "Unknown";
```

**Khi nào check:**
- Dữ liệu từ API response
- Object nested > 1 level (`a.b.c`)
- Array access (`arr[0]?.prop`)
- Function params có thể undefined
- `Map.get()`, `find()`, `querySelector()` — luôn có thể trả null

## 2. Guard Clause (Early Return)

**Return sớm khi điều kiện không hợp lệ.** Tránh nested if.

```typescript
// ❌ Nested hell
function processOrder(order) {
  if (order) {
    if (order.items.length > 0) {
      if (order.status === "pending") {
        // actual logic buried 3 levels deep
      }
    }
  }
}

// ✅ Guard clauses
function processOrder(order) {
  if (!order) return;
  if (order.items.length === 0) return;
  if (order.status !== "pending") return;

  // actual logic at top level
}
```

**Rules:**
- Validate inputs ở đầu function
- Mỗi guard clause = 1 validation + early return/throw
- Logic chính ở cuối, không bị indent

## 3. Error Handling có Context

**KHÔNG BAO GIỜ swallow errors.** Mọi catch block phải log hoặc re-throw với context.

```typescript
// ❌ Nuốt error — debug nightmare
try { await saveUser(data); } catch (e) {}

// ❌ Error message vô nghĩa
catch (e) { throw new Error("Something went wrong"); }

// ✅ Context rõ ràng: cái gì, ở đâu, giá trị gì
catch (e) {
  throw new Error(`Failed to save user id=${data.id}: ${e.message}`);
}

// ✅ Log + re-throw
catch (e) {
  console.error(`[OrderService] Payment failed for order ${orderId}:`, e);
  throw e;
}
```

**Rules:**
- `catch (e) {}` trống = BUG. Luôn handle.
- Error message format: `[Module/Context] What failed + relevant data: original error`
- Không expose internal details ra client (stack trace, SQL, file paths)
- API responses: trả error code + user-friendly message, log chi tiết server-side

## 4. Input Validation ở Boundary

**Validate tại điểm dữ liệu đi vào hệ thống.** Không trust anything from outside.

```typescript
// ❌ Trust API input
app.post("/users", (req, res) => {
  db.insert(req.body); // SQL injection, invalid data
});

// ✅ Validate trước khi xử lý
app.post("/users", (req, res) => {
  const { email, name } = req.body;
  if (!email || !isValidEmail(email)) return res.status(400).json({ error: "Invalid email" });
  if (!name || name.length > 200) return res.status(400).json({ error: "Invalid name" });

  db.insert({ email: sanitize(email), name: sanitize(name) });
});
```

**Boundaries cần validate:**
- API endpoints (req.body, req.params, req.query)
- Environment variables (check tồn tại khi startup)
- File input (check exists, check format)
- User input từ forms
- Data từ external APIs / third-party services

## 5. Edge Cases: Empty, Zero, False

**Phân biệt rõ "không có giá trị" vs "giá trị hợp lệ là 0/empty/false".**

```typescript
// ❌ Bug: if (!count) catches cả count === 0
if (!count) return "No items";

// ✅ Check chính xác
if (count == null) return "No items";  // null hoặc undefined
if (count === 0) return "Empty cart";  // zero là valid value

// ❌ Bug: empty string "" là falsy
const name = user.name || "Anonymous";  // "" bị thay bằng "Anonymous"

// ✅ Nullish coalescing — chỉ replace null/undefined
const name = user.name ?? "Anonymous";  // "" giữ nguyên
```

**Checklist:**
- `||` vs `??` — dùng `??` khi `0`, `""`, `false` là giá trị hợp lệ
- Array: check `arr.length === 0` thay vì `!arr`
- String: check `str === ""` hoặc `str.trim() === ""` thay vì `!str`
- Number: check `num == null` thay vì `!num` (vì `!0` = true)

## 6. Async Race Conditions

**Cleanup async operations. Tránh stale closures.**

```typescript
// ❌ React: update state sau unmount
useEffect(() => {
  fetchData().then(setData);
}, []);

// ✅ Abort controller
useEffect(() => {
  const controller = new AbortController();
  fetchData({ signal: controller.signal })
    .then(setData)
    .catch((e) => {
      if (e.name !== "AbortError") throw e;
    });
  return () => controller.abort();
}, []);

// ❌ Stale closure: click nhanh 2 lần → response cũ ghi đè mới
const handleSearch = async (query) => {
  const results = await search(query);
  setResults(results); // response của query cũ có thể đến sau
};

// ✅ Track latest request
const latestRef = useRef(0);
const handleSearch = async (query) => {
  const id = ++latestRef.current;
  const results = await search(query);
  if (id === latestRef.current) setResults(results); // chỉ dùng response mới nhất
};
```

## 7. Immutable Params

**Không mutate function arguments.** Clone/spread trước khi modify.

```typescript
// ❌ Mutate input — caller không biết object đã bị thay đổi
function addDiscount(order) {
  order.total *= 0.9;  // modified original object!
  return order;
}

// ✅ Return new object
function addDiscount(order) {
  return { ...order, total: order.total * 0.9 };
}

// ❌ Mutate array param
function sortUsers(users) {
  return users.sort((a, b) => a.name.localeCompare(b.name)); // .sort() mutates!
}

// ✅ Spread trước khi sort
function sortUsers(users) {
  return [...users].sort((a, b) => a.name.localeCompare(b.name));
}
```

## 8. Meaningful Error Messages

**Error message phải trả lời: Cái gì lỗi? Ở đâu? Giá trị thực tế?**

```typescript
// ❌ Vô nghĩa
throw new Error("Invalid input");
throw new Error("Not found");
throw new Error("Error occurred");

// ✅ Đủ context để debug
throw new Error(`User not found: id=${userId}`);
throw new Error(`Invalid status transition: ${currentStatus} → ${newStatus}`);
throw new Error(`ENV missing: DATABASE_URL is required but not set`);
throw new Error(`API rate limit exceeded: ${endpoint}, retry after ${retryAfter}s`);
```

**Format:** `[What failed]: [details with actual values]`

## 9. Next.js Env Vars: NEVER Expose Secrets to Client

**`NEXT_PUBLIC_` prefix = exposed to browser. KHÔNG BAO GIỜ dùng cho secrets.**

```env
# ❌ NGUY HIỂM — secret lộ ra browser, ai cũng thấy
NEXT_PUBLIC_DATABASE_URL=postgres://user:pass@host/db
NEXT_PUBLIC_API_SECRET=sk-xxx
NEXT_PUBLIC_STRIPE_SECRET_KEY=sk_live_xxx

# ✅ Server-only — chỉ accessible trong API Routes, Server Components, middleware
DATABASE_URL=postgres://user:pass@host/db
API_SECRET=sk-xxx
STRIPE_SECRET_KEY=sk_live_xxx

# ✅ NEXT_PUBLIC_ chỉ cho public config (không phải secret)
NEXT_PUBLIC_APP_URL=https://myapp.com
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_xxx
NEXT_PUBLIC_GA_ID=G-XXXXXXX
```

**Rules:**
- `NEXT_PUBLIC_` = client-side, công khai, bất kỳ ai inspect browser đều thấy
- Secrets (DB, API keys, tokens, passwords) → **KHÔNG CÓ** `NEXT_PUBLIC_` prefix
- Publishable keys (Stripe pk_, GA ID, app URL) → OK dùng `NEXT_PUBLIC_`
- Nếu cần secret ở client → gọi qua API Route (server-side) rồi trả result về

## Tóm tắt — Inject vào Claude CLI Prompt

```
Coding rules (MUST follow):
1. Always use optional chaining (?.) and nullish coalescing (??) — never assume properties exist
2. Use guard clauses — validate + early return, no nested ifs
3. Never swallow errors — every catch must log or re-throw with context
4. Validate inputs at boundaries — API params, env vars, user input
5. Distinguish empty/zero/false from null — use ?? not ||, check explicitly
6. Handle async cleanup — abort controllers, stale closure prevention
7. Don't mutate function params — spread/clone before modifying
8. Error messages must include: what failed + actual values
9. Next.js: NEVER use NEXT_PUBLIC_ for secrets (DB, API keys, tokens) — only for public config
```
