# Old Barrow Interior — Production Gate

## Current state

The Old Barrow Interior is **not active yet**. `Old Barrow Approach` remains the northern end of the connected production world and the threshold must stay sealed until a real compatible top-down interior art package has been ingested and converted for the live Tiled/Canvas runtime.

This is intentional. Do not connect the threshold to `legacy-world.html`, do not paint a fake dungeon with programmer tiles, and do not use the old side-scroller dungeon micro-packs simply because they are available.

Run the current state guard with:

```bash
python tools/validate_old_barrow_interior_readiness.py
```

While the production interior is absent, a passing result means the exterior threshold POI and blocking barrow-gate collision are still intact and there is no accidental live route into a missing zone.

## Compatible production art

The strongest currently identified source is **Hypnobius — Medieval Interior: Starter RPG Tileset**.

Why it fits the existing Bré Thiar production baseline:

- same artist family already used for Bré Thiar production environment art
- 48×48 source tiles, matching the current source-world scale
- explicitly top-down
- raw PNG support for engines such as Tiled
- Gothic/medieval stone, floor, wall, stair, balcony, and decor vocabulary suitable for an old barrow / ritual crypt conversion
- can be scaled to the established 96×96 runtime world cell without shrinking the 128×160 characters

The dedicated Hypnobius **Top-Down Dungeon Interior Tileset** is still listed as in development as of 2026-08-24, so it is not a shippable dependency yet.

The older Hypnobius Grungy Dungeon wall/floor/props series is a side-scroller/platformer family and must **not** be treated as the production Old Barrow solution.

## Asset intake rule

Do not add an interior zone to `bre-thiar-assets-v2.json` until the actual licensed source package is available for conversion.

When source art is available:

1. Keep the original purchased/source archive outside the repository.
2. Convert only the runtime material required by the game into the existing production-derived cache workflow.
3. Preserve the source-family scale: 48×48 source art → 96×96 runtime world cells.
4. Do not shrink or redraw the established 128×160 player characters to make the environment fit.
5. Create the canonical map as `maps/Old_Barrow_Interior_v1.tmj`.
6. Keep collision, spawns, exits, POIs, encounters, and objective triggers map-backed.
7. Register the new zone as `old_barrow_interior` only after its map and runtime art actually load.
8. Replace the exterior seal collision with a reciprocal approach/interior exit only in the same production change that activates the interior.
9. Re-run the existing world, quest, art, and interior-readiness validators before merge.

## Interior gameplay target

The first production interior should be a real explorable dungeon layer, not a single decorative room. It should support the second act of **The Old Road** with enough spatial separation for exploration and combat progression.

Target structure:

- **Threshold / Entry Chamber** — establishes the interior visual language and provides the reciprocal exit back to Old Barrow Approach.
- **Burial Passages** — branching traversal, blocked sightlines, minor enemy pockets, and environmental storytelling.
- **Objective Rooms** — at least two distinct chambers that make the quest ask the player to explore rather than walk straight to the boss.
- **Stonebound Warden Hall** — a readable arena with enough movement space for the planned encounter and future combat telegraphs.
- **Sealed Deeper Route** — an authored endpoint that can later connect to additional barrow depth without pretending unfinished content already exists.

Exact encounter scripting remains downstream of the environment conversion. The environment must first be visually credible, collision-safe, and fully connected in the production renderer.

## Activation contract

Once `old_barrow_interior` is registered, `tools/validate_old_barrow_interior_readiness.py` changes behavior automatically and requires:

- `maps/Old_Barrow_Interior_v1.tmj`
- orthogonal map orientation
- established 96×96 runtime tile scale
- `zone_id=old_barrow_interior`
- `map_role=dungeon_interior`
- a real, non-placeholder, non-legacy `art_family`
- at least one visible authored tile layer
- `World Objects`, `Collision`, and `Spawns & Triggers` layers
- a valid default spawn
- a route from Old Barrow Approach into the interior
- a reciprocal route from the interior back to Old Barrow Approach
- removal of the exterior `Old Barrow Seal Footprint` / `barrow_gate` collision once the interior is live

## Do not resurrect

The following are explicitly rejected for this production target:

- legacy renderer routing
- flattened screenshot backgrounds as canonical maps
- placeholder dungeon tiles
- fake hand-drawn stone squares created only to claim the zone is connected
- side-scroller dungeon art repurposed as if it were a top-down interior set
- painted-in NPCs or enemies
- hard-coded collision that diverges from the Tiled map

The barrow should remain closed longer rather than open at a lower visual or architectural standard.
