#!/usr/bin/env python3
"""
Browser automation scraper for hc-research-skill.
Handles JS-rendered pages, SPAs, form interactions, and anti-bot bypasses.

Usage:
  # Simple page scrape (JS-rendered)
  python3 browser-scrape.py --url "https://example.com" --mode dynamic

  # Stealth mode (anti-bot/Cloudflare)
  python3 browser-scrape.py --url "https://protected-site.com" --mode stealth

  # Interactive: fill form + click + scrape results
  python3 browser-scrape.py --url "https://site.com/search" --mode interact \
    --actions '[{"action":"select","selector":"#country","value":"Vietnam"},{"action":"click","selector":"#search-btn"},{"action":"wait","ms":3000},{"action":"extract","selector":".results"}]'

  # Full page screenshot + text
  python3 browser-scrape.py --url "https://example.com" --mode dynamic --screenshot /tmp/page.png

  # Extract specific CSS selectors
  python3 browser-scrape.py --url "https://example.com" --mode dynamic --selector ".main-content"

Output: JSON with extracted text, HTML, and metadata.
"""

import argparse
import json
import sys
import time


def scrape_dynamic(url, selector=None, screenshot=None, timeout=30000):
    """Fetch JS-rendered page using Scrapling DynamicFetcher."""
    from scrapling.fetchers import DynamicFetcher

    page = DynamicFetcher.fetch(
        url,
        headless=True,
        network_idle=True,
        timeout=timeout,
        disable_resources=False,
    )

    result = {
        "url": url,
        "mode": "dynamic",
        "status": page.status if hasattr(page, "status") else 200,
        "title": page.css("title::text").get(""),
    }

    if selector:
        elements = page.css(selector)
        result["selector"] = selector
        result["matches"] = len(elements) if hasattr(elements, "__len__") else 0
        result["text"] = (
            elements.getall() if hasattr(elements, "getall") else [str(elements)]
        )
        result["full_text"] = page.css(selector).get_text() if elements else ""
    else:
        result["text"] = page.css("body").get_text()[:50000]

    if screenshot:
        try:
            if hasattr(page, "screenshot"):
                page.screenshot(screenshot)
                result["screenshot"] = screenshot
        except Exception as e:
            result["screenshot_error"] = str(e)

    return result


def scrape_stealth(url, selector=None, screenshot=None, timeout=30000):
    """Fetch with anti-bot bypass using Scrapling StealthyFetcher."""
    from scrapling.fetchers import StealthyFetcher

    page = StealthyFetcher.fetch(
        url,
        headless=True,
        solve_cloudflare=True,
        network_idle=True,
        timeout=timeout,
    )

    result = {
        "url": url,
        "mode": "stealth",
        "status": page.status if hasattr(page, "status") else 200,
        "title": page.css("title::text").get(""),
    }

    if selector:
        elements = page.css(selector)
        result["selector"] = selector
        result["matches"] = len(elements) if hasattr(elements, "__len__") else 0
        result["text"] = (
            elements.getall() if hasattr(elements, "getall") else [str(elements)]
        )
        result["full_text"] = page.css(selector).get_text() if elements else ""
    else:
        result["text"] = page.css("body").get_text()[:50000]

    return result


