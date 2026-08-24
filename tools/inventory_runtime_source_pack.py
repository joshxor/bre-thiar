#!/usr/bin/env python3
"""Read-only inventory for authentic Bré Thiar runtime source packs.

The tool never extracts or writes source art. It reports image entry names, dimensions,
formats, SHA-256 hashes, and whether dimensions align to the established 48px source grid.
Use this before resolving any source crop in docs/RUNTIME_ATLAS_REBUILD_CONTRACT.json.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path

from PIL import Image

IMAGE_SUFFIXES = {".png", ".webp", ".jpg", ".jpeg", ".bmp", ".gif"}


@dataclass(frozen=True)
class ImageRecord:
    source: str
    entry: str
    format: str
    width: int
    height: int
    mode: str
    sha256: str
    bytes: int
    grid48_width: bool
    grid48_height: bool
    grid24_width: bool
    grid24_height: bool


def inspect_bytes(source: str, entry: str, data: bytes) -> ImageRecord | None:
    try:
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            width, height = image.size
            fmt = (image.format or "UNKNOWN").upper()
            mode = image.mode
    except Exception:
        return None
    return ImageRecord(
        source=source,
        entry=entry,
        format=fmt,
        width=width,
        height=height,
        mode=mode,
        sha256=hashlib.sha256(data).hexdigest(),
        bytes=len(data),
        grid48_width=(width % 48 == 0),
        grid48_height=(height % 48 == 0),
        grid24_width=(width % 24 == 0),
        grid24_height=(height % 24 == 0),
    )


def inspect_file(path: Path) -> list[ImageRecord]:
    record = inspect_bytes(str(path), path.name, path.read_bytes())
    return [record] if record else []


def inspect_zip(path: Path) -> list[ImageRecord]:
    records: list[ImageRecord] = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir() or Path(info.filename).suffix.lower() not in IMAGE_SUFFIXES:
                continue
            record = inspect_bytes(str(path), info.filename, archive.read(info))
            if record:
                records.append(record)
    return records


def inspect_directory(path: Path) -> list[ImageRecord]:
    records: list[ImageRecord] = []
    for candidate in sorted(p for p in path.rglob("*") if p.is_file()):
        suffix = candidate.suffix.lower()
        if suffix == ".zip":
            try:
                records.extend(inspect_zip(candidate))
            except zipfile.BadZipFile:
                print(f"WARN: invalid zip skipped: {candidate}", file=sys.stderr)
        elif suffix in IMAGE_SUFFIXES:
            records.extend(inspect_file(candidate))
    return records


def inspect_path(path: Path) -> list[ImageRecord]:
    if path.is_dir():
        return inspect_directory(path)
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".zip":
        return inspect_zip(path)
    if path.suffix.lower() in IMAGE_SUFFIXES:
        return inspect_file(path)
    return []


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory authentic source-pack imagery without extracting or modifying it.")
    parser.add_argument("paths", nargs="+", type=Path, help="Source ZIP, image, or directory to inspect")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    records: list[ImageRecord] = []
    errors: list[str] = []
    for path in args.paths:
        try:
            records.extend(inspect_path(path))
        except Exception as exc:
            errors.append(f"{path}: {exc}")

    records.sort(key=lambda item: (item.source.lower(), item.entry.lower()))

    if args.json:
        print(json.dumps({"images": [asdict(item) for item in records], "errors": errors}, indent=2))
    else:
        print("BRÉ THIAR SOURCE PACK IMAGE INVENTORY")
        print(f"- images: {len(records)}")
        print(f"- source paths: {len(args.paths)}")
        print("- repository writes: none")
        for item in records:
            grid = []
            if item.grid48_width and item.grid48_height:
                grid.append("48x48-grid")
            elif item.grid24_width and item.grid24_height:
                grid.append("24x24-grid")
            elif item.grid48_width or item.grid48_height:
                grid.append("partial-48-grid")
            marker = ", ".join(grid) if grid else "freeform"
            print(f"- {item.entry}: {item.format} {item.width}x{item.height} {item.mode} [{marker}]")
            print(f"  source={item.source}")
            print(f"  sha256={item.sha256} bytes={item.bytes}")
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)

    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
