#!/usr/bin/env python3
"""Search every reachable Git blob for production atlas recovery candidates.

Run from a full-history clone (`git fetch --all --tags` first). This is read-only:
it never checks out, rewrites, or restores a blob. It inspects direct PNG/WebP
blobs plus standalone text/base64 blobs and reports exact geometry matches.
"""
from __future__ import annotations

from base64 import b64decode
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import re
import subprocess
import sys

from PIL import Image


TARGETS = {
    ("PNG", 578, 336): "world_houses_atlas",
    ("PNG", 500, 294): "world_props_atlas",
    ("WEBP", 256, 1280): "wayfarer_iron_warden",
}

DIRECT_SUFFIXES = {".png", ".webp"}
TEXT_SUFFIXES = {".b64", ".txt", ".base64"}
BASE64_RE = re.compile(rb"^[A-Za-z0-9+/=\r\n\t ]+$")
MAX_TEXT_BLOB = 5 * 1024 * 1024


def git(*args: str, input_bytes: bytes | None = None) -> bytes:
    proc = subprocess.run(
        ["git", *args],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace").strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def inspect_image(data: bytes):
    try:
        with Image.open(BytesIO(data)) as image:
            image.load()
            fmt = str(image.format or "").upper()
            width, height = image.size
            target = TARGETS.get((fmt, width, height))
            if target:
                return target, fmt, width, height, image.mode
    except Exception:
        return None
    return None


def decode_text_blob(data: bytes) -> bytes | None:
    if not data or len(data) > MAX_TEXT_BLOB or not BASE64_RE.match(data):
        return None
    compact = b"".join(data.split())
    if not compact or len(compact) % 4:
        return None
    try:
        return b64decode(compact, validate=True)
    except Exception:
        return None


def main() -> int:
    try:
        git("rev-parse", "--is-inside-work-tree")
        objects = git("rev-list", "--objects", "--all").decode("utf-8", "replace").splitlines()
    except Exception as exc:
        print(f"history scan setup failed: {exc}", file=sys.stderr)
        return 2

    # A blob can appear at multiple historical paths; inspect the bytes once but
    # retain the first useful path for review.
    by_sha: dict[str, str] = {}
    for line in objects:
        if not line:
            continue
        parts = line.split(" ", 1)
        oid = parts[0]
        path = parts[1] if len(parts) == 2 else ""
        suffix = Path(path).suffix.lower()
        if suffix in DIRECT_SUFFIXES or suffix in TEXT_SUFFIXES:
            by_sha.setdefault(oid, path)

    matches = []
    inspected_direct = 0
    inspected_text = 0
    for oid, path in by_sha.items():
        suffix = Path(path).suffix.lower()
        try:
            data = git("cat-file", "-p", oid)
        except Exception:
            continue
        decoded = data
        encoding = "binary"
        if suffix in TEXT_SUFFIXES:
            inspected_text += 1
            decoded = decode_text_blob(data)
            encoding = "base64-text"
            if decoded is None:
                continue
        else:
            inspected_direct += 1
        result = inspect_image(decoded)
        if not result:
            continue
        target, fmt, width, height, mode = result
        matches.append(
            {
                "target": target,
                "git_blob": oid,
                "historical_path": path,
                "encoding": encoding,
                "image_format": fmt,
                "width": width,
                "height": height,
                "mode": mode,
                "byte_size": len(decoded),
                "sha256": sha256(decoded).hexdigest(),
            }
        )

    # De-dupe candidate image bytes while retaining different targets distinctly.
    unique = {}
    for match in matches:
        unique.setdefault((match["target"], match["sha256"]), match)
    matches = sorted(unique.values(), key=lambda item: (item["target"], item["historical_path"]))

    print("BRÉ THIAR FULL GIT HISTORY CACHE SCAN")
    print(f"- candidate Git blobs considered: {len(by_sha)}")
    print(f"- direct image blobs inspected: {inspected_direct}")
    print(f"- standalone text/base64 blobs inspected: {inspected_text}")
    print(f"- exact geometry matches: {len(matches)}")
    print("- repository writes: none")
    for match in matches:
        print(
            f"MATCH {match['target']}: blob={match['git_blob']} path={match['historical_path']}\n"
            f"  {match['image_format']} {match['width']}x{match['height']} {match['mode']} "
            f"bytes={match['byte_size']} encoding={match['encoding']}\n"
            f"  sha256={match['sha256']}"
        )

    found = {match["target"] for match in matches}
    missing = sorted(set(TARGETS.values()) - found)
    if missing:
        print("MISSING FROM REACHABLE GIT HISTORY:")
        for target in missing:
            print(f"- {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
