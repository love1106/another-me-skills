# Prompt Build Guide

Detailed category-specific prompt construction rules. Referenced from SKILL.md Step 4.

---

## Prompt Length by Category

| Category | Length | Why |
|----------|--------|-----|
| Logo | 50-100 words | Simple subject, style-driven, fewer elements |
| Product (clean studio) | 80-150 words | Single subject, controlled environment |
| Product (lifestyle/luxury) | 150-300 words | Multiple elements, lighting, props |
| Banner with text | 200-350 words | Layout, text placement, composition all need control |
| Model + Product | 200-400 words | Person description, pose, environment, product, mood |
| Poster/complex | 250-400 words | Multi-element, typography, composition |

**Rule of thumb:** More elements = longer prompt. Single subject on simple background = keep short.

---

## Category-Specific Prompt Structures

### Logo
```
1. Subject (icon/lettermark description — shape, interlocking, symbol)
2. Style (flat vector / 3D metallic / hand-drawn / geometric)
3. Typography (font weight, style, relative size to icon)
4. Colors (exact hex or named colors, max 2-3)
5. Background → transparent
6. Constraints ("works at small sizes", "no gradients", "crisp edges")
```

**DO NOT include:** lighting recipes, depth of field, environment, props. Logos are graphic design, not photography.

### Product (E-commerce)
```
1. Subject (detailed product: shape, material, label text, cap/lid, color, size)
2. Scene/Surface (white infinity / marble / wood / gradient / contextual)
3. Props (max 3-5 complementary items, specify quantity and position)
4. Lighting (specific recipe from prompt-patterns.md §3)
5. Color palette (3-5 named colors)
6. Technical quality (photorealistic, sharp focus, etc.)
7. Negatives (no watermark, no extra objects, etc.)
```

### Banner / Ad Creative
```
1. Layout description (split? centered? grid?)
2. Product placement (position, angle, scale relative to frame)
3. Text — EACH text element specified separately:
   - Content: exact text in quotes
   - Font: style + weight
   - Color: specific
   - Position: exact (upper left, center bottom)
   - Size: relative (large headline, small caption)
4. Background (gradient, solid, scene, pattern)
5. Lighting (matching product + scene)
6. Color palette
7. Technical + format
```

### Model + Product
```
1. Person description:
   - Demographics: age range, ethnicity, gender, build
   - DO NOT over-specify features (ethical + content policy safe)
   - Keep generic: "young Vietnamese woman in her early 20s" ✅
   - Avoid: specific celebrity descriptions ❌
2. Clothing/Styling (specific garments, colors, accessories)
3. Pose + Product Interaction:
   - What they're doing with the product
   - Body language, hand placement, gaze direction
4. Environment (indoor/outdoor, specific location details)
5. Lighting (match environment: window light, golden hour, studio)
6. Mood/Color (warm tones, cool editorial, energetic)
7. Technical (photography style, film type, depth of field)
8. Negatives (no plastic skin, no extra limbs, no watermark)
```

### Poster / Social Visual
```
1. Composition blueprint:
   - Visual hierarchy (what's biggest? what draws eye first?)
   - Text vs image ratio (60/40? 30/70?)
   - Layout structure (centered? asymmetric? grid?)
2. Main visual element (hero image, pattern, illustration)
3. Typography — ALL text specified:
   - Headline (large, specific font style)
   - Subtitle/tagline (smaller, contrasting weight)
   - CTA or date (smallest, supporting)
4. Color blocks (brand colors, how they're distributed)
5. Style/aesthetic (graphic design? illustrated? photographic?)
6. Technical (resolution feel, render style)
```

---

## A/B Variation Strategy

When to generate multiple versions:

| Scenario | Strategy |
|----------|----------|
| User hasn't picked style yet (Step 2) | Describe options in text, DON'T gen multiple images |
| User picked style, unsure about color/layout | Gen 1 → iterate based on feedback |
| User explicitly asks "cho xem 2 kiểu" | Gen 2 variations — same concept, change 1 variable (e.g. color palette swap, or background light vs dark) |
| Final deliverable for client | Offer: "Em gen thêm 1 variation để anh có options trình client?" |

