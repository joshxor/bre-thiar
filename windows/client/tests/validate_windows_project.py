from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
errors: list[str] = []

def need(path: Path, msg: str | None = None):
    if not path.exists():
        errors.append(msg or f"Missing {path.relative_to(ROOT)}")

def map_file(name: str):
    path = ASSETS / "maps" / f"{name}.json"
    need(path)
    return json.loads(path.read_text(encoding="utf-8"))

need(ROOT / "project.godot")
need(ROOT / "scenes" / "main.tscn")
need(ROOT / "scripts" / "main.gd")
need(ROOT / "scripts" / "logical_floor.gd")
need(ASSETS / "characters" / "player_walk_v05.png")
need(ASSETS / "tiles" / "terrain_atlas.png")

for zone in ("overworld", "barrow"):
    m = map_file(zone)
    w, h = int(m["width"]), int(m["height"])
    if len(m["collision"]) != w * h:
        errors.append(f"{zone}: collision length {len(m['collision'])} != {w*h}")
    entry = m["entry"]
    tx, ty = int(entry[0] // m["tileSize"]), int(entry[1] // m["tileSize"])
    if m["collision"][ty*w+tx] != 0:
        errors.append(f"{zone}: entry is blocked")
    for p in m.get("props", []):
        group = p.get("assetGroup", "props" if zone == "barrow" else "scene_props")
        need(ASSETS / group / p["sprite"], f"{zone}: missing prop {group}/{p['sprite']}")
        fg = p.get("foreground")
        if fg:
            fg_group = p.get("foregroundGroup", "foreground")
            need(ASSETS / fg_group / fg, f"{zone}: missing foreground {fg_group}/{fg}")
    for n in m.get("npcs", []):
        need(ASSETS / "npcs" / n["sprite"], f"{zone}: missing NPC {n['sprite']}")
    if zone == "overworld":
        gm = m.get("groundMeta", [])
        if len(gm) != 60:
            errors.append(f"overworld: expected 60 authored ground metatiles, got {len(gm)}")
        for g in gm:
            need(ASSETS / "ground_meta" / g["sprite"], f"overworld: missing metatile {g['sprite']}")

main = (ROOT / "scripts" / "main.gd").read_text(encoding="utf-8")
for forbidden in ("village.webp", "world-live.js", "CanvasRenderingContext2D", "http.server"):
    if forbidden in main:
        errors.append(f"Windows client contains forbidden web/mobile dependency: {forbidden}")
for required in ("groundMeta", "foreground", "collision", "Camera2D", "player_walk_v05.png"):
    if required not in main:
        errors.append(f"Windows client missing required contract token: {required}")

if errors:
    print("BRE THIAR WINDOWS PROJECT VALIDATION FAILED")
    for e in errors:
        print(" -", e)
    raise SystemExit(1)
print("BRE THIAR WINDOWS PROJECT VALIDATION PASSED")
print("overworld: 48x72 logical cells, 60 native ground metatiles")
print("barrow: 64x48 logical cells, native terrain atlas")
print("web/mobile runtime dependency check: clean")
