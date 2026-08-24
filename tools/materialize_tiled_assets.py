#!/usr/bin/env python3
"""Materialize Bré Thiar's checked-in production caches for local Tiled editing.

The public/runtime repo stores production-derived atlases as base64 text caches. This script
reconstructs the actual PNG/WebP files and cuts the Hypnobius world objects into the paths
referenced by maps/tilesets/*.tsj. It does not require or redistribute the original source ZIPs.
"""
from pathlib import Path
from PIL import Image
import base64, io, json

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "assets" / "runtime-v2"
WORLD = ROOT / "assets" / "hypnobius"
CHARS = ROOT / "assets" / "characters" / "v2"
WORLD.mkdir(parents=True, exist_ok=True)
(WORLD / "terrain").mkdir(parents=True, exist_ok=True)
(WORLD / "world").mkdir(parents=True, exist_ok=True)
CHARS.mkdir(parents=True, exist_ok=True)

def decode(path: Path) -> bytes:
    return base64.b64decode("".join(path.read_text().split()))

def image_from_cache(path: Path) -> Image.Image:
    return Image.open(io.BytesIO(decode(path))).convert("RGBA")

manifest = json.loads((ROOT / "bre-thiar-assets-v2.json").read_text())
houses = image_from_cache(CACHE / "world_houses_atlas.b64")
props = image_from_cache(CACHE / "world_props_atlas.b64")

# Terrain source atlas is 5 x 48px inside the props cache; Tiled runtime tiles are 96px.
tx, ty, tw, th = manifest["terrain"]["rect"]
terrain = props.crop((tx, ty, tx + tw, ty + th)).resize((480, 96), Image.Resampling.NEAREST)
terrain.save(WORLD / "terrain" / "bre_thiar_terrain_atlas.png")

for key, spec in manifest["worldTiles"].items():
    atlas_name = spec["atlas"]
    atlas = houses if atlas_name == "houses" else props
    x, y, w, h = manifest["worldAtlases"][atlas_name]["rects"][spec["key"]]
    crop = atlas.crop((x, y, x + w, y + h))
    # Canonical Tiled object images are the 2x runtime world scale.
    crop = crop.resize((w * 2, h * 2), Image.Resampling.NEAREST)
    crop.save(WORLD / "world" / f"{spec['type']}.png")

# Character pair caches: two classes across X, male top / female bottom.
for atlas_name, atlas_spec in manifest["characterAtlases"].items():
    atlas = image_from_cache(ROOT / atlas_spec["cache"])
    for cls, genders in manifest["characters"].items():
        for gender, spec in genders.items():
            if spec["atlas"] != atlas_name:
                continue
            x, y, w, h = spec["rect"]
            atlas.crop((x, y, x + w, y + h)).save(CHARS / f"{cls}_{gender}_directions.png")

print("Materialized Tiled/world and all eight class/gender assets.")
