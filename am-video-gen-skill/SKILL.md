---
name: am-video-gen-skill
version: 1.0.0
author: khoidoan
description: >
  Generate short videos from text prompts or reference images using xAI grok-imagine-video.
  Supports text-to-video, image-to-video (animate still), and reference-to-video (style/subject guide).
  Use when: user asks to create/generate a video, animate an image, make a video clip.
  Triggers: "tạo video", "gen video", "generate video", "tạo clip", "animate image",
  "làm video", "video từ ảnh", "image to video", "text to video", "tạo motion".
  NOT for: long-form video editing (>15s), video with complex audio sync, live streaming.
---

# Video Generation Skill

Converted from hc-video-gen-skill v1.4.0.

## Load Strategy

Read this SKILL.md always. No third-party references needed.

## Tool: `scripts/generate.py`

Gọi xAI `grok-imagine-video` API qua OpenAI-compatible proxy. Async: submit → poll → download.

```bash
python3 skills/am-video-gen-skill/scripts/generate.py \
  --prompt "..." \
  --duration 5 \
  --aspect-ratio 16:9 \
  --resolution 720p
```

| Param | Values | Note |
|-------|--------|------|
| `--prompt` | English string | Always required |
| `--duration` | `1`–`15` | Seconds (default: 5) |
| `--aspect-ratio` | `1:1` \| `16:9` \| `9:16` \| `4:3` \| `3:4` \| `3:2` \| `2:3` | Default: `16:9` |
| `--resolution` | `480p` \| `720p` | Default: `720p` |
| `--image` | File path | Image-to-video: animate this image |
| `--refs` | File paths (space-separated) | Reference-to-video: style/subject guide |
| `--output` | File path | Default: `outbound/vid-TIMESTAMP.mp4` |
| `--model` | string | Default: `grok-imagine-video` |
| `--dry-run` | flag | Validate params + show payload without calling API |

**🔴 `--image` và `--refs` KHÔNG dùng cùng lúc.**

**3 modes:**
| Mode | Params | Mô tả |
|------|--------|--------|
| Text-to-video | `--prompt` only | Tạo video từ text |
| Image-to-video | `--prompt` + `--image` | Animate ảnh tĩnh (ảnh = frame đầu) |
| Reference-to-video | `--prompt` + `--refs` | Dùng ảnh tham chiếu (style, nhân vật, sản phẩm) |

**⚙️ Required env vars:**

Script reads from env vars (priority: VIDEO_* > OPENAI_*):
- `VIDEO_API_BASE` or `OPENAI_BASE_URL` — OpenAI-compatible proxy base URL (one required)
- `VIDEO_API_KEY` or `OPENAI_API_KEY` — API key for video generation (one required)
- `VIDEO_OUTBOUND_DIR` — Output directory (optional, default: `~/.openclaw/workspace/outbound`)

**🔴 LUÔN dùng `scripts/generate.py`, KHÔNG dùng `VideoCreate` built-in.**
`VideoCreate` cần xAI provider config — nếu chưa có sẽ route nhầm (400/401 errors).

**⏱️ Timing & Cost (measured):**
- Async process: submit → poll mỗi 5s → download khi done
- Text-to-video 5s: ~60-90s | 10s: ~120-180s | 15s: ~180-240s
- Image-to-video 5s: ~90-120s | 10s: ~150-210s | 15s: ~210-270s
- Reference-to-video: +30-60s so với image-to-video
- Timeout: 10 phút max (script tự exit)
- **Inform user:** "Chờ em khoảng 3-5 phút nhé" (image/ref-to-video)

**After generating:** Send output via messaging tool with file path + caption.

**📁 Finding user's uploaded images:**
User images from messaging: check inbound media directory.
Find latest: `ls -lt <inbound_media_dir>/ | head -5`

---

## Flow

### Step 0: Verify Images (if user sent images)

**🔴 ALWAYS verify user images before building prompt.**
- Don't trust message metadata/descriptions — they can be wrong
- Visually confirm what's in each image
- Find latest uploads from inbound media directory

**Xác định mode từ ảnh:**
- 1 ảnh + user muốn "animate" → `--image`
- 1 ảnh + user muốn "style/nhân vật này" → `--refs`
- 2+ ảnh → `--refs` — xác định thứ tự: `<IMAGE_1>` = ảnh đầu, `<IMAGE_2>` = ảnh sau
  - Hỏi user nếu chưa rõ: "Ảnh nào là người mẫu, ảnh nào là sản phẩm?"

### Step 1: Route

