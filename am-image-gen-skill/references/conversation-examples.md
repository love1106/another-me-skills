# Conversation Examples

End-to-end examples showing the full Suggest → Refine → Generate flow.

---

## Example 1: Product Photo (Skincare)

**User:** Tạo ảnh sản phẩm cho chai serum vitamin C của em

**Agent (Step 1 → Step 2):**
> Em gợi ý 3 hướng:
> 1. **Clean Studio** — chai serum trên nền trắng, ánh sáng đều, kiểu Shopee/Lazada
> 2. **Ingredient Story** — serum bao quanh bởi lát cam, lá xanh, giọt tinh chất
> 3. **Luxury Dark** — nền đen sang trọng, ánh vàng dramatic, phản chiếu
>
> Anh thích hướng nào?

**User:** Hướng 2

**Agent (Step 3 — only missing info):**
> Tên brand trên chai là gì? Và ảnh dùng cho platform nào (IG post vuông, hay Shopee 1:1)?

**User:** Brand "GLOWLAB", dùng cho IG post

**Agent (Step 4 → builds prompt → Step 5 confirm):**

> 📋 Em confirm trước khi tạo:
> - **Nội dung:** Chai serum GLOWLAB 30ml, bọ quanh bởi lát cam, lá bạc hà, giọt tinh chất trên nền marble
> - **Size:** 1024x1024 (1:1 IG post)
> - **Quality:** high
> - **Format:** jpeg
>
> Confirm để em tạo nhé?

**User:** ok tạo đi

**Agent (Step 6 → generate):**

> Chờ em khoảng 1 phút nhé.

*Internal prompt built:*
```
A fresh, vibrant product photograph of a 30ml glass dropper bottle of vitamin C serum labeled "GLOWLAB" in clean sans-serif white text. The bottle is tall and cylindrical with clear amber glass, a white rubber dropper cap, and golden liquid visible inside. Centered on a light cream marble surface. Surrounding the bottle: 3 thin orange slices, scattered fresh green mint leaves, 2 small golden droplets of serum on the marble, and a halved orange in the background slightly blurred. Soft natural overhead lighting with warm golden tones, shallow depth of field focusing on the bottle. Color palette: amber gold, fresh orange, cream white, green accents. Bright, energetic, natural skincare aesthetic. Square 1:1 composition. Ultra-detailed, photorealistic, commercial product photography. No watermark, no extra text.
```

*Runs script:*
```bash
python3 <skill_path>/scripts/generate.py \
  --prompt "<above>" --size 1024x1024 --quality high --format jpeg
```
*Sends output via SendMessage*

**Agent:**
> Serum GLOWLAB kiểu Ingredient Story. Cần điều chỉnh gì không?

**User:** Đẹp rồi, nhưng muốn nền sáng hơn, bớt cam đi

**Agent (Step 6 — surgical edit: only background + color):**

*Modifies only: "light cream marble" → "pure white surface", removes "halved orange in background", adjusts palette → "amber gold, white, soft green accents"*

*Regenerates → sends*

---

## Example 2: Logo

**User:** Tạo logo cho quán cà phê tên "Mây Cafe"

**Agent (Step 1 → category = logo, Step 2):**
> Em gợi ý 3 hướng:
> 1. **Geometric Minimal** — icon mây đơn giản + typography sạch, 1 màu
> 2. **Organic Handcraft** — chữ viết tay, texture giấy kraft, tone trầm
> 3. **Playful Mascot** — đám mây dễ thương cầm ly cà phê
>
> Anh thích hướng nào?

**User:** Hướng 2, tone nâu ấm

**Agent (Step 3 — refine):**
> Font chữ "Mây Cafe" — kiểu viết tay bay bổng hay viết tay nét đậm mộc mạc?

**User:** Mộc mạc

**Agent (Step 5 → confirm):**

> 📋 Em confirm trước khi tạo:
> - **Nội dung:** Logo "Mây Cafe" — icon mây bút lông, chữ viết tay mộc mạc, tone nâu ấm
> - **Size:** 1024x1024
> - **Quality:** high
> - **Format:** png (nền trong suốt)
>
> Confirm để em tạo nhé?

**User:** Ư

**Agent (Step 6 → generate):**

> Chờ em khoảng 1 phút nhé.

