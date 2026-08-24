#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageFile
import base64
import io
import json
import re

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "bre-thiar-assets-v2.json").read_text())
ImageFile.LOAD_TRUNCATED_IMAGES = True

specs = {}
for name, spec in manifest.get("worldAtlases", {}).items():
    specs[f"world:{name}"] = spec
for name, spec in manifest.get("characterAtlases", {}).items():
    specs[f"character:{name}"] = spec

alphabet = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")

for label, spec in specs.items():
    paths = spec.get("parts") or [spec["cache"]]
    pieces = []
    print(f"CACHE {label}")
    for rel in paths:
        raw = (ROOT / rel).read_text()
        compact = "".join(raw.split())
        invalid = [(i, ch, ord(ch)) for i, ch in enumerate(compact) if ch not in alphabet]
        first_pad = compact.find("=")
        print(
            f"  {rel}: chars={len(compact)} mod4={len(compact)%4} "
            f"invalid={len(invalid)} first_invalid={invalid[:5]} first_pad={first_pad}"
        )
        pieces.append(compact)

    joined = "".join(pieces)
    cleaned = "".join(ch for ch in joined if ch in alphabet)
    core = cleaned.rstrip("=")
    print(
        f"  joined: chars={len(joined)} mod4={len(joined)%4}; "
        f"cleaned={len(cleaned)} mod4={len(cleaned)%4}; core={len(core)} mod4={len(core)%4}"
    )

    successes = []
    for trim in range(0, 9):
        candidate_core = core[:-trim] if trim else core
        if not candidate_core:
            continue
        candidate = candidate_core + "=" * ((-len(candidate_core)) % 4)
        try:
            data = base64.b64decode(candidate, validate=True)
        except Exception:
            continue
        try:
            im = Image.open(io.BytesIO(data))
            im.load()
            successes.append((trim, len(candidate), len(data), im.format, im.size))
        except Exception:
            pass
    print(f"  decodable_image_candidates={successes[:10]}")
