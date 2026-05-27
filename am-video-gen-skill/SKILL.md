---
name: am-video-gen-skill
version: 2.7.0
author: khoidoan
description: >
  Generate, edit, and extend short videos using xAI grok-imagine-video.
  5 modes: text-to-video, image-to-video, reference-to-video, video editing, video extension.
  Triggers: "tạo video", "gen video", "generate video", "animate image", "edit video",
  "sửa video", "extend video", "kéo dài video", "image to video", "text to video".
  NOT for: long-form editing (>15s), audio sync, live streaming.
---

# Video Generation Skill

## 🔴 Critical Rule — ALWAYS Deliver Result

**Script `generate.py` chạy xong = BẮT BUỘC gọi `SendMessage` gửi video cho user NGAY trong cùng turn.**
- KHÔNG kết thúc turn mà chưa gửi video
- KHÔNG để user phải hỏi lại "video đâu?"
- Nếu fail → vẫn phải báo user lỗi gì, KHÔNG im lặng

**🔴 Retry & Progress — KHÔNG chờ user hỏi:**
- Script fail/retry → **báo user ngay** "API lỗi, đang retry..."
- All retries fail → **báo user ngay** lỗi cụ thể + đề xuất hướng khác
- Video gen > 3 phút chưa có kết quả → báo user "Đang chờ API, lâu hơn bình thường"
- KHÔNG im lặng chờ xong mới nói

**Script stdout markers:**
- `PROGRESS: ...` → **Báo user ngay** đang retry/chờ
- `FAILED: ...` → **Báo user ngay** lỗi gì + đề xuất
- `/path/to/output.mp4` → **Gửi video ngay** qua SendMessage

## Load Strategy

Read this SKILL.md always. No third-party references needed.

## Tool: `scripts/generate.py`

```bash
python3 skills/am-video-gen-skill/scripts/generate.py \
  --mode generate \
  --prompt "..." \
  --duration 5 \
  --aspect-ratio 16:9 \
  --resolution 720p
```

### Parameters

| Param | Values | Note |
|-------|--------|------|
| `--mode` | `generate` \| `edit` \| `extend` | Default: `generate` |
| `--prompt` | English string | Required except image-to-video auto |
| `--duration` | `1`–`15` (generate) / `1`–`10` (extend) | Default: 5 |
| `--aspect-ratio` | `1:1`\|`16:9`\|`9:16`\|`4:3`\|`3:4`\|`3:2`\|`2:3` | Default: `16:9`. Generate only |
| `--resolution` | `480p`\|`720p`\|`1080p` | Default: `720p`. Generate only |
| `--image` | File path | Image-to-video (animate this image) |
| `--refs` | File paths | Reference-to-video (style/subject guide) |
| `--video` | File path | Source video for edit/extend |
| `--output` | File path | Default: `outbound/vid-TIMESTAMP.mp4` |
| `--json` | flag | Output structured JSON result |
| `--dry-run` | flag | Validate without calling API |
| `--analyze` | flag | Analyze image ratio vs target, output JSON recommendation (no generation) |
| `--crop` | flag | Auto center-crop image to target ratio before generating |

### 5 Modes

| Mode | Command | Mô tả |
|------|---------|--------|
| Text-to-video | `--prompt` only | Tạo video từ text |
| Image-to-video | `--image` (+ optional `--prompt`) | Animate ảnh tĩnh. Prompt optional — model tự animate |
| Reference-to-video | `--prompt` + `--refs` | Ảnh tham chiếu (style, nhân vật, sản phẩm) |
| Video editing | `--mode edit` + `--video` + `--prompt` | Sửa video có sẵn (thêm/đổi elements). Duration/ratio/res giữ nguyên input |
| Video extension | `--mode extend` + `--video` + `--prompt` + `--duration` | Kéo dài video. Duration = phần mở rộng (1-10s), output = original + extension |

**🔴 Constraints:**
- `--image` và `--refs` KHÔNG dùng cùng lúc
- Edit/extend KHÔNG hỗ trợ custom duration/ratio/res — inherits từ input video
- Extension max 10s (auto-clamped)
- Luôn dùng `scripts/generate.py` hoặc `scripts/seedance.py`, KHÔNG dùng `VideoCreate` built-in

