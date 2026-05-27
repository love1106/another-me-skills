---
name: am-image-gen-skill
version: 2.6.1
author: khoidoan
description: >
  Generate professional images for business: logo, banner, product photography, model+product, mockup.
  Use when: user asks to create/generate/design an image, banner, logo, product photo, ad creative.
  Triggers: "tạo ảnh", "gen ảnh", "design banner", "tạo logo", "ảnh sản phẩm", "product photo",
  "tạo hình", "generate image", "ad creative", "ảnh quảng cáo", "ảnh model", "hình bìa",
  "thumbnail", "đổi nền", "thêm text vào ảnh", "mở rộng ảnh", "mặc thử", "try on",
  "mockup", "storyboard", "grid ảnh".
  NOT for: video generation, UI/UX mockup coding, complex multi-layer Photoshop editing.
---

# Image Generation Skill

## 🔴 Critical Rule — ALWAYS Deliver Result

**Script `generate.py` chạy xong = BẮT BUỘC gọi `SendMessage` gửi ảnh cho user NGAY trong cùng turn.**
- KHÔNG kết thúc turn mà chưa gửi ảnh
- KHÔNG để user phải hỏi lại "ảnh đâu?"
- Nếu generate nhiều ảnh (`--count`) → gửi TỪNG ảnh qua SendMessage
- Nếu fail → vẫn phải báo user lỗi gì, KHÔNG im lặng

**🔴 Retry & Progress — KHÔNG chờ user hỏi:**
- Script fail lần 1 → **báo user ngay** "API lỗi, đang retry..." rồi mới retry
- Retry lần 2 fail → **báo user ngay** lỗi cụ thể + đề xuất hướng khác
- KHÔNG im lặng chờ retry xong mới nói — user phải biết đang xảy ra gì
- Script chạy > 90s chưa có kết quả → báo user "Đang chờ API, hơi lâu hôm nay"

## Load Strategy

Read this SKILL.md always. Load references **on-demand only**:
- Prompt building → `references/prompt-patterns.md`
- Style suggestions → `references/style-presets.md`
- Category structures / UC13-15 → `references/build-guide.md`
- Conversation examples → `references/conversation-examples.md`

## Tool: `scripts/generate.py` (Direct API)

### 🔴 KHÔNG DÙNG `ImageCreate` BUILT-IN TOOL

Lý do: Platform tự động attach toàn bộ media trong conversation vào `ImageCreate` call → vượt 6MB limit → fail.

**Luôn dùng script `generate.py`** — gọi API trực tiếp, tự control ảnh nào gửi, auto-resize.

```bash
python3 <skill_path>/scripts/generate.py \
  --prompt "..." \
  --size 1024x1792 \
  --images /path/to/ref1.jpg \
  --quality high \
  --background transparent \
  --format png
```

| Param | Values | Note |
|-------|--------|------|
| `--prompt` | English string | Always required |
| `--size` | `1024x1024` \| `1024x1792` \| `1792x1024` | Square \| Portrait \| Landscape |
| `--images` | File paths (space-separated) | Auto-resized to 768px/<100KB |
| `--quality` | `medium` \| `high` | medium=draft, high=final |
| `--background` | `transparent` \| `opaque` | Logo/icon = transparent |
| `--format` | `png` \| `jpeg` \| `webp` | Logo=png, photos=jpeg (smaller) |
| `--count` | `1` \| `2` \| `3` \| `4` | Generate multiple variations (default: 1) |
| `--output` | File path | Default: `outbound/gen-TIMESTAMP.ext` |
| `--model` | string | Default: `gpt-image-2` |

**Size mapping:** 1:1→`1024x1024` | 9:16,4:5→`1024x1792` | 16:9→`1792x1024`

**Built-in features:**
- Auto-retry 2x on failure (5s, 10s backoff)
- Auto-resize ref images to 768px (keeps payload small)
- Timestamped output filenames (no overwrite)
- Logs elapsed time per generation

**After generating:** Send output via `SendMessage` with `filePath` + `caption`.

**⏱️ Timing & Cost:**
- Single image (no ref): ~30-60s
- With ref image(s): ~60-120s
- Quality `medium` ~2x faster than `high`
- Cost: ~$0.02-0.08/image depending on quality + size
- Inform user: "Chờ em khoảng 1 phút nhé" trước khi generate

**📁 Finding user's uploaded images:**
User images land in the platform media inbound directory.
To find the latest: `ls -lt <media_inbound_path>/ | head -5`

