#!/usr/bin/env python3
"""
Video generation, editing, and extension via xAI grok-imagine-video.

Modes:
  generate  — text-to-video, image-to-video, reference-to-video (default)
  edit      — edit existing video by prompt
  extend    — extend existing video with new footage

Usage:
  python3 generate.py --prompt "A cat on a beach" --duration 5
  python3 generate.py --image photo.jpg
  python3 generate.py --prompt "Person from <IMAGE_1> wears <IMAGE_2>" --refs person.jpg shirt.jpg
  python3 generate.py --mode edit --video input.mp4 --prompt "Add sunglasses"
  python3 generate.py --mode extend --video input.mp4 --prompt "Camera zooms out" --duration 6

Env vars (priority: VIDEO_* > OPENAI_*):
  VIDEO_API_BASE or OPENAI_BASE_URL — Proxy base URL
  VIDEO_API_KEY  or OPENAI_API_KEY  — API key for authentication
  VIDEO_OUTBOUND_DIR — Output directory (optional)
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
POLL_INTERVAL = 5
POLL_TIMEOUT = 600
MAX_IMG_PX = 1280
MAX_IMG_QUALITY = 85

RATIO_MAP = {
    "1:1": 1.0, "16:9": 16/9, "9:16": 9/16,
    "4:3": 4/3, "3:4": 3/4, "3:2": 3/2, "2:3": 2/3,
}


def get_env():
    """Get and validate required environment variables. Falls back to OPENAI_* if VIDEO_* not set."""
    base = os.environ.get("VIDEO_API_BASE") or os.environ.get("OPENAI_BASE_URL", "")
    key = os.environ.get("VIDEO_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    if not base:
        print("ERROR: Neither VIDEO_API_BASE nor OPENAI_BASE_URL env var is set.", file=sys.stderr)
        sys.exit(1)
    if not key:
        print("ERROR: Neither VIDEO_API_KEY nor OPENAI_API_KEY env var is set.", file=sys.stderr)
        sys.exit(1)
    return base.rstrip("/"), key


def has_imagemagick() -> bool:
    return subprocess.run(["which", "convert"], capture_output=True).returncode == 0


def get_image_dimensions(path: str) -> tuple:
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


def process_image(path: str, target_ratio: str = None, max_px: int = MAX_IMG_PX) -> str:
    """Process image: fit to aspect ratio + cap resolution."""
    if not os.path.isfile(path):
        print(f"ERROR: Image not found: {path}", file=sys.stderr)
        sys.exit(1)

    if not has_imagemagick():
        print("WARNING: ImageMagick not found. Sending image as-is.", file=sys.stderr)
        return path

    w, h = get_image_dimensions(path)
    if w is None:
        return path

    needs_ratio_fit = False
    needs_resize = False

    if target_ratio and target_ratio in RATIO_MAP:
        target_r = RATIO_MAP[target_ratio]
        current_r = w / h
        if abs(current_r - target_r) / max(current_r, target_r) >= 0.02:
            needs_ratio_fit = True

    if max(w, h) > max_px:
        needs_resize = True

    if not needs_ratio_fit and not needs_resize:
        return path

    tmp = f"/tmp/_vid_img_processed_{os.getpid()}.jpg"
    steps = []

    try:
        cmd = ["convert", path]

        if needs_resize:
            cmd.extend(["-resize", f"{max_px}x{max_px}>"])
            steps.append(f"resize ≤{max_px}px")

        if needs_ratio_fit:
            target_r = RATIO_MAP[target_ratio]
            ew = min(w, max_px) if needs_resize and w > h else (min(h, max_px) * w // h if needs_resize else w)
            eh = min(h, max_px) if needs_resize and h >= w else (min(w, max_px) * h // w if needs_resize else h)

            if ew / eh > target_r:
                new_w = ew
                new_h = int(round(ew / target_r))
            else:
                new_h = eh
                new_w = int(round(eh * target_r))
            new_w += new_w % 2
            new_h += new_h % 2
            cmd.extend(["-gravity", "center", "-background", "black", "-extent", f"{new_w}x{new_h}"])
            steps.append(f"pad to {target_ratio}")

        cmd.extend(["-quality", str(MAX_IMG_QUALITY), tmp])
        subprocess.run(cmd, check=True, capture_output=True)

        new_size = os.path.getsize(tmp) // 1024
        print(f"  Processed {Path(path).name}: {', '.join(steps)} → {new_size}KB", file=sys.stderr)
        return tmp

    except Exception as e:
        print(f"WARNING: Image processing failed: {e}. Sending as-is.", file=sys.stderr)
        return path


def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        img_bytes = f.read()
    b64 = base64.b64encode(img_bytes).decode()
    ext = Path(path).suffix.lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
    return f"data:{mime};base64,{b64}"


def encode_video(path: str) -> str:
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
    if output:
        return output
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    tag = f"-{suffix}" if suffix else ""
    return os.path.join(OUTBOUND_DIR, f"vid-{ts}{tag}.mp4")


def api_request(url: str, api_key: str, method: str = "GET", data: dict = None) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"HTTP {e.code}: {error_body[:500]}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        raise


def download_video(url: str, output: str, timeout: int = 180):
    os.makedirs(os.path.dirname(output), exist_ok=True)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        with open(output, "wb") as f:
            f.write(resp.read())
    size_mb = os.path.getsize(output) / (1024 * 1024)
    print(f"  Downloaded: {size_mb:.1f}MB", file=sys.stderr)


def submit_and_poll(base_url: str, api_key: str, endpoint: str, payload: dict,
                    output: str, mode_label: str, json_output: bool = False) -> str:
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
        processed = process_image(args.image, target_ratio=None, max_px=MAX_IMG_PX)
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
    base_url, api_key = get_env()

    if not args.video:
        print("ERROR: --video is required for extend mode.", file=sys.stderr)
        sys.exit(1)
    if not args.prompt:
        print("ERROR: --prompt is required for extend mode.", file=sys.stderr)
        sys.exit(1)

    ext_duration = min(args.duration, 10)
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
    args = parser.parse_args()

    if args.mode == "generate" and not (1 <= args.duration <= 15):
        parser.error("Duration must be 1-15 for generate mode")
    if args.mode == "extend" and not (1 <= args.duration <= 10):
        parser.error("Duration must be 1-10 for extend mode")

    {"generate": cmd_generate, "edit": cmd_edit, "extend": cmd_extend}[args.mode](args)
