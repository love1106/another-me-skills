---
name: am-research-skill
version: 1.1.0
author: khoidoan
description: >
  Research skill — deep web search, scraping, browser automation, and information gathering
  with structured output. Handles static pages, SPAs, JS-rendered content, form interactions,
  and anti-bot bypasses via Playwright/Scrapling.
  Use when: user asks to research a topic, fact-check, compare products/tools, competitive analysis,
  market research, technical deep-dive, scrape dynamic websites, interact with web forms,
  or when built-in web_search isn't enough.
  Triggers: "research", "tìm hiểu", "so sánh", "fact check", "analyze market", "dig deeper",
  "tổng hợp", "nghiên cứu", "survey", "benchmark", "scrape", "crawl", "browser".
  NOT for: simple one-off searches (use web_search), reading a known URL (use web_fetch).
---

# Another Me Research Skill

Deep research via search APIs + web scraping. Structured methodology cho mọi loại research.

## ⚡ Budget Awareness

Mỗi search/fetch call tốn tokens → tốn stamina. Control depth theo task:

| Research Type | Max Queries | Max Scrape Calls | Khi nào |
|---|---|---|---|
| Quick lookup | 1-2 | 0 | Câu hỏi đơn giản, fact check nhanh |
| Standard | 3-5 | 1-2 | So sánh, technical research |
| Deep dive | 5-10 | 3-5 | Market research, competitive analysis |

**Quy tắc:** Bắt đầu từ ít queries nhất. Chỉ escalate khi kết quả chưa đủ. KHÔNG search 10 queries ngay từ đầu.

## Prerequisites

Browser automation cần cài thêm tools. Chạy **1 lần duy nhất** trên server:

```bash
pip install --break-system-packages scrapling[all] && scrapling install
playwright install chromium && playwright install-deps chromium
# Optional: TAVILY_API_KEY=tvly-xxxxx trong ~/.env
```

**Không cài?** Skill vẫn chạy được với `web_search` + `web_fetch`. Browser automation chỉ cần khi gặp SPA/JS-rendered pages.

## Tool Selection (Escalation Path)

```
web_search → web_fetch → Browser dynamic → Browser stealth → Browser interact
```

| Tool | Khi nào | Reference |
|------|---------|-----------|
| `web_search` | Quick search, hầu hết cases | Built-in |
| `web_fetch` | Đọc 1 URL đã biết, static page | Built-in |
| Tavily Search | Deep search + AI summary (cần `TAVILY_API_KEY`) | `references/tavily-search.md` |
| Browser Scraper | JS-rendered, SPA, forms, anti-bot | `references/browser-scraper.md` |

**Luôn dùng `scripts/browser-scrape.py`** thay vì gọi Scrapling trực tiếp. Ưu tiên `interact` mode cho extract data — chính xác hơn `dynamic`/`stealth`.

## Workflow

### Step 1: Classify Research Type

| Type | Ví dụ | Depth | Approach |
|------|-------|-------|----------|
| **Quick lookup** | "React 19 release date?" | 1 query | `web_search` → done |
| **Comparison** | "Next.js vs Remix 2026" | 3-5 queries | Multi-angle search → matrix |
| **Fact-check** | "Có đúng X không?" | 2-3 queries | Cross-reference ≥3 sources |
| **Market research** | "AI coding tools landscape" | 5-10 queries | Systematic survey → report |
| **Technical deep-dive** | "How does Bun's bundler work?" | 3-5 queries | Docs + blogs + benchmarks |
| **Repo research** | "Tìm hiểu repo X" | Clone + read | Clone → README → structure → key files |
| **Competitive analysis** | "So sánh Storims vs đối thủ" | 5+ queries | Features, pricing, reviews |
| **Dynamic site scrape** | "BNI chapter ít thành viên nhất?" | Browser + extract | Browser interact → fill form → extract data |
| **Data collection** | "Lấy danh sách X từ site Y" | Browser + pagination | Browser interact → paginate → aggregate |

