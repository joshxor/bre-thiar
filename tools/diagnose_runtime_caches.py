#!/usr/bin/env python3
"""Temporary CI diagnostic for malformed text-encoded runtime image caches."""
from pathlib import Path
from PIL import Image
import base64
import io
import string

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ("houses", "assets/runtime-v2/world_houses_atlas.b64"),
    ("props", "assets/runtime-v2/world_props_atlas.b64"),
    ("fighter", "assets/runtime-v2/characters/wayfarer_iron_warden_q88.b64"),
]
ALLOWED = set(string.ascii_letters + string.digits + "+/=")

for label, rel in FILES:
    raw = (ROOT / rel).read_text()
    text = "".join(raw.split())
    invalid = [(i, ord(ch)) for i, ch in enumerate(text) if ch not in ALLOWED]
    print(f"CACHE {label}: chars={len(text)} mod4={len(text)%4} invalid_count={len(invalid)}")
    if invalid:
        print(f"- invalid positions/codepoints (first 8): {invalid[:8]}")
    successes = []
    for cut in range(0, 5):
        candidate = text[:-cut] if cut else text
        for pad_count in range(0, 4):
            trial = candidate + ("=" * pad_count)
            try:
                data = base64.b64decode(trial, validate=True)
                with Image.open(io.BytesIO(data)) as im:
                    im.load()
                    successes.append((cut, pad_count, im.format, im.size, im.mode, len(data)))
            except Exception:
                pass
    if successes:
        for item in successes[:8]:
            print(f"- decodes with cut={item[0]} pad={item[1]}: format={item[2]} size={item[3]} mode={item[4]} bytes={item[5]}")
    else:
        print("- no valid image found with cut<=4 and pad<=3")