```
User request
├─ Has image(s)?
│   ├─ 1 ảnh + "animate", "làm cho chuyển động" → Image-to-video
│   ├─ 1 ảnh + "style này", "kiểu này" → Reference-to-video
│   ├─ 1 ảnh SP + yêu cầu chung ("video quảng cáo", "tạo video") → **Smart default:**
│   │   - Ảnh SP studio/nền trắng → Image-to-video (animate tại chỗ)
│   │   - Ảnh SP lifestyle/context → Image-to-video (animate scene)
│   │   - Nói cho user: "Em sẽ animate ảnh SP này thành video [mô tả]. OK chứ?"
│   ├─ 2+ ảnh (người + sản phẩm) → Reference-to-video
│   └─ Unclear → ask: "Anh/chị muốn animate ảnh này hay dùng làm tham chiếu?"
└─ No image
    ├─ Full prompt given → UC-Quick (skip to Step 3)
    ├─ Vague → ask purpose: "Video cho mục đích gì?"
    └─ Clear → Step 2
```

**Quick Mode:** User cung cấp đủ subject + action + ratio + "gen luôn" → skip to Step 3 → **vẫn phải confirm (Step 5)**.
**🔴 KHÔNG BAO GIỜ skip confirm.** Video tốn thời gian (2-5 phút) + chi phí cao hơn image → luôn xác nhận trước.

### Step 2: Suggest Style + Kịch Bản (2-3 options)

**2 lớp suggest:**
- **Lớp 1 — Style:** Cinematic? Lifestyle? Minimal? (tra bảng presets)
- **Lớp 2 — Kịch bản:** Product Hero? Product-in-Use? Brand Story? (tra Product → Scene Mapping bên dưới)

**Flow:**
1. Xác định loại SP từ ảnh/mô tả user
2. Tra **Product → Scene Mapping** → lấy bối cảnh + camera + mood + duration gợi ý
3. Chọn 2-3 **Script Templates** phù hợp
4. Present cho user

Skip nếu user đã specify đầy đủ style + kịch bản.

**Video style presets:**

| Style | Camera + Mood | Good for |
|-------|---------------|----------|
| Cinematic Product | Slow zoom, dramatic lighting, smoke | Luxury, perfume, cosmetics |
| Lifestyle Motion | Tracking shot, natural light, candid | F&B, fashion, daily life |
| Minimal Loop | Static/slow rotate, clean BG, seamless | Product demo, e-commerce |
| Energetic Reel | Quick cuts feel, dynamic angle, bold | Sale, event, Gen Z |
| Aerial/Establish | Drone-style, wide angle, reveal | Travel, real estate, brand |
| Portrait Motion | Subtle movement, shallow DOF, warm | Personal brand, model |

### Step 3: Refine (max 2 questions)

Only ask what's MISSING and CRITICAL:
- Duration unclear? → suggest based on content (product demo 3-5s, storytelling 8-10s, max impact 15s)
- Platform unclear? → ask for aspect ratio
- Non-critical → pick defaults, tell user

**Defaults nếu user không nói:**
- Duration: 5s (ngắn gọn, tiết kiệm)
- Aspect ratio: 16:9 (widescreen)
- Resolution: 720p

### Step 4: Build Prompt

**Always English.** Video prompts khác image prompts — phải mô tả CHUYỂN ĐỘNG.

**Video prompt structure:**
```
[Camera movement] + [Subject action/change] + [Environment] + [Lighting/Mood] + [Style] + [Negatives]
```

**Camera movements:**
- `slow zoom in/out` — dramatic reveal
- `tracking shot following` — action/motion
- `static shot` — product showcase, stability
- `pan left/right` — scene reveal
- `drone aerial shot` — landscape, establishing
- `close-up slowly pulling back` — detail → context
- `orbit/rotate around` — 360° product showcase
- `handheld, slight shake` — documentary/authentic feel

**Temporal language (BẮT BUỘC):**
- "slowly", "gradually", "then", "as the camera moves"
- "begins to", "transitions into", "reveals"
- Mô tả thay đổi theo thời gian, KHÔNG chỉ static scene

**Duration → complexity mapping:**
| Duration | Actions | Example |
|----------|---------|--------|
| 1-3s | 1 simple motion | Product rotate, zoom in |
| 4-7s | 1-2 actions | Zoom + reveal, walk + turn |
| 8-12s | 2-3 actions | Establish → zoom → detail |
| 13-15s | 3-4 actions | Multi-scene, story arc |

