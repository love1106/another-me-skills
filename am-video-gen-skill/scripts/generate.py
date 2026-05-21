#!/usr/bin/env python3
"""
Video generation, editing, and extension via xAI grok-imagine-video.

Modes:
  generate  — text-to-video, image-to-video, reference-to-video (default)
  edit      — edit existing video by prompt
  extend    — extend existing video with new footage

Usage:
  # Text-to-video
  python3 generate.py --prompt "A cat on a beach" --duration 5

  # Image-to-video
  python3 generate.py --prompt "Flower blooms" --image photo.jpg

  # Image-to-video (auto-animate, no prompt needed)
  python3 generate.py --image photo.jpg

  # Reference-to-video
  python3 generate.py --prompt "Person from <IMAGE_1> wears <IMAGE_2>" --refs person.jpg shirt.jpg

  # Edit existing video
  python3 generate.py --mode edit --video input.mp4 --prompt "Add sunglasses"

  # Extend existing video
  python3 generate.py --mode extend --video input.mp4 --prompt "Camera zooms out" --duration 6

Required env vars:
  OPENAI_BASE_URL — Proxy base URL
  OPENAI_API_KEY  — API key
"""

import argparse
import atexit
import base64
import json
import os
import sys
import time
import urllib.request
import subprocess
from pathlib import Path
from datetime import datetime

# Track temp files for cleanup
_temp_files = []

def _cleanup_temp():
    for f in _temp_files:
        try:
            if os.path.exists(f):
                os.unlink(f)
        except OSError:
            pass

atexit.register(_cleanup_temp)

DEFAULT_MODEL = "grok-imagine-video"
OUTBOUND_DIR = os.path.expanduser("~/.openclaw/workspace/outbound")
POLL_INTERVAL = 5
POLL_TIMEOUT = 600
MAX_IMG_PX = 1280       # Cap image longest side before base64
MAX_IMG_QUALITY = 85    # JPEG quality for processed images

# Resolution pixel heights
RES_PX = {"480p": 480, "720p": 720, "1080p": 1080}

# Aspect ratio float values
RATIO_VALUES = {
    "1:1": 1.0, "16:9": 16/9, "9:16": 9/16,
    "4:3": 4/3, "3:4": 3/4, "3:2": 3/2, "2:3": 2/3,
}

# Ratio mismatch threshold (>10% difference = mismatch)
RATIO_MISMATCH_THRESHOLD = 0.10


def get_env():
    """Get and validate required environment variables."""
    base = os.environ.get("OPENAI_BASE_URL", "")
    key = os.environ.get("OPENAI_API_KEY", "")
    if not base:
        print("ERROR: OPENAI_BASE_URL env var not set.", file=sys.stderr)
        sys.exit(1)
    if not key:
        print("ERROR: OPENAI_API_KEY env var not set.", file=sys.stderr)
        sys.exit(1)
    base = base.rstrip("/")
    # Ensure base URL ends with /v1
    if not base.endswith("/v1"):
        base = base + "/v1"
    return base, key


_imagemagick_available = None

