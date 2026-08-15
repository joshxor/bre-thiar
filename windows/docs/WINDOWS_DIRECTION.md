# Windows-first production direction

The mobile/browser proof-of-concept is no longer a production target. Windows is the primary client.

## Non-negotiable visual rules

1. Never flatten an authored zone into one scene-sized screenshot for runtime rendering.
2. The 32px map grid is authoritative for collision/data, not a visual repetition requirement.
3. Outdoor presentation uses authored native metatiles + independent structures/trees + entities + visible foreground roofs/canopies.
4. Foreground occlusion may only come from actual transparent foreground art, never invisible rectangle repaint masks.
5. NPCs and monsters remain independent entities.
6. The Windows build is the visual quality baseline. Any future mobile/web build must derive from it rather than invent a lower-quality art fork.

## v0.7 acceptance target

- Bré Thiar and Rowanwood load as one continuous authored outdoor map.
- Old Barrow loads from the shared map data and native terrain atlas.
- Player uses the directional walk sheet at the approved world scale.
- Shared collision controls movement.
- Map transitions work in both directions.
- NPCs and enemies remain independent runtime entities.
- Foreground roof/canopy sprites are the only world art allowed to occlude the player.
- No browser, GitHub Pages, flattened-map, or mobile-cache dependency exists in the Windows runtime.
