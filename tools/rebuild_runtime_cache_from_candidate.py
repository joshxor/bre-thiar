#!/usr/bin/env python3
"""Validate an approved atlas candidate and optionally rebuild its text cache.

The default mode is dry-run. A write requires BOTH --write and an explicit
--expected-sha256 value matching the candidate bytes. This prevents a geometry-
only scanner hit from silently replacing production art.
"""
from __future__ import annotations

from argparse import ArgumentParser
from base64 import b64encode
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from textwrap import wrap
from zipfile import ZipFile, is_zipfile
import sys

from PIL import Image


TARGETS = {
    "world_houses_atlas": {
        "format": "PNG",
        "size": (578, 336),
        "destination": "assets/runtime-v2/world_houses_atlas.b64",
    },
    "world_props_atlas": {
        "format": "PNG",
        "size": (500, 294),
        "destination": "assets/runtime-v2/world_props_atlas.b64",
    },
    "wayfarer_iron_warden": {
        "format": "WEBP",
        "size": (256, 1280),
        "destination": "assets/runtime-v2/characters/wayfarer_iron_warden_q88.b64",
    },
}

ROOT = Path(__file__).resolve().parents[1]


def load_candidate(source: Path, entry: str | None) -> tuple[bytes, str]:
    source = source.expanduser().resolve()
    if not source.exists():
        raise ValueError(f"source does not exist: {source}")
    if entry:
        if not source.is_file() or not is_zipfile(source):
            raise ValueError("--entry requires a ZIP source")
        with ZipFile(source) as archive:
            try:
                return archive.read(entry), f"{source}!{entry}"
            except KeyError as exc:
                raise ValueError(f"ZIP entry not found: {entry}") from exc
    if source.is_dir():
        raise ValueError("source must be an image file, or use a ZIP with --entry")
    return source.read_bytes(), str(source)


def inspect(data: bytes) -> tuple[str, tuple[int, int], str]:
    with Image.open(BytesIO(data)) as image:
        image.load()
        return str(image.format or "").upper(), image.size, image.mode


def main() -> int:
    parser = ArgumentParser(description="Validate and optionally rebuild one corrupted runtime image cache")
    parser.add_argument("target", choices=sorted(TARGETS))
    parser.add_argument("source", type=Path, help="Candidate image or ZIP archive")
    parser.add_argument("--entry", help="Image path inside ZIP archive")
    parser.add_argument(
        "--expected-sha256",
        help="Required with --write; must exactly match candidate image bytes",
    )
    parser.add_argument("--write", action="store_true", help="Write the derived base64 cache after all checks pass")
    args = parser.parse_args()

    try:
        data, label = load_candidate(args.source, args.entry)
        image_format, image_size, mode = inspect(data)
    except Exception as exc:
        print(f"candidate load failed: {exc}", file=sys.stderr)
        return 2

    spec = TARGETS[args.target]
    actual_hash = sha256(data).hexdigest()
    destination = ROOT / spec["destination"]

    print("BRÉ THIAR RUNTIME CACHE REBUILD CHECK")
    print(f"- target: {args.target}")
    print(f"- source: {label}")
    print(f"- image: {image_format} {image_size[0]}x{image_size[1]} {mode}")
    print(f"- bytes: {len(data)}")
    print(f"- sha256: {actual_hash}")
    print(f"- destination: {destination.relative_to(ROOT)}")

    if image_format != spec["format"]:
        print(f"REFUSED: expected image format {spec['format']}", file=sys.stderr)
        return 3
    if image_size != spec["size"]:
        print(f"REFUSED: expected image size {spec['size'][0]}x{spec['size'][1]}", file=sys.stderr)
        return 3

    if not args.write:
        print("- result: VALID GEOMETRY CANDIDATE; dry-run only, no repository file written")
        print("- next: manually verify the artwork, then rerun with --write --expected-sha256 <hash>")
        return 0

    expected = (args.expected_sha256 or "").strip().lower()
    if not expected:
        print("REFUSED: --write requires --expected-sha256", file=sys.stderr)
        return 4
    if expected != actual_hash:
        print("REFUSED: --expected-sha256 does not match candidate bytes", file=sys.stderr)
        return 4

    encoded = b64encode(data).decode("ascii")
    destination.write_text("\n".join(wrap(encoded, 120)) + "\n")
    print("- result: cache rebuilt from explicitly hash-approved candidate")
    print("- required next step: run the strict production validators before committing")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