**Reference-to-video prompts:**
- Use `<IMAGE_1>`, `<IMAGE_2>` etc. to reference images in prompt
- Example: "The person from <IMAGE_1> walks wearing the outfit from <IMAGE_2>"
- Max 3 references recommended

**Prompt length guidance:**
| Mode | Length | Why |
|------|--------|-----|
| Text-to-video (simple) | 30-60 words | 1 scene, 1 action |
| Text-to-video (story) | 60-120 words | Multi-action, transitions |
| Image-to-video | 20-50 words | Ảnh đã define scene, chỉ cần mô tả motion |
| Reference-to-video | 50-100 words | Cần mô tả interaction với từng `<IMAGE>` |

**Negatives (append nếu cần):**
- `no text, no watermark` (mặc định cho commercial)
- `no abrupt cuts` (smooth transitions)
- `no jittery camera` (stable movement)

**Pre-generate check (critical 5):**
1. Prompt describes MOTION/CHANGE? (not just static scene description)
2. Camera movement specified?
3. Duration matches content complexity?
4. Aspect ratio matches platform? (9:16 = TikTok/Reel, 16:9 = YouTube)
5. ≤ 4 actions for max duration? (quá nhiều → video loãng)

### Step 5: Confirm Before Generate

**�� KHÔNG generate ngay. Phải confirm với user trước.**

```
📋 Confirm trước khi tạo video:
- **Kịch bản:** [mô tả bằng tiếng Việt]
- **Prompt (EN):** "[prompt thực tế]"
- **Mode:** [text-to-video / image-to-video / reference-to-video]
- **Duration:** [N]s | **Ratio:** [ratio] | **Res:** [resolution]
- **Ref images:** [có/không, bao nhiêu]
- **⏱ Estimated:** ~3-5 phút

Confirm để tạo nhé?
```

**🔴 Mọi video đều phải confirm, không có ngoại lệ.**

### Step 6: Generate

```bash
VIDEO_API_BASE="<proxy_base_url>" \
VIDEO_API_KEY="<api_key>" \
python3 -u skills/am-video-gen-skill/scripts/generate.py \
  --prompt "<prompt from Step 4>" \
  --duration <N> \
  --aspect-ratio <ratio> \
  --resolution <resolution> \
  [--image <path>] \
  [--refs <path1> <path2>]
```

**🔴 Exec call rules — QUAN TRỌNG:**
- Gọi bằng exec/Bash tool **với default settings** — KHÔNG override `security`, `ask`, hoặc bất kỳ execution flag nào
- ❌ KHÔNG set `security: "allowlist"`, `ask: "on-miss"`, hoặc tương tự — sẽ trigger approval loop không cần thiết
- ❌ KHÔNG dùng `VideoCreate` built-in — sẽ route sai provider
- ✅ Chỉ cần set env vars `VIDEO_API_BASE` + `VIDEO_API_KEY` inline trước lệnh python3
- ✅ Nếu runtime đã có exec policy `security=full, ask=off` → script chạy thẳng không cần approval

**🔴 Flags quan trọng:**
- `-u` = unbuffered output (thấy progress realtime khi chạy background)
- `timeout 360` = wrap nếu chạy background, tránh treo vĩnh viễn

**After script prints output path:**
1. Send file to user with brief description
2. **Self-evaluate checklist:**
   - ☐ Motion smooth, không giật?
   - ☐ Subject đúng (sản phẩm/người giống reference)?
   - ☐ Camera movement đúng như prompt?
   - ☐ Không có artifact (tay thừa, mặt méo, text lạ)?
3. Defect obvious → nói rõ + đề xuất fix
4. Acceptable → ask "Cần điều chỉnh gì không?"

**If script fails:**

| Error | User message | Action |
|-------|-------------|--------|
| `CONTENT_POLICY` | "Prompt bị chặn bởi bộ lọc. Sửa prompt nhé." | Remove sensitive content |
| Timeout (10 min) | "Video gen quá lâu. Thử rút ngắn duration." | Reduce duration, simplify prompt |
| `expired` | "Request hết hạn. Thử lại." | Retry same params |
| 401/403 | "Lỗi xác thực API. Cần check cấu hình." | STOP — env var issue |
| 422 | "API không nhận dạng payload. Check image format." | Verify `image` field là `{"url": "data:..."}` (object), KHÔNG phải raw string |
| All retries failed | "Không generate được. Thử hướng khác?" | Offer simpler approach |

### Step 6b: Post-Process (Optional)

**Speed-up video** — nếu video cần tăng tốc:
```bash
ffmpeg -i input.mp4 -filter:v "setpts=PTS/1.2" -an output-1.2x.mp4
```
- `1.2` = 1.2x speed | `1.5` = 1.5x
- `-an` = bỏ audio track (video gen không có audio)