### Step 2: Plan Queries / Actions

**Research types (quick lookup → competitive analysis):** Plan queries multi-angle.
**Scrape types (dynamic site scrape, data collection):** Plan browser actions — xem Step 3 Browser Automation.

**Đừng search 1 query rồi xong.** Break down thành multiple angles:

Ví dụ: "So sánh Next.js vs Remix"
```
Query 1: "Next.js vs Remix 2026 comparison"          → overview
Query 2: "Next.js 15 performance benchmarks"          → data điểm A
Query 3: "Remix performance benchmarks 2026"          → data điểm B
Query 4: "Next.js vs Remix developer experience DX"   → góc nhìn DX
Query 5: "companies migrating from Next.js to Remix"  → real-world signals
```

**Query tips:**
- Thêm năm hiện tại để lọc kết quả mới
- Dùng specific terms thay vì broad ("performance benchmarks" > "which is better")
- Search cả tiếng Anh lẫn tiếng Việt nếu relevant

### Step 3: Execute (Escalation Path)

```
web_search (built-in)
  → không đủ depth? → Tavily basic
    → vẫn thiếu? → Tavily advanced (10 results)
      → cần raw content từ page cụ thể? → web_fetch
        → page trống / JS-rendered? → Browser Scraper (dynamic)
          → bị block / anti-bot? → Browser Scraper (stealth)
            → cần click/fill form? → Browser Scraper (interact)
```

#### Browser Automation Escalation

Khi `web_fetch` trả về trang trống hoặc thiếu content (SPA, JS-rendered):

```bash
# Mode 1: Dynamic — render JS, lấy full content
python3 scripts/browser-scrape.py --url "URL" --mode dynamic

# Mode 2: Stealth — bypass anti-bot, Cloudflare
python3 scripts/browser-scrape.py --url "URL" --mode stealth

# Mode 3: Interact — fill form, click, extract results
python3 scripts/browser-scrape.py --url "URL" --mode interact \
  --actions '[
    {"action":"select","selector":"#dropdown","value":"option"},
    {"action":"click","selector":"button[type=submit]"},
    {"action":"wait","ms":3000},
    {"action":"extract","selector":".results"},
    {"action":"extract_table","selector":"table.data"}
  ]'

# Screenshot for debugging
python3 scripts/browser-scrape.py --url "URL" --mode dynamic --screenshot /tmp/page.png
```

**Interact mode actions:**
| Action | Params | Mô tả |
|--------|--------|--------|
| `wait` | `ms` | Chờ N milliseconds |
| `click` | `selector` | Click element |
| `type` | `selector`, `value` | Nhập text vào input |
| `select` | `selector`, `value` | Chọn option trong dropdown |
| `scroll` | `direction`, `amount` | Scroll trang |
| `wait_for` | `selector`, `timeout` | Chờ element xuất hiện |
| `extract` | `selector` | Lấy text từ elements |
| `extract_links` | `selector` (scope) | Lấy tất cả links (href + text) trong scope |
| `extract_table` | `selector` | Lấy data từ table (rows + cells) |
| `extract_all_text` | — | Lấy toàn bộ text trên trang |
| `evaluate` | `expression`, `collect` | Chạy JavaScript trên page, trả kết quả. `collect:true` → thêm vào extracted[] |
| `goto` | `url`, `wait_until` | Navigate đến URL mới trong cùng browser session |
| `dismiss_overlay` | `selectors` (optional) | Đóng cookie/consent popup. Auto-detect 26 patterns (button, a, div) |
| `screenshot` | `path`, `full_page` | Chụp screenshot |

**Output to file:** Thêm `--output /tmp/data.json` để ghi kết quả ra file thay vì stdout (hữu ích khi data lớn).