*Prompt: ~80 words, transparent background, 1:1*
```
A hand-crafted artisanal logo for a Vietnamese café called "Mây Cafe". A simple stylized cloud icon drawn with rough brush strokes above the text. The text "Mây Cafe" in rustic hand-lettered thick brush script, slightly imperfect and organic. Warm earthy color palette: dark roasted brown (#3D1C02) with cream (#FFF8E7) accents. Aged kraft paper texture feel. No background (transparent). Minimalist composition, works at small sizes. No gradients, no 3D effects.
```

*Runs:*
```bash
python3 <skill_path>/scripts/generate.py \
  --prompt "<above>" --size 1024x1024 --quality high --background transparent --format png
```

---

## Example 3: Banner with Reference Image

**User:** *[sends image of a competitor's banner]* Tạo banner kiểu này cho brand của anh, tên "VitaFresh", sale 30%

**Agent (Step 0 — verify image):**
```bash
ls -lt <media_inbound>/ | head -3
# → file_580---abc123.jpg
```
*Uses `image` tool to verify: confirms it's a competitor banner with split layout, blue gradient.*

**Agent (Step 1 → UC1 Style Reference + Banner):**
> Em thấy reference: layout split (trái text, phải sản phẩm), nền gradient xanh, style energetic.
> 
> Em sẽ giữ layout + style tương tự, thay content thành VitaFresh. Sản phẩm VitaFresh là gì?

**User:** Nước ép trái cây đóng chai

**Agent (Step 3):**
> Ratio: FB post (1:1) hay IG story (9:16)?

**User:** FB post

**Agent (Step 5 → confirm):**

> 📋 Em confirm trước khi tạo:
> - **Nội dung:** Banner VitaFresh nước ép trái cây, layout split, sale 30%, style theo reference
> - **Size:** 1024x1024 (FB post)
> - **Quality:** high
> - **Format:** jpeg
> - **Ref images:** 1 (ảnh banner mẫu)
>
> Confirm để em tạo nhé?

**User:** ok

**Agent (Step 6 → generate):**

> Chờ em khoảng 1-2 phút nhé (có ref image).

```bash
python3 <skill_path>/scripts/generate.py \
  --prompt "<built prompt using UC1 skeleton>" \
  --size 1024x1024 --quality high --format jpeg \
  --images <media_inbound>/file_580---abc123.jpg
```
*Script outputs path → agent sends via SendMessage*

---

## Example 4: Quick Mode (Power User)

**User:** Gen ảnh: chai nước hoa đen sang trọng, nền đen, ánh vàng, khói, 1:1, luxury dark, không text

**Agent (detects UC12 — full prompt provided, skips Steps 1-3, vào Step 5 confirm):**

> 📋 Em confirm trước khi tạo:
> - **Nội dung:** Chai nước hoa đen, nền đen, ánh sáng vàng dramatic, khói, luxury dark
> - **Size:** 1024x1024
> - **Quality:** high
> - **Format:** jpeg
>
> Confirm để em tạo nhé?

**User:** tạo đi

**Agent:**
> Chờ em khoảng 1 phút nhé.

*Builds enhanced prompt from user's description, adds lighting/material/technical detail → generates*

**Agent:**
> Luxury dark perfume. Cần tweak gì không?

---

## Example 5: Catalog Series (UC5)

**User:** Em có 5 sản phẩm skincare cùng dòng. Tạo ảnh catalog cùng style cho tất cả.

**Agent:**
> OK, em tạo ảnh đầu tiên trước. Sản phẩm đầu là gì?

**User:** Sữa rửa mặt 150ml, chai pump trắng

**Agent:** *generates first image (P1 Clean Studio)*

**User:** Đẹp, giữ style này

**Agent:**
> Em save style này làm template. Gửi em tên + mô tả ngắn 4 SP còn lại, em gen lần lượt cùng style nhé.
> Đã confirm style rồi nên em sẽ gen luôn không hỏi lại từng ảnh.
>
> *[Saves base prompt to session context for reuse]*

**User:** 
- Toner 200ml chai trong suốt
- Serum 30ml dropper amber  
- Kem dưỡng 50ml jar trắng
- Mặt nạ gói 25ml sachet bạc

**Agent:** *generates each, swapping only the product description, keeping everything else identical — không confirm lại từng ảnh vì user đã confirm style*
