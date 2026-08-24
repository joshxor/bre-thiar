#!/usr/bin/env python3
"""Report finite Tiled tile-layer lengths and row boundaries for production zones."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "bre-thiar-assets-v2.json").read_text())

print("BRÉ THIAR TILED LAYER LENGTH DIAGNOSTIC")
for zone_id, spec in manifest.get("zones", {}).items():
    game_map = json.loads((ROOT / spec["map"]).read_text())
    width = game_map.get("width", 0)
    height = game_map.get("height", 0)
    expected = width * height
    print(f"ZONE {zone_id}: {width}x{height} expected_cells={expected}")
    for layer in game_map.get("layers", []):
        if layer.get("type") != "tilelayer":
            continue
        data = layer.get("data", [])
        delta = len(data) - expected
        tail = data[-8:] if data else []
        print(f"- {layer.get('name')}: cells={len(data)} delta={delta} tail={tail}")
        if delta == 0:
            continue
        rows = [data[i:i + width] for i in range(0, len(data), width)] if width else []
        for idx, row in enumerate(rows):
            marker = "overflow" if idx >= height else "map"
            print(f"  row[{idx:02d}] {marker} len={len(row)} data={row}")
        if len(data) < expected:
            missing = expected - len(data)
            print(f"  missing_cells={missing}; missing logical coordinates begin at index={len(data)}")
