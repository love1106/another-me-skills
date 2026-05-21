---
name: am-video-gen-skill
version: 2.0.1
author: khoidoan
description: >
  Generate, edit, and extend short videos using xAI grok-imagine-video.
  5 modes: text-to-video, image-to-video, reference-to-video, video editing, video extension.
  Triggers: "tạo video", "gen video", "generate video", "animate image", "edit video",
  "sửa video", "extend video", "kéo dài video", "image to video", "text to video".
  NOT for: long-form editing (>15s), audio sync, live streaming.
---

# Video Generation Skill

Converted from hc-video-gen-skill v2.0.0.

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

### 5 Modes

| Mode | Command | Mô tả |
|------|---------|--------|
| Text-to-video | `--prompt` only | Tạo video từ text |
| Image-to-video | `--image` (+ optional `--prompt`) | Animate ảnh tĩnh. Prompt optional — model tự animate |
| Reference-to-video | `--prompt` + `--refs` | Ảnh tham chiếu (style, nhân vật, sản phẩm) |
| Video editing | `--mode edit` + `--video` + `--prompt` | Sửa video có sẵn. Duration/ratio/res giữ nguyên input |
| Video extension | `--mode extend` + `--video` + `--prompt` + `--duration` | Kéo dài video. Duration = phần mở rộng (1-10s) |

**�� Constraints:**
- `--image` và `--refs` KHÔNG dùng cùng lúc
- Edit/extend KHÔNG hỗ trợ custom ratio/res — inherits từ input video
- Extension max 10s (auto-clamped)
- Luôn dùng `scripts/generate.py`, KHÔNG dùng `VideoCreate` built-in

**⚙️ Env vars (priority: VIDEO_* > OPENAI_*):**
- `VIDEO_API_BASE` or `OPENAI_BASE_URL`
- `VIDEO_API_KEY` or `OPENAI_API_KEY`
- `VIDEO_OUTBOUND_DIR` (optional)

**⏱️ Timing:**
- Text-to-video: ~60-90s (5s) / ~120-180s (10s) / ~180-240s (15s)
- Image-to-video: +30s | Ref-to-video: +60s | Edit/extend: tương đương i2v
- Timeout: 10 phút max

---

## Flow

### Step 0: Verify Images (if sent)

**🔴 ALWAYS verify user images before building prompt.**
- 1 ảnh + "animate" → `--image`
- 1 ảnh + "style/nhân vật" → `--refs`
- 2+ ảnh → `--refs` (hỏi thứ tự nếu chưa rõ)

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

Skip nếu user đã specify đủ.

**Style presets:** Cinematic | Lifestyle | Minimal | Energetic | Aerial | Portrait

**Scene Mapping:**

| SP | Bối cảnh | Camera | Duration |
|----|----------|--------|----------|
| Nước hoa | Marble, khói, ánh vàng | Slow zoom + orbit | 5-8s |
| Skincare | Bathroom, giọt nước | Close-up → pull back | 5-8s |
| Thời trang | Runway, phố, studio | Tracking shot | 8-10s |
| F&B | Café, bàn gỗ, steam | Slow zoom + tilt | 5-8s |
| Tech | Bàn minimal, LED | Orbit 360° | 5s |
| Trang sức | Velvet, spotlight | Extreme close-up | 3-5s |
| Nội thất | Phòng khách, nắng | Slow pan reveal | 8-10s |

### Step 3: Refine (max 2 questions)

Chỉ hỏi gì MISSING + CRITICAL. Defaults: 5s / 16:9 / 720p.

### Step 4: Build Prompt

**Always English.** Phải mô tả CHUYỂN ĐỘNG.

**Structure:** `[Camera movement] + [Subject action] + [Environment] + [Lighting/Mood]`

**Camera:** slow zoom | tracking shot | static | pan L/R | drone | orbit | close-up pull back | handheld

**Temporal language (BẮT BUỘC):** "slowly", "gradually", "then", "begins to"

**Duration → complexity:** 1-3s = 1 action | 4-7s = 1-2 | 8-12s = 2-3 | 13-15s = 3-4

