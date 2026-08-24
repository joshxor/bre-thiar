#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "bre-thiar-assets-v2.json"
APPROACH_MAP_PATH = ROOT / "maps" / "Old_Barrow_Approach_v1.tmj"
INTERIOR_ZONE = "old_barrow_interior"
INTERIOR_MAP_BASENAME = "Old_Barrow_Interior_v1.tmj"

errors = []
notes = []


def fail(message):
    errors.append(message)


def props(obj):
    return {p["name"]: p.get("value") for p in obj.get("properties", [])}


def layer(map_data, name):
    return next((item for item in map_data.get("layers", []) if item.get("name") == name), None)


def load_json(path, label):
    if not path.exists():
        fail(f"missing {label}: {path.relative_to(ROOT)}")
        return None
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        fail(f"invalid JSON in {label}: {exc}")
        return None


manifest = load_json(MANIFEST_PATH, "world manifest")
approach = load_json(APPROACH_MAP_PATH, "Old Barrow Approach map")

if manifest is None or approach is None:
    print("OLD BARROW INTERIOR READINESS FAILED")
    for error in errors:
        print("-", error)
    sys.exit(1)

zones = manifest.get("zones", {})
approach_triggers = layer(approach, "Spawns & Triggers") or {"objects": []}
approach_collision = layer(approach, "Collision") or {"objects": []}

threshold = next(
    (
        obj
        for obj in approach_triggers.get("objects", [])
        if obj.get("type") == "poi"
        and (obj.get("name") == "Barrow Threshold" or props(obj).get("id") == "barrow_threshold")
    ),
    None,
)
seal = next(
    (
        obj
        for obj in approach_collision.get("objects", [])
        if obj.get("name") == "Old Barrow Seal Footprint" or obj.get("type") == "barrow_gate"
    ),
    None,
)
interior_exits = []
for obj in approach_triggers.get("objects", []):
    if obj.get("type") != "exit":
        continue
    if props(obj).get("destination_zone") == INTERIOR_ZONE:
        interior_exits.append(obj)

interior_spec = zones.get(INTERIOR_ZONE)

# State A: no production interior yet. The exterior must stay safely sealed.
if interior_spec is None:
    if threshold is None:
        fail("sealed state is missing the Barrow Threshold POI")
    if seal is None:
        fail("sealed state is missing the barrow gate collision footprint")
    if interior_exits:
        fail("sealed state must not contain an active exit to old_barrow_interior")

    if not errors:
        notes.append("state=SEALED")
        notes.append("production interior is not registered in bre-thiar-assets-v2.json")
        notes.append("barrow threshold POI and blocking collision are intact")
        print("OLD BARROW INTERIOR READINESS PASSED")
        for note in notes:
            print("-", note)
        sys.exit(0)

# State B: the production interior has been activated. Require a real map and reciprocal route.
map_value = interior_spec.get("map")
if not map_value:
    fail("old_barrow_interior zone is missing its map path")
    interior_path = ROOT / "maps" / INTERIOR_MAP_BASENAME
else:
    interior_path = ROOT / map_value

if interior_path.name != INTERIOR_MAP_BASENAME:
    fail(f"old_barrow_interior must use maps/{INTERIOR_MAP_BASENAME}")

interior = load_json(interior_path, "Old Barrow Interior map")
if interior is not None:
    if interior.get("orientation") != "orthogonal":
        fail("Old Barrow Interior must be orthogonal")
    if (interior.get("tilewidth"), interior.get("tileheight")) != (96, 96):
        fail("Old Barrow Interior must use the established 96x96 runtime world cell")

    map_props = {p["name"]: p.get("value") for p in interior.get("properties", [])}
    if map_props.get("zone_id") != INTERIOR_ZONE:
        fail("Old Barrow Interior map must declare zone_id=old_barrow_interior")
    if map_props.get("map_role") != "dungeon_interior":
        fail("Old Barrow Interior map must declare map_role=dungeon_interior")
    art_family = str(map_props.get("art_family") or "").strip()
    if not art_family:
        fail("Old Barrow Interior map must declare a non-empty art_family")
    elif "placeholder" in art_family.lower() or "legacy" in art_family.lower():
        fail("Old Barrow Interior art_family may not be placeholder or legacy art")

    names = {item.get("name") for item in interior.get("layers", [])}
    for required in ("World Objects", "Collision", "Spawns & Triggers"):
        if required not in names:
            fail(f"Old Barrow Interior is missing required layer: {required}")
    visible_tilelayers = [
        item
        for item in interior.get("layers", [])
        if item.get("type") == "tilelayer" and item.get("visible", True)
    ]
    if not visible_tilelayers:
        fail("Old Barrow Interior needs at least one visible authored tile layer")

    interior_triggers = layer(interior, "Spawns & Triggers") or {"objects": []}
    spawns = {
        obj.get("name")
        for obj in interior_triggers.get("objects", [])
        if obj.get("type") == "spawn"
    }
    default_spawn = interior_spec.get("defaultSpawn")
    if not default_spawn:
        fail("old_barrow_interior zone is missing defaultSpawn")
    elif default_spawn not in spawns:
        fail(f"Old Barrow Interior is missing default spawn: {default_spawn}")

    return_exit = None
    for obj in interior_triggers.get("objects", []):
        if obj.get("type") != "exit":
            continue
        p = props(obj)
        if p.get("destination_zone") == "old_barrow_approach":
            return_exit = obj
            break
    if return_exit is None:
        fail("Old Barrow Interior needs an exit back to old_barrow_approach")
    else:
        destination_spawn = props(return_exit).get("destination_spawn")
        approach_spawns = {
            obj.get("name")
            for obj in approach_triggers.get("objects", [])
            if obj.get("type") == "spawn"
        }
        if destination_spawn and destination_spawn not in approach_spawns:
            fail(
                "Old Barrow Interior return exit points to missing approach spawn: "
                + destination_spawn
            )

if not interior_exits:
    fail("activated old_barrow_interior zone requires an approach exit into the interior")
elif len(interior_exits) > 1:
    fail("Old Barrow Approach contains multiple exits into old_barrow_interior")
else:
    destination_spawn = props(interior_exits[0]).get("destination_spawn")
    if interior is not None:
        interior_triggers = layer(interior, "Spawns & Triggers") or {"objects": []}
        interior_spawns = {
            obj.get("name")
            for obj in interior_triggers.get("objects", [])
            if obj.get("type") == "spawn"
        }
        if destination_spawn and destination_spawn not in interior_spawns:
            fail(
                "Old Barrow Approach interior exit points to missing interior spawn: "
                + destination_spawn
            )

if seal is not None:
    fail("activated interior still has the Old Barrow Seal Footprint/barrow_gate collision")

if errors:
    print("OLD BARROW INTERIOR READINESS FAILED")
    for error in errors:
        print("-", error)
    sys.exit(1)

print("OLD BARROW INTERIOR READINESS PASSED")
print("- state=ACTIVE")
print("- production interior map is registered and reciprocal route contract is valid")
