#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
MAPS = ROOT / "maps"
RUNTIME = ROOT / "bre-thiar-world-live-v4.js"

required_maps = {
    "bre_thiar": "Bre_Thiar_Village_Hub_v1.tmj",
    "rowanwood": "Rowanwood_Verge_v1.tmj",
    "old_barrow_approach": "Old_Barrow_Approach_v1.tmj",
}
loaded = {}
for key, name in required_maps.items():
    p = MAPS / name
    if not p.exists():
        raise SystemExit(f"Missing map: {p}")
    loaded[key] = json.loads(p.read_text())

def trigger_names(m):
    layer = next((x for x in m["layers"] if x["name"] == "Spawns & Triggers"), None)
    if not layer:
        raise SystemExit("Missing Spawns & Triggers layer")
    return {o["name"]: o for o in layer.get("objects", [])}

bre = trigger_names(loaded["bre_thiar"])
row = trigger_names(loaded["rowanwood"])
bar = trigger_names(loaded["old_barrow_approach"])

for name, table in [
    ("North Exit", bre),
    ("Old Rowan", row),
    ("North Exit", row),
    ("Barrow Threshold", bar),
]:
    if name not in table:
        raise SystemExit(f"Quest dependency missing: {name}")

def props(o):
    return {p["name"]: p["value"] for p in o.get("properties", [])}

assert props(bre["North Exit"]).get("destination_zone") == "rowanwood"
assert props(row["North Exit"]).get("destination_zone") == "old_barrow_approach"

src = RUNTIME.read_text()
required_tokens = [
    "title:'The Old Road'",
    "questObjective()",
    "setupQuestMenu()",
    "questOnZoneEntered",
    "advanceQuest",
    "n.name==='Eira'",
    "n.name==='Old Rowan'",
    "n.name==='Barrow Threshold'",
    "reward='Rowan Charm'",
    "quest.status==='completed'",
]
for token in required_tokens:
    if token not in src:
        raise SystemExit(f"Quest runtime contract missing: {token}")

if "walk/combat cycles are not faked" not in src:
    raise SystemExit("Animation honesty contract missing")

print("OLD ROAD QUEST VALIDATION PASSED")
print("Runtime: bre-thiar-world-live-v4.js")
print("Route: Bré Thiar -> Rowanwood Verge -> Old Barrow Approach")
print("Stages: Eira -> Old Rowan -> Barrow Threshold")
print("Reward: Rowan Charm")
