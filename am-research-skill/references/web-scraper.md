
# Web Scraper Skill

Extract data from difficult websites using Scrapling — adaptive scraping framework with anti-bot bypass.

## When to Use (instead of web_fetch)

| Situation | Tool |
|-----------|------|
| Simple static page | `web_fetch` |
| Page returns empty/blocked | **Scrapling** (StealthyFetcher) |
| SPA / JS-rendered content | **Scrapling** (DynamicFetcher) |
| Cloudflare protected | **Scrapling** (StealthyFetcher + solve_cloudflare) |
| Need to interact (click, scroll) | **Scrapling** (DynamicFetcher) |
| Crawl multiple pages | **Scrapling** (Spider) |
| Extract structured data (tables, lists) | **Scrapling** (CSS/XPath selectors) |

## Prerequisites

- Python 3.9+
- Playwright browsers (for DynamicFetcher/StealthyFetcher)

## Post-Install

### 1. Install Scrapling

**macOS:**
```bash
pip install scrapling[all]
scrapling install
```

**Linux (Ubuntu/Debian):**
```bash
# Fix PATH if needed (for dpkg/ldconfig)
export PATH="/usr/local/sbin:/usr/sbin:/sbin:$PATH"

# Install system dependencies for Playwright
apt-get update && apt-get install -y libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1

# Install scrapling
pip install --break-system-packages scrapling[all]

# Install Playwright browsers + system deps
playwright install-deps chromium
scrapling install
```

**With venv (recommended for both platforms):**
```bash
python3 -m venv ~/.venvs/scraper
source ~/.venvs/scraper/bin/activate
pip install scrapling[all]
scrapling install
```

### 2. Verify Installation

```bash
# Quick test - static fetch
python3 -c "
from scrapling.fetchers import Fetcher
page = Fetcher.get('https://quotes.toscrape.com/')
quotes = page.css('.quote .text::text').getall()
print(f'Found {len(quotes)} quotes')
print(quotes[0] if quotes else 'No quotes found')
"

# Test stealth fetch (bypass anti-bot)
python3 -c "
from scrapling.fetchers import StealthyFetcher
page = StealthyFetcher.fetch('https://example.com', headless=True)
print(page.css('h1::text').get())
"
```

## Usage

### 1. Quick Fetch (static sites)

```python
from scrapling.fetchers import Fetcher

page = Fetcher.get('https://example.com')
title = page.css('h1::text').get()
links = page.css('a::attr(href)').getall()
text = page.css('body').get_text()
```

### 2. Stealth Fetch (anti-bot / Cloudflare)

```python
from scrapling.fetchers import StealthyFetcher

# Bypass Cloudflare Turnstile
page = StealthyFetcher.fetch(
    'https://protected-site.com',
    headless=True,
    solve_cloudflare=True,
    network_idle=True
)
data = page.css('.content').get_text()
```

### 3. Dynamic Fetch (SPA / JS-rendered)

```python
from scrapling.fetchers import DynamicFetcher

page = DynamicFetcher.fetch(
    'https://spa-site.com',
    headless=True,
    network_idle=True,
    disable_resources=False
)
data = page.css('.dynamic-content::text').getall()
```

### 4. Session (multiple requests, keep cookies)

```python
from scrapling.fetchers import StealthySession

with StealthySession(headless=True) as session:
    login_page = session.fetch('https://site.com/login')
    dashboard = session.fetch('https://site.com/dashboard')
    data = dashboard.css('.data-table tr').getall()
```

### 5. Spider (crawl multiple pages)

```python
from scrapling.spiders import Spider, Response

class ProductSpider(Spider):
    name = "products"
    start_urls = ["https://shop.com/products"]
    concurrent_requests = 5

    async def parse(self, response: Response):
        for product in response.css('.product'):
            yield {
                "name": product.css('.name::text').get(),
                "price": product.css('.price::text').get(),
                "url": product.css('a::attr(href)').get(),
            }
        next_page = response.css('.next a::attr(href)').get()
        if next_page:
            yield response.follow(next_page)

result = ProductSpider().start()
result.items.to_json("products.json")
```

### 6. CLI (no code needed)

```bash
# Extract page content to markdown
scrapling extract get 'https://example.com' output.md

# Extract specific element
scrapling extract get 'https://example.com' output.txt --css-selector '.main-content'

# Stealth mode + Cloudflare bypass
scrapling extract stealthy-fetch 'https://protected-site.com' output.html --solve-cloudflare

# Dynamic (JS-rendered)
scrapling extract fetch 'https://spa-site.com' output.md --no-headless
```

## Selection Methods

```python
# CSS selectors (Scrapy-style)
page.css('.class')
page.css('#id')
page.css('div.product h2::text')
page.css('a::attr(href)')
page.css('.quote .text::text').getall()

# XPath
page.xpath('//div[@class="product"]')
page.xpath('//h2/text()').getall()

# BeautifulSoup-style
page.find_all('div', class_='product')
page.find_all('a', {'href': True})

# Text search
page.find_by_text('Add to Cart', tag='button')

# Navigation
element.parent
element.next_sibling
element.children
element.find_similar()
```

## Fetcher Selection Guide

```
Need to fetch a page?
  ├─ Static HTML, no protection → Fetcher (fastest)
  ├─ Need browser TLS fingerprint → Fetcher(impersonate='chrome')
  ├─ Cloudflare / anti-bot → StealthyFetcher(solve_cloudflare=True)
  ├─ SPA / JS-rendered → DynamicFetcher(network_idle=True)
  └─ Multiple requests, keep session → *Session variant
```

## Troubleshooting

- **Empty content**: Site is SPA → use `DynamicFetcher` with `network_idle=True`
- **403/Blocked**: Use `StealthyFetcher` with `solve_cloudflare=True`
- **Timeout**: Increase timeout `StealthyFetcher.fetch(url, timeout=60000)`
- **Missing browsers**: Run `scrapling install` to install Playwright browsers
- **Linux deps missing**: Run `playwright install-deps chromium`
- **dpkg errors on Linux**: Run `export PATH="/usr/local/sbin:/usr/sbin:/sbin:$PATH" && dpkg --configure -a` first