**⚙️ Environment:**
Script reads from env vars (priority: IMAGE_* > OPENAI_*):
- `IMAGE_API_BASE` or `OPENAI_BASE_URL` — LLM proxy base URL (one required)
- `IMAGE_API_KEY` or `OPENAI_API_KEY` — API key for image generation (one required)

---

## Flow

### Step 0: Verify Images (if user sent images)

**🔴 ALWAYS verify user images with `image` tool before building prompt.**
- Don't trust message metadata/descriptions — they can be wrong
- Use `image(image=<path>, prompt="What product/object is in this image?")`
- Note the correct file paths for passing to `--images` later

### Step 1: Route

```
User request
├─ Has image(s)?
│   ├─ Multiple → UC9 (Moodboard)
│   └─ Single
│       ├─ "kiểu như này" → UC1 (Style Ref)
│       ├─ "đổi/xóa nền" → UC6 (BG Replace)
│       ├─ "mở rộng/resize" → UC7 (Outpaint)
│       ├─ "thêm text/chữ" → UC8 (Text in Image — LLM render, KHÔNG overlay thủ công)
│       ├─ "mặc thử/try on" → UC13 (Try-On)
│       ├─ "mockup/đặt lên" → UC15 (3D Mockup)
│       ├─ Logo + wants banner → UC3
│       ├─ Product photo → UC2 (Product→Scene)
│       └─ Person → UC4 (Model→Context)
└─ No image
    ├─ Grid/storyboard → UC14
    ├─ Series/batch → UC5 (Catalog)
    ├─ Full prompt given → UC12 (skip to Step 4)
    ├─ Vague → ask purpose first
    └─ Clear → Step 2
```

**Quick Mode:** User provides subject + style + ratio + explicitly says "gen luôn" / "không cần hỏi" → skip to Step 4 → **vẫn phải confirm (Step 5)** trước khi generate.
**Skip Confirm:** Chỉ khi user nói rõ "gen luôn không cần confirm" hoặc đang trong catalog series đã confirm style (UC5).

### Step 2: Suggest (2-3 options)

Format:
```
Em gợi ý [N] hướng:
1. **[Style]** — [1-line visual preview]
2. **[Style]** — [1-line visual preview]
3. **[Style]** — [1-line visual preview]
Anh/chị thích hướng nào?
```

Pick presets from `references/style-presets.md`. Max 3. Skip if user already specified style.

### Step 3: Refine (max 2 questions)

Only ask what's MISSING and CRITICAL:
- Text on image? → ask brand name / headline
- Platform unclear? → ask for aspect ratio
- Non-critical fields → pick defaults, tell user

### Step 4: Build Prompt

**Always English.** Structure per category:
- **Logo:** Subject → Style → Colors → transparent BG → Constraints
- **Product:** Subject → Scene → Lighting → Palette → Technical → Negatives
- **Banner:** Layout → Product → Text(exact+font+position+color) → BG → Technical
- **Model:** Person → Clothing → Pose → Environment → Lighting → Mood → Negatives
- **Poster:** Composition → Visual → Typography → Colors → Style → Technical

Length: 50w (logo) → 400w (complex). Detail = `references/build-guide.md`.

**Pre-generate check** (critical 5):
1. Subject visually specific? (shape, color, material)
2. No style contradictions?
3. Elements ≤ 7, text ≤ 3?
4. Lighting named specifically?
5. Vietnamese text with diacritics? → **Luôn đưa vào prompt cho LLM render** (gpt-image-2 xử lý text tốt). Ghi exact text trong prompt. Nếu kết quả sai chữ → retry với prompt nhấn mạnh hơn (ALL CAPS instruction, repeat text). KHÔNG tự overlay bằng ImageMagick/FFmpeg.

### Step 5: Confirm Before Generate

**🔴 KHÔNG generate ngay. Phải confirm với user trước.**

Sau khi build prompt xong, show cho user review:
```
📋 Em confirm trước khi tạo:
- **Prompt:** [tóm tắt ngắn gọn bằng tiếng Việt]
- **Size:** [size]
- **Quality:** [quality]
- **Format:** [format]
- **Ref images:** [có/không, bao nhiêu]

Confirm để em tạo nhé?
```

**Chỉ chạy generate SAU KHI user confirm** ("ok", "tạo đi", "confirm", "ư", v.v.)
Nếu user muốn sửa → quay lại Step 3/4 điều chỉnh → confirm lại.