def scrape_interact(url, actions, timeout=30000):
    """
    Interactive scraping: navigate, fill forms, click buttons, extract results.

    Actions format (JSON array):
    [
      {"action": "wait", "ms": 2000},
      {"action": "click", "selector": "#btn"},
      {"action": "type", "selector": "#input", "value": "text"},
      {"action": "select", "selector": "#dropdown", "value": "option_value"},
      {"action": "scroll", "direction": "down", "amount": 500},
      {"action": "wait_for", "selector": ".results", "timeout": 10000},
      {"action": "extract", "selector": ".results"},
      {"action": "extract_table", "selector": "table.data"},
      {"action": "screenshot", "path": "/tmp/step.png"}
    ]
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=timeout)

        result = {
            "url": url,
            "mode": "interact",
            "title": page.title(),
            "steps": [],
            "extracted": [],
        }

        if isinstance(actions, str):
            actions = json.loads(actions)

        for i, act in enumerate(actions):
            step_result = {"step": i + 1, "action": act["action"]}

            try:
                if act["action"] == "wait":
                    ms = act.get("ms", 1000)
                    page.wait_for_timeout(ms)
                    step_result["status"] = f"waited {ms}ms"

                elif act["action"] == "click":
                    page.click(act["selector"], timeout=act.get("timeout", 5000))
                    page.wait_for_timeout(act.get("wait_after", 1000))
                    step_result["status"] = f"clicked {act['selector']}"

                elif act["action"] == "type":
                    page.fill(act["selector"], act["value"])
                    step_result["status"] = f"typed into {act['selector']}"

                elif act["action"] == "select":
                    page.select_option(act["selector"], act["value"])
                    page.wait_for_timeout(act.get("wait_after", 1000))
                    step_result["status"] = f"selected {act['value']} in {act['selector']}"

                elif act["action"] == "scroll":
                    amount = act.get("amount", 500)
                    direction = act.get("direction", "down")
                    delta = amount if direction == "down" else -amount
                    page.mouse.wheel(0, delta)
                    page.wait_for_timeout(500)
                    step_result["status"] = f"scrolled {direction} {amount}px"

                elif act["action"] == "wait_for":
                    page.wait_for_selector(
                        act["selector"], timeout=act.get("timeout", 10000)
                    )
                    step_result["status"] = f"found {act['selector']}"

                elif act["action"] == "extract":
                    elements = page.query_selector_all(act["selector"])
                    texts = []
                    for el in elements:
                        texts.append(el.inner_text())
                    step_result["status"] = f"extracted {len(texts)} elements"
                    step_result["data"] = texts
                    result["extracted"].extend(texts)

                elif act["action"] == "extract_table":
                    table = page.query_selector(act["selector"])
                    if table:
                        rows = table.query_selector_all("tr")
                        table_data = []
                        for row in rows:
                            cells = row.query_selector_all("td, th")
                            table_data.append(
                                [cell.inner_text().strip() for cell in cells]
                            )
                        step_result["status"] = f"extracted table with {len(table_data)} rows"
                        step_result["data"] = table_data
                        result["extracted"].append(
                            {"type": "table", "rows": table_data}
                        )
                    else:
                        step_result["status"] = "table not found"

                elif act["action"] == "screenshot":
                    path = act.get("path", f"/tmp/step_{i}.png")
                    page.screenshot(path=path, full_page=act.get("full_page", False))
                    step_result["status"] = f"screenshot saved to {path}"

                elif act["action"] == "evaluate":
                    expr = act.get("expression", act.get("js", ""))
                    if expr:
                        eval_result = page.evaluate(expr)
                        step_result["status"] = "evaluated"
                        step_result["data"] = eval_result
                        if act.get("collect", False):
                            result["extracted"].append(eval_result)
                    else:
                        step_result["status"] = "error: no expression provided"

                elif act["action"] == "goto":
                    target_url = act.get("url", "")
                    if target_url:
                        page.goto(
                            target_url,
                            wait_until=act.get("wait_until", "networkidle"),
                            timeout=act.get("timeout", timeout),
                        )
                        step_result["status"] = f"navigated to {target_url}"
                    else:
                        step_result["status"] = "error: no url provided"

                elif act["action"] == "extract_links":
                    scope = act.get("selector", "body")
                    container = page.query_selector(scope)
                    if container:
                        anchors = container.query_selector_all("a[href]")
                        links = []
                        for a in anchors:
                            href = a.get_attribute("href") or ""
                            text = a.inner_text().strip()
                            if href and not href.startswith(("javascript:", "#")):
                                links.append({"text": text, "href": href})
                        step_result["status"] = f"extracted {len(links)} links"
                        step_result["data"] = links
                        result["extracted"].append(
                            {"type": "links", "items": links}
                        )
                    else:
                        step_result["status"] = f"container {scope} not found"

                elif act["action"] == "extract_all_text":
                    text = page.inner_text("body")
                    step_result["data"] = text[:50000]
                    step_result["status"] = f"extracted {len(text)} chars"
                    result["extracted"].append(text[:50000])

                elif act["action"] == "dismiss_overlay":
                    dismissed = False
                    selectors = act.get("selectors", [
                        # Button variants
                        "button:has-text('Accept')",
                        "button:has-text('Accept All')",
                        "button:has-text('Đồng ý')",
                        "button:has-text('OK')",
                        "button:has-text('Got it')",
                        "button:has-text('I agree')",
                        "button:has-text('TÔI ĐÃ HIỂU')",
                        "button:has-text('Tôi đã hiểu')",
                        # Non-button clickables (a, div, span)
                        "a:has-text('Accept')",
                        "a:has-text('Đồng ý')",
                        "a:has-text('TÔI ĐÃ HIỂU')",
                        "a:has-text('Tôi đã hiểu')",
                        "a:has-text('OK')",
                        "a:has-text('Got it')",
                        "[class*='cookie'] a",
                        "[class*='cookie'] div[role=button]",
                        # Generic cookie/consent containers
                        "[class*='cookie'] button",
                        "[id*='cookie'] button",
                        "[class*='consent'] button",
                        "[class*='consent'] a",
                        "[class*='overlay'] button",
                        "[class*='banner'] button:has-text('Accept')",
                        # Aria-based
                        "[aria-label*='cookie'] button",
                        "[aria-label*='consent'] button",
                    ])
                    for sel in selectors:
                        try:
                            btn = page.query_selector(sel)
                            if btn and btn.is_visible():
                                btn.click()
                                page.wait_for_timeout(500)
                                dismissed = True
                                step_result["status"] = f"dismissed overlay via {sel}"
                                break
                        except Exception:
                            continue
                    if not dismissed:
                        step_result["status"] = "no overlay found to dismiss"

                else:
                    step_result["status"] = f"unknown action: {act['action']}"

            except Exception as e:
                step_result["status"] = "error"
                step_result["error"] = str(e)

            result["steps"].append(step_result)

        browser.close()

    return result


def run_with_retry(func, max_retries=2, **kwargs):
    """Run a scrape function with automatic retry on failure."""
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            result = func(**kwargs)
            result["attempt"] = attempt
            return result
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait_sec = attempt * 3
                print(
                    json.dumps(
                        {
                            "retry": attempt,
                            "max": max_retries,
                            "error": str(e),
                            "waiting": f"{wait_sec}s",
                        }
                    ),
                    file=sys.stderr,
                )
                time.sleep(wait_sec)
    raise last_error


def main():
    parser = argparse.ArgumentParser(description="Browser automation scraper")
    parser.add_argument("--url", required=True, help="URL to scrape")
    parser.add_argument(
        "--mode",
        choices=["dynamic", "stealth", "interact"],
        default="dynamic",
        help="Scraping mode",
    )
    parser.add_argument("--selector", help="CSS selector to extract")
    parser.add_argument("--screenshot", help="Screenshot output path")
    parser.add_argument("--actions", help="JSON array of actions (interact mode)")
    parser.add_argument(
        "--timeout", type=int, default=30000, help="Timeout in ms (default 30000)"
    )
    parser.add_argument(
        "--retries", type=int, default=2, help="Max retries on failure (default 2)"
    )
    parser.add_argument(
        "--output", help="Write JSON output to file instead of stdout"
    )

    args = parser.parse_args()

    try:
        if args.mode == "dynamic":
            result = run_with_retry(
                scrape_dynamic,
                max_retries=args.retries,
                url=args.url,
                selector=args.selector,
                screenshot=args.screenshot,
                timeout=args.timeout,
            )
        elif args.mode == "stealth":
            result = run_with_retry(
                scrape_stealth,
                max_retries=args.retries,
                url=args.url,
                selector=args.selector,
                screenshot=args.screenshot,
                timeout=args.timeout,
            )
        elif args.mode == "interact":
            if not args.actions:
                print(
                    json.dumps(
                        {"error": "interact mode requires --actions JSON array"}
                    )
                )
                sys.exit(1)
            result = run_with_retry(
                scrape_interact,
                max_retries=args.retries,
                url=args.url,
                actions=args.actions,
                timeout=args.timeout,
            )

        output_json = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_json)
            print(json.dumps({"saved_to": args.output, "size": len(output_json)}))
        else:
            print(output_json)

    except Exception as e:
        print(
            json.dumps(
                {
                    "error": str(e),
                    "url": args.url,
                    "mode": args.mode,
                    "retries_exhausted": True,
                }
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
