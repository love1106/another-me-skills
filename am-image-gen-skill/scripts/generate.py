#!/usr/bin/env python3
"""
Image generation via OpenAI-compatible API (direct call).
Bypasses ImageCreate tool to avoid platform auto-attach media bug.

Usage:
  python3 generate.py --prompt "..." --size 1024x1792 [--images img1.jpg img2.jpg] \
    [--output out.png] [--quality high|medium|low] [--background transparent|opaque|auto] \
    [--format png|jpeg|webp] [--model gpt-image-2]

Env vars (priority: IMAGE_* > OPENAI_*):
  IMAGE_API_BASE or OPENAI_BASE_URL — OpenAI-compatible base URL
  IMAGE_API_KEY  or OPENAI_API_KEY  — API key for authentication
"""

import argparse
import atexit
import base64
import json
import os
import shutil
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

DEFAULT_MODEL = "gpt-image-2"
OUTBOUND_DIR = os.environ.get("IMAGE_OUTBOUND_DIR", os.path.expanduser("~/.openclaw/workspace/outbound"))
MAX_REF_PX_SINGLE = 768   # Max px for single ref image
MAX_REF_PX_MULTI = 512    # Max px when multiple refs (keep payload small)
MAX_REF_KB = 100           # Skip resize if already under this
MAX_PAYLOAD_WARN_KB = 200  # Warn if payload exceeds this
TIMEOUT = 180              # seconds per attempt
MAX_RETRIES = 2            # retry up to 2 times on failure


def fail(msg: str):
    """Print FAILED marker to stdout and exit. Agent MUST notify user."""
    print(f"FAILED: {msg}")
    sys.stdout.flush()
    sys.exit(1)


def progress(msg: str):
    """Print PROGRESS marker to stdout. Agent SHOULD notify user."""
    print(f"PROGRESS: {msg}")
    sys.stdout.flush()


