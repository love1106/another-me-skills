---
name: am-devices
version: 2.0.0
author: khoidoan
description: >
  Điều khiển thiết bị của user qua SSH và CUA (Computer-Use Agent).
  Chạy lệnh, check thông tin, mở app, chụp screenshot, GUI control, transfer file.
  Kết nối qua Tailscale VPN. SSH-first, CUA-fallback.
  Use when: user hỏi về thiết bị, muốn chạy lệnh, check info, copy file, screenshot.
  Triggers: "thiết bị", "device", "máy tính", "laptop", "PC", "chạy lệnh",
  "mở app", "screenshot", "chụp màn hình", "copy file", "transfer".
  NOT for: CUA GUI interaction (→ am-computer-use), device linking/pairing,
  OpenClaw node pairing, network troubleshooting.
---

# My Devices — Điều khiển thiết bị qua SSH + CUA

Skill này cho phép kết nối và điều khiển thiết bị thật (PC, laptop, Mac) của user qua Tailscale VPN.

**Nguyên tắc: SSH-first, CUA-fallback** — ưu tiên SSH (rẻ, nhanh, 0 vision tokens). Chỉ dùng CUA khi cần GUI.

> 🔗 **Task cần GUI?** (click, type, đọc màn hình) → chuyển sang **am-computer-use**.

## Permissions

- reads: [devices.json, remote files via SSH/SCP]
- writes: [remote files via SSH/SCP, local temp files (/tmp/)]
- external: [SSH to linked devices, SCP file transfer]
- destructive: [remote command execution, remote file modification]
- requires_confirmation: [shutdown, restart, delete, format, install software]

## SSH Options

```bash
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519"
SCP_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -i ~/.openclaw/.ssh/id_ed25519"
```

> ⚠️ **Re-define mỗi exec session.** Biến không share giữa các lần chạy lệnh.

## Bước 1: Đọc danh sách thiết bị

```bash
cat ~/.openclaw/devices.json 2>/dev/null || echo "❌ Chưa có thiết bị. Hướng dẫn user liên kết device trong Dashboard."
```

### devices.json schema

```json
{
  "devices": [
    {
      "id": "device-uuid",
      "name": "Tên thiết bị",
      "ip": "100.x.x.x",
      "sshUser": "username",
      "platform": "windows | mac | linux",
      "status": "online | offline",
      "features": 3,
      "cua": { "port": 5000, "authToken": "hex", "mode": "background" }
    }
  ],
  "updatedAt": "ISO timestamp"
}
```

| Field | Mô tả |
|-------|--------|
| `features` | Bitwise: 0=none, 1=SSH, 2=CUA, 3=SSH+CUA |
| `cua` | CUA config (chỉ có khi `features & 2`). Port: Windows=5000, macOS=8000 |
| `platform` | `windows` / `mac` / `linux` |
| `status` | `online` / `offline` (cập nhật mỗi 2 phút) |

### Routing: SSH vs CUA

| Dùng SSH (skill này) | Dùng CUA (→ am-computer-use) |
|----------------------|------------------------------|
| Chạy CLI command | Click button, menu, dialog |
| Install/remove package | Điền form, nhập text vào GUI app |
| Đọc/sửa file, check system info | Nhìn/đọc nội dung trên màn hình |
| Copy/move file (scp) | Tương tác GUI app (browser, editor...) |
| Check process, service, logs | Chụp + phân tích screenshot |

> ⚠️ Nếu `features & 2` và task cần GUI → **chuyển sang am-computer-use**, không làm ở đây.

## Bước 2: Chọn thiết bị & Kiểm tra status

- **1 device** → dùng luôn
- **Nhiều device** → match keyword ("laptop", "PC", tên). Ambiguous → list cho user chọn.
- **BẮT BUỘC check status**: `"online"` → OK. `"offline"` → KHÔNG SSH, báo user.

## Bước 3: SSH vào thiết bị

```bash
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519"
ssh $SSH_OPTS {sshUser}@{ip} "{command}"
```

### Xử lý kết quả

- **exit 0** → hiển thị output
- **exit 255** (connection refused/timeout) → báo user: "Không kết nối được. Máy có thể tắt hoặc mất mạng."
- **Không retry quá 1 lần** — fail thì báo ngay.

### Ví dụ

```bash
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -o BatchMode=yes -i ~/.openclaw/.ssh/id_ed25519"

# Check hostname
ssh $SSH_OPTS {sshUser}@{ip} "hostname && whoami"

# System info (Windows)
ssh $SSH_OPTS {sshUser}@{ip} "systeminfo | findstr /B /C:\"OS\" /C:\"Total Physical\""

# PowerShell
ssh $SSH_OPTS {sshUser}@{ip} "powershell -Command 'Get-Process | Select -First 10'"

# Mở app
ssh $SSH_OPTS {sshUser}@{ip} "start chrome"         # Windows
ssh $SSH_OPTS {sshUser}@{ip} "open -a 'Google Chrome'" # macOS
```

## File Transfer

```bash
SCP_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -i ~/.openclaw/.ssh/id_ed25519"

# Upload
scp $SCP_OPTS /local/file {sshUser}@{ip}:/remote/path

# Download
scp $SCP_OPTS {sshUser}@{ip}:/remote/file /local/path
```

## Screenshot (SSH method)

> 💡 Nếu device có CUA (`features & 2`), **ưu tiên CUA screenshot** — xem **am-computer-use**.

**macOS:** `ssh $SSH_OPTS {sshUser}@{ip} "screencapture -x /tmp/am-screenshot.png"`
**Windows:** `ssh $SSH_OPTS {sshUser}@{ip} "nircmd savescreenshot C:\\Users\\{sshUser}\\am-screenshot.png"`
**Linux:** `ssh $SSH_OPTS {sshUser}@{ip} "DISPLAY=:0 scrot /tmp/am-screenshot.png"`

Kéo về + phân tích:
```bash
SCP_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5 -i ~/.openclaw/.ssh/id_ed25519"
scp $SCP_OPTS {sshUser}@{ip}:/tmp/am-screenshot.png /tmp/am-screenshot.png
# Dùng tool image để phân tích
```

Sau đó xóa file tạm cả 2 bên.

## Platform Notes

| Platform | Shell | Path | Mở app |
|----------|-------|------|--------|
| Windows | `cmd.exe`, `powershell -Command '...'` | `C:\Users\{user}\` | `start chrome` |
| macOS | `zsh` | `/Users/{user}/` | `open -a "App Name"` |
| Linux | `bash` | `/home/{user}/` | `xdg-open /path` |

> ⚠️ **GUI apps qua SSH** có thể không hiện trên desktop user. Windows `start` thường OK. macOS/Linux cần `DISPLAY`.
>
> 💡 **Cần tương tác GUI?** → **am-computer-use**

## Bảo mật

- **KHÔNG** xóa/format mà không confirm user
- **KHÔNG** đọc/gửi file chứa passwords, keys, tokens
- **KHÔNG** install software mà không confirm user
- **LUÔN** confirm trước: shutdown, restart, delete, format, install
