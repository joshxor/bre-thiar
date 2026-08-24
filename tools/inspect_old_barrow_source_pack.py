#!/usr/bin/env python3
"""Inspect a licensed Old Barrow interior source pack without copying it into the repo."""
from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import asdict, dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile, is_zipfile
import json
import sys

from PIL import Image

SOURCE_TILE = 48


@dataclass
class Candidate:
    path: str
    width: int
    height: int
    mode: str
    grid_48: bool
    tile_columns: int | None
    tile_rows: int | None


def archive_digest(path: Path) -> str:
    h = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect_png(name: str, data: bytes) -> Candidate:
    with Image.open(BytesIO(data)) as image:
        image.load()
        width, height = image.size
        grid = width % SOURCE_TILE == 0 and height % SOURCE_TILE == 0
        return Candidate(
            path=name,
            width=width,
            height=height,
            mode=image.mode,
            grid_48=grid,
            tile_columns=width // SOURCE_TILE if grid else None,
            tile_rows=height // SOURCE_TILE if grid else None,
        )


def iter_zip_pngs(path: Path) -> Iterable[tuple[str, bytes]]:
    with ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            if name.lower().endswith(".png") and not name.endswith("/"):
                yield name, archive.read(name)


def iter_dir_pngs(path: Path) -> Iterable[tuple[str, bytes]]:
    for item in sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() == ".png"):
        yield item.relative_to(path).as_posix(), item.read_bytes()


def main() -> int:
    parser = ArgumentParser(
        description=(
            "Read-only inspection for the licensed Old Barrow interior source package. "
            "The source remains outside the repository; this tool only reports PNG geometry."
        )
    )
    parser.add_argument("source", type=Path, help="Purchased ZIP archive or extracted source directory")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    if not source.exists():
        print(f"source does not exist: {source}", file=sys.stderr)
        return 2

    source_kind: str
    digest: str | None = None
    if source.is_file() and is_zipfile(source):
        source_kind = "zip"
        digest = archive_digest(source)
        entries = iter_zip_pngs(source)
    elif source.is_dir():
        source_kind = "directory"
        entries = iter_dir_pngs(source)
    else:
        print("source must be a ZIP archive or directory", file=sys.stderr)
        return 2

    candidates: list[Candidate] = []
    failures: list[str] = []
    for name, data in entries:
        try:
            candidates.append(inspect_png(name, data))
        except Exception as exc:
            failures.append(f"{name}: {exc}")

    grid_candidates = [item for item in candidates if item.grid_48]
    report = {
        "source_kind": source_kind,
        "source_name": source.name,
        "source_sha256": digest,
        "source_tile": SOURCE_TILE,
        "png_count": len(candidates),
        "grid_48_count": len(grid_candidates),
        "decode_failures": failures,
        "candidates": [asdict(item) for item in candidates],
        "repo_write_performed": False,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("OLD BARROW SOURCE PACK INSPECTION")
        print(f"- source: {source.name} ({source_kind})")
        if digest:
            print(f"- sha256: {digest}")
        print(f"- PNG images: {len(candidates)}")
        print(f"- 48px-grid candidates: {len(grid_candidates)}")
        print("- repository writes: none")
        if grid_candidates:
            print("48px-grid PNG candidates:")
            for item in grid_candidates:
                print(
                    f"  - {item.path}: {item.width}x{item.height} "
                    f"({item.tile_columns}x{item.tile_rows} source cells)"
                )
        if failures:
            print("Decode warnings:")
            for failure in failures:
                print(f"  - {failure}")

    if not candidates:
        print("No PNG assets found in the supplied source package.", file=sys.stderr)
        return 3
    if not grid_candidates:
        print(
            "No PNG asset is aligned to the established 48px source grid; "
            "do not ingest this package without manual review.",
            file=sys.stderr,
        )
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
