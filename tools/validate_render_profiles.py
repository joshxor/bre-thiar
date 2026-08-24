#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "bre-thiar-assets-v2.json"
RUNTIME_PATH = ROOT / "bre-thiar-world-live-v4.js"
PLAY_PATH = ROOT / "play.html"

errors = []


def fail(message):
    errors.append(message)


def load_json(path, label):
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        fail(f"could not parse {label}: {exc}")
        return None


def get_layer(game_map, name):
    return next((layer for layer in game_map.get("layers", []) if layer.get("name") == name), None)


manifest = load_json(MANIFEST_PATH, "world manifest")
if manifest is None:
    print("RENDER PROFILE VALIDATION FAILED")
    for error in errors:
        print("-", error)
    sys.exit(1)

profiles = manifest.get("renderProfiles")
if not isinstance(profiles, dict) or not profiles:
    fail("manifest must define at least one render profile")
    profiles = {}

if manifest.get("version") != "bre-thiar-hypnobius-v4.0":
    fail("manifest version must be bre-thiar-hypnobius-v4.0")

for name, profile in profiles.items():
    tile_layers = profile.get("tileLayers")
    if not isinstance(tile_layers, list) or not tile_layers or not all(isinstance(x, str) and x for x in tile_layers):
        fail(f"render profile {name} must define non-empty tileLayers")
    if not isinstance(profile.get("worldTilesetMatch"), str) or not profile.get("worldTilesetMatch"):
        fail(f"render profile {name} must define worldTilesetMatch")
    if not isinstance(profile.get("worldFirstGid"), int) or profile.get("worldFirstGid", 0) < 1:
        fail(f"render profile {name} must define positive worldFirstGid")
    for field in ("terrainGids", "worldGids"):
        bounds = profile.get(field)
        if not (
            isinstance(bounds, list)
            and len(bounds) == 2
            and all(isinstance(value, int) for value in bounds)
            and 0 <= bounds[0] <= bounds[1]
        ):
            fail(f"render profile {name} must define valid {field} [min,max]")

zones = manifest.get("zones") or {}
if not zones:
    fail("manifest has no zones")

for zone_id, spec in zones.items():
    profile_name = spec.get("renderProfile")
    if profile_name not in profiles:
        fail(f"zone {zone_id} references missing render profile {profile_name!r}")
        continue

    map_value = spec.get("map")
    if not map_value:
        fail(f"zone {zone_id} has no map")
        continue
    map_path = ROOT / map_value
    if not map_path.exists():
        fail(f"zone {zone_id} map is missing: {map_value}")
        continue
    game_map = load_json(map_path, f"{zone_id} map")
    if game_map is None:
        continue

    profile = profiles[profile_name]
    required_layers = set(profile.get("tileLayers", [])) | {"World Objects", "Collision", "Spawns & Triggers"}
    names = {layer.get("name") for layer in game_map.get("layers", [])}
    missing = required_layers - names
    if missing:
        fail(f"zone {zone_id} is missing profile-required layers: {sorted(missing)}")

    terrain_min, terrain_max = profile.get("terrainGids", [0, -1])
    for layer_name in profile.get("tileLayers", []):
        tile_layer = get_layer(game_map, layer_name)
        if not tile_layer:
            continue
        expected_count = game_map.get("width", 0) * game_map.get("height", 0)
        data = tile_layer.get("data", [])
        if len(data) != expected_count:
            fail(f"zone {zone_id}:{layer_name} has {len(data)} cells; expected {expected_count}")
        bad = next((gid for gid in data if gid and not terrain_min <= gid <= terrain_max), None)
        if bad is not None:
            fail(f"zone {zone_id}:{layer_name} uses terrain GID {bad} outside profile range")

    world_min, world_max = profile.get("worldGids", [0, -1])
    world_objects = get_layer(game_map, "World Objects") or {"objects": []}
    bad_world = next(
        (
            obj
            for obj in world_objects.get("objects", [])
            if not world_min <= obj.get("gid", -1) <= world_max
        ),
        None,
    )
    if bad_world:
        fail(
            f"zone {zone_id}:{bad_world.get('name')} uses world GID "
            f"{bad_world.get('gid')} outside profile range"
        )

    match = profile.get("worldTilesetMatch", "")
    if not any(match in str(ref.get("source", "")) for ref in game_map.get("tilesets", [])):
        fail(f"zone {zone_id} has no tileset matching render profile token {match!r}")

runtime = RUNTIME_PATH.read_text() if RUNTIME_PATH.exists() else ""
if not runtime:
    fail("bre-thiar-world-live-v4.js is missing")
else:
    required_runtime_tokens = (
        "function renderProfile()",
        "manifest.renderProfiles",
        "profile.tileLayers",
        "profile.worldTiles",
        "profile.worldTilesetMatch",
        "renderProfile().worldTiles",
    )
    for token in required_runtime_tokens:
        if token not in runtime:
            fail(f"v4 runtime is missing render-profile contract token: {token}")

play = PLAY_PATH.read_text() if PLAY_PATH.exists() else ""
if "bre-thiar-world-live-v4.js?v=hypnobius-world-v4.0" not in play:
    fail("play.html does not load the v4 zone-aware runtime")
if "bre-thiar-world-live-v3.js" in play:
    fail("play.html still references the superseded v3 runtime")

if errors:
    print("RENDER PROFILE VALIDATION FAILED")
    for error in errors:
        print("-", error)
    sys.exit(1)

print("RENDER PROFILE VALIDATION PASSED")
print(f"- {len(profiles)} render profile(s) validated across {len(zones)} zone(s)")
print("- current outdoor maps retain their established layer/GID contracts")
print("- play.html loads the v4 zone-aware runtime")
print("- future interior zones can supply a distinct render profile without changing outdoor rendering")