**⚙️ Required env vars:**
- **grok-imagine-video:** `OPENAI_BASE_URL` + `OPENAI_API_KEY`
- **Seedance 2.0:** `ARK_API_KEY` + `BYTEPLUS_ARK_BASE_URL` + `SEEDANCE_MODEL` + `SEEDANCE_FAST_MODEL`

**⏱️ Timing:**
- Text-to-video: ~60-90s (5s) / ~120-180s (10s) / ~180-240s (15s)
- Image-to-video: +30s so với text | Ref-to-video: +60s
- Edit/extend: tương đương image-to-video
- Timeout: 10 phút max

**💰 Cost Estimation (grok-imagine-video via proxy):**
- ~$0.02-0.05/video (text/image-to-video)
- +$0.03 nếu cần outpaint trước (gpt-image-2)
- Crop: $0 thêm

**📐 Resolution Guidance:**
| Res | Pixel | Speed | Use case |
|-----|-------|-------|----------|
| 480p | ~480p | Nhanh nhất | Draft/preview |
| 720p | ~720p | Cân bằng ✅ | **Mặc định — đủ cho social media** |
| 1080p | ~1080p | Chậm hơn ~50% | Presentation, website hero |

**📁 User images:** `ls -lt /root/.openclaw/media/inbound/ | head -5`

---

## Flow

### Step 0: Verify Images (if sent)

**🔴 ALWAYS verify user images with `image` tool before building prompt.**
- `image(image=<path>, prompt="What is in this image?")` for EACH image
- 1 ảnh + "animate" → `--image`
- 1 ảnh + "style/nhân vật" → `--refs`
- 2+ ảnh → `--refs` (hỏi thứ tự nếu chưa rõ)

### Step 0.5: Confirm Product Identity

**🔴 BẮT BUỘC khi có ảnh sản phẩm. KHÔNG assume loại sản phẩm từ hình dáng.**

Sau khi verify ảnh, HỎI user xác nhận:
```
📸 Em thấy ảnh là [mô tả hình dáng].
Sản phẩm này là gì? (VD: nước hoa, bình nước, loa bluetooth...)
```

**Tại sao:** Nhiều sản phẩm trông giống nhau (nước hoa vs bình nước, loa vs đèn). Assume sai → prompt sai → video sai hoàn toàn.

**Skip khi:** User đã nói rõ sản phẩm trong request (VD: "tạo video cho chai nước hoa này").

### Step 0.6: Smart Ratio Handling (Crop or Outpaint)

**🔴 Khi ảnh gốc ratio khác target ratio >10%, phải xử lý trước khi gen video.**

**Bước 1: Analyze** — chạy `--analyze` để get recommendation:
```bash
python3 skills/am-video-gen-skill/scripts/generate.py \
  --image <path> --aspect-ratio 9:16 --analyze
```
Output JSON với `action`: `none` | `crop` | `outpaint`

**Bước 2: Execute theo recommendation:**

| action | Khi nào | Cách làm | Nhược |
|--------|---------|----------|-------|
| `none` | Ratio đã match (≤10%) | Gửi thẳng | — |
| `crop` | Mất ≤50% width/height | Thêm `--crop` vào lệnh gen | Cần SP ở giữa ảnh |
| `outpaint` | Crop mất >50% | Dùng `gpt-image-2` extend trước | Chi tiết SP có thể thay đổi nhẹ (~$0.03) |

**Crop** (recommend mặc định):
```bash
python3 skills/am-video-gen-skill/scripts/generate.py \
  --image <path> --prompt "..." --aspect-ratio 9:16 --crop
```
- Center-crop ảnh về target ratio trước khi gen
- SP giữ nguyên 100% chi tiết, chỉ cắt background
- 0 cost thêm, 0 latency thêm

**Outpaint** (khi crop không đủ):
```bash
# Bước 1: Extend canvas bằng gpt-image-2
IMAGE_API_BASE="$OPENAI_BASE_URL" IMAGE_API_KEY="$OPENAI_API_KEY" \
python3 skills/am-image-gen-skill/scripts/generate.py \
  --prompt "Extend background to portrait format. Keep product exactly as-is, centered. [mô tả background]." \
  --images <path> --size 1024x1792 --quality high --output /tmp/extended.png

# Bước 2: Gen video từ ảnh đã extend
python3 skills/am-video-gen-skill/scripts/generate.py \
  --image /tmp/extended.png --prompt "..." --aspect-ratio 9:16
```
- ⚠️ Warn user: chi tiết SP có thể bị thay đổi nhẹ (tỷ lệ, màu sắc, text)

