#!/usr/bin/env python3
"""Search all reachable historical text blobs for production-asset provenance clues.

Read-only. The goal is to recover deleted notes, source filenames, archive names,
or import-path references that can identify the authentic source for the three
corrupted runtime atlases.
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

TERMS = (
    "wayfarer",
    "iron warden",
    "iron_warden",
    "128x160",
    "128×160",
    "hypnobius",
    "source archive",
    "source pack",
    "vendor",
    "character pack",
    "medieval village exterior",
    "dark swamp",
)
TEXT_SUFFIXES = {
    ".md", ".txt", ".json", ".js", ".py", ".html", ".css", ".yml", ".yaml", ".toml", ".ini", ".tmj", ".tsj"
}
MAX_BLOB = 2 * 1024 * 1024


def git(*args: str) -> bytes:
    proc = subprocess.run(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace").strip() or f"git {' '.join(args)} failed")
    return proc.stdout


def main() -> int:
    try:
        objects = git("rev-list", "--objects", "--all").decode("utf-8", "replace").splitlines()
    except Exception as exc:
        print(f"provenance search setup failed: {exc}", file=sys.stderr)
        return 2

    candidates: dict[str, str] = {}
    for line in objects:
        if not line:
            continue
        oid, *rest = line.split(" ", 1)
        path = rest[0] if rest else ""
        if Path(path).suffix.lower() in TEXT_SUFFIXES:
            candidates.setdefault(oid, path)

    matches = []
    for oid, path in candidates.items():
        try:
            size = int(git("cat-file", "-s", oid).decode().strip())
            if size > MAX_BLOB:
                continue
            raw = git("cat-file", "-p", oid)
            text = raw.decode("utf-8", "replace")
        except Exception:
            continue
        lowered = text.lower()
        hit_terms = [term for term in TERMS if term.lower() in lowered]
        if not hit_terms:
            continue
        snippets = []
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            line_lower = line.lower()
            if not any(term.lower() in line_lower for term in hit_terms):
                continue
            start = max(0, idx - 1)
            end = min(len(lines), idx + 2)
            snippet = " | ".join(part.strip() for part in lines[start:end] if part.strip())
            if snippet and snippet not in snippets:
                snippets.append(snippet[:700])
            if len(snippets) >= 4:
                break
        matches.append((path, oid, hit_terms, snippets))

    matches.sort(key=lambda item: item[0])
    print("BRÉ THIAR HISTORICAL ASSET PROVENANCE SEARCH")
    print(f"- text blobs considered: {len(candidates)}")
    print(f"- matching unique blobs: {len(matches)}")
    for path, oid, hit_terms, snippets in matches:
        print(f"MATCH path={path} blob={oid} terms={','.join(hit_terms)}")
        for snippet in snippets:
            print(f"  {snippet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
