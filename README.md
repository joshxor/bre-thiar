# Bré Thiar

Bré Thiar is a separate, original top-down social fantasy MMO prototype inspired by the social depth and four-direction readability of classic online RPGs while using its own world, art, systems, and identity.

## Private mobile test

The repository stays private.

**Launch the current private mobile QA build:**

https://codespaces.new/joshxor/bre-thiar

Create the codespace from `main`. The checked-in dev-container automatically starts the preview server on port `8000`; the repository root redirects to the current `play.html` QA slice.

## Current production-art baseline

- Browser/Canvas client with map-backed movement and collision
- Canonical Bré Thiar village map: `maps/Bre_Thiar_Village_Hub_v1.tmj`
- Approved Hypnobius medieval village/cabin/swamp art family implemented as production-derived runtime caches
- 96px runtime world cells from the source 48px world family
- Current 128×160 player sprites remain unchanged
- Wayfarer, Iron Warden, Trail Ranger, and Runekeeper are available in male/female variants
- Four real directional views per current character; walk/combat/cast cycles are not fabricated
- Independent world objects, NPC/player entities, collisions, spawn point, POIs, and four cardinal exits
- Rowanwood / Old Barrow previous native-grid QA retained at `legacy-world.html`

## Current QA runtime

`play.html` is the current Bré Thiar village QA entry point. It loads the canonical Tiled map, reconstructs the checked-in Hypnobius world atlases and character atlases in-browser, derives collision/spawns from map data, supports keyboard/touch movement, class/gender switching, local position persistence, interaction, and Y-sorted world-object/player rendering.

The generated concept map is **not** used as a runtime background texture. The playable village is reconstructed from actual game assets and authoritative map data.

## Tiled editing

The repository keeps production-derived assets as text caches rather than redistributing the original source archives. To reconstruct the PNGs used by the Tiled tilesets locally:

```bash
python -m pip install Pillow
python tools/materialize_tiled_assets.py
```

Then open:

```text
maps/Bre_Thiar_Village_Hub_v1.tmj
```

## Validation

Run the integration validator before changing or shipping the village package:

```bash
python -m pip install Pillow
python tools/validate_hypnobius_integration.py
```

The validator checks map geometry/layers/GIDs, world-cache decoding and atlas rectangles, collision/spawn/exit contracts, and all eight class/gender direction strips.

## Project rules

- Bré Thiar remains completely separate from Ebonmere, Ember & Oak, Coolinator Wrath, Greenhollow, and all other projects.
- Do not ship a lower-quality "mobile-lite" art fork.
- Canonical world/collision data remains map-backed; flattened screenshots are never the authoritative map source.
- NPCs and monsters are entities, never painted into canonical environment art.
- Collision must remain derived from authoritative map data.
- The 128×160 character art is not shrunk to solve environment scale; world art scales around the characters.
- Programmer-art/debug-looking maps are not acceptable as finished content.
- Do not change repository visibility merely to enable testing.
