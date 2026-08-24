#!/usr/bin/env python3
from pathlib import Path
import json, sys

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/"bre-thiar-assets-v2.json").read_text())
errors=[]

def fail(msg): errors.append(msg)
zones=manifest.get("zones",{})
expected={"bre_thiar","rowanwood","old_barrow_approach"}
if set(zones)!=expected: fail(f"zones mismatch: {set(zones)}")

maps={}
for zid,spec in zones.items():
    p=ROOT/spec["map"]
    if not p.exists():
        fail(f"{zid}: missing map {p}")
        continue
    m=json.loads(p.read_text())
    maps[zid]=m
    if m.get("orientation")!="orthogonal": fail(f"{zid}: not orthogonal")
    if (m.get("tilewidth"),m.get("tileheight"))!=(96,96): fail(f"{zid}: tile size is not 96x96")
    names={l["name"] for l in m.get("layers",[])}
    required={"Ground","Swamp","Roads","World Objects","Collision","Spawns & Triggers"}
    if not required.issubset(names): fail(f"{zid}: missing layers {required-names}")
    for lname in ("Ground","Swamp","Roads"):
        L=next((l for l in m["layers"] if l["name"]==lname),None)
        if L and len(L["data"])!=m["width"]*m["height"]: fail(f"{zid}:{lname} wrong tile count")
        if L:
            bad=[g for g in L["data"] if g not in (0,1,2,3,4,5)]
            if bad: fail(f"{zid}:{lname} invalid terrain GID {bad[0]}")
    wo=next((l for l in m["layers"] if l["name"]=="World Objects"),{"objects":[]})
    for o in wo["objects"]:
        if not 6 <= o["gid"] <= 19: fail(f"{zid}:{o['name']} invalid world GID {o['gid']}")
    tr=next((l for l in m["layers"] if l["name"]=="Spawns & Triggers"),{"objects":[]})
    spawns={o["name"] for o in tr["objects"] if o.get("type")=="spawn"}
    if spec["defaultSpawn"] not in spawns: fail(f"{zid}: missing default spawn {spec['defaultSpawn']}")

# Verify every connected exit destination and spawn.
for zid,m in maps.items():
    tr=next(l for l in m["layers"] if l["name"]=="Spawns & Triggers")
    for o in tr["objects"]:
        if o.get("type")!="exit": continue
        props={p["name"]:p.get("value") for p in o.get("properties",[])}
        dz=props.get("destination_zone")
        if not dz: continue
        if dz not in zones:
            fail(f"{zid}:{o['name']} unknown destination {dz}")
            continue
        ds=props.get("destination_spawn") or zones[dz]["defaultSpawn"]
        dest=maps.get(dz)
        if dest:
            dtr=next(l for l in dest["layers"] if l["name"]=="Spawns & Triggers")
            if not any(x.get("type")=="spawn" and x["name"]==ds for x in dtr["objects"]):
                fail(f"{zid}:{o['name']} missing destination spawn {dz}:{ds}")

contracts=[
    ("bre_thiar","North Exit","rowanwood","South Entry"),
    ("rowanwood","South Exit","bre_thiar","North Arrival"),
    ("rowanwood","North Exit","old_barrow_approach","South Entry"),
    ("old_barrow_approach","South Exit","rowanwood","North Entry"),
]
for zid,name,dz,ds in contracts:
    if zid not in maps: continue
    tr=next(l for l in maps[zid]["layers"] if l["name"]=="Spawns & Triggers")
    o=next((x for x in tr["objects"] if x["name"]==name),None)
    if not o:
        fail(f"missing contract exit {zid}:{name}"); continue
    props={p["name"]:p.get("value") for p in o.get("properties",[])}
    if props.get("destination_zone")!=dz or props.get("destination_spawn")!=ds:
        fail(f"bad contract {zid}:{name}: {props}")

if errors:
    print("WORLD CONTINUITY VALIDATION FAILED")
    for e in errors: print("-",e)
    sys.exit(1)
print("WORLD CONTINUITY VALIDATION PASSED")
for zid,m in maps.items():
    wo=next(l for l in m["layers"] if l["name"]=="World Objects")
    co=next(l for l in m["layers"] if l["name"]=="Collision")
    tr=next(l for l in m["layers"] if l["name"]=="Spawns & Triggers")
    print(f"{zid}: {m['width']}x{m['height']}, {len(wo['objects'])} objects, {len(co['objects'])} collisions, {len(tr['objects'])} triggers")
