---
name: am-research-skill
version: 1.0.0
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

## Prerequisites

Browser automation cần cài thêm tools. Chạy **1 lần duy nhất** trên server:

```bash
# 1. Cài Scrapling + Playwright (browser automation)
pip install --break-system-packages scrapling[all]
scrapling install

# 2. Cài Playwright browsers
playwright install chromium
playwright install-deps chromium

# 3. (Optional) Tavily Search — deep search với AI summary
# Cần đăng ký tại https://tavily.com → lấy API key (free tier có)
# Thêm vào ~/.env: TAVILY_API_KEY=tvly-xxxxx
# Không có? web_search built-in đủ dùng cho hầu hết cases
```

**Verify:**
```bash
python3 -c "from scrapling.fetchers import Fetcher; print('Scrapling OK')"
playwright --version
```

**Không cài?** Skill vẫn chạy được với `web_search` + `web_fetch` (built-in). Browser automation chỉ cần khi gặp SPA/JS-rendered pages.

## Tool Selection

```
Cần research?
  ├─ Quick answer, 1-2 sources → web_search (built-in)
  ├─ Deep research, AI summary → Tavily Search (optional, cần API key)
  ├─ Static page content → web_fetch (built-in)
  ├─ JS-rendered / SPA → Browser Scraper (dynamic mode)
  ├─ Anti-bot / Cloudflare → Browser Scraper (stealth mode)
  ├─ Form interaction (dropdown, click, submit) → Browser Scraper (interact mode)
  └─ Crawl multi-page structured data → Browser Scraper (interact + pagination)
```

| Tool | Khi nào | API Key? | Reference |
|------|---------|----------|-----------|
| `web_search` | Quick search, hầu hết cases | Không | Built-in |
| `web_fetch` | Đọc 1 URL đã biết, static page | Không | Built-in |
| Tavily Search | Deep search, AI summary, multi-source | `TAVILY_API_KEY` | `references/tavily-search.md` |
| Browser Scraper | JS-rendered, SPA, forms, anti-bot, pagination | Không | `references/browser-scraper.md` |

**Notes:**
- Scrapling (trong `references/web-scraper.md`) là thư viện Python bên dưới Browser Scraper.
- Dùng `scripts/browser-scrape.py` thay vì gọi Scrapling trực tiếp — script đã wrap đầy đủ 3 modes.
- **Ưu tiên `interact` mode** cho extract data — `dynamic`/`stealth` modes (Scrapling) CSS selector có thể trả rỗng cho một số sites. `interact` mode (Playwright trực tiếp) extract chính xác hơn.

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

#### Error Handling & Retry

Khi browser scraping thất bại:

```
Browser error?
  ├─ Timeout → tăng --timeout (60000+), thêm wait actions
  ├─ Element not found → screenshot trước để debug selector
  ├─ Anti-bot / CAPTCHA → chuyển sang stealth mode
  ├─ Page crash → retry tối đa 2 lần, giảm disable_resources
  └─ Data incomplete → check pagination, scroll to load more
```

**Auto-retry strategy:**
1. Lần 1: chạy bình thường
2. Lần 2: tăng timeout + thêm wait
3. Lần 3: đổi mode (dynamic → stealth) hoặc thêm screenshot debug
4. Sau 3 lần fail → báo user kèm screenshot + error details

**Repo research — flow riêng:**
```
1. Clone shallow: git clone --depth 1 <url> /tmp/<repo-name>
2. Đọc README.md → hiểu mục đích, stack, setup
3. Xem structure: find . -type f | head -50, cat package.json
4. Đọc key files: entry points, config, architecture docs
5. Tổng hợp: stack, features, patterns, đánh giá quality
```
Kết hợp web search nếu cần thêm context (blog posts, reviews về repo đó).

**Parallel khi có thể:** Nếu queries independent → chạy song song (multiple web_search hoặc Tavily calls).

**Rate limiting:** Tavily — max 2-3 calls liên tiếp, chờ 1-2s giữa các call.

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

Format theo research type:

**Quick lookup:**
> [Answer] — Source: [URL]

**Comparison:**
```
## So sánh X vs Y

| Tiêu chí | X | Y |
|-----------|---|---|
| Performance | ... | ... |
| DX | ... | ... |
| Ecosystem | ... | ... |

**Kết luận:** [recommendation + reasoning]

**Sources:** [list URLs]
```

**Fact-check:**
```
## Fact Check: [claim]

**Verdict:** ✅ Đúng / ❌ Sai / ⚠️ Partly true

**Evidence:**
- Source 1: [support/contradict] — [URL]
- Source 2: [support/contradict] — [URL]

**Nuance:** [nếu có]
```

**Market research / Deep-dive:**
```
## [Topic] Research Report

### Executive Summary
[2-3 câu tóm tắt]

### Findings
#### [Sub-topic 1]
...
#### [Sub-topic 2]
...

### Key Takeaways
- ...

### Limitations
- [data gaps, bias, outdated info]

### Sources
1. [title] — [URL] (published [date])
```

**Dynamic site scrape / Data collection:**
```
## Scrape Report: [site/topic]

**Source:** [URL]
**Method:** Browser Scraper ([mode])
**Records:** [N items collected]
**Pages scraped:** [N/total]

### Data
[table hoặc structured list]

### Notes
- [data completeness: full / partial]
- [cần login? bị rate limit?]
- [thời điểm scrape]
```

## Rules

1. **Luôn cite sources** — mỗi claim phải có URL đi kèm
2. **Ghi rõ confidence level** — đặc biệt khi ít sources hoặc info conflicting
3. **Không hallucinate data** — nếu không tìm thấy → nói thẳng "không tìm thấy info về X"
4. **Prefer recent** — ưu tiên sources < 1 năm tuổi, flag nếu dùng sources cũ
5. **Separate fact vs opinion** — ghi rõ đâu là data, đâu là nhận định
6. **Escalate tools, don't give up** — nếu web_fetch trống → thử browser dynamic → stealth → interact
7. **Screenshot khi debug** — browser fail? chụp screenshot trước khi retry để xem page state
8. **Respect rate limits** — chờ giữa các request, không spam site liên tục
9. **Data scraping ethics** — chỉ scrape public data, tôn trọng robots.txt, không bypass auth trừ khi user cung cấp credentials

## Permissions

- **reads:** web pages (public URLs), git repos (shallow clone to /tmp)
- **writes:** /tmp/ (screenshots, scraped data), workspace output files
- **external:** web_search API, web_fetch API, Tavily API (optional), target websites via browser
- **destructive:** none
- **requires_confirmation:** none (read-only research)
