---
name: am-devices
description: "Điều khiển thiết bị của user qua SSH — chạy lệnh, check thông tin, mở app, chụp screenshot, transfer file. Kết nối qua Tailscale VPN."
---

# My Devices — Điều khiển thiết bị của user qua SSH

Skill này cho phép bạn kết nối và điều khiển các thiết bị (PC, laptop, Mac) mà user đã liên kết. Đây KHÔNG phải OpenClaw pairing — đây là thiết bị thật của user được kết nối qua Tailscale VPN.

## SSH Options (dùng xuyên suốt skill)

Define 1 lần, dùng lại ở mọi command:

```bash
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519"
SCP_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -i ~/.openclaw/.ssh/id_ed25519"
```

> ⚠️ **Biến không share giữa exec sessions.** Phải re-define `SSH_OPTS`/`SCP_OPTS` mỗi lần chạy lệnh mới.

## Khi nào dùng skill này

- User hỏi về "thiết bị", "device", "máy tính", "laptop", "PC" của họ
- User muốn chạy lệnh trên máy tính cá nhân
- User muốn check thông tin, mở app, copy file trên thiết bị
- User hỏi "kết nối với device nào", "device nào đang online"

## Bước 1: Đọc danh sách thiết bị

```bash
if [ -f ~/.openclaw/devices.json ]; then
  cat ~/.openclaw/devices.json
else
  echo "❌ Chưa có thiết bị nào được liên kết. Hướng dẫn user liên kết device trong Another Me dashboard."
fi
```

### devices.json schema

```json
[
  {
    "name": "PC Văn Phòng",
    "ip": "100.123.151.70",
    "sshUser": "PC",
    "os": "windows",
    "status": "online",
    "lastSeen": "2026-03-14T12:00:00Z"
  }
]
```

| Field | Mô tả |
|-------|--------|
| `name` | Tên hiển thị do user đặt |
| `ip` | Tailscale IP |
| `sshUser` | SSH username |
| `os` | `windows` / `macos` / `linux` |
| `status` | `online` / `offline` (cập nhật mỗi 2 phút) |
| `lastSeen` | Lần cuối device phản hồi |

## Bước 2: Chọn thiết bị & Kiểm tra status

### Chọn thiết bị
- **1 device** → dùng luôn
- **Nhiều device** → match theo keyword user nói ("laptop", "PC", tên device). Nếu vẫn ambiguous → **list ra cho user chọn**, không đoán.

### Kiểm tra status
**BẮT BUỘC** trước khi SSH:
- `"status": "online"` → OK, tiến hành SSH
- `"status": "offline"` → **KHÔNG SSH**. Báo user ngay: "Thiết bị [tên] đang offline. Kiểm tra xem máy có bật và kết nối mạng không."

## Bước 3: SSH vào thiết bị

```bash
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519"
ssh $SSH_OPTS {sshUser}@{ip} "{command}"
```

### Xử lý kết quả SSH

- **Thành công** (exit 0) → hiển thị output cho user
- **Connection refused / timeout** (exit 255) → báo user ngay: "Không kết nối được tới thiết bị. Có thể máy đang tắt hoặc mất mạng."
- **KHÔNG retry nhiều lần** — nếu fail lần đầu, báo user luôn. Không thử lại quá 1 lần.

### Ví dụ thực tế

```bash
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519"

# Check hostname + user
ssh $SSH_OPTS PC@100.123.151.70 "hostname && whoami"

# System info (Windows)
ssh $SSH_OPTS PC@100.123.151.70 "systeminfo | findstr /B /C:\"OS\" /C:\"Total Physical\""

# Chạy PowerShell command
ssh $SSH_OPTS PC@100.123.151.70 "powershell -Command 'Get-Process | Select -First 10'"

# Mở app (Windows) — chỉ hoạt động nếu SSH session có desktop access
ssh $SSH_OPTS PC@100.123.151.70 "start chrome"
```

## File Transfer (scp)

```bash
SCP_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -i ~/.openclaw/.ssh/id_ed25519"

# Upload file lên thiết bị
scp $SCP_OPTS /local/file {sshUser}@{ip}:/remote/path

# Download file từ thiết bị
scp $SCP_OPTS {sshUser}@{ip}:/remote/file /local/path
```

## Screenshot — Chụp màn hình thiết bị

Chụp screenshot từ xa → kéo ảnh về → phân tích bằng vision model.

### Chụp

```bash
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519"
SCP_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -i ~/.openclaw/.ssh/id_ed25519"
```

**Mac:**
```bash
ssh $SSH_OPTS {user}@{ip} "screencapture -x /tmp/am-screenshot.png"
```

**Linux (X11):**
```bash
ssh $SSH_OPTS {user}@{ip} "DISPLAY=:0 scrot /tmp/am-screenshot.png"
# Fallback nếu scrot không có:
ssh $SSH_OPTS {user}@{ip} "DISPLAY=:0 import -window root /tmp/am-screenshot.png"
```

**Windows (dùng nircmd — recommended):**
```bash
ssh $SSH_OPTS {user}@{ip} "nircmd savescreenshot C:\\Users\\{user}\\am-screenshot.png"
```

Nếu không có `nircmd`, dùng PowerShell:
```bash
ssh $SSH_OPTS {user}@{ip} "powershell -File C:\\scripts\\screenshot.ps1"
```
> Agent có thể tạo `screenshot.ps1` trên device lần đầu nếu cần.

### Kéo ảnh về

```bash
# Mac/Linux
scp $SCP_OPTS {user}@{ip}:/tmp/am-screenshot.png /tmp/am-screenshot.png

# Windows
scp $SCP_OPTS {user}@{ip}:C:/Users/{user}/am-screenshot.png /tmp/am-screenshot.png
```

### Phân tích

Dùng tool `image` để phân tích screenshot:
```
image(image="/tmp/am-screenshot.png", prompt="Describe what's on screen")
```

### Dọn dẹp

Sau khi phân tích, xóa file tạm:
```bash
ssh $SSH_OPTS {user}@{ip} "rm /tmp/am-screenshot.png"
rm /tmp/am-screenshot.png
```

## Platform Notes

| Platform | Shell | Path style | Mở app |
|----------|-------|------------|--------|
| Windows | `cmd.exe` (default), `powershell -Command '...'` | `C:\Users\PC\Desktop` | `start chrome` |
| macOS | `zsh` | `/Users/{user}/` | `open -a "Google Chrome"` |
| Linux | `bash` | `/home/{user}/` | `xdg-open /path/to/file` |

> ⚠️ **GUI apps qua SSH:** Mở app GUI (Chrome, Finder...) qua SSH có thể không hiện trên màn hình user nếu SSH session không có desktop context. Trên Windows thường hoạt động với `start`. Trên Mac/Linux cần `DISPLAY` env var.

## Bảo mật

- **KHÔNG** chạy lệnh xóa/format mà không hỏi user trước
- **KHÔNG** đọc hoặc gửi file chứa mật khẩu, key, token ra ngoài
- **KHÔNG** install software trên device mà không hỏi user
- Luôn confirm với user trước khi thực hiện thao tác nguy hiểm (shutdown, restart, delete)