**Catalog/Batch (UC5):** Confirm ảnh đầu tiên đầy đủ. Các ảnh tiếp theo cùng style → generate luôn không cần confirm từng ảnh.
**Iterate (Step 7):** Tweak nhỏ → không cần confirm lại (user đã chấp nhận hướng, chỉ đang chỉnh).

### Step 6: Generate

Run script (see Tool section above for full params):
```bash
IMAGE_API_BASE="<proxy_base_url>" \
IMAGE_API_KEY="<api_key>" \
python3 <skill_path>/scripts/generate.py \
  --prompt "<prompt from Step 4>" \
  --size <size> --quality high \
  --images <ref paths if UC1-9> \
  --format <jpeg for photos, png for logos>
```

**🔴 Exec call rules — QUAN TRỌNG:**
- Gọi bằng exec/Bash tool **với default settings** — KHÔNG override `security`, `ask`, hoặc bất kỳ execution flag nào
- ❌ KHÔNG set `security: "allowlist"`, `ask: "on-miss"`, hoặc tương tự — sẽ trigger approval loop không cần thiết
- ❌ KHÔNG dùng `ImageCreate` built-in — sẽ auto-attach conversation media gây fail >6MB
- ✅ Chỉ cần set env vars `IMAGE_API_BASE` + `IMAGE_API_KEY` inline trước lệnh python3
- ✅ Nếu runtime đã có exec policy `security=full, ask=off` → script chạy thẳng không cần approval

**Size defaults:** Logo→`1024x1024` | Social/Model/Poster→`1024x1792` | Web banner→`1792x1024` | Product→`1024x1024`

**🔴 MUST SEND RESULT — KHÔNG ĐƯỢC KẾT THÚC TURN MÀ CHƯA GỬI ẢNH:**

Script stdout sẽ in ra 1 trong 3 loại marker:
- `PROGRESS: ...` → **Báo user ngay** đang retry, không chờ
- `FAILED: ...` → **Báo user ngay** lỗi gì + đề xuất (sửa prompt / thử lại / hướng khác)
- `/path/to/output.jpg` → **Gửi ảnh ngay** qua SendMessage

Sau khi script in ra output path:
1. **NGAY LẬP TỨC** gọi `SendMessage(action=send, filePath=<output path>, caption=<brief description>)`
2. **Nếu SendMessage FAIL** (file quá lớn, timeout, Telegram reject):
   a. Check file size: `ls -lh <output path>`
   b. Nếu > 10MB → compress: `convert <path> -quality 80 -resize 2048x2048\> <path_compressed.jpg>` rồi gửi lại
   c. Nếu vẫn fail → thử gửi bằng `asDocument: true`
   d. Nếu tất cả fail → **BÁO USER NGAY**: "Ảnh đã tạo xong nhưng gửi bị lỗi [chi tiết]. Đang thử lại..."
   e. KHÔNG BAO GIỜ im lặng khi SendMessage fail
3. Self-evaluate: subject intact? text correct? style match?
4. Defect obvious → adjust prompt, re-run script → gửi lại
5. Acceptable → note imperfections + ask "Cần điều chỉnh gì không?"

⚠️ **Anti-patterns (CẤM):**
- Script chạy xong → agent kết thúc turn mà quên SendMessage → ĐÃ XẢY RA NHIỀU LẦN
- Script retry → im lặng chờ → user không biết đang xảy ra gì
- Script fail → không báo → user tưởng đang chạy
- **SendMessage fail → im lặng** → ảnh tạo xong nhưng user không nhận được

**⚠️ Script buffering:** Bash tool buffer stdout cho đến khi script kết thúc. Nếu script chạy > 60s → dùng `timeout` và check exit code:
```bash
timeout 180 python3 <skill_path>/scripts/generate.py --prompt "..." ... ; echo "EXIT:$?"
```
Nếu exit code != 0 → đọc stdout cho FAILED marker → báo user ngay.

**If script fails after retries:**

| Error | User message | Action |
|-------|-------------|--------|
| `CONTENT_POLICY` | "Prompt bị chặn bởi bộ lọc an toàn. Em sửa prompt nhé." | Remove brand names, soften descriptions, make generic |
| Timeout / 5xx | "API đang chậm, em thử lại với chất lượng thấp hơn." | Retry `--quality medium`, reduce ref image count |
| 401/403 | "Lỗi xác thực API. Cần check cấu hình." | STOP — env var issue |
| Prompt too long | "Prompt quá dài, em rút gọn." | Trim to <400 words, remove redundant details |
| All retries failed | "Không generate được sau 3 lần. [error detail]. Thử hướng khác nhé?" | Offer alternative approach |

### Step 7: Iterate

