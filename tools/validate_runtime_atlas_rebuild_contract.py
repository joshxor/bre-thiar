#!/usr/bin/env python3
"""Validate the runtime-atlas rebuild contract against the active v4 manifest."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "bre-thiar-assets-v2.json"
CONTRACT_PATH = ROOT / "docs" / "RUNTIME_ATLAS_REBUILD_CONTRACT.json"

EXPECTED_SOURCE_PACKS = {
    "medieval_village_exterior": (
        "MedievalVillageExteriorv1.0.zip",
        "9283c11a67b13c7a2254e19551995d9743b8606d339890c0a268b6082fca7468",
    ),
    "dark_swamp_starter": (
        "Dark_Swamp_Starter_Pack_v1.0.zip",
        "43cb4478dd3b4f80cf9f8e58f66bf68f4e08d37e2618f5d5ee3d9cae5dcf660e",
    ),
}
EXPECTED_WORLD_OUTPUT_HASHES = {
    "world_houses_atlas": "f31ab8fb16d4511593af1023eb48e1a09b9b89b63feb095c173a31480a3a7130",
    "world_props_atlas": "8a931bc0d4a26b637e0836267689f43a8dad2f8fb021ab18fae7f8714a8bf8f9",
}

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


def sha256_string(value, label: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        fail(f"{label} must be a lowercase 64-character SHA-256")


def validate_source_state(slot: dict, label: str) -> None:
    status = slot.get("sourceStatus")
    if status not in {"unresolved", "verified", "verified_composite"}:
        fail(f"{label} sourceStatus must be unresolved, verified, or verified_composite")
        return
    source_file = slot.get("sourceFile")
    source_rect = slot.get("sourceRect")
    if status == "unresolved":
        if source_file is not None or source_rect is not None:
            fail(f"{label} unresolved source mapping must keep sourceFile/sourceRect null")
    elif status == "verified":
        if not isinstance(source_file, str) or not source_file.strip():
            fail(f"{label} verified mapping requires sourceFile")
        rect_tuple(source_rect, f"{label} sourceRect")
    else:
        if source_file is not None or source_rect is not None:
            fail(f"{label} verified_composite mapping must keep sourceFile/sourceRect null")
        if not isinstance(slot.get("recipe"), str) or not slot["recipe"].strip():
            fail(f"{label} verified_composite mapping requires a non-empty recipe")


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


def slots_by_key(target: dict) -> dict[str, dict]:
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

source_packs = contract.get("sourcePacks")
if not isinstance(source_packs, dict):
    fail("contract sourcePacks must be an object")
    source_packs = {}
if set(source_packs) != set(EXPECTED_SOURCE_PACKS):
    fail(f"contract sourcePacks must be exactly {sorted(EXPECTED_SOURCE_PACKS)}")
for key, (filename, expected_sha) in EXPECTED_SOURCE_PACKS.items():
    spec = source_packs.get(key, {}) if isinstance(source_packs.get(key), dict) else {}
    if spec.get("filename") != filename:
        fail(f"source pack {key} filename must be {filename}")
    if spec.get("sha256") != expected_sha:
        fail(f"source pack {key} SHA-256 must match the verified received archive")
    sha256_string(spec.get("sha256"), f"source pack {key} sha256")
    if spec.get("status") != "verified_received":
        fail(f"source pack {key} status must be verified_received")

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
if houses.get("sourcePackStatus") != "verified_source_received":
    fail("world_houses_atlas sourcePackStatus must be verified_source_received")
if houses.get("rebuildTool") != "tools/rebuild_world_atlases_from_source_packs.py":
    fail("world_houses_atlas rebuildTool must use the verified source-pack compositor")
if houses.get("expectedPngSha256") != EXPECTED_WORLD_OUTPUT_HASHES["world_houses_atlas"]:
    fail("world_houses_atlas expectedPngSha256 must match the verified derived image")
sha256_string(houses.get("expectedPngSha256"), "world_houses_atlas expectedPngSha256")
house_slots = slots_by_key(houses)
house_rects = houses_manifest.get("rects", {})
if set(house_slots) != set(house_rects):
    fail("house rebuild slots must exactly match manifest house rect keys")
for key, rect in house_rects.items():
    if house_slots.get(key, {}).get("destinationRect") != rect:
        fail(f"house slot {key} destinationRect must match manifest rect")
    if house_slots.get(key, {}).get("sourceStatus") != "verified_composite":
        fail(f"house slot {key} must remain a verified_composite source recipe")

# Props/terrain: object slots mirror props rects and the terrain slot mirrors manifest terrain.rect.
props_manifest = manifest.get("worldAtlases", {}).get("props", {})
props = targets.get("world_props_atlas", {}) if isinstance(targets.get("world_props_atlas"), dict) else {}
if props.get("format") != "PNG":
    fail("world_props_atlas format must be PNG")
if props.get("size") != [500, 294]:
    fail("world_props_atlas size must remain 500x294")
if props.get("destination") != props_manifest.get("cache"):
    fail("world_props_atlas destination must match manifest props cache")
if props.get("sourcePackStatus") != "verified_source_received":
    fail("world_props_atlas sourcePackStatus must be verified_source_received")
if props.get("rebuildTool") != "tools/rebuild_world_atlases_from_source_packs.py":
    fail("world_props_atlas rebuildTool must use the verified source-pack compositor")
if props.get("expectedPngSha256") != EXPECTED_WORLD_OUTPUT_HASHES["world_props_atlas"]:
    fail("world_props_atlas expectedPngSha256 must match the verified derived image")
sha256_string(props.get("expectedPngSha256"), "world_props_atlas expectedPngSha256")
if manifest.get("terrain", {}).get("atlas") != "props":
    fail("active terrain atlas must remain props for this rebuild contract")
props_slots = slots_by_key(props)
expected_prop_rects = dict(props_manifest.get("rects", {}))
expected_prop_rects["terrain"] = manifest.get("terrain", {}).get("rect")
if set(props_slots) != set(expected_prop_rects):
    fail("props rebuild slots must exactly match manifest props rects plus terrain")
for key, rect in expected_prop_rects.items():
    if props_slots.get(key, {}).get("destinationRect") != rect:
        fail(f"props slot {key} destinationRect must match active manifest")
    if props_slots.get(key, {}).get("sourceStatus") == "unresolved":
        fail(f"props slot {key} must be verified from the received world source packs")

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
fighter_slots = slots_by_key(fighter)
if set(fighter_slots) != set(expected_fighter_rects):
    fail("fighter rebuild slots must exactly match live fighter-backed class/gender entries")
for key, rect in expected_fighter_rects.items():
    slot = fighter_slots.get(key, {})
    if slot.get("destinationRect") != rect:
        fail(f"fighter slot {key} destinationRect must match active manifest")
    if slot.get("sourceStatus") != "unresolved":
        fail(f"fighter slot {key} must remain unresolved until authentic provenance is recovered")

rows = manifest.get("directionRows", {})
expected_rows = [name for name, _ in sorted(rows.items(), key=lambda item: item[1])]
if fighter.get("directionRows") != expected_rows:
    fail("fighter directionRows must match active manifest row order")
if fighter.get("directionCell") != manifest.get("characterCell"):
    fail("fighter directionCell must match active manifest characterCell")
if fighter.get("sourceProvenanceStatus") != "unresolved":
    fail("fighter sourceProvenanceStatus must remain unresolved until authentic source evidence exists")

if errors:
    print("RUNTIME ATLAS REBUILD CONTRACT: FAIL")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print("RUNTIME ATLAS REBUILD CONTRACT: PASS")
print("- verified Hypnobius world source archive hashes are locked")
print("- world house/props source mappings and output slots match the active v4 manifest")
print("- deterministic world-atlas PNG hashes are locked")
print("- fighter class/gender geometry matches the active v4 manifest and provenance remains unresolved")
