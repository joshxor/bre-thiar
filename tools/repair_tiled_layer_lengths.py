#!/usr/bin/env python3
"""Guarded repair for three known malformed finite Tiled tile-layer arrays.

This utility is intentionally narrow. It only accepts the exact malformed
signatures diagnosed in Rowanwood Verge and Old Barrow Approach. It removes
only off-map zero overflow and restores the missing final Old Barrow road row
by continuing the identical two-cell road pattern present in rows 0-10.

Default mode is check-only. Use --write to persist the deterministic repair.
"""
from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
ROWANWOOD = ROOT / "maps/Rowanwood_Verge_v1.tmj"
BARROW = ROOT / "maps/Old_Barrow_Approach_v1.tmj"
BARROW_ROAD_ROW = [0, 0, 0, 0, 0, 0, 0, 3, 3, 0, 0, 0, 0, 0, 0, 0]


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def layer(game_map: dict, name: str) -> dict:
    found = next((item for item in game_map.get("layers", []) if item.get("name") == name), None)
    if found is None or found.get("type") != "tilelayer":
        raise ValueError(f"{name}: expected tilelayer")
    return found


def validate_all_lengths(label: str, game_map: dict) -> None:
    expected = game_map.get("width", 0) * game_map.get("height", 0)
    for item in game_map.get("layers", []):
        if item.get("type") != "tilelayer":
            continue
        actual = len(item.get("data", []))
        if actual != expected:
            raise ValueError(f"{label}:{item.get('name')} has {actual} cells; expected {expected}")


def inspect_and_repair(write: bool) -> bool:
    rowanwood = load(ROWANWOOD)
    barrow = load(BARROW)

    if (rowanwood.get("width"), rowanwood.get("height")) != (18, 14):
        raise ValueError("Rowanwood geometry changed; refusing narrow repair")
    if (barrow.get("width"), barrow.get("height")) != (16, 12):
        raise ValueError("Old Barrow Approach geometry changed; refusing narrow repair")

    rw_swamp = layer(rowanwood, "Swamp")
    b_swamp = layer(barrow, "Swamp")
    b_roads = layer(barrow, "Roads")

    rw_expected = 18 * 14
    b_expected = 16 * 12
    changed = False

    rw_data = list(rw_swamp.get("data", []))
    if len(rw_data) == rw_expected:
        pass
    elif len(rw_data) == rw_expected + 15 and rw_data[rw_expected:] == [0] * 15:
        print("Rowanwood Swamp: removing 15 off-map zero cells")
        rw_swamp["data"] = rw_data[:rw_expected]
        changed = True
    else:
        raise ValueError(
            f"Rowanwood Swamp signature changed: {len(rw_data)} cells; "
            "expected clean 252 or diagnosed 267 with 15 trailing zeroes"
        )

    swamp_data = list(b_swamp.get("data", []))
    if len(swamp_data) == b_expected:
        pass
    elif len(swamp_data) == b_expected + 16 and swamp_data[b_expected:] == [0] * 16:
        print("Old Barrow Swamp: removing one off-map zero row")
        b_swamp["data"] = swamp_data[:b_expected]
        changed = True
    else:
        raise ValueError(
            f"Old Barrow Swamp signature changed: {len(swamp_data)} cells; "
            "expected clean 192 or diagnosed 208 with 16 trailing zeroes"
        )

    road_data = list(b_roads.get("data", []))
    if len(road_data) == b_expected:
        if road_data[-16:] != BARROW_ROAD_ROW:
            raise ValueError("Old Barrow Roads is full-length but final row no longer matches the south-road contract")
    elif len(road_data) == b_expected - 16:
        rows = [road_data[index:index + 16] for index in range(0, len(road_data), 16)]
        if len(rows) != 11 or any(row != BARROW_ROAD_ROW for row in rows):
            raise ValueError("Old Barrow Roads no longer matches the diagnosed 11-row vertical-road signature")
        print("Old Barrow Roads: restoring final south-edge road row")
        b_roads["data"] = road_data + BARROW_ROAD_ROW
        changed = True
    else:
        raise ValueError(
            f"Old Barrow Roads signature changed: {len(road_data)} cells; "
            "expected clean 192 or diagnosed 176"
        )

    if not changed:
        validate_all_lengths("rowanwood", rowanwood)
        validate_all_lengths("old_barrow_approach", barrow)
        print("TILED LAYER REPAIR CHECK: CLEAN")
        return False

    if not write:
        print("TILED LAYER REPAIR CHECK: REPAIR REQUIRED (dry-run; no files written)")
        return True

    validate_all_lengths("rowanwood", rowanwood)
    validate_all_lengths("old_barrow_approach", barrow)
    ROWANWOOD.write_text(json.dumps(rowanwood, ensure_ascii=False, separators=(",", ":")) + "\n")
    BARROW.write_text(json.dumps(barrow, ensure_ascii=False, separators=(",", ":")) + "\n")
    print("TILED LAYER REPAIR: WRITTEN")
    print("- Rowanwood Swamp: 252 cells")
    print("- Old Barrow Swamp: 192 cells")
    print("- Old Barrow Roads: 192 cells with south-edge continuation")
    return True


def main() -> int:
    parser = ArgumentParser(description="Check or repair the diagnosed Bré Thiar Tiled layer-length defects")
    parser.add_argument("--write", action="store_true", help="Persist the exact guarded repair")
    args = parser.parse_args()
    try:
        needs_or_made_change = inspect_and_repair(args.write)
    except Exception as exc:
        print(f"TILED LAYER REPAIR REFUSED: {exc}", file=sys.stderr)
        return 2
    if needs_or_made_change and not args.write:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
