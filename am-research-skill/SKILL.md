---
name: am-research-skill
version: 2.1.0
author: khoidoan
description: >
  Research skill — deep web search, scraping, browser automation, YouTube transcript summary,
  and information gathering with structured output.
  Use when: research topic, fact-check, compare, competitive analysis, market research,
  scrape dynamic sites, summarize YouTube video/podcast.
  Triggers: "research", "tìm hiểu", "so sánh", "fact check", "tổng hợp", "nghiên cứu",
  "tóm tắt video", "summary video", "youtube", "scrape", "crawl", "benchmark".
  NOT for: simple one-off searches (use web_search), reading a known URL (use web_fetch).
---

# Another Me Research Skill

Deep research via search APIs + web scraping. Structured methodology cho mọi loại research.

## Prerequisites

Skill chạy được với `web_search` + `web_fetch` (built-in). Optional tools check trước khi dùng:
- `python3 -c "from youtube_transcript_api import YouTubeTranscriptApi"` → YouTube transcript
- `command -v playwright` → Browser automation

## Tool Selection (Escalation)

```
web_search → web_fetch → YouTube Transcript → Browser (dynamic → stealth → interact)
```

| Tool | Khi nào | Cần cài? |
|------|---------|----------|
| `web_search` | Quick search, hầu hết cases | Built-in |
| `web_fetch` | Đọc 1 URL, static page | Built-in |
| YouTube Transcript | YouTube link → subtitle → summary | `youtube-transcript-api` |
| Browser Scraper | SPA, forms, anti-bot | `scrapling` + `playwright` |

## Workflow

### Step 1: Classify & Route

| Type | Queries | Approach |
|------|---------|----------|
| Quick lookup | 1 | `web_search` → done |
| Comparison / Fact-check | 2-5 | Multi-angle search → cross-reference |
| Market / Deep-dive | 5-10 | Systematic survey → report |
| YouTube summary | 0 | `youtube-transcript.py` → LLM summary |
| Site scrape / Data | Browser | `browser-scrape.py` → extract |
| Repo research | Clone | `git clone --depth 1` → read key files |

### Step 2: Plan Queries

**Đừng search 1 query rồi xong.** Break down multi-angle (overview + data points + DX + real-world signals).

Tips: thêm năm hiện tại, dùng specific terms, search cả tiếng Anh lẫn Việt nếu relevant.

### Step 3: Execute

Escalate theo Tool Selection ở trên. Mỗi bước thất bại → thử tool tiếp theo.

#### YouTube / Video Summary

```bash
python3 <skill_dir>/scripts/youtube-transcript.py --url "YOUTUBE_URL" --lang vi
python3 <skill_dir>/scripts/youtube-transcript.py --url "YOUTUBE_URL" --output /tmp/transcript.txt  # file dài
```

`ok: false` → báo user "Video không có phụ đề". OK → đọc transcript → tóm tắt.
Supports: `youtube.com/watch?v=`, `youtu.be/`, Shorts. Cost: $0 transcript + ~$0.01 LLM.

#### Browser Automation (nếu có)

```bash
python3 <skill_dir>/scripts/browser-scrape.py --url "URL" --mode dynamic|stealth|interact
```
Chi tiết: [references/browser-scraper.md](references/browser-scraper.md). Không có browser tools → skip, dùng `web_fetch`.

### Step 4: Validate

- **≥3 sources đồng ý** → high confidence | **1 source** → ghi "chưa verify"
- Ưu tiên sources < 1 năm, flag info cũ
- Scrape data: check completeness (pagination count vs extracted), spot check 2-3 items

### Step 5: Output

Mọi output **PHẢI có sources**. Format theo type:

| Type | Format |
|------|--------|
| Quick lookup | `[Answer] — Source: [URL]` |
| Comparison | Table (criteria × options) + kết luận + sources |
| Fact-check | Verdict (✅/❌/⚠️) + evidence từ ≥2 sources |
| Deep-dive | Summary → findings → takeaways → limitations → sources |
| YouTube summary | 📝 Summary bullets + ⏱️ duration + source link |
| Scrape | Source + method + records count + data table + completeness notes |

## Rules

1. **Cite sources** — mỗi claim phải có URL
2. **Không hallucinate** — không tìm thấy → nói thẳng
3. **Escalate tools** — web_fetch trống → browser dynamic → stealth → interact
4. **Respect limits** — chờ giữa requests, chỉ scrape public data, tôn trọng robots.txt
5. **Prefer free transcript** — YouTube có subtitle → dùng transcript API ($0), KHÔNG dùng Whisper

## Permissions

**reads:** web pages, git repos (shallow clone) | **writes:** /tmp/ (screenshots, data) | **external:** web_search, web_fetch, Tavily, browser, YouTube transcript API | **destructive:** none
