#!/usr/bin/env python3
"""State-aware contract validation for The Old Road Act II."""
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "bre-thiar-assets-v2.json"
RUNTIME_PATH = ROOT / "bre-thiar-world-live-v4.js"
INTERIOR_ZONE = "old_barrow_interior"

errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def load_json(path: Path, label: str):
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        fail(f"could not read {label}: {exc}")
        return None


def props(obj: dict) -> dict:
    return {item["name"]: item.get("value") for item in obj.get("properties", [])}


def layer(game_map: dict, name: str):
    return next((item for item in game_map.get("layers", []) if item.get("name") == name), None)


manifest = load_json(MANIFEST_PATH, "world manifest")
runtime = RUNTIME_PATH.read_text() if RUNTIME_PATH.exists() else ""

if manifest is None or not runtime:
    if not runtime:
        fail("active v4 runtime is missing")
    print("OLD ROAD ACT II CONTRACT FAILED")
    for error in errors:
        print("-", error)
    sys.exit(1)

zones = manifest.get("zones", {})
interior_spec = zones.get(INTERIOR_ZONE)

# State A: the interior is not active. Preserve the shipped Act I completion semantics and save contract.
if interior_spec is None:
    required_act1_tokens = (
        "title:'The Old Road'",
        "n.name==='Barrow Threshold'",
        "quest.status='completed'",
        "quest.stage=4",
        "quest.reward='Rowan Charm'",
        "localStorage.setItem('bre-thiar-hypnobius-v3'",
    )
    for token in required_act1_tokens:
        if token not in runtime:
            fail(f"sealed state lost existing Old Road save/completion token: {token}")

    forbidden_live_tokens = (
        "old_road_act2_objective_1",
        "old_road_act2_objective_2",
        "stonebound_warden",
        "migrateOldRoadAct2",
    )
    for token in forbidden_live_tokens:
        if token in runtime:
            fail(f"sealed state contains live Act II runtime token: {token}")

    if not errors:
        print("OLD ROAD ACT II CONTRACT PASSED")
        print("- state=SEALED")
        print("- existing stage-4 Rowan Charm completion remains authoritative")
        print("- no dormant interior encounter has been exposed in the active runtime")
        sys.exit(0)

# State B: the interior is live. Require a complete second-act quest package.
map_value = (interior_spec or {}).get("map")
if not map_value:
    fail("active old_barrow_interior zone is missing its map")
    interior = None
else:
    interior = load_json(ROOT / map_value, "Old Barrow Interior map")

if interior is not None:
    map_props = {item["name"]: item.get("value") for item in interior.get("properties", [])}
    if map_props.get("quest_contract") != "old_road_act2_v1":
        fail("Old Barrow Interior must declare quest_contract=old_road_act2_v1")

    trigger_layer = layer(interior, "Spawns & Triggers") or {"objects": []}
    objects = trigger_layer.get("objects", [])
    quest_steps = {props(obj).get("quest_step") for obj in objects if props(obj).get("quest_step")}
    required_steps = {
        "old_road_act2_entry",
        "old_road_act2_objective_1",
        "old_road_act2_objective_2",
        "old_road_act2_warden",
        "old_road_act2_deeper_seal",
    }
    missing = required_steps - quest_steps
    if missing:
        fail(f"Old Barrow Interior is missing Act II quest-step triggers: {sorted(missing)}")

    encounters = [
        obj
        for obj in objects
        if obj.get("type") == "encounter" and props(obj).get("encounter_id") == "stonebound_warden"
    ]
    if len(encounters) != 1:
        fail(f"expected exactly one Stonebound Warden encounter trigger, got {len(encounters)}")

required_runtime_tokens = (
    "migrateOldRoadAct2",
    "old_road_act2_objective_1",
    "old_road_act2_objective_2",
    "stonebound_warden",
    "Stonebound Warden",
    "Rowan Charm",
)
for token in required_runtime_tokens:
    if token not in runtime:
        fail(f"active Act II runtime contract missing: {token}")

if errors:
    print("OLD ROAD ACT II CONTRACT FAILED")
    for error in errors:
        print("-", error)
    sys.exit(1)

print("OLD ROAD ACT II CONTRACT PASSED")
print("- state=ACTIVE")
print("- stage-4 saves have an explicit Act II migration hook")
print("- two exploration objectives, Warden encounter, and deeper seal are map-backed")
print("- Rowan Charm continuity is retained")
