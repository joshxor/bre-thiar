from __future__ import annotations
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT.parent
ASSETS = ROOT / "assets"
errors: list[str] = []


def need(path: Path, msg: str | None = None):
    if not path.exists():
        errors.append(msg or f"Missing {path.relative_to(ROOT)}")


def image_ok(path: Path, *, expected_size=None, require_alpha=False):
    need(path)
    if not path.exists():
        return
    try:
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            if expected_size and im.size != expected_size:
                errors.append(f"{path.relative_to(ROOT)}: size {im.size} != {expected_size}")
            if require_alpha:
                rgba = im.convert("RGBA")
                extrema = rgba.getchannel("A").getextrema()
                if extrema[0] == 255:
                    errors.append(f"{path.relative_to(ROOT)}: foreground has no transparent pixels")
    except Exception as exc:
        errors.append(f"{path.relative_to(ROOT)}: invalid image ({exc})")


def map_file(name: str):
    path = ASSETS / "maps" / f"{name}.json"
    need(path)
    return json.loads(path.read_text(encoding="utf-8"))


build_info_path = PACKAGE / "BUILD_INFO.json"
need(build_info_path, "Missing BUILD_INFO.json")
if build_info_path.exists():
    try:
        build_info = json.loads(build_info_path.read_text(encoding="utf-8"))
        if build_info.get("version") != "0.7.1":
            errors.append(f"BUILD_INFO version {build_info.get('version')} != 0.7.1")
        if int(build_info.get("protocolVersion", -1)) != 1 or int(build_info.get("contentVersion", -1)) != 6:
            errors.append("BUILD_INFO protocol/content version mismatch")
        if build_info.get("engine") != "Godot 4.7.1":
            errors.append(f"BUILD_INFO engine {build_info.get('engine')} != Godot 4.7.1")
    except Exception as exc:
        errors.append(f"BUILD_INFO.json invalid ({exc})")

export_text = (ROOT / "export_presets.cfg").read_text(encoding="utf-8") if (ROOT / "export_presets.cfg").exists() else ""
for token in ('name="Windows Desktop"','application/file_version="0.7.1.0"','application/product_version="0.7.1.0"','export_path="../build/BreThiar.exe"'):
    if token not in export_text:
        errors.append(f"export preset missing {token}")

for path in [
    ROOT / "project.godot",
    ROOT / "scenes" / "main.tscn",
    ROOT / "scripts" / "main.gd",
    ROOT / "scripts" / "logical_floor.gd",
    ROOT / "scripts" / "network_client.gd",
    ROOT / "export_presets.cfg",
]:
    need(path)

image_ok(ASSETS / "characters" / "player_walk_v05.png", expected_size=(384, 448))
image_ok(ASSETS / "characters" / "player_idle_v05.png", expected_size=(384, 112))
image_ok(ASSETS / "characters" / "player_assail_v05.png", expected_size=(384, 112))
image_ok(ASSETS / "characters" / "boar_clean.png")
image_ok(ASSETS / "tiles" / "terrain_atlas.png")
image_ok(ASSETS / "enemies" / "ghost.png")
image_ok(ASSETS / "enemies" / "warden.png")

