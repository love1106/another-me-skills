#!/usr/bin/env python3
"""
Video generation via xAI grok-imagine-video through OpenAI-compatible proxy.
Supports: text-to-video, image-to-video, reference-to-video.

Usage:
  # Text-to-video
  python3 generate.py --prompt "A cat walking on a beach" --duration 5

  # Image-to-video (animate a still image)
  python3 generate.py --prompt "The flower blooms slowly" --image /path/to/img.jpg

  # Reference-to-video (style/subject reference)
  python3 generate.py --prompt "Model walks on runway wearing <IMAGE_1>" --refs /path/to/ref1.jpg /path/to/ref2.jpg

Required env vars:
  VIDEO_API_BASE — Proxy base URL (e.g. https://your-proxy.example.com/v1)
  VIDEO_API_KEY  — API key for authentication
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
import subprocess
from pathlib import Path
from datetime import datetime

DEFAULT_MODEL = "grok-imagine-video"
OUTBOUND_DIR = os.environ.get("VIDEO_OUTBOUND_DIR", os.path.expanduser("~/.openclaw/workspace/outbound"))
POLL_INTERVAL = 5       # seconds between polls
POLL_TIMEOUT = 600      # 10 minutes max wait
MAX_REF_PX = 768        # Max px for reference images
MAX_REF_KB = 200        # Skip resize if already under this


def get_env():
    """Get and validate required environment variables."""
    base = os.environ.get("VIDEO_API_BASE", "")
    key = os.environ.get("VIDEO_API_KEY", "")
    if not base:
        print("ERROR: VIDEO_API_BASE env var not set.", file=sys.stderr)
        sys.exit(1)
    if not key:
        print("ERROR: VIDEO_API_KEY env var not set.", file=sys.stderr)
        sys.exit(1)
    return base.rstrip("/"), key


def resize_image(path: str, max_px: int) -> bytes:
    """Resize image to max_px on longest side, return JPEG bytes."""
    if subprocess.run(["which", "convert"], capture_output=True).returncode != 0:
        print("WARNING: ImageMagick 'convert' not found. Sending image as-is.", file=sys.stderr)
        with open(path, "rb") as f:
            return f.read()
    tmp = "/tmp/_vid_img_resize.jpg"
    subprocess.run(
        ["convert", path, "-resize", f"{max_px}x{max_px}>", "-quality", "80", tmp],
        check=True, capture_output=True
    )
    with open(tmp, "rb") as f:
        return f.read()


def encode_image(path: str) -> str:
    """Encode image as base64 data URI, resizing if needed."""
    if not os.path.isfile(path):
        print(f"ERROR: Image not found: {path}", file=sys.stderr)
        sys.exit(1)
    size_kb = os.path.getsize(path) / 1024
    if size_kb > MAX_REF_KB:
        img_bytes = resize_image(path, MAX_REF_PX)
        print(f"  Resized {Path(path).name}: {size_kb:.0f}KB → {len(img_bytes)//1024}KB", file=sys.stderr)
    else:
        with open(path, "rb") as f:
            img_bytes = f.read()
    b64 = base64.b64encode(img_bytes).decode()
    ext = Path(path).suffix.lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
    return f"data:{mime};base64,{b64}"


def make_output_path(output: str) -> str:
    """Generate output path with timestamp."""
    if output:
        return output
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return os.path.join(OUTBOUND_DIR, f"vid-{ts}.mp4")


def api_request(url: str, api_key: str, method: str = "GET", data: dict = None) -> dict:
    """Make an API request, return parsed JSON."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"HTTP {e.code}: {error_body[:500]}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        raise


def download_video(url: str, output: str, timeout: int = 120):
    """Download video from URL to local file with timeout."""
    os.makedirs(os.path.dirname(output), exist_ok=True)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        with open(output, "wb") as f:
            f.write(resp.read())
    size_mb = os.path.getsize(output) / (1024 * 1024)
    print(f"  Downloaded: {size_mb:.1f}MB", file=sys.stderr)