def validate_env():
    """Check required environment variables. Falls back to OPENAI_* if IMAGE_* not set."""
    base = os.environ.get("IMAGE_API_BASE") or os.environ.get("OPENAI_BASE_URL", "")
    key = os.environ.get("IMAGE_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    if not base:
        fail("ENV_MISSING - Neither IMAGE_API_BASE nor OPENAI_BASE_URL env var is set.")
    if not key:
        fail("ENV_MISSING - Neither IMAGE_API_KEY nor OPENAI_API_KEY env var is set.")
    return base, key


def validate_images(paths: list) -> list:
    """Validate image paths exist and are readable. Exit with clear error if not."""
    valid = []
    for p in paths:
        if not os.path.isfile(p):
            fail(f"IMAGE_NOT_FOUND - {p}")
        size_kb = os.path.getsize(p) / 1024
        if size_kb < 1:
            fail(f"IMAGE_EMPTY - {p} ({size_kb:.1f}KB)")
        valid.append(p)
    return valid


def resize_image(path: str, max_px: int) -> bytes:
    """Resize image to max_px on longest side. Preserves PNG format for transparency."""
    if not shutil.which("convert"):
        print("WARNING: ImageMagick 'convert' not found. Sending image as-is.", file=sys.stderr)
        with open(path, "rb") as f:
            return f.read()
    ext = Path(path).suffix.lower()
    is_png = ext == ".png"
    out_ext = "png" if is_png else "jpg"
    tmp = f"/tmp/_img_resize_{os.getpid()}.{out_ext}"
    _temp_files.append(tmp)
    cmd = ["convert", path, "-resize", f"{max_px}x{max_px}>"]
    if not is_png:
        cmd += ["-quality", "75"]
    cmd.append(tmp)
    subprocess.run(cmd, check=True, capture_output=True)
    with open(tmp, "rb") as f:
        return f.read()


def encode_image(path: str, max_px: int) -> str:
    """Encode image as base64 data URI, resizing if >MAX_REF_KB."""
    size_kb = os.path.getsize(path) / 1024
    if size_kb > MAX_REF_KB:
        img_bytes = resize_image(path, max_px)
        print(f"  Resized {Path(path).name}: {size_kb:.0f}KB → {len(img_bytes)//1024}KB ({max_px}px)", file=sys.stderr)
    else:
        with open(path, "rb") as f:
            img_bytes = f.read()
    b64 = base64.b64encode(img_bytes).decode()
    ext = Path(path).suffix.lower().lstrip(".")
    mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
    return f"data:{mime};base64,{b64}"


def make_output_path(output: str, fmt: str) -> str:
    """Generate output path with timestamp if default."""
    if output:
        return output
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    ext = fmt if fmt else "png"
    return os.path.join(OUTBOUND_DIR, f"gen-{ts}.{ext}")


def generate(prompt: str, size: str, images: list = None, quality: str = "high",
             background: str = None, output: str = None, fmt: str = None, model: str = None,
             count: int = 1, dry_run: bool = False):
    base_url, api_key = validate_env()
    model_name = model or DEFAULT_MODEL

    # Validate and encode images
    if images:
        images = validate_images(images)
        max_px = MAX_REF_PX_SINGLE if len(images) == 1 else MAX_REF_PX_MULTI
        endpoint = f"{base_url}/images/edits"
        payload = {
            "model": model_name,
            "prompt": prompt,
            "images": [{"image_url": encode_image(img, max_px)} for img in images],
            "size": size,
            "quality": quality,
        }
    else:
        endpoint = f"{base_url}/images/generations"
        payload = {
            "model": model_name,
            "prompt": prompt,
            "size": size,
            "quality": quality,
        }

    if count > 1:
        payload["n"] = count
    if background:
        payload["background"] = background
    if fmt:
        payload["output_format"] = fmt

    data = json.dumps(payload).encode()
    payload_kb = len(data) // 1024

    if dry_run:
        dry_payload = {k: ("<base64 images>" if k == "images" else v) for k, v in payload.items()}
        print(f"[DRY RUN] {endpoint}", file=sys.stderr)
        print(f"[DRY RUN] {json.dumps(dry_payload, indent=2)}", file=sys.stderr)
        print("DRY_RUN_OK")
        return

    if payload_kb > MAX_PAYLOAD_WARN_KB:
        print(f"  ⚠️ Payload large ({payload_kb}KB) — may timeout with multiple images", file=sys.stderr)

    # Retry loop
    result = None
    elapsed = 0
    for attempt in range(1, MAX_RETRIES + 2):
        req = urllib.request.Request(
            endpoint,
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        print(f"[Attempt {attempt}] {endpoint} | payload {payload_kb}KB | timeout {TIMEOUT}s", file=sys.stderr)
        t0 = time.time()

        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                result = json.loads(resp.read())
            elapsed = time.time() - t0
            print(f"  Response in {elapsed:.1f}s", file=sys.stderr)
            break
        except urllib.error.HTTPError as e:
            elapsed = time.time() - t0
            error_body = e.read().decode()[:300] if e.fp else ""
            print(f"  HTTP {e.code} after {elapsed:.1f}s: {error_body}", file=sys.stderr)
            if e.code == 429:
                wait = 30  # Rate limit — longer backoff
                progress(f"Rate limited (429). Waiting {wait}s... (attempt {attempt}/{MAX_RETRIES+1})")
                time.sleep(wait)
            elif attempt <= MAX_RETRIES:
                wait = 5 * attempt
                progress(f"Attempt {attempt} failed (HTTP {e.code}). Retrying in {wait}s... (attempt {attempt+1}/{MAX_RETRIES+1})")
                time.sleep(wait)
            else:
                fail(f"All {MAX_RETRIES + 1} attempts failed. Last error: HTTP {e.code} {error_body[:200]}")
        except Exception as e:
            elapsed = time.time() - t0
            print(f"  FAILED after {elapsed:.1f}s: {e}", file=sys.stderr)
            if attempt <= MAX_RETRIES:
                wait = 5 * attempt
                progress(f"Attempt {attempt} failed ({e}). Retrying in {wait}s... (attempt {attempt+1}/{MAX_RETRIES+1})")
                time.sleep(wait)
            else:
                fail(f"All {MAX_RETRIES + 1} attempts failed. Last error: {e}")

    if not result or "data" not in result or not result["data"]:
        error_msg = json.dumps(result)[:500] if result else "No response"
        if "content_policy" in error_msg.lower() or "safety" in error_msg.lower():
            fail(f"CONTENT_POLICY - Prompt bị chặn bởi bộ lọc an toàn. Cần sửa prompt.")
        else:
            fail(f"API_ERROR - {error_msg}")

    # Save output(s)
    output_paths = []
    for idx, img_data in enumerate(result["data"]):
        if count > 1 and not output:
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            ext = fmt if fmt else "png"
            out_path = os.path.join(OUTBOUND_DIR, f"gen-{ts}-{idx+1}.{ext}")
        else:
            out_path = make_output_path(output, fmt or "png")
        os.makedirs(os.path.dirname(out_path), exist_ok=True)

        if "b64_json" in img_data:
            with open(out_path, "wb") as f:
                f.write(base64.b64decode(img_data["b64_json"]))
            size_mb = os.path.getsize(out_path) / (1024 * 1024)
            print(out_path)
            print(f"  {size_mb:.1f}MB | {elapsed:.1f}s | {quality}", file=sys.stderr)
        elif "url" in img_data:
            urllib.request.urlretrieve(img_data["url"], out_path)
            size_mb = os.path.getsize(out_path) / (1024 * 1024)
            print(out_path)
            print(f"  {size_mb:.1f}MB | from URL", file=sys.stderr)
        else:
            fail(f"UNEXPECTED_RESPONSE - keys: {list(img_data.keys())}")
        output_paths.append(out_path)

    if count > 1:
        print(f"  Generated {len(output_paths)} images total", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate image via OpenAI-compatible API")
    parser.add_argument("--prompt", required=True, help="Image prompt (English)")
    parser.add_argument("--size", default="1024x1024", help="1024x1024 | 1024x1792 | 1792x1024")
    parser.add_argument("--images", nargs="*", help="Reference image file paths")
    parser.add_argument("--output", help="Output path (default: outbound/gen-TIMESTAMP.ext)")
    parser.add_argument("--quality", default="high", choices=["low", "medium", "high"])
    parser.add_argument("--background", choices=["transparent", "opaque", "auto"])
    parser.add_argument("--format", choices=["png", "jpeg", "webp"], help="Output format")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model (default: {DEFAULT_MODEL})")
    parser.add_argument("--count", type=int, default=1, choices=[1, 2, 3, 4], help="Number of images (1-4)")
    parser.add_argument("--dry-run", action="store_true", help="Validate params without calling API")
    args = parser.parse_args()

    generate(
        prompt=args.prompt,
        size=args.size,
        images=args.images,
        quality=args.quality,
        background=args.background,
        output=args.output,
        fmt=args.format,
        model=args.model,
        count=args.count,
        dry_run=args.dry_run,
    )