**Trình bày cho user:**
```
⚠️ Ảnh gốc [WxH] (ratio [X]) ≠ target [ratio].
🔧 Recommend: [crop/outpaint] — [reason]
[Nếu outpaint:] Lưu ý: chi tiết SP có thể thay đổi nhẹ.
Anh chọn:
1. [Crop/Outpaint] về [target_ratio]
2. Dùng [nearest_ratio] (match ảnh gốc)
```

### Step 1: Route

```
User request
├─ Has video?
│   ├─ "sửa", "edit", "thêm X vào video" → Edit mode
│   └─ "kéo dài", "extend", "tiếp tục" → Extend mode
├─ Has image(s)?
│   ├─ 1 ảnh + "animate" → Image-to-video
│   ├─ 1 ảnh + no direction → Image-to-video (auto, suggest prompt)
│   ├─ 2+ ảnh → Reference-to-video
│   └─ Unclear → ask
└─ No image/video
    ├─ Full prompt → Step 3
    └─ Vague → ask purpose
```

**🔴 KHÔNG skip confirm (Step 5).** Video tốn 2-5 phút + chi phí cao.

### Step 2: Suggest Style (2-3 options)

Tra bảng Scene Mapping → chọn kịch bản phù hợp. Skip nếu user đã specify đủ.

**Style presets:** Cinematic (slow zoom, dramatic) | Lifestyle (tracking, natural) | Minimal (static/rotate, clean) | Energetic (dynamic, bold) | Aerial (drone, wide) | Portrait (subtle, warm)

**Scene Mapping (quick ref):**

| SP | Bối cảnh | Camera | Duration |
|----|----------|--------|----------|
| Nước hoa | Marble, khói, ánh vàng | Slow zoom + orbit | 5-8s |
| Skincare | Bathroom, giọt nước, gương | Close-up → pull back | 5-8s |
| Mỹ phẩm/Son | Vanity table, petal, soft pink | Slow zoom + tilt down | 5-8s |
| Thời trang | Runway, phố, studio | Tracking shot | 8-10s |
| Giày/Sneaker | Concrete, street, studio floor | Low angle orbit | 5-8s |
| Đồng hồ | Leather pad, spotlight, macro | Extreme close-up orbit | 5-8s |
| F&B | Café, bàn gỗ, steam | Slow zoom + tilt | 5-8s |
| Tech | Bàn minimal, LED | Orbit 360° | 5s |
| Trang sức | Velvet, spotlight | Extreme close-up | 3-5s |
| Nội thất | Phòng khách, nắng | Slow pan reveal | 8-10s |
| Túi xách | Marble counter, gold accent | Slow pan + orbit | 5-8s |
| Đồ gia dụng | Kitchen/living room, natural | Medium shot + zoom | 5-8s |

### Step 3: Refine (max 2 questions)

Chỉ hỏi gì MISSING + CRITICAL. Defaults: 5s / 16:9 / 720p.

### Step 4: Build Prompt

**Always English.** Phải mô tả CHUYỂN ĐỘNG.

**Structure:** `[Camera movement] + [Subject action] + [Environment] + [Lighting/Mood]`

**Camera:** slow zoom in/out | tracking shot | static | pan L/R | drone | orbit | close-up pull back | handheld

**Temporal language (BẮT BUỘC):** "slowly", "gradually", "then", "begins to", "transitions into"

**Duration → complexity:** 1-3s = 1 action | 4-7s = 1-2 | 8-12s = 2-3 | 13-15s = 3-4

**Reference prompts:** Use `<IMAGE_1>`, `<IMAGE_2>` etc.

**Edit prompts:** Mô tả thay đổi mong muốn, ngắn gọn. VD: "Add sunglasses", "Change outfit to red dress"

**Extend prompts:** Mô tả tiếp theo. VD: "Camera zooms out to reveal cityscape"

**Negatives (append nếu cần):** `no text, no watermark, no abrupt cuts`

**🎯 Prompt Examples by Product Category:**