def _install_imagemagick() -> bool:
    """Attempt to install ImageMagick via apt-get. Returns True if successful."""
    try:
        print("INFO: ImageMagick not found. Installing...", file=sys.stderr)
        subprocess.run(
            ["apt-get", "update", "-qq"],
            capture_output=True, timeout=60
        )
        result = subprocess.run(
            ["apt-get", "install", "-y", "-qq", "imagemagick"],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            print("INFO: ImageMagick installed successfully.", file=sys.stderr)
            return True
        print(f"WARNING: ImageMagick install failed: {result.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"WARNING: ImageMagick install error: {e}", file=sys.stderr)
    return False


def has_imagemagick() -> bool:
    """Check if ImageMagick is available, auto-install if missing (cached)."""
    global _imagemagick_available
    if _imagemagick_available is None:
        _imagemagick_available = subprocess.run(["which", "convert"], capture_output=True).returncode == 0
        if not _imagemagick_available:
            if _install_imagemagick():
                _imagemagick_available = subprocess.run(["which", "convert"], capture_output=True).returncode == 0
    return _imagemagick_available


def get_image_dimensions(path: str) -> tuple:
    """Get image width and height using ImageMagick identify."""
    try:
        result = subprocess.run(
            ["identify", "-format", "%w %h", path],
            capture_output=True, text=True, check=True
        )
        w, h = result.stdout.strip().split()
        return int(w), int(h)
    except Exception as e:
        print(f"WARNING: Cannot get image dimensions: {e}", file=sys.stderr)
        return None, None


def process_image(path: str, max_px: int = MAX_IMG_PX) -> str:
    """Process image: resize if too large. Returns path to processed image."""
    if not os.path.isfile(path):
        print(f"ERROR: Image not found: {path}", file=sys.stderr)
        sys.exit(1)

    if not has_imagemagick():
        print("WARNING: ImageMagick not found. Sending image as-is.", file=sys.stderr)
        return path

    w, h = get_image_dimensions(path)
    if w is None:
        return path

    ratio = w / h
    print(f"  Image: {w}x{h} (ratio {ratio:.2f})", file=sys.stderr)

    # Only resize if too large
    if max(w, h) <= max_px:
        return path

    tmp = f"/tmp/_vid_img_processed_{os.getpid()}.jpg"
    _temp_files.append(tmp)

    try:
        cmd = ["convert", path, "-resize", f"{max_px}x{max_px}>",
               "-quality", str(MAX_IMG_QUALITY), tmp]
        subprocess.run(cmd, check=True, capture_output=True)

        new_size = os.path.getsize(tmp) // 1024
        print(f"  Resized {Path(path).name}: {w}x{h} → ≤{max_px}px ({new_size}KB)", file=sys.stderr)
        return tmp

    except Exception as e:
        print(f"WARNING: Image processing failed: {e}. Sending as-is.", file=sys.stderr)
        return path


def find_nearest_ratio(img_ratio: float) -> str:
    """Find the nearest supported aspect ratio string for a given ratio."""
    best = min(RATIO_VALUES.items(), key=lambda kv: abs(kv[1] - img_ratio))
    return best[0]


def analyze_ratio(image_path: str, target_ratio: str) -> dict:
    """Analyze image vs target ratio, recommend crop or outpaint.

    Returns dict with:
      - action: 'none' | 'crop' | 'outpaint'
      - reason: human-readable explanation
      - img_w, img_h, img_ratio: source image info
      - target_ratio_str, target_ratio_val: target info
      - crop_box: (left, top, right, bottom) if action=crop
      - nearest_ratio: closest supported ratio to image
    """
    w, h = get_image_dimensions(image_path)
    if w is None:
        return {"action": "none", "reason": "Cannot read image dimensions"}

    img_ratio = w / h
    target_val = RATIO_VALUES.get(target_ratio)
    if target_val is None:
        return {"action": "none", "reason": f"Unknown target ratio: {target_ratio}"}

    nearest = find_nearest_ratio(img_ratio)
    mismatch = abs(img_ratio - target_val) / max(img_ratio, target_val)

    result = {
        "img_w": w, "img_h": h, "img_ratio": round(img_ratio, 3),
        "target_ratio_str": target_ratio, "target_ratio_val": round(target_val, 3),
        "nearest_ratio": nearest, "mismatch_pct": round(mismatch * 100, 1),
    }

    # No mismatch — image already matches target
    if mismatch <= RATIO_MISMATCH_THRESHOLD:
        result["action"] = "none"
        result["reason"] = f"Image ratio {img_ratio:.2f} matches target {target_ratio} (mismatch {mismatch*100:.0f}%)"
        return result

    # Try crop: can we crop to target ratio without losing too much?
    if img_ratio > target_val:
        # Image is wider than target — crop width
        new_w = int(h * target_val)
        crop_left = (w - new_w) // 2
        crop_box = (crop_left, 0, crop_left + new_w, h)
        lost_pct = (w - new_w) / w * 100
    else:
        # Image is taller than target — crop height
        new_h = int(w / target_val)
        crop_top = (h - new_h) // 2
        crop_box = (0, crop_top, w, crop_top + new_h)
        lost_pct = (h - new_h) / h * 100

    # Crop is safe if we lose ≤50% and the remaining area is reasonable
    # (product is usually centered, so center crop works)
    if lost_pct <= 50:
        result["action"] = "crop"
        result["crop_box"] = crop_box
        result["crop_lost_pct"] = round(lost_pct, 1)
        result["reason"] = (
            f"Crop recommended: {w}x{h} → {crop_box[2]-crop_box[0]}x{crop_box[3]-crop_box[1]} "
            f"(lose {lost_pct:.0f}% {'width' if img_ratio > target_val else 'height'}). "
            f"Product at center should be preserved."
        )
    else:
        result["action"] = "outpaint"
        result["crop_lost_pct"] = round(lost_pct, 1)
        result["reason"] = (
            f"Outpaint recommended: crop would lose {lost_pct:.0f}% {'width' if img_ratio > target_val else 'height'} "
            f"(too aggressive). AI extend is safer but may alter product details slightly."
        )

    return result


def crop_image(image_path: str, target_ratio: str) -> str:
    """Center-crop image to target aspect ratio. Returns path to cropped image."""
    w, h = get_image_dimensions(image_path)
    if w is None:
        return image_path

    target_val = RATIO_VALUES.get(target_ratio)
    if target_val is None:
        return image_path

    img_ratio = w / h
    if abs(img_ratio - target_val) / max(img_ratio, target_val) <= RATIO_MISMATCH_THRESHOLD:
        print(f"  Crop skipped: ratio already matches", file=sys.stderr)
        return image_path

    if img_ratio > target_val:
        new_w = int(h * target_val)
        new_w += new_w % 2  # even
        offset = (w - new_w) // 2
        geometry = f"{new_w}x{h}+{offset}+0"
    else:
        new_h = int(w / target_val)
        new_h += new_h % 2  # even
        offset = (h - new_h) // 2
        geometry = f"{w}x{new_h}+0+{offset}"

    tmp = f"/tmp/_vid_img_cropped_{os.getpid()}.jpg"
    _temp_files.append(tmp)
    try:
        cmd = ["convert", image_path, "-crop", geometry, "+repage",
               "-quality", str(MAX_IMG_QUALITY), tmp]
        subprocess.run(cmd, check=True, capture_output=True)
        cw, ch = get_image_dimensions(tmp)
        print(f"  Cropped: {w}x{h} → {cw}x{ch} (target {target_ratio})", file=sys.stderr)
        return tmp
    except Exception as e:
        print(f"WARNING: Crop failed: {e}. Sending as-is.", file=sys.stderr)
        return image_path


def encode_image(path: str) -> str:
    """Encode image file as base64 data URI."""
    with open(path, "rb") as f:
        img_bytes = f.read()
    b64 = base64.b64encode(img_bytes).decode()
    ext = Path(path).suffix.lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
    return f"data:{mime};base64,{b64}"


def encode_video(path: str) -> str:
    """Encode video file as base64 data URI."""
    if not os.path.isfile(path):
        print(f"ERROR: Video not found: {path}", file=sys.stderr)
        sys.exit(1)
    size_mb = os.path.getsize(path) / (1024 * 1024)
    if size_mb > 100:
        print(f"ERROR: Video too large ({size_mb:.1f}MB). Max ~100MB for base64.", file=sys.stderr)
        sys.exit(1)
    print(f"  Encoding video: {size_mb:.1f}MB", file=sys.stderr)
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:video/mp4;base64,{b64}"


def make_output_path(output: str, suffix: str = "") -> str:
    """Generate output path with timestamp."""
    if output:
        return output
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    tag = f"-{suffix}" if suffix else ""
    return os.path.join(OUTBOUND_DIR, f"vid-{ts}{tag}.mp4")


def api_request(url: str, api_key: str, method: str = "GET", data: dict = None, timeout: int = 60) -> dict:
    """Make an API request, return parsed JSON."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    if body:
        size_kb = len(body) // 1024
        if size_kb > 100:
            print(f"  Payload: {size_kb}KB", file=sys.stderr)
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"HTTP {e.code}: {error_body[:500]}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        raise


def download_video(url: str, output: str, timeout: int = 180, retries: int = 3):
    """Download video from URL to local file with retry."""
    os.makedirs(os.path.dirname(output), exist_ok=True)
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                with open(output, "wb") as f:
                    f.write(resp.read())
            size_mb = os.path.getsize(output) / (1024 * 1024)
            print(f"  Downloaded: {size_mb:.1f}MB", file=sys.stderr)
            return
        except Exception as e:
            if attempt < retries:
                wait = 5 * attempt
                print(f"  Download failed (attempt {attempt}): {e}. Retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"ERROR: Download failed after {retries} attempts: {e}", file=sys.stderr)
                raise


def submit_and_poll(base_url: str, api_key: str, endpoint: str, payload: dict,
                    output: str, mode_label: str, json_output: bool = False) -> str:
    """Submit request, poll for completion, download result. Returns output path."""
    t0 = time.time()
    result = None

    for attempt in range(1, 4):
        print(f"[Submit attempt {attempt}] POST {endpoint}", file=sys.stderr)
        try:
            result = api_request(endpoint, api_key, method="POST", data=payload, timeout=120)
            break
        except Exception as e:
            if attempt < 3:
                wait = 5 * attempt
                print(f"  Submit failed, retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"ERROR: Failed to submit after 3 attempts: {e}", file=sys.stderr)
                sys.exit(1)

    request_id = result.get("request_id")
    if not request_id:
        print(f"ERROR: No request_id in response: {json.dumps(result)[:300]}", file=sys.stderr)
        sys.exit(1)
    print(f"  request_id: {request_id}", file=sys.stderr)

    # Poll
    poll_url = f"{base_url}/videos/{request_id}"
    poll_count = 0
    max_polls = POLL_TIMEOUT // POLL_INTERVAL

    while poll_count < max_polls:
        time.sleep(POLL_INTERVAL)
        poll_count += 1
        elapsed = time.time() - t0

        try:
            status_result = api_request(poll_url, api_key)
        except Exception:
            backoff = min(POLL_INTERVAL * 2, 15)
            print(f"  [Poll {poll_count}] Failed to check status, backoff {backoff}s...", file=sys.stderr)
            time.sleep(backoff)
            continue

        status = status_result.get("status", "unknown")

        if status == "done":
            video_url = status_result.get("video", {}).get("url")
            video_duration = status_result.get("video", {}).get("duration", "?")
            print(f"  [Poll {poll_count}] Done in {elapsed:.0f}s | Duration: {video_duration}s", file=sys.stderr)

            if not video_url:
                print(f"ERROR: No video URL in response: {json.dumps(status_result)[:300]}", file=sys.stderr)
                sys.exit(1)

            out_path = make_output_path(output, mode_label)
            download_video(video_url, out_path)

            if json_output:
                result_data = {
                    "status": "ok",
                    "mode": mode_label,
                    "path": out_path,
                    "duration": video_duration,
                    "elapsed_seconds": round(elapsed),
                    "size_mb": round(os.path.getsize(out_path) / (1024 * 1024), 1),
                }
                print(json.dumps(result_data))
            else:
                print(out_path)
            print(f"  {elapsed:.0f}s total | {mode_label}", file=sys.stderr)
            return out_path

        elif status in ("failed", "expired"):
            print(f"  [Poll {poll_count}] Status: {status} after {elapsed:.0f}s", file=sys.stderr)
            error_detail = json.dumps(status_result)[:500]
            print(f"ERROR: Video generation {status}: {error_detail}", file=sys.stderr)
            if json_output:
                print(json.dumps({"status": "error", "error": status, "detail": error_detail[:200]}))
            sys.exit(1)

        else:
            if poll_count % 3 == 0:
                print(f"  [Poll {poll_count}] Still generating... ({elapsed:.0f}s elapsed)", file=sys.stderr)

    elapsed = time.time() - t0
    print(f"ERROR: Timeout after {elapsed:.0f}s ({max_polls} polls). request_id: {request_id}", file=sys.stderr)
    sys.exit(1)


def cmd_generate(args):
    """Handle generate mode: text-to-video, image-to-video, reference-to-video."""
    base_url, api_key = get_env()

    if args.image and args.refs:
        print("ERROR: Cannot use both --image and --refs. Pick one.", file=sys.stderr)
        sys.exit(1)

    payload = {
        "model": args.model,
        "duration": args.duration,
        "aspect_ratio": args.aspect_ratio,
        "resolution": args.resolution,
    }
    if args.prompt:
        payload["prompt"] = args.prompt

    mode = "text-to-video"
    if args.image:
        mode = "image-to-video"
        img_path = args.image
        # Auto-crop if requested
        if args.crop:
            img_path = crop_image(img_path, args.aspect_ratio)
        processed = process_image(img_path, max_px=MAX_IMG_PX)
        payload["image"] = {"url": encode_image(processed)}
        if not args.prompt:
            mode = "image-to-video-auto"
    elif args.refs:
        mode = "reference-to-video"
        payload["reference_images"] = [
            {"url": encode_image(process_image(r, max_px=MAX_IMG_PX))} for r in args.refs
        ]
    elif not args.prompt:
        print("ERROR: --prompt is required for text-to-video.", file=sys.stderr)
        sys.exit(1)

    print(f"Mode: {mode} | Duration: {args.duration}s | Ratio: {args.aspect_ratio} | Res: {args.resolution}", file=sys.stderr)

    if args.dry_run:
        dry_payload = {}
        for k, v in payload.items():
            if k == "image":
                dry_payload[k] = "<base64 image>"
            elif k == "reference_images":
                dry_payload[k] = f"<{len(v)} ref images>"
            else:
                dry_payload[k] = v
        print(f"[DRY RUN] {json.dumps(dry_payload, indent=2)}", file=sys.stderr)
        print("DRY_RUN_OK")
        return

    endpoint = f"{base_url}/videos/generations"
    submit_and_poll(base_url, api_key, endpoint, payload, args.output, mode, args.json)


def cmd_edit(args):
    """Handle edit mode: edit existing video by prompt."""
    base_url, api_key = get_env()

    if not args.video:
        print("ERROR: --video is required for edit mode.", file=sys.stderr)
        sys.exit(1)
    if not args.prompt:
        print("ERROR: --prompt is required for edit mode.", file=sys.stderr)
        sys.exit(1)

    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "video": {"url": encode_video(args.video)},
    }

    print(f"Mode: edit | Video: {args.video}", file=sys.stderr)

    if args.dry_run:
        dry = {k: ("<base64 video>" if k == "video" else v) for k, v in payload.items()}
        print(f"[DRY RUN] {json.dumps(dry, indent=2)}", file=sys.stderr)
        print("DRY_RUN_OK")
        return

    endpoint = f"{base_url}/videos/edits"
    submit_and_poll(base_url, api_key, endpoint, payload, args.output, "edit", args.json)


def cmd_extend(args):
    """Handle extend mode: extend existing video."""
    base_url, api_key = get_env()

    if not args.video:
        print("ERROR: --video is required for extend mode.", file=sys.stderr)
        sys.exit(1)
    if not args.prompt:
        print("ERROR: --prompt is required for extend mode.", file=sys.stderr)
        sys.exit(1)

    ext_duration = min(args.duration, 10)  # Extension max 10s
    if args.duration > 10:
        print(f"WARNING: Extension max 10s. Clamped from {args.duration}s.", file=sys.stderr)

    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "video": {"url": encode_video(args.video)},
        "duration": ext_duration,
    }

    print(f"Mode: extend | Video: {args.video} | Extension: {ext_duration}s", file=sys.stderr)

    if args.dry_run:
        dry = {k: ("<base64 video>" if k == "video" else v) for k, v in payload.items()}
        print(f"[DRY RUN] {json.dumps(dry, indent=2)}", file=sys.stderr)
        print("DRY_RUN_OK")
        return

    endpoint = f"{base_url}/videos/extensions"
    submit_and_poll(base_url, api_key, endpoint, payload, args.output, "extend", args.json)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Video generation/editing/extension via xAI grok-imagine-video",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--mode", default="generate", choices=["generate", "edit", "extend"],
                        help="Operation mode (default: generate)")
    parser.add_argument("--prompt", help="Prompt (English). Required for text-to-video, edit, extend. Optional for image-to-video.")
    parser.add_argument("--duration", type=int, default=5, metavar="1-15",
                        help="Duration in seconds. Generate: 1-15 (default 5). Extend: 1-10 (default 5).")
    parser.add_argument("--aspect-ratio", default="16:9",
                        choices=["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"],
                        help="Aspect ratio (default: 16:9). Only for generate mode.")
    parser.add_argument("--resolution", default="720p", choices=["480p", "720p", "1080p"],
                        help="Resolution (default: 720p). Only for generate mode.")
    parser.add_argument("--image", help="Source image for image-to-video")
    parser.add_argument("--refs", nargs="*", help="Reference images for reference-to-video")
    parser.add_argument("--video", help="Source video for edit/extend modes")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model (default: {DEFAULT_MODEL})")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    parser.add_argument("--dry-run", action="store_true", help="Validate params without calling API")
    parser.add_argument("--analyze", action="store_true",
                        help="Analyze image ratio vs target and recommend crop/outpaint (no generation)")
    parser.add_argument("--crop", action="store_true",
                        help="Auto center-crop image to target aspect ratio before generating")
    args = parser.parse_args()

    # Validate duration range
    if args.mode == "generate" and not (1 <= args.duration <= 15):
        parser.error("Duration must be 1-15 for generate mode")
    if args.mode == "extend" and not (1 <= args.duration <= 10):
        parser.error("Duration must be 1-10 for extend mode")

    # Handle --analyze: ratio analysis only, no generation
    if args.analyze:
        if not args.image:
            parser.error("--analyze requires --image")
        result = analyze_ratio(args.image, args.aspect_ratio)
        print(json.dumps(result, indent=2))
        sys.exit(0)

    {"generate": cmd_generate, "edit": cmd_edit, "extend": cmd_extend}[args.mode](args)
