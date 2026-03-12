# Weather Skill

Tra cứu thời tiết hiện tại và dự báo cho bất kỳ địa điểm nào.

## Khi nào dùng
- User hỏi về thời tiết, nhiệt độ, dự báo
- Cần kiểm tra thời tiết trước khi đề xuất hoạt động ngoài trời

## Cách dùng

### wttr.in (đơn giản, nhanh)
```bash
curl -s "wttr.in/Ho+Chi+Minh?format=3"
# Output: Ho Chi Minh City: ⛅️ +32°C

curl -s "wttr.in/Hanoi?lang=vi"
# Output: Dự báo chi tiết tiếng Việt
```

### Open-Meteo API (chi tiết hơn)
```bash
# Lấy tọa độ
curl -s "https://geocoding-api.open-meteo.com/v1/search?name=Saigon&count=1"

# Lấy thời tiết
curl -s "https://api.open-meteo.com/v1/forecast?latitude=10.82&longitude=106.63&current_weather=true"
```

## Lưu ý
- Không cần API key
- wttr.in có rate limit ~100 req/giờ
- Ưu tiên wttr.in cho câu hỏi đơn giản, Open-Meteo cho dữ liệu chi tiết
