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

## Connected production world

The active QA runtime now uses three connected canonical Tiled maps:

- `maps/Bre_Thiar_Village_Hub_v1.tmj`
- `maps/Rowanwood_Verge_v1.tmj`
- `maps/Old_Barrow_Approach_v1.tmj`

World continuity is:

`Bré Thiar` north exit → `Rowanwood Verge` south entry → `Old Barrow Approach` south entry

Returning south reverses those connections. The Old Barrow interior is intentionally not routed back into legacy art; the threshold remains closed until that interior receives its own compatible production-art conversion.

The previous native-grid Bré Thiar / Rowanwood / Old Barrow QA remains available at `legacy-world.html` for regression comparison only.

## Current QA runtime

`play.html` loads `bre-thiar-world-live-v3.js`, reconstructs the checked-in Hypnobius world atlases and character atlases in-browser, loads the active Tiled map by zone, derives collision/spawns/exits from map data, supports keyboard/touch movement, class/gender switching, local position persistence, interaction, and Y-sorted world-object/NPC/player rendering.

The generated concept map is **not** used as a runtime background texture. The playable world is reconstructed from actual game assets and authoritative map data.

## Tiled editing

The repository keeps production-derived assets as text caches rather than redistributing the original source archives. To reconstruct the PNGs used by the Tiled tilesets locally:

```bash
python -m pip install Pillow
python tools/materialize_tiled_assets.py
```

Then open any canonical `.tmj` map under `maps/`.

## Validation

Run both validators before changing or shipping the production-art world package:

```bash
python -m pip install Pillow
python tools/validate_hypnobius_integration.py
python tools/validate_world_continuity.py
```

The integration validator checks map geometry/layers/GIDs, world-cache decoding and atlas rectangles, collision/spawn/exit contracts, and all eight class/gender direction strips. The continuity validator checks the connected-zone map contracts and reciprocal Bré Thiar ↔ Rowanwood ↔ Old Barrow Approach transitions.

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
