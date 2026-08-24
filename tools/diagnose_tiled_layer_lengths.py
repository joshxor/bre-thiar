#!/usr/bin/env python3
"""Report finite Tiled tile-layer data lengths for every production zone."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "bre-thiar-assets-v2.json").read_text())

print("BRÉ THIAR TILED LAYER LENGTH DIAGNOSTIC")
for zone_id, spec in manifest.get("zones", {}).items():
    game_map = json.loads((ROOT / spec["map"]).read_text())
    expected = game_map.get("width", 0) * game_map.get("height", 0)
    print(
        f"ZONE {zone_id}: {game_map.get('width')}x{game_map.get('height')} "
        f"expected_cells={expected}"
    )
    for layer in game_map.get("layers", []):
        if layer.get("type") != "tilelayer":
            continue
        data = layer.get("data", [])
        delta = len(data) - expected
        tail = data[-8:] if data else []
        print(
            f"- {layer.get('name')}: cells={len(data)} delta={delta} "
            f"tail={tail}"
        )
