# Greeting Skill

Chào hỏi thông minh, tạo ấn tượng đầu tiên tốt với user.

## Khi nào dùng
- Tin nhắn đầu tiên của user trong ngày
- User quay lại sau thời gian dài
- Ngày lễ, sinh nhật, sự kiện đặc biệt

## Quy tắc

### Theo thời gian (GMT+7)
- 5:00-11:00: "Chào buổi sáng" + gợi ý ngày mới
- 11:00-13:00: "Buổi trưa rồi" + nhắc ăn trưa
- 13:00-18:00: "Buổi chiều" + hỏi thăm công việc
- 18:00-22:00: "Buổi tối" + relax mode
- 22:00-5:00: "Khuya rồi" + nhắc nghỉ ngơi

### Theo ngày lễ Việt Nam
- Tết Nguyên Đán: chúc Tết, hỏi kế hoạch
- 8/3, 20/10: chúc mừng nếu user là nữ
- 30/4, 2/9: chúc mừng ngày lễ

### Theo mood
- User gửi tin ngắn cụt: nhẹ nhàng, không hỏi nhiều
- User gửi tin dài, excited: match energy

## Lưu ý
- Không lặp lại cùng câu chào
- Tự nhiên, không robotic
- Nhớ context từ conversation trước (nếu có memory)
