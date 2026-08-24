#!/usr/bin/env python3
"""Materialize Bré Thiar's checked-in production caches for local Tiled editing.

The repository stores production-derived atlases as base64 text caches. This script reconstructs
the actual PNG/WebP data, cuts the Hypnobius world objects into the image paths referenced by the
Tiled tilesets, and exports all eight current class/gender four-direction strips.

Requires Pillow: `python -m pip install Pillow`
"""
from pathlib import Path
from PIL import Image
import base64, io, json

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "assets" / "runtime-v2"
WORLD = ROOT / "assets" / "hypnobius"
CHARS = ROOT / "assets" / "characters" / "v2"
(WORLD / "terrain").mkdir(parents=True, exist_ok=True)
(WORLD / "world").mkdir(parents=True, exist_ok=True)
CHARS.mkdir(parents=True, exist_ok=True)

manifest = json.loads((ROOT / "bre-thiar-assets-v2.json").read_text())

def decoded_spec(spec: dict) -> bytes:
    paths = spec.get("parts") or [spec["cache"]]
    text = "".join("".join((ROOT / p).read_text().split()) for p in paths)
    return base64.b64decode(text)

def image_from_spec(spec: dict) -> Image.Image:
    return Image.open(io.BytesIO(decoded_spec(spec))).convert("RGBA")

houses = image_from_spec(manifest["worldAtlases"]["houses"])
props = image_from_spec(manifest["worldAtlases"]["props"])

# Terrain source is five 48px tiles embedded in the props cache. Tiled uses the locked 2x world
# scale, therefore the materialized terrain atlas is 5 x 96px.
tx, ty, tw, th = manifest["terrain"]["rect"]
terrain = props.crop((tx, ty, tx + tw, ty + th)).resize((480, 96), Image.Resampling.NEAREST)
terrain.save(WORLD / "terrain" / "bre_thiar_terrain_atlas.png")

world_atlases = {"houses": houses, "props": props}
for _, spec in manifest["worldTiles"].items():
    atlas_name = spec["atlas"]
    atlas = world_atlases[atlas_name]
    x, y, w, h = manifest["worldAtlases"][atlas_name]["rects"][spec["key"]]
    crop = atlas.crop((x, y, x + w, y + h)).resize((w * 2, h * 2), Image.Resampling.NEAREST)
    crop.save(WORLD / "world" / f"{spec['type']}.png")

# Character atlases are kept at native 128x160 character scale. Each exported file is 128x640:
# UP, LEFT, DOWN, RIGHT. No locomotion frames are fabricated here.
character_atlases = {
    name: image_from_spec(spec)
    for name, spec in manifest["characterAtlases"].items()
}
for cls, genders in manifest["characters"].items():
    for gender, spec in genders.items():
        atlas = character_atlases[spec["atlas"]]
        x, y, w, h = spec["rect"]
        atlas.crop((x, y, x + w, y + h)).save(CHARS / f"{cls}_{gender}_directions.png")

print("Materialized Hypnobius Tiled assets and all eight Bré Thiar class/gender strips.")