| Category | Example Prompt |
|----------|---------------|
| Nước hoa | `Slow orbit around a luxury perfume bottle on white marble. Golden mist particles drift slowly through warm backlight. Shallow depth of field, elegant mood.` |
| Skincare | `Close-up of skincare serum bottle as a water droplet falls slowly onto the cap, ripple effect. Camera gradually pulls back to reveal full product on bathroom shelf. Soft diffused light.` |
| Giày/Sneaker | `Low angle tracking shot of sneaker on concrete surface. Camera slowly orbits from heel to toe. Dramatic side lighting with subtle dust particles. Urban mood.` |
| F&B | `Slow zoom into a coffee cup on rustic wooden table. Steam rises gently, catching warm morning sunlight from window. Shallow focus gradually shifts to latte art.` |
| Trang sức | `Extreme close-up of diamond ring on dark velvet. Camera slowly rotates as light catches facets, creating prismatic reflections. Transitions to slight pull-back revealing full ring.` |
| Tech | `Clean orbit around wireless earbuds on minimal white desk. Soft LED glow reflects on surface. Camera completes smooth 180-degree rotation. Modern, sleek aesthetic.` |

**🔴 Image-to-video prompt tips:**
- Mô tả CHUYỂN ĐỘNG của camera/môi trường, KHÔNG mô tả lại sản phẩm (model đã thấy ảnh)
- Focus: camera movement + lighting changes + ambient effects (khói, nước, ánh sáng)
- Bad: "A perfume bottle on marble" (static, redundant with image)
- Good: "Slow orbit, golden mist drifts through backlight, subtle reflection on marble surface"

### Step 5: Confirm Before Generate

**🔴 BẮT BUỘC confirm. Không ngoại lệ.**

```
📋 Confirm:
- **Kịch bản:** [mô tả VN]
- **Mode:** [mode] | **Duration:** [N]s | **Ratio:** [ratio] | **Res:** [res]
- **⏱ Estimated:** ~[N] phút
Anh confirm em tạo nhé?
```

### Step 6: Generate

```bash
cd ~/.openclaw/workspace && \
OPENAI_BASE_URL="$HIP_IMAGE_BASE_URL" \
OPENAI_API_KEY="$HIP_IMAGE_API_KEY" \
python3 -u skills/am-video-gen-skill/scripts/generate.py \
  --mode <mode> \
  --prompt "<prompt>" \
  --duration <N> \
  --aspect-ratio <ratio> \
  --resolution <resolution> \
  [--image <path>] \
  [--crop] \
  [--refs <path1> <path2>] \
  [--video <path>]
```

**🔴 Image-to-video: ALWAYS run `--analyze` first, add `--crop` if recommended.**

**Flags:** `-u` = unbuffered progress. Set `OPENAI_BASE_URL` + `OPENAI_API_KEY` env vars.

**🔴 MUST SEND RESULT — KHÔNG ĐƯỢC KẾT THÚC TURN MÀ CHƯA GỬI VIDEO:**

Sau khi script in ra output path:
1. **NGAY LẬP TỨC** gọi `SendMessage(action=send, filePath=<output path>, caption=<description>)`
2. **Nếu SendMessage FAIL** (file quá lớn, timeout, Telegram reject):
   a. Check file size: `ls -lh <output path>`
   b. Nếu > 50MB → compress: `ffmpeg -i <path> -b:v 2M -maxrate 3M -bufsize 4M <compressed.mp4>` rồi gửi lại
   c. Nếu vẫn fail → thử gửi bằng `asDocument: true`
   d. Nếu tất cả fail → **BÁO USER NGAY**: "Video đã tạo xong nhưng gửi bị lỗi [chi tiết]. Đang thử lại..."
   e. KHÔNG BAO GIỜ im lặng khi SendMessage fail
3. Ask "Cần điều chỉnh gì không?"

⚠️ **Anti-patterns (CẤM):**
- Script chạy xong → agent kết thúc turn mà quên SendMessage → ĐÃ XẢY RA NHIỀU LẦN
- Script retry → im lặng chờ → user không biết đang xảy ra gì
- Script fail → không báo → user tưởng đang chạy
- **SendMessage fail → im lặng** → video tạo xong nhưng user không nhận được

**Error handling:**

| Error | Action |
|-------|--------|
| `CONTENT_POLICY` | Soften prompt |
| Timeout | Reduce duration/resolution, simplify prompt |
| `expired` | Retry same params |
| 401/403 | STOP — env var issue |
| 422 | Check image/video format |
| 429 | Rate limit — wait 30-60s, retry |
| 500/502/503 | Server error — retry 2-3x with backoff |

