#!/usr/bin/env python3
"""Validate the runtime-atlas rebuild contract against the active v4 manifest."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "bre-thiar-assets-v2.json"
CONTRACT_PATH = ROOT / "docs" / "RUNTIME_ATLAS_REBUILD_CONTRACT.json"

errors: list[str] = []


def fail(message: str) -> None:
    errors.append(message)


def rect_tuple(value, label: str):
    if not isinstance(value, list) or len(value) != 4 or not all(isinstance(v, int) for v in value):
        fail(f"{label} must be a four-integer rect")
        return None
    x, y, w, h = value
    if min(x, y) < 0 or min(w, h) <= 0:
        fail(f"{label} must have non-negative origin and positive size")
        return None
    return x, y, w, h


def validate_source_state(slot: dict, label: str) -> None:
    status = slot.get("sourceStatus")
    if status not in {"unresolved", "verified"}:
        fail(f"{label} sourceStatus must be unresolved or verified")
        return
    source_file = slot.get("sourceFile")
    source_rect = slot.get("sourceRect")
    if status == "unresolved":
        if source_file is not None or source_rect is not None:
            fail(f"{label} unresolved source mapping must keep sourceFile/sourceRect null")
    else:
        if not isinstance(source_file, str) or not source_file.strip():
            fail(f"{label} verified mapping requires sourceFile")
        rect_tuple(source_rect, f"{label} sourceRect")


def validate_target_canvas(target: dict, label: str) -> None:
    size = target.get("size")
    if not isinstance(size, list) or len(size) != 2 or not all(isinstance(v, int) and v > 0 for v in size):
        fail(f"{label} size must be two positive integers")
        return
    width, height = size
    slots = target.get("slots")
    if not isinstance(slots, list) or not slots:
        fail(f"{label} must define at least one slot")
        return
    seen: set[str] = set()
    for slot in slots:
        if not isinstance(slot, dict):
            fail(f"{label} contains a non-object slot")
            continue
        key = slot.get("key")
        if not isinstance(key, str) or not key:
            fail(f"{label} slot missing key")
            continue
        if key in seen:
            fail(f"{label} contains duplicate slot {key}")
        seen.add(key)
        rect = rect_tuple(slot.get("destinationRect"), f"{label}/{key} destinationRect")
        if rect:
            x, y, w, h = rect
            if x + w > width or y + h > height:
                fail(f"{label}/{key} destinationRect exceeds {width}x{height} canvas")
        validate_source_state(slot, f"{label}/{key}")


def slots_by_key(target: dict, label: str) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for slot in target.get("slots", []):
        if isinstance(slot, dict) and isinstance(slot.get("key"), str):
            result[slot["key"]] = slot
    return result


try:
    manifest = json.loads(MANIFEST_PATH.read_text())
    contract = json.loads(CONTRACT_PATH.read_text())
except Exception as exc:
    print(f"RUNTIME ATLAS REBUILD CONTRACT: FATAL: {exc}")
    sys.exit(1)

if manifest.get("version") != "bre-thiar-hypnobius-v4.0":
    fail("active manifest must remain bre-thiar-hypnobius-v4.0 for this contract")
if contract.get("version") != 1:
    fail("rebuild contract version must be 1")

targets = contract.get("targets")
if not isinstance(targets, dict):
    fail("contract targets must be an object")
    targets = {}

expected_targets = {"world_houses_atlas", "world_props_atlas", "wayfarer_iron_warden"}
if set(targets) != expected_targets:
    fail(f"contract targets must be exactly {sorted(expected_targets)}")

for key, target in targets.items():
    if isinstance(target, dict):
        validate_target_canvas(target, key)
    else:
        fail(f"target {key} must be an object")

# Houses: destination slots must exactly mirror the live world-atlas manifest.
houses_manifest = manifest.get("worldAtlases", {}).get("houses", {})
houses = targets.get("world_houses_atlas", {}) if isinstance(targets.get("world_houses_atlas"), dict) else {}
if houses.get("format") != "PNG":
    fail("world_houses_atlas format must be PNG")
if houses.get("size") != [578, 336]:
    fail("world_houses_atlas size must remain 578x336")
if houses.get("destination") != houses_manifest.get("cache"):
    fail("world_houses_atlas destination must match manifest houses cache")
house_slots = slots_by_key(houses, "world_houses_atlas")
house_rects = houses_manifest.get("rects", {})
if set(house_slots) != set(house_rects):
    fail("house rebuild slots must exactly match manifest house rect keys")
for key, rect in house_rects.items():
    if house_slots.get(key, {}).get("destinationRect") != rect:
        fail(f"house slot {key} destinationRect must match manifest rect")

# Props/terrain: object slots mirror props rects and the terrain slot mirrors manifest terrain.rect.
props_manifest = manifest.get("worldAtlases", {}).get("props", {})
props = targets.get("world_props_atlas", {}) if isinstance(targets.get("world_props_atlas"), dict) else {}
if props.get("format") != "PNG":
    fail("world_props_atlas format must be PNG")
if props.get("size") != [500, 294]:
    fail("world_props_atlas size must remain 500x294")
if props.get("destination") != props_manifest.get("cache"):
    fail("world_props_atlas destination must match manifest props cache")
if manifest.get("terrain", {}).get("atlas") != "props":
    fail("active terrain atlas must remain props for this rebuild contract")
props_slots = slots_by_key(props, "world_props_atlas")
expected_prop_rects = dict(props_manifest.get("rects", {}))
expected_prop_rects["terrain"] = manifest.get("terrain", {}).get("rect")
if set(props_slots) != set(expected_prop_rects):
    fail("props rebuild slots must exactly match manifest props rects plus terrain")
for key, rect in expected_prop_rects.items():
    if props_slots.get(key, {}).get("destinationRect") != rect:
        fail(f"props slot {key} destinationRect must match active manifest")

# Fighter: four class/gender strips must mirror every live character that points at fighter.
fighter_manifest = manifest.get("characterAtlases", {}).get("fighter", {})
fighter = targets.get("wayfarer_iron_warden", {}) if isinstance(targets.get("wayfarer_iron_warden"), dict) else {}
if fighter.get("format") != "WEBP":
    fail("wayfarer_iron_warden format must be WEBP")
if fighter.get("size") != [256, 1280]:
    fail("wayfarer_iron_warden size must remain 256x1280")
if fighter.get("destination") != fighter_manifest.get("cache"):
    fail("fighter destination must match active manifest fighter cache")

expected_fighter_rects: dict[str, list[int]] = {}
for cls, genders in manifest.get("characters", {}).items():
    for gender, spec in genders.items():
        if spec.get("atlas") == "fighter":
            expected_fighter_rects[f"{cls}_{gender}"] = spec.get("rect")
fighter_slots = slots_by_key(fighter, "wayfarer_iron_warden")
if set(fighter_slots) != set(expected_fighter_rects):
    fail("fighter rebuild slots must exactly match live fighter-backed class/gender entries")
for key, rect in expected_fighter_rects.items():
    if fighter_slots.get(key, {}).get("destinationRect") != rect:
        fail(f"fighter slot {key} destinationRect must match active manifest")

rows = manifest.get("directionRows", {})
expected_rows = [name for name, _ in sorted(rows.items(), key=lambda item: item[1])]
if fighter.get("directionRows") != expected_rows:
    fail("fighter directionRows must match active manifest row order")
if fighter.get("directionCell") != manifest.get("characterCell"):
    fail("fighter directionCell must match active manifest characterCell")
if fighter.get("sourceProvenanceStatus") not in {"unresolved", "verified"}:
    fail("fighter sourceProvenanceStatus must be unresolved or verified")

if errors:
    print("RUNTIME ATLAS REBUILD CONTRACT: FAIL")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("RUNTIME ATLAS REBUILD CONTRACT: PASS")
print("- world house/props output slots match the active v4 manifest")
print("- fighter class/gender strips and direction geometry match the active v4 manifest")
print("- unresolved source mappings remain explicitly null; no crop guessing is encoded")
