#!/usr/bin/env python3
"""
Fetch YouTube video transcript (subtitles) without Whisper.
Uses youtube-transcript-api — free, no API key needed.

Usage:
  python3 youtube-transcript.py --url "https://youtube.com/watch?v=xxx"
  python3 youtube-transcript.py --url "https://youtu.be/xxx" --lang vi
  python3 youtube-transcript.py --url "https://youtube.com/watch?v=xxx" --output /tmp/transcript.txt
  python3 youtube-transcript.py --url "https://youtube.com/watch?v=xxx" --json

Output: Plain text transcript (or JSON with timestamps)
Exit 0 = success, 1 = error (no subtitles, invalid URL, etc.)

Prerequisites: pip install youtube-transcript-api
"""

import argparse
import json
import re
import sys


def extract_video_id(url: str) -> str | None:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$',  # bare video ID
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def fetch_transcript(video_id: str, lang: str | None = None) -> dict:
    """Fetch transcript, trying requested language first, then fallback."""
    from youtube_transcript_api import YouTubeTranscriptApi

    ytt_api = YouTubeTranscriptApi()

    # List available transcripts
    transcript_list = ytt_api.list(video_id)

    # Build available languages info
    available = []
    for t in transcript_list:
        available.append({
            "language": t.language,
            "language_code": t.language_code,
            "is_generated": t.is_generated,
        })

    # Try to fetch in preferred order
    lang_prefs = []
    if lang:
        lang_prefs.append(lang)
    # Common fallbacks
    lang_prefs.extend(["vi", "en", "en-US", "en-GB"])
    # Remove duplicates while preserving order
    seen = set()
    lang_prefs = [x for x in lang_prefs if not (x in seen or seen.add(x))]

    transcript = None
    used_lang = None

    for try_lang in lang_prefs:
        try:
            transcript = ytt_api.fetch(video_id, languages=[try_lang])
            used_lang = try_lang
            break
        except Exception:
            continue

    # If no preferred language worked, try any available
    if transcript is None:
        try:
            transcript = ytt_api.fetch(video_id)
            used_lang = "auto"
        except Exception:
            pass

    if transcript is None:
        return {
            "ok": False,
            "error": "No subtitles available for this video",
            "video_id": video_id,
            "available_languages": available,
        }

    # Build result
    snippets = []
    full_text_parts = []
    total_duration = 0

    for snippet in transcript.snippets:
        snippets.append({
            "text": snippet.text,
            "start": snippet.start,
            "duration": snippet.duration,
        })
        full_text_parts.append(snippet.text)
        total_duration = max(total_duration, snippet.start + snippet.duration)

    full_text = " ".join(full_text_parts)
    # Clean up common artifacts
    full_text = re.sub(r'\[.*?\]', '', full_text)  # Remove [Music], [Applause], etc.
    full_text = re.sub(r'\s+', ' ', full_text).strip()

    return {
        "ok": True,
        "video_id": video_id,
        "language": used_lang,
        "duration_seconds": round(total_duration),
        "duration_human": f"{int(total_duration // 60)}m{int(total_duration % 60)}s",
        "segment_count": len(snippets),
        "text": full_text,
        "word_count": len(full_text.split()),
        "segments": snippets,
        "available_languages": available,
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch YouTube transcript")
    parser.add_argument("--url", required=True, help="YouTube video URL or video ID")
    parser.add_argument("--lang", default=None, help="Preferred language code (e.g. vi, en)")
    parser.add_argument("--output", "-o", default=None, help="Output file path")
    parser.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON (with timestamps)")
    args = parser.parse_args()

    video_id = extract_video_id(args.url)
    if not video_id:
        print(json.dumps({"ok": False, "error": f"Invalid YouTube URL: {args.url}"}))
        sys.exit(1)

    try:
        result = fetch_transcript(video_id, args.lang)
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e), "video_id": video_id}))
        sys.exit(1)

    if not result["ok"]:
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)

    # Output
    if args.as_json:
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = result["text"]

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        # Print metadata to stdout
        print(json.dumps({
            "ok": True,
            "saved_to": args.output,
            "video_id": video_id,
            "language": result["language"],
            "duration": result["duration_human"],
            "word_count": result["word_count"],
        }, ensure_ascii=False))
    else:
        print(output)


if __name__ == "__main__":
    main()