### Step 6b: Post-Process (Optional)

```bash
# Speed-up (1.2x)
ffmpeg -i input.mp4 -filter:v "setpts=PTS/1.2" -an output.mp4

# Slow-mo (0.5x)
ffmpeg -i input.mp4 -filter:v "setpts=PTS/0.5" -an output.mp4

# Trim (cut to 1s-12s)
ffmpeg -i input.mp4 -ss 1 -to 12 -c copy output.mp4

# Loop 3x
ffmpeg -stream_loop 2 -i input.mp4 -c copy output.mp4

# Reverse
ffmpeg -i input.mp4 -vf reverse -an output.mp4

# Add background music (auto-fade)
ffmpeg -i input.mp4 -i music.mp3 -shortest -c:v copy -c:a aac output.mp4

# Concatenate 2 videos
echo "file 'a.mp4'\nfile 'b.mp4'" > /tmp/list.txt
ffmpeg -f concat -safe 0 -i /tmp/list.txt -c copy output.mp4

# GIF preview (first 3s, 480px wide)
ffmpeg -i input.mp4 -t 3 -vf "fps=12,scale=480:-1" -loop 0 output.gif
```

### Step 7: Iterate

- Surgical edit prompt only. **Confirm lại** mỗi lần.
- ≤ 3 tweaks cùng base → suggest đổi hướng
- Track changes, không lặp

---

## Tư Vấn Proactive

| User yêu cầu | Tư vấn |
|-------------|--------|
| Duration 15s cho SP rotate | "3-5s đủ, 15s sẽ repetitive" |
| "Thêm chữ lên video" | "Text hay sai. Tạo video trước, overlay sau" |
| Text-to-video cho SP cụ thể | "Image-to-video giữ đúng SP hơn" |
| Nhiều người | "1 người tốt nhất, 2+ có thể méo mặt" |
| Close-up tay | "Hay bị artifact, medium shot an toàn hơn" |
| Muốn video dài hơn 15s | "Generate 15s + extend thêm 10s = 25s tổng" |
| Edit nhưng đổi quá nhiều | "Edit chỉ sửa nhẹ (thêm/đổi element). Đổi nhiều → generate mới" |
| Ảnh vuông → video 9:16 | "Ảnh 1:1 mà output 9:16 sẽ bị stretch. Dùng 1:1 giữ đúng SP, hoặc chấp nhận biến dạng nhẹ" |
| Muốn series video | "Tạo từng video riêng, giữ prompt style nhất quán. Extend nối thêm 10s nếu cần" |

---

## Aspect Ratio Quick Reference

| Platform | Ratio | Duration |
|----------|-------|----------|
| TikTok/Reels/Stories | 9:16 | 5-15s |
| YouTube/Web | 16:9 | 5-15s |
| Instagram post | 1:1 | 5-10s |

## Tool: `scripts/seedance.py` (Seedance 2.0 — Alternative)

**Khi nào dùng Seedance thay grok-imagine-video:**
- grok timeout/fail liên tục → chuyển Seedance làm fallback
- User yêu cầu nhanh (fast model ~40s vs grok ~90s)
- User muốn 1080p (Seedance 1080p ổn định hơn)

```bash
python3 skills/am-video-gen-skill/scripts/seedance.py \
  --prompt "..." \
  --duration 5 \
  --aspect-ratio 9:16 \
  --resolution 720p \
  [--image photo.jpg] \
  [--fast]
```

| Param | Values | Note |
|-------|--------|------|
| `--prompt` | English string | Required |
| `--duration` | `5` \| `10` \| `15` | Only these 3 values |
| `--aspect-ratio` | Same as grok | Default: `16:9` |
| `--resolution` | `480p`\|`720p`\|`1080p` | Default: `720p` |
| `--image` | File path | Image-to-video |
| `--fast` | flag | Fast model (~40s vs ~108s) |
| `--output` | File path | Default: `outbound/vid-TIMESTAMP-seedance.mp4` |

**⚠️ Seedance limitations vs grok:**
- KHÔNG có reference-to-video (`--refs`)
- KHÔNG có edit/extend mode
- Duration chỉ 3 giá trị (5/10/15), không tùy chỉnh
- Text-to-video + image-to-video only

**⚙️ Required env vars:** `ARK_API_KEY` + `BYTEPLUS_ARK_BASE_URL` + `SEEDANCE_MODEL` + `SEEDANCE_FAST_MODEL`

