# Multi-Round Review Methodology

Quy trình review skill qua nhiều vòng, mỗi vòng đổi góc tiếp cận, cho đến khi không còn tìm được issue đáng kể.

## Nguyên tắc cốt lõi

- **Không bao giờ tự tin nói "clean" cho đến khi thật sự simulate chạy từng bước**
- **Mỗi round đổi góc tiếp cận** — không lặp lại cách review cũ
- **Fix xong mới review tiếp** — không gom issues qua nhiều rounds
- **User confirm trước khi push**

## Danh sách các góc review

### Góc cơ bản (áp dụng cho MỌI skill)

| Góc | Mô tả | Khi nào dùng |
|---|---|---|
| **Logic & Consistency** | Mâu thuẫn giữa steps, thứ tự sai, references lệch | Luôn dùng ở round đầu |
| **Completeness** | Thiếu step, thiếu hướng dẫn, gap trong flow | Round 2-3 |
| **Clarity & Ambiguity** | Instruction mơ hồ, ai làm gì không rõ, có thể hiểu sai | Mọi skill |
| **Deep Simulation** | Đóng vai agent chạy workflow với scenario thật | Bắt buộc ít nhất 1 round |
| **Edge Cases** | Input rỗng, file không tồn tại, tool chưa setup, state bất thường | Mọi skill |
| **Adversarial** | Cố tìm cách phá workflow, scenarios bất thường | Bắt buộc ở round cuối |

### Góc chuyên biệt (chỉ khi skill có yếu tố tương ứng)

| Góc | Mô tả | Khi nào dùng |
|---|---|---|
| **Shell & Commands** | Syntax, biến scope, portability (bash/zsh), commands hang | Skill có shell commands |
| **Resilience** | Survive khi sub-tool behave bất thường, cleanup khi fail | Skill gọi tools/processes bên ngoài |
| **Variable & State** | Biến có available across sessions, data flow giữa steps | Skill chạy qua nhiều exec sessions |
| **API & Integration** | API keys, rate limits, error handling, response format | Skill gọi APIs |
| **Security** | Secrets exposure, input validation, permission escalation | Skill xử lý data nhạy cảm |
| **Anthropic Standards** | Size (<5K words), progressive disclosure, description quality, composability | Mọi skill — dùng 1 lần trong review |

> 📎 Chi tiết Anthropic Standards: đọc `anthropic-skill-guidelines.md` → chạy Quality Checklist.

## Suggested Flow

1. **Round đầu** → **Logic & Consistency** (luôn bắt đầu ở đây)
2. **Rounds giữa** → Chọn theo loại skill: Completeness, Clarity, Simulation, Edge Cases, và các góc chuyên biệt phù hợp
3. **Round cuối** → **Adversarial** (bắt buộc, luôn kết thúc ở đây)

## Cách chạy mỗi round

1. **Chọn góc** — chọn góc chưa dùng, phù hợp với skill
2. **Đọc toàn bộ** — đọc file từ đầu đến cuối, không skip
3. **Simulate** — ít nhất 1 scenario thực tế, trace từng bước
4. **Ghi findings** — bảng: #, Mức (🔴🟡🟢), Issue
5. **Trình bày** — gửi user
6. **User approve → fix tất cả → commit**
7. **Round tiếp** — trên phiên bản đã fix

**Nếu 1 round có >10 issues:** chia thành 2 rounds — fix 🔴 trước, 🟡🟢 round sau.

## Khi nào dừng?

**Guideline số rounds** (không phải hard rule):
- **Patch nhỏ** (typo, config): 1-2 rounds
- **Patch phức tạp** (bug logic): ~3 rounds
- **Improve/Refactor**: ~5 rounds

**Điều kiện dừng** (ưu tiên cao hơn guideline):
- Adversarial round trả về ≤ 1 issue 🟢 → **DONE** (dù chưa đủ guideline số rounds)
- Không bao giờ dừng sớm vì "thấy ổn rồi" — luôn chạy ít nhất 1 round adversarial cuối

## Checklist nhanh cho mỗi round

```
[ ] Đọc toàn bộ file từ đầu đến cuối (không skip)
[ ] Chọn góc tiếp cận khác round trước
[ ] Simulate ít nhất 1 scenario thực tế
[ ] Trace từng bước/instruction trong skill
[ ] Trình bày findings dạng bảng (Mức + Issue)
[ ] User approve → fix → commit
[ ] Không nói "clean" trừ khi adversarial round trả về ≤ 1 issue 🟢
```

## Anti-patterns (TRÁNH)

- ❌ "Không thấy issue nào nữa" sau 2-3 rounds → **luôn có, đổi góc nhìn**
- ❌ Review chỉ đọc mà không simulate → **phải trace thật sự**
- ❌ Fix nhiều thứ không commit → **atomic commits sau mỗi round**
- ❌ Skip adversarial round → **round quan trọng nhất, phải chạy**
- ❌ Copy nguyên từ tham khảo → **adapt cho context, không transplant**
- ❌ Apply coding-specific checks cho non-coding skill → **chọn góc phù hợp**
