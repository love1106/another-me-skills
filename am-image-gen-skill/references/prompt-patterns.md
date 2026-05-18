# Prompt Engineering Patterns for GPT-Image-2

## Prompt Structure (Order matters)

```
[Subject & Composition] + [Style/Aesthetic] + [Lighting] + [Color Palette] + [Technical] + [Text] + [Negatives]
```

## 1. Subject & Composition

### Framing
- "centered slightly to the right" — offset creates visual interest
- "shot from a low close-up angle" — lifestyle/editorial feel  
- "top-down flat lay" — e-commerce catalog style
- "three-quarter top-down perspective" — product showcase
- "intimate medium shot" / "full-body framing" — for model shots

### Scene Description
- Be SPECIFIC about quantities: "1 bottle", "3 flowers", "5 citrus pieces"
- Describe spatial relationships: "in the foreground left", "behind the bottle"
- Use layers: foreground → subject → midground → background

## 2. Style & Aesthetic Keywords

### Photography Styles
- `studio product photography` — clean, commercial
- `editorial fashion photography` — lifestyle, aspirational
- `cinematic` — dramatic, film-like depth
- `35mm film photography` — analog warmth, grain
- `commercial food photography` — appetizing, glossy
- `luxury beauty campaign aesthetic` — high-end cosmetics
- `tilt-shift miniature aesthetic` — creative diorama style

### Art Styles
- `flat vector illustration` — logo, icon
- `hand-drawn watercolor` — organic, artisanal  
- `retro travel poster style` — vintage promotional
- `modern pencil illustration` — editorial illustration
- `hyper-realistic CGI render` — 3D product visualization

### Mood Modifiers
- `premium`, `luxury`, `high-end` — expensive feel
- `vibrant`, `energetic`, `bold` — attention-grabbing
- `minimal`, `clean`, `understated` — sophisticated
- `warm`, `cozy`, `intimate` — personal, lifestyle
- `dramatic`, `moody`, `cinematic` — high contrast storytelling

## 3. Lighting Recipes

### Studio Product
- "soft diffused lighting, no harsh shadows, clean background"
- "dramatic side lighting with strong specular highlights"
- "rim lighting highlighting edges, dark background"

### Lifestyle/Editorial
- "soft natural window light, shallow depth of field"
- "golden hour warm sunlight streaming from the left"
- "harsh direct on-camera flash, high contrast" (editorial edge)

### Luxury/Dark
- "dramatic warm lighting from upper left, golden highlights, deep reflections"
- "high-contrast, low-key lighting, crisp specular highlights on metal"
- "soft luminous bloom in background, moody atmosphere"

### Food/Product
- "glossy high-energy with strong sun flare, saturated colors"
- "overhead soft box lighting, slight steam/mist"

## 4. Color Palette Patterns

Instead of "colorful", be specific:
- "warm black-and-gold color palette"
- "muted beige and black palette"
- "saturated citrus colors (orange, lime green, golden yellow)"
- "pastel pink gradient with subtle bubble details"
- "deep navy, champagne gold, and ivory white"

## 5. Technical Quality Phrases

- `photorealistic, 8K resolution` — maximum detail
- `ultra-detailed, sharp focus` — clarity
- `shallow depth of field, soft bokeh` — subject isolation
- `realistic reflections, crisp packaging detail` — product realism
- `subtle film grain, high detail` — analog authenticity
- `Unreal Engine 5 render style` — CGI/3D products

## 6. Text Rendering

GPT-Image-2 handles text well. Pattern:
- Specify exact text in quotes: `reading "BRAND NAME"`
- Describe font style: "elegant serif", "bold sans-serif", "hand-written script"
- Specify placement: "upper left", "centered bottom", "along the top edge"
- Specify size relation: "large headline", "small caption", "prominent"
- Color: "in warm beige letters", "white text with gold outline"

**Example (English text):**
```
Add elegant serif headline text on the upper left reading "Premium Perfume" in large warm beige letters, with a smaller serif subheading beneath reading "Subtlety and Elegance", plus a thin short gold horizontal line below.
```

**Vietnamese text on images:**
- GPT-Image-2 CAN render Vietnamese with diacritics (tiếng Việt có dấu)
- Write the EXACT Vietnamese text in the prompt: `reading "Đẹp Tự Nhiên"`
- Short text (1-3 words) → usually accurate
- Long Vietnamese text (sentences) → may have diacritic errors. Warn user.
- If critical accuracy needed → suggest generating without text, then overlay text separately (Canva/Figma)
- Common patterns: brand name (often ASCII), tagline (often Vietnamese), price ("Đồng" or "VNĐ")

## 7. Negative Constraints

Always include for commercial work:
- `no watermark, no text` (if no text needed)
- `no blur, no noise` (quality)
- `no extra limbs, no deformed hands` (if people present)
- `clean background, no distracting elements`
- `no plastic skin, no airbrushing` (for realistic portraits)

## 8. Advanced Techniques

### Parametric Arguments
For reusable prompts, use variables for:
- Product name/brand
- Colors (primary, secondary)
- Text content (headline, tagline, CTA)
- Scene setting (location, time of day)

### Composition Control
- Reference grid: "organized into a clean grid system"
- Visual flow: "S-shaped composition", "diagonal leading line"
- Negative space: "large areas of negative space", "clean white space on left for text"

### Composition by Aspect Ratio