**Trim video:**
```bash
ffmpeg -i input.mp4 -ss 1 -to 12 -c copy output-trimmed.mp4
```

### Step 7: Iterate

- Surgical edit: change ONLY the section user wants tweaked
- Minor tweak → modify prompt, **confirm lại**, rồi mới re-run
- **≤ 3 tweaks** cùng base prompt → nếu vẫn chưa ưng → đề xuất hướng khác
- **Structural change** → coi như request mới, confirm lại (Step 5)

---

## Tư Vấn Proactive

**Chặn sớm các vấn đề thường gặp:**
| User yêu cầu | Vấn đề | Tư vấn |
|-------------|---------|--------|
| Duration 15s cho product rotate | Quá dài | "3-5s là đủ, 15s sẽ repetitive." |
| 4 actions trong 5s | Không đủ | "5s chỉ fit 1-2 actions. Tăng 10s?" |
| "Thêm chữ lên video" | Model render text kém | "Tạo video trước, overlay text bằng CapCut/Canva sau." |
| Text-to-video cho SP cụ thể | Sẽ không giống SP | "Image-to-video từ ảnh SP sẽ giữ đúng SP hơn." |
| Nhiều người trong 1 video | Model limitation | "Model xử lý 1 người tốt nhất. 2+ người có thể bị méo." |
| Close-up tay cầm SP | Artifact risk | "Close-up tay hay bị artifact. Zoom medium shot thay thế?" |

---

## Product → Scene Mapping

| Loại sản phẩm | Bối cảnh gợi ý | Camera | Mood | Duration |
|---------------|----------------|--------|------|----------|
| Nước hoa / Perfume | Marble surface, khói, ánh vàng | Slow zoom in + orbit | Luxury, dramatic | 5-8s |
| Skincare / Mỹ phẩm | Bathroom shelf, giọt nước, lá xanh | Close-up → pull back | Fresh, clean | 5-8s |
| Thời trang / Quần áo | Runway, phố đi bộ, studio | Tracking shot | Editorial, confident | 8-10s |
| F&B / Đồ uống | Quán cà phê, bàn gỗ, steam | Slow zoom + tilt | Warm, inviting | 5-8s |
| Điện tử / Tech | Bàn minimal, ánh LED, tối | Orbit 360° | Sleek, modern | 5s |
| Trang sức / Jewelry | Velvet, spotlight, phản chiếu | Extreme close-up + zoom | Elegant, sparkling | 3-5s |
| Giày dép / Sneakers | Phố, skatepark, studio | Low angle tracking | Energetic, urban | 5-8s |
| Nội thất / Furniture | Phòng khách, ánh nắng cửa sổ | Slow pan reveal | Cozy, lifestyle | 8-10s |
| Đồ ăn / Food | Bàn ăn, tay gắp, steam | Close-up → top-down | Appetizing, sensory | 5-8s |

## Script Templates

**Template A: Product Hero** — `[Camera: orbit/zoom] [Scene: product on surface] [Action: lighting/smoke] [Mood]`

**Template B: Product-in-Use** — `[Camera: tracking/medium] [Scene: person + environment] [Action: interact with product] [Mood]`

**Template C: Lifestyle/Brand** — `[Camera: establishing → zoom] [Scene: location + brand] [Action: ambient → human → product reveal] [Mood]`

**Template D: Fashion/Model** — `[Camera: tracking/slow-mo] [Scene: runway/street/studio] [Action: walk + pose + fabric movement] [Mood]`

## Limitations

**Hard limits:**
- Max duration: 15s per generation
- Max 3 reference images recommended
- `--image` và `--refs` không dùng cùng lúc
- No audio generation (video only)

**Known weaknesses:**
- Text rendering trong video thường sai → overlay text sau
- Nhiều người (>2) trong 1 frame → face distortion
- Close-up hands → extra fingers, artifacts
- Complex physics (water splash, fabric sim) → inconsistent
- 15s video có thể bị lặp motion nếu prompt đơn giản

## Changelog

### v1.0.0 (2026-05-19)
- Initial AM conversion from hc-video-gen-skill v1.4.0
- Generic env vars (`VIDEO_API_BASE`, `VIDEO_API_KEY`, `VIDEO_OUTBOUND_DIR`)
- Removed platform-specific paths, VM references
- All 3 modes: text-to-video, image-to-video, reference-to-video
- Post-process guide (ffmpeg speed-up + trim)
