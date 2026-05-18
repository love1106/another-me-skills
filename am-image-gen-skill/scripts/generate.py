#!/usr/bin/env python3
"""
Image generation via OpenAI-compatible API (direct call).
Bypasses ImageCreate tool to avoid platform auto-attach media bug.

Usage:
  python3 generate.py --prompt "..." --size 1024x1792 [--images img1.jpg img2.jpg] \
    [--output out.png] [--quality high|medium|low] [--background transparent|opaque|auto] \
    [--format png|jpeg|webp] [--model gpt-image-2]

Required env vars:
  IMAGE_API_BASE — OpenAI-compatible base URL (e.g. https://api.openai.com/v1)
  IMAGE_API_KEY  — API key for authentication
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

DEFAULT_MODEL = "gpt-image-2"
OUTBOUND_DIR = os.environ.get("IMAGE_OUTBOUND_DIR", os.path.expanduser("~/.openclaw/workspace/outbound"))
MAX_REF_PX_SINGLE = 768   # Max px for single ref image
MAX_REF_PX_MULTI = 512    # Max px when multiple refs (keep payload small)
MAX_REF_KB = 100           # Skip resize if already under this
MAX_PAYLOAD_WARN_KB = 200  # Warn if payload exceeds this
TIMEOUT = 180              # seconds per attempt
MAX_RETRIES = 2            # retry up to 2 times on failure


def validate_env():
    """Check required environment variables."""
    base = os.environ.get("IMAGE_API_BASE")
    key = os.environ.get("IMAGE_API_KEY")
    if not base:
        print("ERROR: IMAGE_API_BASE env var not set.", file=sys.stderr)
        print("  Set it to your OpenAI-compatible API base URL.", file=sys.stderr)
        sys.exit(1)
    if not key:
        print("ERROR: IMAGE_API_KEY env var not set.", file=sys.stderr)
        sys.exit(1)
    return base, key


def validate_images(paths: list) -> list:
    """Validate image paths exist and are readable."""
    valid = []
    for p in paths:
        if not os.path.isfile(p):
            print(f"ERROR: Image not found: {p}", file=sys.stderr)
            print(f"  Hint: check your media inbound directory for recent uploads", file=sys.stderr)
            sys.exit(1)
        size_kb = os.path.getsize(p) / 1024
        if size_kb < 1:
            print(f"ERROR: Image too small (possibly empty): {p} ({size_kb:.1f}KB)", file=sys.stderr)
            sys.exit(1)
        valid.append(p)
    return valid


def resize_image(path: str, max_px: int) -> bytes:
    """Resize image to max_px on longest side, return JPEG bytes."""
    if not subprocess.run(["which", "convert"], capture_output=True).returncode == 0:
        print("WARNING: ImageMagick 'convert' not found. Sending image as-is.", file=sys.stderr)
        with open(path, "rb") as f:
            return f.read()
    tmp = "/tmp/_img_resize.jpg"
    subprocess.run(
        ["convert", path, "-resize", f"{max_px}x{max_px}>", "-quality", "75", tmp],
        check=True, capture_output=True
    )
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
             background: str = None, output: str = None, fmt: str = None, model: str = None):
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

    if background:
        payload["background"] = background
    if fmt:
        payload["output_format"] = fmt

    data = json.dumps(payload).encode()
    payload_kb = len(data) // 1024

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
        except Exception as e:
            elapsed = time.time() - t0
            print(f"  FAILED after {elapsed:.1f}s: {e}", file=sys.stderr)
            if attempt <= MAX_RETRIES:
                wait = 5 * attempt
                print(f"  Retrying in {wait}s...", file=sys.stderr)
                time.sleep(wait)
            else:
                print(f"ERROR: All {MAX_RETRIES + 1} attempts failed.", file=sys.stderr)
                sys.exit(1)

    if not result or "data" not in result or not result["data"]:
        error_msg = json.dumps(result)[:500] if result else "No response"
        if "content_policy" in error_msg.lower() or "safety" in error_msg.lower():
            print(f"CONTENT_POLICY: Prompt rejected by safety filter.", file=sys.stderr)
            print(f"  Fix: Remove brand names, reduce skin exposure, make descriptions generic.", file=sys.stderr)
        else:
            print(f"API ERROR: {error_msg}", file=sys.stderr)
        sys.exit(1)

    # Save output
    img_data = result["data"][0]
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
        print(f"UNEXPECTED RESPONSE: {list(img_data.keys())}", file=sys.stderr)
        sys.exit(1)


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
    )
