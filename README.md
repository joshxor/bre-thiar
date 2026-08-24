# Bré Thiar

Bré Thiar is a separate, original top-down social fantasy MMO prototype inspired by the social depth and four-direction readability of classic online RPGs while using its own world, art, systems, and identity.

## Private mobile test

The repository stays private.

**Launch the current private mobile QA build:**

https://codespaces.new/joshxor/bre-thiar

Create the codespace from `main`. The checked-in dev-container automatically starts the preview server on port `8000`; the repository root redirects to the current `play.html` QA slice.

## Current production-art baseline

- Browser/Canvas client with map-backed movement and collision
- Approved Hypnobius medieval village/cabin/swamp art family implemented as production-derived runtime caches
- 96px runtime world cells from the source 48px world family
- Current 128×160 player sprites remain unchanged
- Wayfarer, Iron Warden, Trail Ranger, and Runekeeper are available in male/female variants
- Four real directional views per current character; walk/combat/cast cycles are not fabricated
- Independent world objects, NPC/player entities, collisions, spawns, POIs, and map-backed exits
- Zone-selected render profiles so future production interiors can use their own authored tile layers and object mappings without changing the outdoor maps

## Connected production world

The active QA runtime uses three connected canonical Tiled maps:

- `maps/Bre_Thiar_Village_Hub_v1.tmj`
- `maps/Rowanwood_Verge_v1.tmj`
- `maps/Old_Barrow_Approach_v1.tmj`

World continuity is:

`Bré Thiar` north exit → `Rowanwood Verge` south entry → `Old Barrow Approach` south entry

Returning south reverses those connections. The Old Barrow interior is intentionally not routed back into legacy art; the threshold remains closed until that interior receives its own compatible production-art conversion.

The previous native-grid Bré Thiar / Rowanwood / Old Barrow QA remains available at `legacy-world.html` for regression comparison only.

## Old Barrow Interior production gate

`Old Barrow Interior` is the next hard production target, but it is not registered as a live zone yet.

The current strongest compatible art source is the released Hypnobius **Medieval Interior - Starter RPG Tileset**: it uses the same 48×48 source scale, is explicitly top-down/Tiled-friendly, and matches the established medieval/Gothic production family. The dedicated Hypnobius **Top-Down Dungeon Interior Tileset** is still in development and is not treated as a shippable dependency.

The approach remains sealed until the actual licensed source package is available for conversion. Do not substitute the legacy renderer, programmer-art dungeon tiles, flattened map imagery, or the older side-scroller Grungy Dungeon packs.

The licensed package can be inspected without copying source art into the repository:

```bash
python tools/inspect_old_barrow_source_pack.py /path/to/source.zip
```

The exact activation and asset-intake contract is documented in `docs/OLD_BARROW_INTERIOR_PRODUCTION_GATE.md`. The save-compatible second-act quest contract is documented in `docs/OLD_ROAD_ACT_II_CONTRACT.md`.

## Current playable quest

`The Old Road` is the first persistent cross-zone quest in the production-art world:

1. Speak with Eira in Bré Thiar.
2. Take the north road into Rowanwood Verge.
3. Find and inspect the Old Rowan.
4. Reach the Old Barrow Approach and examine the Barrow Threshold.
5. Complete the quest and receive the Rowan Charm.

Quest progress is stored with the current local QA save state and is shown in the in-game menu.

Act II remains dormant while the barrow is sealed. When the production interior activates, existing stage-4 Rowan Charm saves must migrate forward instead of being reset or re-rewarded.

## Current QA runtime

`play.html` loads `bre-thiar-world-live-v4.js`, reconstructs the checked-in Hypnobius world atlases and character atlases in-browser, loads the active Tiled map by zone, selects that zone's render profile, derives collision/spawns/exits from map data, supports keyboard/touch movement, class/gender switching, persistent quest/world state, interaction prompts, and Y-sorted world-object/NPC/player rendering.

The current three zones all use `hypnobius_outdoor_v1`, which preserves the existing `Ground` / `Swamp` / `Roads` terrain layers and outdoor `world_objects` mapping exactly. A future Old Barrow Interior profile can supply different authored tile-layer names and world-object mappings without hard-wiring dungeon art into the outdoor renderer.

The generated concept map is **not** used as a runtime background texture. The playable world is reconstructed from actual game assets and authoritative map data.

## Tiled editing

The repository keeps production-derived assets as text caches rather than redistributing the original source archives. To reconstruct the PNGs used by the Tiled tilesets locally:

```bash
python -m pip install Pillow
python tools/materialize_tiled_assets.py
```

Then open any canonical `.tmj` map under `maps/`.

## Validation

Run the validators before changing or shipping the production-art world package:

```bash
python -m pip install Pillow
python tools/validate_hypnobius_integration.py
python tools/validate_world_continuity.py
python tools/validate_old_road_quest.py
python tools/validate_old_road_act2_contract.py
python tools/validate_old_barrow_interior_readiness.py
python tools/validate_render_profiles.py
```

The validators cover asset-cache decoding, map geometry/layers/GIDs, world-object atlas rectangles, collision/spawn/exit contracts, all eight class/gender direction strips, reciprocal connected-zone transitions, the Old Road quest dependency chain, save-compatible Act II activation, the Old Barrow sealed/active production contract, and zone-to-render-profile compatibility.

The Old Barrow and Act II validators are intentionally state-aware. While no production interior is registered they verify that the threshold remains safely sealed and the shipped stage-4 Rowan Charm completion remains authoritative; once `old_barrow_interior` is registered they require a real interior map, production art metadata, valid map-backed layers/spawns, reciprocal routing, save migration, map-backed Act II objectives/encounter metadata, and removal of the exterior gate collision.

## Project rules

- Bré Thiar remains completely separate from Ebonmere, Ember & Oak, Coolinator Wrath, Greenhollow, and all other projects.
- Do not ship a lower-quality "mobile-lite" art fork.
- Canonical world/collision data remains map-backed; flattened screenshots are never the authoritative map source.
- NPCs and monsters are entities, never painted into canonical environment art.
- Collision must remain derived from authoritative map data.
- The 128×160 character art is not shrunk to solve environment scale; world art scales around the characters.
- Do not route a converted production-art zone into the legacy renderer just to make a connection look complete; convert the next zone first, then open the route.
- Programmer-art/debug-looking maps are not acceptable as finished content.
- Do not change repository visibility merely to enable testing.