---

**🔴 Text trong video:** Luôn tạo video KHÔNG text trước, overlay text sau (CapCut/Canva). Model render text sai gần như chắc chắn. Nếu user yêu cầu text → tư vấn overlay sau, KHÔNG thêm vào prompt.

## Changelog

### v2.7.0 (2026-05-27)
- **Critical Rule:** Delivery enforcement — MUST SendMessage after generate, never end turn silently
- **Seedance 2.0:** Alt engine documented (text/image-to-video, fast mode ~40s) + `scripts/seedance.py`
- **Text overlay rule:** Always render video without text, overlay later
- **PROGRESS/FAILED markers:** stdout markers for agent to notify user
- **SendMessage fail handling:** compress (ffmpeg) → asDocument → notify user
- **Anti-patterns:** 4 banned patterns documented

### v2.6.0 (2026-05-26)
- Delivery enforcement, PROGRESS/FAILED stdout markers in generate.py
- SendMessage fail handling, anti-patterns

### v2.5.0 (2026-05-21)
- **Improve:** Submit timeout 60s→120s (large payload support for video/image base64)
- **Improve:** Payload size logging (>100KB → print size for debug)
- **Improve:** Download retry (3 attempts with backoff — was single attempt, fail=lost video)
- **Improve:** Post-process recipes: +slow-mo, loop, reverse, add music, concat, GIF preview
- **New:** Troubleshooting table (9 common issues + fixes)
- **Clean:** Changelog compacted (older entries collapsed)

### v2.4.0 (2026-05-21)
- Cached ImageMagick check, temp file cleanup (atexit), poll backoff
- Cost estimation, resolution guidance, `--crop` in Step 6, 429/5xx error handling

### v2.3.0 (2026-05-21)
- `--analyze` + `--crop` flags, smart ratio handling (crop ≤50% / outpaint >50%)
- `analyze_ratio()`, `crop_image()`, `find_nearest_ratio()`

### v2.2.0–v2.0.0 (2026-05-20–21)
- Scene Mapping 7→12 categories, prompt examples per category, image-to-video prompt tips
- Product identity confirmation (Step 0.5), ratio mismatch warning
- Remove dead padding code, dimension logging
- Video editing (`--mode edit`), extension (`--mode extend`), 1080p, auto-animate, `--json`
- Unified `submit_and_poll()`, smart image capping ≤1280px

### v1.3.0–v1.5.0 (2026-05-19–20)
- Fix image field format, aspect ratio stretch, env var snippet, timing data

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| SP bị stretch/méo trong video | Ảnh ratio ≠ target ratio | `--analyze` → `--crop` hoặc match ratio |
| Video đen/trống | Ảnh quá tối hoặc quá nhỏ | Tăng brightness, dùng ảnh ≥500px |
| SP bị biến thành vật khác | Prompt mô tả sai loại SP | Step 0.5 confirm product identity |
| Submit timeout | Payload quá lớn (video >50MB) | Compress video trước, giảm resolution |
| `expired` status | Server timeout gen phía API | Retry cùng params, giảm duration nếu lặp lại |
| Video bị loop/lặp motion | Duration quá dài cho 1 action | Giảm duration hoặc thêm action vào prompt |
| Chữ/logo sai | Model weakness | Tạo video không text, overlay sau bằng CapCut |
| `CONTENT_POLICY` | Prompt bị filter | Bỏ từ sensitive, mô tả trung tính hơn |
| Cropped video cắt mất SP | SP không ở giữa ảnh | Dùng outpaint thay crop, hoặc manual crop offset |

## Limitations

**Hard limits:**
- Max generate duration: 15 seconds | Max extension: 10 seconds
- Resolution: max 1080p (720p recommended for speed)
- No audio generation (add music via CapCut/Canva)
- Async: 1-5 phút/video
- `--image` + `--refs` mutually exclusive
- Edit: duration/ratio/res locked to input video

**Known model weaknesses:**
- ❌ Text rendering — overlay sau
- ⚠️ Tay/ngón tay — biến dạng, tránh close-up
- ⚠️ 2+ người — merge/swap faces
- ⚠️ Chuyển động nhanh — blur/artifact
- ⚠️ Logo chi tiết — không chính xác 100%
- ✅ Tốt: slow motion, product rotate, zoom, nature, smoke, lighting