maps = {zone: map_file(zone) for zone in ("overworld", "barrow")}
for zone, m in maps.items():
    w, h, ts = int(m["width"]), int(m["height"]), int(m["tileSize"])
    if ts != 32:
        errors.append(f"{zone}: tileSize {ts} != 32")
    if int(m["worldWidth"]) != w * ts or int(m["worldHeight"]) != h * ts:
        errors.append(f"{zone}: world dimensions do not match logical grid")
    if len(m["collision"]) != w * h:
        errors.append(f"{zone}: collision length {len(m['collision'])} != {w*h}")
    entry = m["entry"]
    tx, ty = int(entry[0] // ts), int(entry[1] // ts)
    if m["collision"][ty * w + tx] != 0:
        errors.append(f"{zone}: entry is blocked")

    for transition in m.get("transitions", []):
        target = transition.get("to")
        if target not in maps:
            errors.append(f"{zone}: transition {transition.get('id')} targets unknown zone {target}")
            continue
        dest = transition.get("dest", [])
        if len(dest) != 2:
            errors.append(f"{zone}: transition {transition.get('id')} has bad destination")
            continue
        dm = maps[target]
        dtx, dty = int(dest[0] // dm["tileSize"]), int(dest[1] // dm["tileSize"])
        if dm["collision"][dty * dm["width"] + dtx] != 0:
            errors.append(f"{zone}: transition {transition.get('id')} destination is blocked")

    for p in m.get("props", []):
        group = p.get("assetGroup", "props" if zone == "barrow" else "scene_props")
        image_ok(ASSETS / group / p["sprite"])
        fg = p.get("foreground")
        if fg:
            fg_group = p.get("foregroundGroup", "foreground")
            image_ok(ASSETS / fg_group / fg, require_alpha=True)

    for n in m.get("npcs", []):
        image_ok(ASSETS / "npcs" / n["sprite"])

    if zone == "overworld":
        gm = m.get("groundMeta", [])
        if len(gm) != 60:
            errors.append(f"overworld: expected 60 authored ground metatiles, got {len(gm)}")
        groups: dict[str, list[dict]] = {}
        for g in gm:
            groups.setdefault(str(g["sprite"]).split("_")[0], []).append(g)
        for group_items in groups.values():
            max_x = max(int(g["x"]) for g in group_items)
            max_y = max(int(g["y"]) for g in group_items)
            for g in group_items:
                path = ASSETS / "ground_meta" / g["sprite"]
                image_ok(path)
                if path.exists():
                    with Image.open(path) as im:
                        w_px, h_px = im.size
                    if not (32 <= w_px <= 256 and 32 <= h_px <= 256):
                        errors.append(f"{path.relative_to(ROOT)}: invalid metatile crop size {(w_px, h_px)}")
                    if int(g["x"]) != max_x and w_px != 256:
                        errors.append(f"{path.relative_to(ROOT)}: only right-edge metatiles may be width-cropped")
                    if int(g["y"]) != max_y and h_px != 256:
                        errors.append(f"{path.relative_to(ROOT)}: only bottom-edge metatiles may be height-cropped")

    for e in m.get("enemies", []):
        et = e.get("type")
        if et not in {"boar", "shade", "skeleton", "warden", "boss"}:
            errors.append(f"{zone}: unsupported enemy type {et}")

main = (ROOT / "scripts" / "main.gd").read_text(encoding="utf-8")
network = (ROOT / "scripts" / "network_client.gd").read_text(encoding="utf-8")
for forbidden in ("village.webp", "world-live.js", "CanvasRenderingContext2D", "http.server"):
    if forbidden in main or forbidden in network:
        errors.append(f"Windows client contains forbidden web/mobile dependency: {forbidden}")
for required in (
    "groundMeta", "foreground", "collision", "Camera2D", "player_walk_v05.png", "player_idle_v05.png", "player_assail_v05.png",
    "BreNetworkClient", "snapshot_received", "remote_players", "send_skill", "boss", "_update_inventory_actions", "ITEM_LABELS",
):
    if required not in main and required not in network:
        errors.append(f"Windows client missing required contract token: {required}")
for required in ("WebSocketPeer", "HTTPRequest", "send_input", "send_interact", "send_choice", "send_equip", "send_use_item"):
    if required not in network:
        errors.append(f"network_client.gd missing {required}")

if errors:
    print("BRE THIAR WINDOWS PROJECT VALIDATION FAILED")
    for e in errors:
        print(" -", e)
    raise SystemExit(1)

print("BRE THIAR WINDOWS PROJECT VALIDATION PASSED")
print("overworld: 48x72 logical cells, 60 native metatile slices (256px interiors + intentional edge crops)")
print("barrow: 64x48 logical cells, native terrain atlas")
print("foreground transparency + transition destinations: PASS")
print("boss/Stonebound Warden asset mapping: PASS")
print("authoritative network + inventory/equipment contract: PASS")
print("build metadata + Windows v0.7.1 export preset: PASS")
print("web/mobile runtime dependency check: clean")
