# Windows-first production direction

The mobile/browser proof-of-concept is no longer a production target. Windows is the primary client.

## Non-negotiable visual rules

1. Never flatten an authored zone into one scene-sized screenshot for runtime rendering.
2. The 32px map grid is authoritative for collision/data, not a visual repetition requirement.
3. Outdoor presentation uses authored native metatiles + independent structures/trees + entities + visible foreground roofs/canopies.
4. Foreground occlusion may only come from actual transparent foreground art, never invisible rectangle repaint masks.
5. NPCs and monsters remain independent entities.
6. The Windows build is the visual quality baseline. Any future mobile/web build must derive from it rather than invent a lower-quality art fork.

## v0.7.1 production architecture

- Offline mode exists only for native visual/map QA; online play is server-authoritative.
- The Godot client may predict local cardinal movement for responsiveness, but snapshots own final position, zone, HP/MP, enemy state, inventory, equipment, quests, Path, faith, and civic state.
- Inventory/equipment UI must issue server actions; client-side inventory mutation is forbidden.
- Displayed combat ATK/DEF comes from server-provided effective values including equipment bonuses.
- Protocol/content versions are explicit and incompatible sessions must be rejected.
- Windows release builds are produced through `BUILD_WINDOWS_EXE.bat`; do not hand-package arbitrary editor folders as releases.
