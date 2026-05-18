---
name: am-image-gen-skill
version: 1.0.0
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

Converted from hc-image-gen-skill v2.3.0.

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
| `--output` | File path | Default: `outbound/gen-TIMESTAMP.ext` |
| `--model` | string | Default: `gpt-image-2` |

**Size mapping:** 1:1→`1024x1024` | 9:16,4:5→`1024x1792` | 16:9→`1792x1024`

**Built-in features:**
- Auto-retry 2x on failure (5s, 10s backoff)
- Auto-resize ref images to 768px (keeps payload small)
- Timestamped output filenames (no overwrite)
- Logs elapsed time per generation

**After generating:** Send output via `SendMessage` with `filePath` + `caption`.

**📁 Finding user's uploaded images:**
User images land in the platform media inbound directory.
To find the latest: `ls -lt <media_inbound_path>/ | head -5`

**⚙️ Environment:**
Script reads from env vars (configure per deployment):
- `IMAGE_API_BASE` — LLM proxy base URL (required)
- `IMAGE_API_KEY` — API key for image generation (required)

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
│       ├─ "thêm text/chữ" → UC8 (Text Overlay)
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

**Quick Mode:** User provides subject + style + ratio + "gen luôn" → skip to Step 4.

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
5. Vietnamese text exact with diacritics? (warn if long)

### Step 5: Generate

Run script (see Tool section above for full params):
```bash
python3 <skill_path>/scripts/generate.py \
  --prompt "<prompt from Step 4>" \
  --size <size> --quality high \
  --images <ref paths if UC1-9> \
  --format <jpeg for photos, png for logos>
```

**Size defaults:** Logo→`1024x1024` | Social/Model/Poster→`1024x1792` | Web banner→`1792x1024` | Product→`1024x1024`

**After script prints OK:**
1. Send file: `SendMessage(action=send, filePath=<output path>, caption=<brief description>)`
2. Self-evaluate: subject intact? text correct? style match?
3. Defect obvious → adjust prompt, re-run script
4. Acceptable → note imperfections + ask "Cần điều chỉnh gì không?"

**If script fails after retries:** Simplify prompt (fewer elements). Content policy → soften. Timeout → `--quality medium`.

### Step 6: Iterate

- Surgical edit: change ONLY the section user wants tweaked
- Minor tweak → modify prompt only, re-run script
- Structural change → pass previous output as `--images` ref
- Script prints output path on stdout — capture it for reuse
- Max 3 tweaks same base → suggest fresh direction
- Draft = `--quality medium`, final = `--quality high`

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

### UC8: Text Overlay
`"Keep image as-is. Add [EXACT TEXT] in [FONT] [COLOR] at [POSITION]. [Optional: semi-transparent banner for readability]. Don't alter original."`

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
