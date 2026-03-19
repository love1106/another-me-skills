# Browser Verify — PinchTab Reference

Verify UI changes in a real browser using PinchTab — headless Chrome controlled via CLI/HTTP API.

## Prerequisites

- **PinchTab** installed (`pinchtab` CLI available in PATH)
- **Chrome/Chromium** installed on the machine
- Dev server running (e.g., `npm run dev` on localhost)

## Install PinchTab

```bash
# One-liner (recommended)
curl -fsSL https://pinchtab.com/install.sh | bash

# Or via npm
npm install -g pinchtab

# Verify
pinchtab --version
```

## Usage

### Quick Verify (single page)

```bash
pinchtab &>/tmp/pinchtab.log &
sleep 3
pinchtab nav http://localhost:3000/orders
pinchtab snap -i -c
pinchtab text
pinchtab screenshot -o /tmp/orders-page.png
pkill -f "pinchtab"
```

### Form Testing

⚠️ **Quan trọng:**
- Sau `nav`, phải `snap` trước để lấy refs mới
- Dùng `click` + `type` (không dùng `fill` — có thể không trigger input events)
- Form submit: dùng `eval "document.querySelector('form').submit()"` hoặc `press <ref> Enter`

```bash
pinchtab nav http://localhost:3000/login
sleep 2
pinchtab snap -i -c       # Lấy refs: e2=username, e3=password, e1=submit

pinchtab click e2
pinchtab type e2 "admin@test.com"
pinchtab click e3
pinchtab type e3 "password123"

# Submit (chọn 1 cách)
pinchtab press e3 Enter
# hoặc: pinchtab eval "document.querySelector('form').submit()"

sleep 2
pinchtab snap -i -c       # Verify redirect
pinchtab text             # Verify success message
pinchtab screenshot -o /tmp/login-result.png
```

### Multi-Page Flow

```bash
# Login
pinchtab nav http://localhost:3000/login
pinchtab fill e3 "admin@test.com"
pinchtab fill e5 "password123"
pinchtab click e7
sleep 2

# Navigate to feature
pinchtab nav http://localhost:3000/dashboard
pinchtab snap -i -c
pinchtab screenshot -o /tmp/dashboard.png

# Test new feature
pinchtab click e12
sleep 1
pinchtab snap -i -c
pinchtab screenshot -o /tmp/new-feature.png
```

### JavaScript Execution

```bash
pinchtab eval "window.__errors || 'no errors'"
pinchtab eval "getComputedStyle(document.querySelector('.header')).display"
pinchtab eval "document.documentElement.clientWidth"
```

## Claude CLI Integration

When using Claude CLI (Step 5), include PinchTab in allowed tools:

```bash
--allowedTools "Bash(pinchtab:*)"
```

## Cheat Sheet

| Task | Command |
|------|---------|
| Start server | `pinchtab &>/tmp/pinchtab.log &` |
| Health check | `curl -s http://localhost:9867/health` |
| Navigate | `pinchtab nav <url>` |
| Snapshot (compact) | `pinchtab snap -i -c` |
| Extract text | `pinchtab text` |
| Click element | `pinchtab click <ref>` |
| Type text | `pinchtab type <ref> "text"` |
| Fill input | `pinchtab fill <ref> "text"` ⚠️ may not trigger events |
| Press key | `pinchtab press <ref> Enter` |
| Submit form | `pinchtab eval "document.querySelector('form').submit()"` |
| Screenshot | `pinchtab screenshot -o <path>` |
| PDF export | `pinchtab pdf -o <path>` |
| Run JS | `pinchtab eval "expression"` |
| Stop | `pkill -f "pinchtab"` |

## Verification Checklist

- [ ] Page loads without errors
- [ ] Key elements visible (headings, buttons, forms)
- [ ] Text content correct
- [ ] Interactive elements work (click, fill, submit)
- [ ] Navigation flows correct
- [ ] No console errors (`pinchtab eval "window.__errors"`)
- [ ] Screenshot captured for PR evidence

## Known Issues & Workarounds

| Issue | Workaround |
|-------|-----------|
| `fill` không trigger input events | Dùng `click` + `type` thay vì `fill` |
| `click` button không submit form | Dùng `eval "form.submit()"` hoặc `press <ref> Enter` |
| Refs thay đổi sau navigate | Luôn `snap` lại sau `nav` để lấy refs mới |
| Compact refs (`-c`) khác full refs | Dùng compact refs (`-i -c`) nhất quán |

## Troubleshooting

- **"connection refused"**: PinchTab not running → `pinchtab &>/tmp/pinchtab.log &`
- **"ref e5 not found"**: Page changed hoặc chưa snap → `pinchtab snap -i -c` trước
- **Blank screenshot**: Page still loading → add `sleep 2` before screenshot
- **Chrome not found**: Install Chrome or set `CHROME_PATH=/path/to/chrome`
- **Port conflict**: `PINCHTAB_PORT=9870 pinchtab` to use different port
