#!/usr/bin/env python3
"""Static validation for the Bré Thiar Hypnobius/Tiled village integration."""
from pathlib import Path
from PIL import Image
import base64, io, json, string, sys

ROOT = Path(__file__).resolve().parents[1]
errors = []

def fail(msg):
    errors.append(msg)

def diagnose_cache_text(paths, text):
    allowed=set(string.ascii_letters+string.digits+"+/=")
    invalid=[(i,ord(ch)) for i,ch in enumerate(text) if ch not in allowed]
    print(f"CACHE DIAGNOSTIC {paths}: chars={len(text)} mod4={len(text)%4} invalid_count={len(invalid)}")
    if invalid:
        print(f"- invalid positions/codepoints (first 8): {invalid[:8]}")
    successes=[]
    for cut in range(0,5):
        candidate=text[:-cut] if cut else text
        for pad_count in range(0,4):
            trial=candidate+("="*pad_count)
            try:
                data=base64.b64decode(trial,validate=True)
                with Image.open(io.BytesIO(data)) as im:
                    im.load()
                    successes.append((cut,pad_count,im.format,im.size,im.mode,len(data)))
            except Exception:
                pass
    if successes:
        for item in successes[:8]:
            print(f"- image decodes with cut={item[0]} pad={item[1]}: format={item[2]} size={item[3]} mode={item[4]} bytes={item[5]}")
    else:
        print("- no valid image found with cut<=4 and pad<=3")

def decoded_spec(spec: dict) -> bytes:
    paths = spec.get("parts") or [spec["cache"]]
    try:
        text = "".join("".join((ROOT / p).read_text().split()) for p in paths)
        return base64.b64decode(text, validate=True)
    except Exception as exc:
        try:
            diagnose_cache_text(paths,text)
        except Exception as diag_exc:
            print(f"CACHE DIAGNOSTIC FAILED {paths}: {diag_exc}")
        fail(f"cache decode failed for {paths}: {exc}")
        return b""

def image_from_spec(name: str, spec: dict):
    data = decoded_spec(spec)
    if not data:
        return None
    try:
        im = Image.open(io.BytesIO(data)).convert("RGBA")
        im.load()
        return im
    except Exception as exc:
        fail(f"image decode failed for {name}: {exc}")
        return None

try:
    manifest = json.loads((ROOT / "bre-thiar-assets-v2.json").read_text())
    game_map = json.loads((ROOT / manifest["map"]).read_text())
    terrain_ts = json.loads((ROOT / "maps/tilesets/terrain.tsj").read_text())
    world_ts = json.loads((ROOT / "maps/tilesets/world_objects.tsj").read_text())
except Exception as exc:
    print(f"FATAL: could not parse integration JSON: {exc}")
    sys.exit(1)

if (game_map.get("width"), game_map.get("height"), game_map.get("tilewidth"), game_map.get("tileheight")) != (14, 8, 96, 96):
    fail("canonical map geometry must be 14x8 cells at 96x96")

layers = {layer["name"]: layer for layer in game_map.get("layers", [])}
required_layers = ["Ground", "Swamp", "Roads", "World Objects", "Collision", "Spawns & Triggers"]
for name in required_layers:
    if name not in layers:
        fail(f"missing map layer: {name}")

for name in ["Ground", "Swamp", "Roads"]:
    if name in layers and len(layers[name].get("data", [])) != 112:
        fail(f"{name} must contain exactly 112 tile cells")

terrain_ref = next((t for t in game_map.get("tilesets", []) if "terrain" in t.get("source", "")), None)
world_ref = next((t for t in game_map.get("tilesets", []) if "world_objects" in t.get("source", "")), None)
if not terrain_ref or not world_ref:
    fail("map must reference both terrain and world-object tilesets")
else:
    tf = terrain_ref["firstgid"]
    for layer_name in ["Ground", "Swamp", "Roads"]:
        for gid in layers.get(layer_name, {}).get("data", []):
            if gid and not (tf <= gid < tf + terrain_ts.get("tilecount", 0)):
                fail(f"{layer_name} contains out-of-range terrain gid {gid}")
    wf = world_ref["firstgid"]
    for obj in layers.get("World Objects", {}).get("objects", []):
        local_id = obj.get("gid", 0) - wf
        if str(local_id) not in manifest.get("worldTiles", {}):
            fail(f"world object {obj.get('name')} uses unmapped gid {obj.get('gid')}")

world_images = {}
for name, spec in manifest.get("worldAtlases", {}).items():
    world_images[name] = image_from_spec(f"world atlas {name}", spec)

for atlas_name, spec in manifest.get("worldAtlases", {}).items():
    im = world_images.get(atlas_name)
    if im is None:
        continue
    W, H = im.size
    for key, rect in spec.get("rects", {}).items():
        x, y, w, h = rect
        if min(x, y, w, h) < 0 or x + w > W or y + h > H:
            fail(f"world rect {atlas_name}/{key} falls outside atlas {im.size}")

char_images = {}
for name, spec in manifest.get("characterAtlases", {}).items():
    char_images[name] = image_from_spec(f"character atlas {name}", spec)

expected_classes = {"wayfarer", "iron_warden", "trail_ranger", "runekeeper"}
if set(manifest.get("characters", {})) != expected_classes:
    fail("character manifest must contain exactly the four canonical classes")

sheet_count = 0
for cls, genders in manifest.get("characters", {}).items():
    if set(genders) != {"male", "female"}:
        fail(f"{cls} must contain male and female assets")
    for gender, spec in genders.items():
        sheet_count += 1
        im = char_images.get(spec.get("atlas"))
        if im is None:
            continue
        x, y, w, h = spec["rect"]
        if (w, h) != (128, 640):
            fail(f"{cls}/{gender} direction strip must be 128x640, got {(w, h)}")
            continue
        if x + w > im.width or y + h > im.height:
            fail(f"{cls}/{gender} crop falls outside character atlas {im.size}")
            continue
        strip = im.crop((x, y, x + w, y + h))
        for row in range(4):
            frame = strip.crop((0, row * 160, 128, (row + 1) * 160))
            if frame.getbbox() is None:
                fail(f"{cls}/{gender} direction row {row} is empty")

if sheet_count != 8:
    fail(f"expected 8 class/gender direction strips, got {sheet_count}")

if world_ts.get("tilecount") != 14:
    fail(f"world tileset must define 14 object types, got {world_ts.get('tilecount')}")
if len(layers.get("World Objects", {}).get("objects", [])) != 22:
    fail("canonical village map must contain 22 placed world objects")
if len(layers.get("Collision", {}).get("objects", [])) != 6:
    fail("canonical village map must contain 6 collision regions")

triggers = layers.get("Spawns & Triggers", {}).get("objects", [])
spawns = [o for o in triggers if o.get("type") == "spawn"]
exits = [o for o in triggers if o.get("type") == "exit"]
spawn_names = {o.get("name") for o in spawns}
if spawn_names != {"Player Spawn", "North Arrival"}:
    fail(f"canonical village spawns mismatch: {sorted(spawn_names)}")
if len(exits) != 4:
    fail(f"expected four cardinal exits, got {len(exits)}")

if errors:
    print("BRE THIAR HYPNOBIUS INTEGRATION: FAIL")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("BRE THIAR HYPNOBIUS INTEGRATION: PASS")
print("- 14x8 Tiled village at 96px runtime grid")
print("- 22 placed world objects / 6 collision regions / 2 named spawns / 4 exits")
print("- world caches decode and rects are in bounds")
print("- all 8 canonical class/gender direction strips decode with 4 non-empty directions")