**Reference prompts:** Use `<IMAGE_1>`, `<IMAGE_2>` etc.

**Edit prompts:** Mô tả thay đổi. VD: "Add sunglasses", "Change outfit to red"

**Extend prompts:** Mô tả tiếp theo. VD: "Camera zooms out to reveal cityscape"

**Negatives:** `no text, no watermark, no abrupt cuts`

### Step 5: Confirm Before Generate

**🔴 BẮT BUỘC confirm. Không ngoại lệ.**

```
📋 Confirm:
- **Kịch bản:** [mô tả VN]
- **Mode:** [mode] | **Duration:** [N]s | **Ratio:** [ratio] | **Res:** [res]
- **⏱ Estimated:** ~[N] phút
Confirm để tạo nhé?
```

### Step 6: Generate

```bash
VIDEO_API_BASE="<proxy_base_url>" \
VIDEO_API_KEY="<api_key>" \
python3 -u skills/am-video-gen-skill/scripts/generate.py \
  --mode <mode> \
  --prompt "<prompt>" \
  --duration <N> \
  --aspect-ratio <ratio> \
  --resolution <resolution> \
  [--image <path>] \
  [--refs <path1> <path2>] \
  [--video <path>]
```

**🔴 Exec rules:**
- Gọi bằng exec/Bash tool **với default settings**
- ❌ KHÔNG override `security`, `ask` flags
- ❌ KHÔNG dùng `VideoCreate` built-in
- ✅ Set env vars `VIDEO_API_BASE` + `VIDEO_API_KEY` inline
- `-u` = unbuffered progress

**After success:** Send file to user with description.

**Error handling:**

| Error | Action |
|-------|--------|
| `CONTENT_POLICY` | Soften prompt |
| Timeout | Reduce duration/resolution |
| `expired` | Retry same params |
| 401/403 | STOP — env var issue |
| 422 | Check image/video format |

### Step 6b: Post-Process (Optional)

```bash
ffmpeg -i input.mp4 -filter:v "setpts=PTS/1.2" -an output.mp4  # Speed-up
ffmpeg -i input.mp4 -ss 1 -to 12 -c copy output.mp4            # Trim
```

### Step 7: Iterate

- Surgical edit prompt only. **Confirm lại** mỗi lần.
- ≤ 3 tweaks → suggest đổi hướng

---

## Tư Vấn Proactive

| User yêu cầu | Tư vấn |
|-------------|--------|
| Duration 15s cho SP rotate | "3-5s đủ, 15s repetitive" |
| "Thêm chữ lên video" | "Text hay sai. Tạo video trước, overlay sau" |
| Text-to-video cho SP cụ thể | "Image-to-video giữ đúng SP hơn" |
| Nhiều người | "1 người tốt nhất, 2+ có thể méo mặt" |
| Muốn video > 15s | "Generate 15s + extend thêm 10s = 25s tổng" |
| Edit đổi quá nhiều | "Edit sửa nhẹ. Đổi nhiều → generate mới" |

## Limitations

**Hard limits:** Max 15s generate / 10s extend / 1080p / no audio / `--image` + `--refs` exclusive / edit inherits input props

**Weaknesses:** ❌ text rendering | ⚠️ hands/fingers | ⚠️ 2+ people | ⚠️ fast motion | ⚠️ logos | ✅ slow-mo, rotate, zoom, nature, smoke

## Changelog

### v2.0.0 (2026-05-20)
- **New:** Video editing (`--mode edit --video --prompt`)
- **New:** Video extension (`--mode extend --video --prompt --duration 1-10`)
- **New:** 1080p resolution, image-to-video auto (prompt optional), `--json` output
- **Improve:** Unified image processing (resize + ratio fit single pass), `submit_and_poll()` shared
- **Improve:** SKILL.md trimmed ~40%
- **Fix:** Aspect ratio stretch (v1.2.0 fix retained)

### v1.2.0 (2026-05-20)
- Fix: Image-to-video aspect ratio stretch via `fit_image_to_ratio()`

### v1.0.0 (2026-05-19)
- Initial AM conversion from hc-video-gen-skill v1.4.0