**1:1 (Square):**
- Subject dead center or rule-of-thirds offset
- Symmetric compositions work well
- Equal visual weight in all directions
- Text: top or bottom strip, or overlaid on subject

**4:5 (Portrait — IG post):**
- Subject upper-center, extra bottom space for text/CTA
- Or: product bottom-third, scene/mood fills top two-thirds
- Slight vertical bias — good for full-body model shots

**9:16 (Vertical — Story/Reel/TikTok):**
- Strong vertical hierarchy: header → hero → CTA
- Subject should have vertical orientation (standing bottle, full-body model)
- Leave top 15% and bottom 15% lighter for platform UI overlap (Telegram/IG have buttons there)
- Text stacked vertically, not wide horizontal

**16:9 (Wide — Web hero/FB cover):**
- Subject off-center (left or right third)
- Opposite side for text block
- Horizontal flow: eye moves left-to-right
- Good for split-layout (product left, text right)
- Avoid centering everything — feels static in wide format

**3:1 / 4:1 (Ultra-wide — website banner):**
- Very limited vertical space — subject must be compact
- Text + product side-by-side, both vertically centered
- Keep it simple: 2-3 elements max
- Often just: logo + tagline + subtle background texture

### Material Realism
- Glass: "realistic glass refraction, transparency, condensation droplets"
- Metal: "brushed metal textures, specular highlights, reflective surface"
- Fabric: "realistic fabric wrinkles and drape, silk texture"
- Skin: "visible subtle skin texture and micro pores, realistic dewy glow"

### Scale/Context Tricks
- Miniature diorama: "tiny figurine workers", "tilt-shift miniature aesthetic"
- Product hero: "oversized product as focal point"
- Lifestyle context: "placed naturally in a lived-in environment"

---

## 9. Anti-Patterns (AVOID These)

### Vague Quality Words
- ❌ "beautiful", "good lighting", "high quality", "nice colors"
- ✅ Be SPECIFIC: what kind of beautiful? what lighting setup? which colors?

### Style Contradiction
- ❌ "minimalist with lots of decorative elements"
- ❌ "vintage retro with modern neon cyberpunk"
- ✅ Pick ONE dominant style. Add subtle accent from another if needed.

### Overloading
- ❌ Cramming 10+ objects/elements → messy composition
- ✅ Max 5-7 distinct elements. Let the subject breathe.

### Generic Subjects
- ❌ "a bottle" → model guesses random shape/color
- ✅ "a tall cylindrical glass bottle with matte white label and rose gold pump cap"

### Conflicting Technical Instructions
- ❌ "photorealistic" + "cartoon style" in same prompt
- ❌ "8K detailed" + "soft dreamy blur everywhere"
- ✅ Commit to one rendering approach

### Text Overload
- ❌ 4+ different text elements → model struggles with placement
- ✅ Max 2-3 text elements (headline + subtitle + small logo/CTA)

### Negative Prompt Abuse
- ❌ Long list of 20 negatives → confuses model
- ✅ Only negate what's LIKELY to appear unwanted (3-5 max)

---

## 10. Vietnamese → English Product Description Guide

When user describes product in Vietnamese, translate with VISUAL SPECIFICITY:

| Việt | ❌ Literal | ✅ Visual English |
|------|-----------|-------------------|
| kem chống nắng | sunscreen | "a sleek 50ml tube of facial sunscreen with SPF50+ label, white body, coral-orange cap" |
| nước hoa | perfume | "a tall sculpted glass flacon with amber-gold liquid, crystal stopper, metallic collar" |
| đồng hồ | watch | "a stainless steel chronograph with black dial, two subdials, leather strap" |
| túi xách | handbag | "a medium structured leather tote in cognac brown, gold hardware, top handles" |
| điện thoại | phone | "a modern smartphone with edge-to-edge display, titanium frame, triple camera array" |
| giày | shoes | "a pair of white leather low-top sneakers with gum sole, minimal stitching" |
| sữa rửa mặt | cleanser | "a 150ml pump bottle of facial cleanser, frosted glass, mint-green label" |
| bánh | cake | "a round 3-layer chocolate cake with dark ganache drip, fresh berries on top" |
| cà phê | coffee | "a ceramic cup of Vietnamese drip coffee with condensed milk layer visible" |
| áo dài | ao dai | "a Vietnamese silk ao dai in emerald green with gold embroidery, matching pants" |

**Rule:** Always ask yourself — can the model "see" what I'm describing? If not, add shape, material, color, size cues.

---

## 11. Common Product Shapes & Materials Vocabulary

### Container Shapes
- Bottle: cylindrical / rectangular / hourglass / dropper / pump / spray
- Jar: round wide-mouth / hexagonal / apothecary
- Tube: squeeze tube / airless pump / roller
- Box: cube / rectangular / pillow-shaped / sleeve + tray

### Materials (describe the SURFACE)
- Glass: clear / frosted / smoky / amber / ribbed
- Plastic: matte / glossy / translucent / metallic finish
- Metal: brushed steel / polished chrome / rose gold / oxidized brass
- Paper/Card: kraft / matte laminated / soft-touch / embossed / foil-stamped
- Fabric: silk / linen / canvas / velvet / leather (smooth/pebbled/suede)

### Label & Packaging Detail
- Typography: serif / sans-serif / script / hand-lettered / mono
- Finish: matte / gloss / spot UV / foil (gold/silver/holographic)
- Elements: icon / pattern / border / seal / barcode area
