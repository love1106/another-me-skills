# Browser Scraper

Browser automation tool for scraping JS-rendered pages, SPAs, and interactive websites.
Uses Playwright (interact mode) and Scrapling (dynamic/stealth modes).

## Prerequisites

- Python 3.9+
- Playwright browsers installed (`playwright install chromium`)
- Scrapling installed (`pip install scrapling[all] && scrapling install`)

## Script Location

`scripts/browser-scrape.py`

## Modes

### 1. Dynamic (JS-rendered pages)

Renders full page with JavaScript, waits for network idle.

```bash
python3 scripts/browser-scrape.py --url "https://spa-site.com" --mode dynamic
python3 scripts/browser-scrape.py --url "https://spa-site.com" --mode dynamic --selector ".content"
python3 scripts/browser-scrape.py --url "https://spa-site.com" --mode dynamic --screenshot /tmp/page.png
```

### 2. Stealth (anti-bot / Cloudflare bypass)

Uses Scrapling StealthyFetcher with Cloudflare solve.

```bash
python3 scripts/browser-scrape.py --url "https://protected-site.com" --mode stealth
python3 scripts/browser-scrape.py --url "https://protected-site.com" --mode stealth --selector ".data"
```

### 3. Interact (form filling, clicking, multi-step)

Full Playwright automation. Define actions as JSON array.

```bash
python3 scripts/browser-scrape.py --url "https://site.com/search" --mode interact \
  --actions '[
    {"action":"select","selector":"#country","value":"Vietnam"},
    {"action":"click","selector":"button[type=submit]"},
    {"action":"wait","ms":3000},
    {"action":"extract_table","selector":"table.results"},
    {"action":"screenshot","path":"/tmp/results.png","full_page":true}
  ]'
```

## Actions Reference (interact mode)

| Action | Required Params | Optional Params | Description |
|--------|----------------|-----------------|-------------|
| `wait` | `ms` | — | Wait N milliseconds |
| `click` | `selector` | `timeout`, `wait_after` | Click an element |
| `type` | `selector`, `value` | — | Fill text input |
| `select` | `selector`, `value` | `wait_after` | Select dropdown option |
| `scroll` | — | `direction` (up/down), `amount` | Scroll page |
| `wait_for` | `selector` | `timeout` | Wait for element to appear |
| `extract` | `selector` | — | Get inner text of matching elements |
| `extract_table` | `selector` | — | Get table as 2D array (rows × cells) |
| `extract_links` | — | `selector` (scope container) | Get all links (href + text) within scope |
| `extract_all_text` | — | — | Get all text from page body |
| `evaluate` | `expression` | `collect` (bool) | Run JavaScript expression on page, return result |
| `goto` | `url` | `wait_until` | Navigate to new URL within same browser session |
| `dismiss_overlay` | — | `selectors` (custom list) | Close cookie/consent popups. 26 auto-detect patterns (button, a, div) |
| `screenshot` | — | `path`, `full_page` | Take screenshot |

## Output Format

JSON object with:
- `url` — target URL
- `mode` — scraping mode used
- `title` — page title
- `steps[]` — array of step results (interact mode)
- `extracted[]` — collected data from extract actions
- `text` — full text (dynamic/stealth mode)

## Common Patterns

### Pagination
```json
[
  {"action":"click","selector":"button[type=submit]"},
  {"action":"wait","ms":3000},
  {"action":"extract","selector":".results .item"},
  {"action":"click","selector":".pagination .next"},
  {"action":"wait","ms":2000},
  {"action":"extract","selector":".results .item"}
]
```

### Login + Scrape
```json
[
  {"action":"type","selector":"#username","value":"user@email.com"},
  {"action":"type","selector":"#password","value":"pass123"},
  {"action":"click","selector":"button[type=submit]"},
  {"action":"wait_for","selector":".dashboard","timeout":10000},
  {"action":"extract","selector":".dashboard-data"}
]
```

### Dropdown Search Form
```json
[
  {"action":"select","selector":"#region","value":"HCM"},
  {"action":"wait","ms":1000},
  {"action":"click","selector":"#search-btn"},
  {"action":"wait","ms":3000},
  {"action":"extract_table","selector":"table.results"}
]
```

## Additional Flags

```bash
# Save output to file (useful for large datasets)
python3 scripts/browser-scrape.py --url "URL" --mode interact --actions '[...]' --output /tmp/data.json

# Custom retry count
python3 scripts/browser-scrape.py --url "URL" --mode dynamic --retries 3
```

## Troubleshooting

- **Timeout:** Increase `--timeout` (default 30000ms) or add `wait` actions
- **Element not found:** Use `wait_for` before `click`/`extract`
- **Wrong selector:** Take `screenshot` first to see actual page state
- **Anti-bot blocked:** Switch from `dynamic` to `stealth` mode
- **Need cookies/session:** Use `interact` mode with login actions first