**How to create meaningful variations:**
- Change ONLY ONE variable between versions:
  - Version A: warm palette / Version B: cool palette
  - Version A: left-aligned text / Version B: centered text
  - Version A: clean white bg / Version B: gradient bg
- DON'T change everything — user can't evaluate if all variables shift at once
- Label clearly: "Version A (warm) vs Version B (cool)"

---

## Virtual Try-On Prompts (UC13)

When user wants product ON a person (clothes, accessories, glasses):

**Approach 1: User has product image + wants it on a generic model**
```
"A [PERSON DESCRIPTION] wearing/using the [PRODUCT from reference image].
The [product] fits naturally — realistic fabric draping/material interaction.
[POSE] in [ENVIRONMENT]. [LIGHTING]. [STYLE].
Keep the product design exactly as shown in the reference — same pattern, color, details."
```

**Approach 2: User has person image + product description (no product photo)**
```
"Keep the person from the reference image — same appearance, hairstyle, body.
Dress them in [DETAILED PRODUCT DESCRIPTION — material, color, cut, pattern, fit].
Natural fabric draping and body interaction. Same environment/lighting as original
or [NEW ENVIRONMENT]. Photorealistic, editorial fashion photography."
```

**Limitations to inform user:**
- Works best for: clothing (top half), hats, glasses, jewelry, bags
- Harder for: exact shoe fit, full outfit change, tight-fitting detailed garments
- If product has complex pattern/logo → may not be 100% faithful

---

## Multi-Frame / Storyboard Prompts (UC14)

When user needs a grid of images in one frame:

**Grid prompt pattern:**
```
"A [NxN] grid layout presenting [PRODUCT/CONCEPT] across [N] panels.
[Describe EACH panel]:
- Panel 1 (top-left): [scene/angle description]
- Panel 2 (top-center): [scene/angle description]
- Panel 3 (top-right): [scene/angle description]
...
All panels share the same [STYLE], [COLOR PALETTE], and [PRODUCT IDENTITY].
Clean grid lines separating panels, [BACKGROUND COLOR] between frames.
[Optional: numbered labels or titles per panel].
Professional commercial presentation, consistent lighting across all panels."
```

**Common layouts:**
- **2x2 (4 panels):** Product angles (front, side, top, detail)
- **3x3 (9 panels):** TVC storyboard (sequence of scenes)
- **1x3 horizontal:** Before → During → After
- **2x3 (6 panels):** Product line showcase (6 SKUs same style)

**Tips:**
- Keep panels ≤ 9 (more = each panel too small for detail)
- Describe each panel explicitly — don't leave to imagination
- Specify shared elements (style, lighting, palette) once at the end

---

## 3D Mockup Prompts (UC15)

When user wants product displayed ON a device/object:

**Phone/Tablet mockup:**
```
"A realistic 3D mockup of [APP/WEBSITE SCREENSHOT] displayed on a modern smartphone
with thin bezels, slightly tilted at [ANGLE] on [SURFACE].
The screen shows [DESCRIBE WHAT'S ON SCREEN].
[ENVIRONMENT]. [LIGHTING creating realistic screen glow and device reflections].
Premium tech product photography, photorealistic device rendering."
```

**Packaging/Merchandise mockup:**
```
"A photorealistic mockup of [DESIGN/LOGO] applied to [OBJECT: mug/tshirt/tote bag/box].
The [object] is [POSITION/ANGLE] on [SURFACE] in [ENVIRONMENT].
The print/design wraps naturally following the object's contours.
Realistic fabric texture/material properties. [LIGHTING]. Commercial product photography."
```

**Common mockup objects:**
- Phone/tablet screen → app showcase
- T-shirt/hoodie → merch design
- Mug/tumbler → branded drinkware
- Tote bag → logo placement
- Business card → brand identity
- Billboard/poster frame → outdoor ad
- Laptop screen → website/dashboard
- Packaging box → product packaging