def generate(prompt: str, duration: int = 5, aspect_ratio: str = "16:9",
             resolution: str = "720p", image: str = None, refs: list = None,
             output: str = None, model: str = None, dry_run: bool = False):
    base_url, api_key = get_env()
    model_name = model or DEFAULT_MODEL

    # Build payload
    payload = {
        "model": model_name,
        "prompt": prompt,
        "duration": duration,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
    }

    # Determine mode
    if image and refs:
        print("ERROR: Cannot use both --image and --refs. Pick one.", file=sys.stderr)
        sys.exit(1)

    mode = "text-to-video"
    if image:
        mode = "image-to-video"
        payload["image"] = {"url": encode_image(image)}
    elif refs:
        mode = "reference-to-video"
        payload["reference_images"] = [{"url": encode_image(r)} for r in refs]

    print(f"Mode: {mode} | Model: {model_name} | Duration: {duration}s | Ratio: {aspect_ratio} | Res: {resolution}", file=sys.stderr)

    if dry_run:
        print("[DRY RUN] Would submit:", file=sys.stderr)
        # Don't log full base64 images in dry run
        dry_payload = {k: ("<base64 image>" if k == "image" else
                          f"<{len(v)} ref images>" if k == "reference_images" else v)
                       for k, v in payload.items()}
        print(f"  {json.dumps(dry_payload, indent=2)}", file=sys.stderr)
        print("DRY_RUN_OK", file=sys.stdout)
        return

    # Step 1: Submit generation request (with retry)
    endpoint = f"{base_url}/videos/generations"
    t0 = time.time()
    result = None
    for attempt in range(1, 4):
        print(f"[Submit attempt {attempt}] POST {endpoint}", file=sys.stderr)
        try:
            result = api_request(endpoint, api_key, method="POST", data=payload)
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

    # Step 2: Poll for completion
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
            print(f"  [Poll {poll_count}] Failed to check status, retrying...", file=sys.stderr)
            continue

        status = status_result.get("status", "unknown")

        if status == "done":
            video_url = status_result.get("video", {}).get("url")
            video_duration = status_result.get("video", {}).get("duration", "?")
            print(f"  [Poll {poll_count}] Done in {elapsed:.0f}s | Video duration: {video_duration}s", file=sys.stderr)

            if not video_url:
                print(f"ERROR: No video URL in response: {json.dumps(status_result)[:300]}", file=sys.stderr)
                sys.exit(1)

            # Download video
            out_path = make_output_path(output)
            download_video(video_url, out_path)

            # Machine-parseable output on stdout
            print(out_path)
            print(f"  {elapsed:.0f}s total | {mode} | {resolution}", file=sys.stderr)
            return

        elif status in ("failed", "expired"):
            print(f"  [Poll {poll_count}] Status: {status} after {elapsed:.0f}s", file=sys.stderr)
            error_detail = json.dumps(status_result)[:500]
            print(f"ERROR: Video generation {status}: {error_detail}", file=sys.stderr)
            sys.exit(1)

        else:
            # Still pending — log every 15s (3 polls)
            if poll_count % 3 == 0:
                print(f"  [Poll {poll_count}] Still generating... ({elapsed:.0f}s elapsed)", file=sys.stderr)

    # Timeout
    elapsed = time.time() - t0
    print(f"ERROR: Timeout after {elapsed:.0f}s ({max_polls} polls). request_id: {request_id}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate video via xAI grok-imagine-video")
    parser.add_argument("--prompt", required=True, help="Video prompt (English)")
    parser.add_argument("--duration", type=int, default=5, choices=range(1, 16),
                        metavar="1-15", help="Video duration in seconds (default: 5)")
    parser.add_argument("--aspect-ratio", default="16:9",
                        choices=["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"],
                        help="Aspect ratio (default: 16:9)")
    parser.add_argument("--resolution", default="720p", choices=["480p", "720p"],
                        help="Resolution (default: 720p)")
    parser.add_argument("--image", help="Source image for image-to-video (animates the image)")
    parser.add_argument("--refs", nargs="*", help="Reference images for reference-to-video (style/subject guide)")
    parser.add_argument("--output", help="Output path (default: outbound/vid-TIMESTAMP.mp4)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model (default: {DEFAULT_MODEL})")
    parser.add_argument("--dry-run", action="store_true", help="Validate params and show payload without calling API")
    args = parser.parse_args()

    generate(
        prompt=args.prompt,
        duration=args.duration,
        aspect_ratio=args.aspect_ratio,
        resolution=args.resolution,
        image=args.image,
        refs=args.refs,
        output=args.output,
        model=args.model,
        dry_run=args.dry_run,
    )