**Cookie banners:** Nhiều site có popup cookie chặn interaction. Thêm `dismiss_overlay` làm action đầu tiên:
```json
[
  {"action": "dismiss_overlay"},
  {"action": "click", "selector": "#search-btn"},
  ...
]
```

**Pagination:** Nếu data phân trang, chạy nhiều lần script hoặc thêm nhiều click-next + extract actions:
```json
[
  {"action": "dismiss_overlay"},
  {"action": "click", "selector": "button[type=submit]"},
  {"action": "wait", "ms": 3000},
  {"action": "extract", "selector": ".results .item"},
  {"action": "click", "selector": ".next-page, .pagination a:last-child"},
  {"action": "wait", "ms": 2000},
  {"action": "extract", "selector": ".results .item"},
  {"action": "click", "selector": ".next-page, .pagination a:last-child"},
  {"action": "wait", "ms": 2000},
  {"action": "extract", "selector": ".results .item"}
]
```
Kết quả tất cả `extract` actions gộp vào `extracted[]` array.

#### Error Handling

Script `browser-scrape.py` tự retry 2 lần. Nếu vẫn fail:
1. Thêm `--screenshot /tmp/debug.png` để xem page state
2. Escalate mode: `dynamic` → `stealth` → `interact`
3. Tăng `--timeout 60000` nếu page load chậm
4. Sau 3 lần fail → báo user kèm screenshot

**Repo research — flow riêng:**
```
git clone --depth 1 <url> /tmp/<repo-name>
→ README.md → package.json → key files → tổng hợp
```

**Rate limiting:** Tavily max 2-3 calls liên tiếp, chờ 1-2s giữa các call.

### Step 4: Cross-Reference & Validate

**Research types:**
- **≥3 sources đồng ý** → high confidence
- **2 sources conflict** → ghi rõ cả 2 quan điểm + note conflict
- **Chỉ 1 source** → ghi rõ "single source, chưa verify"
- **Số liệu / stats** → ưu tiên official docs, peer-reviewed, hoặc benchmark repos
- **Dates matter** → ghi rõ thời điểm publish, đánh dấu info cũ > 1 năm

**Scrape types:**
- **Data completeness** → kiểm tra đã lấy hết pages chưa (pagination count vs extracted count)
- **Data freshness** → ghi rõ thời điểm scrape, data có thể thay đổi
- **Spot check** → verify 2-3 items bằng web_search hoặc manual check
- **Edge cases** → entries bị thiếu cột, unicode lỗi, duplicates

### Step 5: Output

Format theo research type — mọi output PHẢI có sources:

| Type | Format |
|------|--------|
| Quick lookup | `[Answer] — Source: [URL]` |
| Comparison | Table (tiêu chí × options) + kết luận + sources |
| Fact-check | Verdict (✅/❌/⚠️) + evidence từ ≥2 sources |
| Deep-dive | Executive summary → findings → key takeaways → limitations → sources |
| Scrape | Source URL + method + records count + data (table/list) + completeness notes |

## Rules

1. **Cite sources** — mỗi claim phải có URL
2. **Ghi confidence** — ≥3 sources đồng ý = high, 1 source = "chưa verify"
3. **Không hallucinate** — không tìm thấy → nói thẳng
4. **Prefer recent** — ưu tiên < 1 năm, flag sources cũ
5. **Escalate tools** — web_fetch trống → browser dynamic → stealth → interact
6. **Respect limits** — chờ giữa requests, chỉ scrape public data, tôn trọng robots.txt
7. **Budget first** — bắt đầu ít queries, chỉ escalate khi thiếu data (xem Budget Awareness)

## Permissions

- **reads:** web pages (public URLs), git repos (shallow clone to /tmp)
- **writes:** /tmp/ (screenshots, scraped data), workspace output files
- **external:** web_search API, web_fetch API, Tavily API (optional), target websites via browser
- **destructive:** none
- **requires_confirmation:** none (read-only research)
