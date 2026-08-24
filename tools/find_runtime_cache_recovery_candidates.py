#!/usr/bin/env python3
"""Find authentic source candidates for corrupted production runtime caches.

This tool is deliberately read-only. It scans ordinary image files and ZIP
archives supplied by the operator, matches image geometry against the known
production atlas contracts, and reports hashes/locations for manual review.
It never writes runtime caches, extracts archives, or chooses a candidate.
"""
from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Iterable
from zipfile import BadZipFile, ZipFile, is_zipfile
import json
import os
import sys

from PIL import Image


@dataclass(frozen=True)
class Target:
    key: str
    fmt: str
    width: int
    height: int
    destination: str
    note: str


TARGETS = (
    Target(
        key="world_houses_atlas",
        fmt="PNG",
        width=578,
        height=336,
        destination="assets/runtime-v2/world_houses_atlas.b64",
        note="independent Hypnobius house atlas; not a flattened village image",
    ),
    Target(
        key="world_props_atlas",
        fmt="PNG",
        width=500,
        height=294,
        destination="assets/runtime-v2/world_props_atlas.b64",
        note="independent Hypnobius props/terrain atlas; not a flattened village image",
    ),
    Target(
        key="wayfarer_iron_warden",
        fmt="WEBP",
        width=256,
        height=1280,
        destination="assets/runtime-v2/characters/wayfarer_iron_warden_q88.b64",
        note="four 128x640 class/gender direction strips; not the old 96x112 mobile player sheet",
    ),
)

IMAGE_SUFFIXES = {".png", ".webp"}
SKIP_DIR_NAMES = {
    ".git",
    ".godot",
    "node_modules",
    "__pycache__",
}
KNOWN_REJECT_BASENAMES = {
    "village.webp",
    "village_front.webp",
    "player.webp",
}


@dataclass
class Candidate:
    target: str
    source: str
    container: str
    entry: str | None
    image_format: str
    width: int
    height: int
    mode: str
    byte_size: int
    sha256: str
    destination: str
    review_note: str


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def inspect_image(data: bytes) -> tuple[str, int, int, str]:
    with Image.open(BytesIO(data)) as image:
        image.load()
        fmt = str(image.format or "").upper()
        width, height = image.size
        return fmt, width, height, image.mode


def match_target(fmt: str, width: int, height: int) -> Target | None:
    return next(
        (
            target
            for target in TARGETS
            if target.fmt == fmt and target.width == width and target.height == height
        ),
        None,
    )


def iter_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    for current, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in SKIP_DIR_NAMES]
        base = Path(current)
        for name in files:
            yield base / name


def candidate_from_bytes(
    *,
    data: bytes,
    source: str,
    container: str,
    entry: str | None,
) -> Candidate | None:
    try:
        fmt, width, height, mode = inspect_image(data)
    except Exception:
        return None
    target = match_target(fmt, width, height)
    if target is None:
        return None
    basename = Path(entry or source).name.lower()
    reject_hint = basename in KNOWN_REJECT_BASENAMES
    note = target.note
    if reject_hint:
        note += "; WARNING: basename matches a known legacy/mobile derivative and must be rejected unless manually proven otherwise"
    return Candidate(
        target=target.key,
        source=source,
        container=container,
        entry=entry,
        image_format=fmt,
        width=width,
        height=height,
        mode=mode,
        byte_size=len(data),
        sha256=digest(data),
        destination=target.destination,
        review_note=note,
    )


def scan_regular_image(path: Path) -> Candidate | None:
    if path.suffix.lower() not in IMAGE_SUFFIXES:
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return None
    return candidate_from_bytes(
        data=data,
        source=str(path),
        container="file",
        entry=None,
    )


