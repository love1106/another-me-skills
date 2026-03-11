# My Devices — Điều khiển thiết bị của user qua SSH

Skill này cho phép bạn kết nối và điều khiển các thiết bị (PC, laptop, Mac) mà user đã liên kết. Đây KHÔNG phải OpenClaw pairing — đây là thiết bị thật của user được kết nối qua Tailscale VPN.

## Khi nào dùng skill này

- User hỏi về "thiết bị", "device", "máy tính", "laptop", "PC" của họ
- User muốn chạy lệnh trên máy tính cá nhân
- User muốn check thông tin, mở app, copy file trên thiết bị
- User hỏi "kết nối với device nào", "device nào đang online"

## Bước 1: Đọc danh sách thiết bị

```bash
cat ~/.openclaw/devices.json
```

File này chứa danh sách thiết bị đã liên kết, cập nhật tự động mỗi 2 phút.

## Bước 2: Kiểm tra trước khi SSH

**BẮT BUỘC**: Kiểm tra `status` trong devices.json TRƯỚC khi SSH:
- `"status": "online"` → OK, tiến hành SSH
- `"status": "offline"` → **KHÔNG SSH**. Báo user ngay: "Thiết bị [tên] đang offline. Kiểm tra xem máy có bật và kết nối mạng không."

## Bước 3: SSH vào thiết bị

**LUÔN dùng timeout 5 giây** để tránh chờ lâu:

```bash
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519 {sshUser}@{ip} "{command}"
```

### Xử lý kết quả SSH

- **Thành công** (exit 0) → hiển thị output cho user
- **Connection refused / timeout** (exit 255) → báo user ngay: "Không kết nối được tới thiết bị. Có thể máy đang tắt hoặc mất mạng."
- **KHÔNG retry nhiều lần** — nếu fail lần đầu, báo user luôn. Không thử lại quá 1 lần.

### Ví dụ thực tế

```bash
# Check hostname + user
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519 PC@100.123.151.70 "hostname && whoami"

# Xem file trên Desktop (Windows)
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519 PC@100.123.151.70 "dir C:\Users\PC\Desktop"

# System info (Windows)
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519 PC@100.123.151.70 "systeminfo | findstr /B /C:\"OS\" /C:\"Total Physical\""

# Chạy PowerShell command
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519 PC@100.123.151.70 "powershell -Command 'Get-Process | Select -First 10'"

# Mở app (Windows)  
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519 PC@100.123.151.70 "start chrome"
```

## File Transfer (scp)

```bash
# Upload file lên thiết bị
scp -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i ~/.openclaw/.ssh/id_ed25519 /local/file {sshUser}@{ip}:/remote/path

# Download file từ thiết bị
scp -o StrictHostKeyChecking=no -o ConnectTimeout=5 -i ~/.openclaw/.ssh/id_ed25519 {sshUser}@{ip}:/remote/file /local/path
```

## Platform Notes

### Windows
- Shell mặc định: `cmd.exe`  
- Dùng PowerShell: `powershell -Command '...'`
- Path: backslash `C:\Users\PC\Desktop`
- Mở app: `start chrome`, `start notepad`

### macOS  
- Shell: `zsh`
- Mở app: `open -a "Google Chrome"`, `open /path/to/file`

### Linux
- Shell: `bash`
- Mở app: `xdg-open /path/to/file`

## Bảo mật

- KHÔNG chạy lệnh xóa/format mà không hỏi user trước
- KHÔNG đọc hoặc gửi file chứa mật khẩu, key, token ra ngoài
- Luôn confirm với user trước khi thực hiện thao tác nguy hiểm
