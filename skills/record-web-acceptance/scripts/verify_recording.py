"""Check a delivered browser recording against its original JSON receipt (offline)."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def seconds(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{field} must be a finite number of seconds")
    return value


def run(command):
    result = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    if result.returncode:
        raise ValueError(f"{command[0]} failed: {result.stderr.strip()[:1000]}")
    return result.stdout


def verify(movie, receipt_path):
    with receipt_path.open(encoding="utf-8") as stream:
        receipt = json.load(stream)
    if not isinstance(receipt, dict) or not isinstance(receipt.get("media"), dict):
        raise ValueError("receipt must contain a media object")
    expected = receipt["media"]
    expected_hash = expected.get("sha256")
    if not isinstance(expected_hash, str) or not re.fullmatch("[0-9a-fA-F]{64}", expected_hash):
        raise ValueError("media.sha256 must be a SHA-256 hex digest")
    if digest(movie) != expected_hash.lower():
        raise ValueError("SHA-256 differs from the receipt")

    # Only local inputs. The first display video excludes embedded cover art.
    source = str(movie.resolve())
    data = json.loads(run([
        "ffprobe", "-v", "error", "-protocol_whitelist", "file,pipe", "-select_streams", "V:0",
        "-show_entries", "stream=width,height,codec_name:format=duration", "-of", "json", source,
    ]))
    if not data.get("streams"):
        raise ValueError("no display video stream")
    video = data["streams"][0]
    duration = float(data.get("format", {}).get("duration", "nan"))
    declared = seconds(expected.get("duration_s"), "media.duration_s")
    if not math.isfinite(duration) or min(duration, declared) <= 0 or abs(duration - declared) > 0.1:
        raise ValueError(f"duration mismatch (file {duration}s, receipt {declared}s; tolerance 0.1s)")

    chapters = receipt.get("chapters", [])
    if not isinstance(chapters, list):
        raise ValueError("chapters must be an array when present")
    previous = -1
    for chapter in chapters:
        if not isinstance(chapter, dict) or not isinstance(chapter.get("title"), str) or not chapter["title"].strip():
            raise ValueError("every chapter needs a title")
        start = seconds(chapter.get("start_s"), "chapter.start_s")
        if not (0 <= start < duration and start > previous):
            raise ValueError(f"chapter outside the timeline or out of order: {chapter['title']}")
        previous = start

    progress = run([
        "ffmpeg", "-nostdin", "-v", "error", "-xerror", "-err_detect", "explode",
        "-protocol_whitelist", "file,pipe", "-i", source, "-map", "0:V:0", "-map", "0:a?",
        "-fps_mode", "passthrough", "-progress", "pipe:1", "-nostats", "-f", "null", "-",
    ])
    frames = re.findall(r"^frame=\s*(\d+)$", progress, flags=re.MULTILINE)
    if not frames or int(frames[-1]) < 1 or "progress=end" not in progress.splitlines():
        raise ValueError("decoder did not complete a video stream")
    video["nb_frames"] = int(frames[-1])
    for key in ("width", "height", "codec_name", "nb_frames"):
        if key in expected and str(expected[key]) != str(video[key]):
            raise ValueError(f"{key} mismatch (file {video[key]}, receipt {expected[key]})")
    return {"media_check": "passed", "duration_s": duration, "chapters": len(chapters), **video}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("movie", type=Path)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.movie, args.receipt), ensure_ascii=False))
    except (OSError, ValueError) as exc:
        print(f"Media check failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
