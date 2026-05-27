#!/usr/bin/env python3
"""
Video generation via BytePlus ARK Seedance 2.0.

Async task pattern: create task → poll → download.

Usage:
  # Text-to-video
  python3 seedance.py --prompt "A cat on a beach" --duration 5

  # Fast model
  python3 seedance.py --prompt "A cat on a beach" --fast

  # Image-to-video
  python3 seedance.py --prompt "Flower blooms" --image photo.jpg

Required env vars:
  ARK_API_KEY          — BytePlus ARK API key
  BYTEPLUS_ARK_BASE_URL — Base URL (e.g. https://ark.ap-southeast.bytepluses.com/api/v3)
  SEEDANCE_MODEL       — Model ID for standard (e.g. dreamina-seedance-2-0-260128)
  SEEDANCE_FAST_MODEL  — Model ID for fast variant
"""

import argparse
import atexit
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

OUTBOUND_DIR = os.path.expanduser("~/.openclaw/workspace/outbound")
POLL_INTERVAL_INITIAL = 10
POLL_INTERVAL_MAX = 30
POLL_TIMEOUT = 600
MAX_IMG_PX = 1280
MAX_IMG_QUALITY = 85

RATIO_MAP = {
    "1:1": "1:1", "16:9": "16:9", "9:16": "9:16",
    "4:3": "4:3", "3:4": "3:4", "3:2": "3:2", "2:3": "2:3",
}

_temp_files = []

def _cleanup():
    for f in _temp_files:
        try:
            if os.path.exists(f):
                os.unlink(f)
        except OSError:
            pass

atexit.register(_cleanup)


def fail(msg: str):
    """Print FAILED marker to stdout and exit. Agent MUST notify user."""
    print(f"FAILED: {msg}")
    sys.stdout.flush()
    sys.exit(1)


def progress(msg: str):
    """Print PROGRESS marker to stdout. Agent SHOULD notify user."""
    print(f"PROGRESS: {msg}")
    sys.stdout.flush()


def get_env():
    """Get required env vars."""
    api_key = os.environ.get("ARK_API_KEY", "")
    base_url = os.environ.get("BYTEPLUS_ARK_BASE_URL", "")
    model = os.environ.get("SEEDANCE_MODEL", "")
    fast_model = os.environ.get("SEEDANCE_FAST_MODEL", "")

    if not api_key:
        fail("ENV_MISSING - ARK_API_KEY env var not set.")
    if not base_url:
        fail("ENV_MISSING - BYTEPLUS_ARK_BASE_URL env var not set.")
    if not model:
        fail("ENV_MISSING - SEEDANCE_MODEL env var not set.")

    base_url = base_url.rstrip("/")
    return api_key, base_url, model, fast_model


def api_request(url, api_key, method="GET", data=None, timeout=120):
    """Make API request, return parsed JSON."""
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


def get_image_dimensions(path):
    """Get w, h via ImageMagick identify."""
    try:
        r = subprocess.run(["identify", "-format", "%w %h", path],
                           capture_output=True, text=True, check=True)
        w, h = r.stdout.strip().split()
        return int(w), int(h)
    except Exception:
        return None, None


def process_image(path, max_px=MAX_IMG_PX):
    """Resize if too large. Returns processed path."""
    if not os.path.isfile(path):
        fail(f"IMAGE_NOT_FOUND - {path}")

    w, h = get_image_dimensions(path)
    if w is None:
        return path

    print(f"  Image: {w}x{h}", file=sys.stderr)

    if max(w, h) <= max_px:
        return path

    tmp = f"/tmp/_sd_img_{os.getpid()}.jpg"
    _temp_files.append(tmp)
    try:
        subprocess.run(
            ["convert", path, "-resize", f"{max_px}x{max_px}>",
             "-quality", str(MAX_IMG_QUALITY), tmp],
            check=True, capture_output=True
        )
        nw, nh = get_image_dimensions(tmp)
        print(f"  Resized: {w}x{h} → {nw}x{nh}", file=sys.stderr)
        return tmp
    except Exception as e:
        print(f"WARNING: Resize failed: {e}", file=sys.stderr)
        return path