def scan_zip(path: Path) -> tuple[list[Candidate], list[str]]:
    matches: list[Candidate] = []
    warnings: list[str] = []
    try:
        with ZipFile(path) as archive:
            for info in archive.infolist():
                if info.is_dir() or Path(info.filename).suffix.lower() not in IMAGE_SUFFIXES:
                    continue
                try:
                    data = archive.read(info)
                except Exception as exc:
                    warnings.append(f"{path}!{info.filename}: read failed: {exc}")
                    continue
                candidate = candidate_from_bytes(
                    data=data,
                    source=f"{path}!{info.filename}",
                    container=str(path),
                    entry=info.filename,
                )
                if candidate:
                    matches.append(candidate)
    except (BadZipFile, OSError) as exc:
        warnings.append(f"{path}: ZIP scan failed: {exc}")
    return matches, warnings


def main() -> int:
    parser = ArgumentParser(
        description=(
            "Read-only search for authentic images matching the three corrupted "
            "Bré Thiar production atlas contracts."
        )
    )
    parser.add_argument(
        "roots",
        nargs="+",
        type=Path,
        help="Directories, image files, or ZIP archives to scan",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    matches: list[Candidate] = []
    warnings: list[str] = []
    scanned_files = 0
    scanned_zips = 0

    for raw_root in args.roots:
        root = raw_root.expanduser().resolve()
        if not root.exists():
            warnings.append(f"missing root: {root}")
            continue
        for path in iter_files(root):
            scanned_files += 1
            suffix = path.suffix.lower()
            if suffix in IMAGE_SUFFIXES:
                candidate = scan_regular_image(path)
                if candidate:
                    matches.append(candidate)
                continue
            if suffix == ".zip":
                try:
                    valid_zip = is_zipfile(path)
                except OSError:
                    valid_zip = False
                if not valid_zip:
                    continue
                scanned_zips += 1
                found, zip_warnings = scan_zip(path)
                matches.extend(found)
                warnings.extend(zip_warnings)

    # De-duplicate identical bytes found in repeated backups while retaining the
    # first location. Operators can use the hash to find duplicate copies.
    unique: dict[tuple[str, str], Candidate] = {}
    for candidate in matches:
        unique.setdefault((candidate.target, candidate.sha256), candidate)
    matches = sorted(unique.values(), key=lambda item: (item.target, item.source.lower()))

    found_targets = {candidate.target for candidate in matches}
    missing_targets = [target.key for target in TARGETS if target.key not in found_targets]
    report = {
        "read_only": True,
        "scanned_files": scanned_files,
        "scanned_zip_archives": scanned_zips,
        "target_contracts": [target.__dict__ for target in TARGETS],
        "candidate_count": len(matches),
        "candidates": [candidate.__dict__ for candidate in matches],
        "missing_targets": missing_targets,
        "warnings": warnings,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("BRÉ THIAR RUNTIME CACHE RECOVERY SCAN")
        print(f"- files visited: {scanned_files}")
        print(f"- ZIP archives inspected: {scanned_zips}")
        print(f"- unique geometry matches: {len(matches)}")
        print("- repository writes: none")
        for candidate in matches:
            location = candidate.source
            print(
                f"MATCH {candidate.target}: {location}\n"
                f"  {candidate.image_format} {candidate.width}x{candidate.height} "
                f"{candidate.mode} · {candidate.byte_size} bytes\n"
                f"  sha256={candidate.sha256}\n"
                f"  intended destination={candidate.destination}\n"
                f"  review={candidate.review_note}"
            )
        if missing_targets:
            print("MISSING TARGETS:")
            for key in missing_targets:
                print(f"- {key}")
        if warnings:
            print("WARNINGS:")
            for warning in warnings[:50]:
                print(f"- {warning}")
            if len(warnings) > 50:
                print(f"- ... {len(warnings) - 50} additional warning(s)")

    # A geometry match is evidence for manual review, not automatic approval.
    # Exit 0 when all three target types have at least one candidate; otherwise
    # return 3 so scripted recovery sessions can tell that more source data is needed.
    return 0 if not missing_targets else 3


if __name__ == "__main__":
    raise SystemExit(main())