- Surgical edit: change ONLY the section user wants tweaked
- Minor tweak → modify prompt only, re-run script. Không cần confirm lại.
- Structural change → pass previous output as `--images` ref:
  ```bash
  --images <previous output path from script stdout>
  ```
- Script prints output path on stdout — capture it for reuse
- Draft = `--quality medium`, final = `--quality high`

**Iterate limits:**
- **≤ 3 tweaks** cùng base prompt → nếu vẫn chưa ưng, nói: "Hướng này đã đến giới hạn. Thử hướng khác nhé?" → quay lại Step 2
- **Structural change** (composition, style khác hẳn) → coi như request mới, confirm lại (Step 5)
- **Track changes:** Note từng lần tweak đã làm gì để không lặp lại

---

## Use Cases (Prompt Skeletons)

### UC1: Style Reference
`"Create a new image in the exact same style, lighting, and color palette as the reference. Replace the subject with [NEW]. Maintain [composition/background/mood]."`

### UC2: Product → Scene
`"Keep the product exactly as shown — same shape, label, colors. Place it in [SCENE]. [LIGHTING]. [SURFACE]. [PALETTE]. Sharp focus, commercial quality. No watermark."`

### UC3: Logo → Banner
`"Create a [BANNER TYPE] incorporating the provided logo at [POSITION]. Features [VISUAL ELEMENTS] with [PALETTE matching logo]. [TEXT] in [FONT] at [POSITION]. Professional design."`

### UC4: Model → Context
`"Keep the person's appearance/hairstyle/build. Place in [ENVIRONMENT]. [POSE] with [PRODUCT]. [LIGHTING]. Editorial style. No watermark."`
⚠️ Likeness may not be 100% — inform user.

### UC5: Catalog Series
Save base prompt after first approval. Subsequent: swap product description only, keep everything else identical.

### UC6: Background Replace
`"Keep [SUBJECT] exactly as shown. Replace background with [NEW BG]. Seamless blending, consistent lighting from [DIRECTION]."`

### UC7: Outpainting
`"Extend canvas from [ORIGINAL] to [TARGET RATIO]. Keep original intact in center. Seamlessly continue [environment] into new areas."`

### UC8: Text in Image
**🔴 LUÔN đưa text vào prompt cho LLM render. KHÔNG tự overlay bằng ImageMagick/FFmpeg/drawtext.**

Nếu có ảnh gốc (ref image):
`"Keep the image exactly as shown. Render the text [EXACT TEXT] in [FONT STYLE] [COLOR] at [POSITION]. The text must be pixel-perfect, no typos. [Optional: semi-transparent dark banner behind text for readability]. Do not alter the original image content."`

Nếu tạo mới:
`"Create [SCENE/DESIGN]. Include the text [EXACT TEXT] rendered in [FONT STYLE] [COLOR] at [POSITION]. Text must be sharp, correctly spelled, and readable."`

Tips cho text chính xác:
- Ghi text EXACT trong prompt, bao bằng ngoặc kép: `the text "SALE 50%"`
- Viết thêm instruction: `spell each letter exactly as given`
- Tiếng Việt có dấu: ghi rõ từng chữ + thêm `Vietnamese diacritics must be exact`
- Nếu output sai chữ → retry với nhấn mạnh mạnh hơn, KHÔNG chuyển sang overlay thủ công

### UC9: Moodboard
`"Combine: from image 1 take [composition], from image 2 take [palette], from image 3 take [lighting]. Subject: [NEW]. Ensure coherence."`

### UC10-12: Simple Cases
- **UC10 Variations:** Gen 1 → offer more variations (change 1 variable only)
- **UC11 Vague:** Ask "Ảnh cho mục đích gì?" → normal flow
- **UC12 Full prompt:** Review → enhance if needed → generate

### UC13-15: Advanced (detail in `references/build-guide.md`)
- **UC13 Virtual Try-On:** Product image + generic model, or person + product desc. Best for upper-body/accessories.
- **UC14 Multi-Frame:** Grid layout (2x2, 3x3, 1x3). Describe each panel explicitly.
- **UC15 3D Mockup:** Design/logo on object (phone, mug, shirt, box, billboard).

---

## References
- `references/prompt-patterns.md` — Techniques, anti-patterns, Vietnamese guide, composition-by-ratio
- `references/style-presets.md` — 25 presets with examples + industry mapping + aspect ratio table
- `references/build-guide.md` — Category structures, A/B strategy, UC13-15 prompts
- `references/conversation-examples.md` — 5 end-to-end flows
