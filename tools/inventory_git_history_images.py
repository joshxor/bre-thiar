#!/usr/bin/env python3
"""Inventory decodable image blobs across every reachable Git ref.

Read-only recovery aid. Unlike the strict recovery-candidate scanner, this tool
reports *all* direct PNG/WebP images and standalone base64/text blobs that decode
as images. This can reveal component strips (for example 128x640 character
strips) even when no final composite atlas survived.
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

DIRECT_SUFFIXES = {".png", ".webp"}
TEXT_SUFFIXES = {".b64", ".txt", ".base64"}
BASE64_RE = re.compile(rb"^[A-Za-z0-9+/=\r\n\t ]+$")
MAX_TEXT_BLOB = 5 * 1024 * 1024


def git(*args: str) -> bytes:
    proc = subprocess.run(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace").strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def decode_text(data: bytes) -> bytes | None:
    if not data or len(data) > MAX_TEXT_BLOB or not BASE64_RE.match(data):
        return None
    compact = b"".join(data.split())
    if not compact or len(compact) % 4:
        return None
    try:
        return b64decode(compact, validate=True)
    except Exception:
        return None


def inspect(data: bytes):
    try:
        with Image.open(BytesIO(data)) as image:
            image.load()
            return str(image.format or "").upper(), image.size, image.mode
    except Exception:
        return None


def main() -> int:
    try:
        objects = git("rev-list", "--objects", "--all").decode("utf-8", "replace").splitlines()
    except Exception as exc:
        print(f"inventory setup failed: {exc}", file=sys.stderr)
        return 2

    by_sha: dict[str, str] = {}
    for line in objects:
        if not line:
            continue
        oid, *rest = line.split(" ", 1)
        path = rest[0] if rest else ""
        if Path(path).suffix.lower() in DIRECT_SUFFIXES | TEXT_SUFFIXES:
            by_sha.setdefault(oid, path)

    found = []
    for oid, path in by_sha.items():
        suffix = Path(path).suffix.lower()
        try:
            raw = git("cat-file", "-p", oid)
        except Exception:
            continue
        data = raw
        encoding = "binary"
        if suffix in TEXT_SUFFIXES:
            data = decode_text(raw)
            encoding = "base64-text"
            if data is None:
                continue
        info = inspect(data)
        if not info:
            continue
        fmt, (width, height), mode = info
        found.append({
            "path": path,
            "blob": oid,
            "encoding": encoding,
            "format": fmt,
            "width": width,
            "height": height,
            "mode": mode,
            "bytes": len(data),
            "sha256": sha256(data).hexdigest(),
        })

    found.sort(key=lambda item: (item["width"] * item["height"], item["width"], item["height"], item["path"]))
    print("BRÉ THIAR HISTORICAL IMAGE INVENTORY")
    print(f"- decodable unique image blobs: {len(found)}")
    for item in found:
        flags = []
        if (item["width"], item["height"]) == (128, 640):
            flags.append("POTENTIAL_CHARACTER_STRIP")
        if (item["width"], item["height"]) == (128, 160):
            flags.append("POTENTIAL_CHARACTER_DIRECTION_FRAME")
        if (item["width"], item["height"]) == (256, 1280):
            flags.append("FULL_CHARACTER_ATLAS_GEOMETRY")
        flag_text = f" flags={','.join(flags)}" if flags else ""
        print(
            f"- {item['format']} {item['width']}x{item['height']} {item['mode']} "
            f"bytes={item['bytes']} encoding={item['encoding']}{flag_text}\n"
            f"  path={item['path']} blob={item['blob']}\n"
            f"  sha256={item['sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