def encode_image_b64(path):
    """Encode image as base64 string (no data URI prefix)."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def encode_image_data_uri(path):
    """Encode image as data URI."""
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = Path(path).suffix.lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
            "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
    return f"data:{mime};base64,{b64}"


def download_video(url, output, timeout=180, retries=3):
    """Download video with retry."""
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                with open(output, "wb") as f:
                    f.write(resp.read())
            size_mb = os.path.getsize(output) / (1024 * 1024)
            print(f"  Downloaded: {size_mb:.1f}MB → {output}", file=sys.stderr)
            return
        except Exception as e:
            if attempt < retries:
                wait = 5 * attempt
                print(f"  Download retry {attempt}: {e}. Wait {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"ERROR: Download failed after {retries} attempts: {e}", file=sys.stderr)
                raise


def make_output_path(output, suffix=""):
    if output:
        return output
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    tag = f"-{suffix}" if suffix else ""
    return os.path.join(OUTBOUND_DIR, f"vid-{ts}{tag}.mp4")


def sessions_spawn(api_key, base_url, model, content, ratio="16:9",
                duration=5, resolution="720p", watermark=False):
    """Create a Seedance video generation task.

    Returns task_id string.
    """
    url = f"{base_url}/contents/generations/tasks"

    payload = {
        "model": model,
        "content": content,
        "duration": duration,
        "watermark": watermark,
    }

    # ratio and resolution for text-to-video
    if ratio:
        payload["ratio"] = ratio
    if resolution:
        payload["resolution"] = resolution

    print(f"  POST {url}", file=sys.stderr)
    print(f"  Model: {model} | Duration: {duration}s | Ratio: {ratio} | Res: {resolution}", file=sys.stderr)

    for attempt in range(1, 4):
        try:
            result = api_request(url, api_key, method="POST", data=payload, timeout=120)
            break
        except Exception as e:
            if attempt < 3:
                wait = 10 * attempt
                progress(f"Submit attempt {attempt} failed ({e}). Retrying in {wait}s... (attempt {attempt+1}/3)")
                time.sleep(wait)
            else:
                fail(f"SUBMIT_FAILED - After 3 attempts: {e}")

    # Response should have { "id": "cgt-..." }
    task_id = result.get("id")
    if not task_id:
        fail(f"NO_TASK_ID - Response: {json.dumps(result)[:300]}")

    print(f"  Task ID: {task_id}", file=sys.stderr)
    return task_id


def poll_task(api_key, base_url, task_id):
    """Poll task until succeeded/failed. Returns result dict."""
    url = f"{base_url}/contents/generations/tasks/{task_id}"
    t0 = time.time()
    interval = POLL_INTERVAL_INITIAL
    poll_count = 0

    while True:
        elapsed = time.time() - t0
        if elapsed > POLL_TIMEOUT:
            fail(f"TIMEOUT - {elapsed:.0f}s. Task: {task_id}")

        time.sleep(interval)
        poll_count += 1

        try:
            result = api_request(url, api_key, timeout=30)
        except Exception as e:
            print(f"  [Poll {poll_count}] Error: {e}. Retrying...", file=sys.stderr)
            interval = min(interval + 5, POLL_INTERVAL_MAX)
            continue

        status = result.get("status", "unknown")

        if status == "succeeded":
            print(f"  [Poll {poll_count}] Succeeded in {elapsed:.0f}s", file=sys.stderr)
            return result
        elif status in ("failed", "expired", "cancelled"):
            error = result.get("error", {})
            print(f"  [Poll {poll_count}] {status} after {elapsed:.0f}s: {json.dumps(error)[:300]}", file=sys.stderr)
            fail(f"GEN_{status.upper()} - {json.dumps(error)[:200]}")
        else:
            if poll_count % 3 == 0:
                print(f"  [Poll {poll_count}] {status}... ({elapsed:.0f}s)", file=sys.stderr)
            if elapsed > 60 and poll_count % 6 == 0:
                progress(f"Still generating... {elapsed:.0f}s elapsed. Seedance gen takes 1-3 min.")
            # Exponential backoff capped
            interval = min(interval * 1.5, POLL_INTERVAL_MAX)


def extract_video_url(result):
    """Extract video URL from task result."""
    # Try common response structures
    # Structure 1: result.content.video_url
    content = result.get("content", {})
    if isinstance(content, dict):
        video_url = content.get("video_url")
        if video_url:
            return video_url

    # Structure 2: result.output.video_url or result.output.video.url
    output = result.get("output", {})
    if isinstance(output, dict):
        video_url = output.get("video_url")
        if video_url:
            return video_url
        video = output.get("video", {})
        if isinstance(video, dict):
            video_url = video.get("url")
            if video_url:
                return video_url

    # Structure 3: result.video_url
    video_url = result.get("video_url")
    if video_url:
        return video_url

    # Structure 4: result.data[0].url (Volcengine style)
    data = result.get("data", [])
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            video_url = first.get("url") or first.get("video_url")
            if video_url:
                return video_url

    print(f"WARNING: Could not find video URL. Full response:", file=sys.stderr)
    print(json.dumps(result, indent=2)[:1000], file=sys.stderr)
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Video generation via BytePlus ARK Seedance 2.0"
    )
    parser.add_argument("--prompt", required=True, help="Text prompt (English)")
    parser.add_argument("--duration", type=int, default=5, choices=[5, 10, 15],
                        help="Duration: 5, 10, or 15 seconds (default: 5)")
    parser.add_argument("--aspect-ratio", default="16:9",
                        choices=["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"],
                        help="Aspect ratio (default: 16:9)")
    parser.add_argument("--resolution", default="720p", choices=["480p", "720p", "1080p"],
                        help="Resolution (default: 720p)")
    parser.add_argument("--image", help="Image for image-to-video")
    parser.add_argument("--fast", action="store_true", help="Use fast model variant")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    parser.add_argument("--dry-run", action="store_true", help="Validate without calling API")
    parser.add_argument("--watermark", action="store_true", help="Add watermark")
    args = parser.parse_args()

    api_key, base_url, model, fast_model = get_env()

    if args.fast:
        if not fast_model:
            fail("ENV_MISSING - SEEDANCE_FAST_MODEL env var not set.")
        model = fast_model

    # Build content array
    content = [{"type": "text", "text": args.prompt}]
    mode_label = "seedance-t2v"

    if args.image:
        mode_label = "seedance-i2v"
        processed = process_image(args.image, max_px=MAX_IMG_PX)
        img_uri = encode_image_data_uri(processed)
        content.append({
            "type": "image_url",
            "image_url": {"url": img_uri}
        })

    print(f"Mode: {mode_label} | Model: {model}", file=sys.stderr)
    print(f"Duration: {args.duration}s | Ratio: {args.aspect_ratio} | Res: {args.resolution}", file=sys.stderr)

    if args.dry_run:
        dry_content = []
        for c in content:
            if c.get("type") == "image_url":
                dry_content.append({"type": "image_url", "image_url": "<base64>"})
            else:
                dry_content.append(c)
        print(f"[DRY RUN] model={model}, content={json.dumps(dry_content)}", file=sys.stderr)
        print("DRY_RUN_OK")
        return

    # Create task
    t0 = time.time()
    task_id = sessions_spawn(
        api_key, base_url, model, content,
        ratio=args.aspect_ratio,
        duration=args.duration,
        resolution=args.resolution,
        watermark=args.watermark,
    )

    # Poll
    result = poll_task(api_key, base_url, task_id)
    elapsed = time.time() - t0

    # Extract and download
    video_url = extract_video_url(result)
    if not video_url:
        fail("NO_VIDEO_URL - in task result")

    out_path = make_output_path(args.output, mode_label)
    download_video(video_url, out_path)

    if args.json:
        print(json.dumps({
            "status": "ok",
            "mode": mode_label,
            "model": model,
            "path": out_path,
            "task_id": task_id,
            "duration": args.duration,
            "elapsed_seconds": round(elapsed),
            "size_mb": round(os.path.getsize(out_path) / (1024 * 1024), 1),
        }))
    else:
        print(out_path)

    print(f"  Total: {elapsed:.0f}s | {mode_label}", file=sys.stderr)


if __name__ == "__main__":
    main()
