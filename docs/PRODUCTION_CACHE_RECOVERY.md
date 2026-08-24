# Production Runtime Cache Recovery

## Current status

Production validation originally exposed three historically corrupted runtime image caches:

- `assets/runtime-v2/world_houses_atlas.b64`
- `assets/runtime-v2/world_props_atlas.b64`
- `assets/runtime-v2/characters/wayfarer_iron_warden_q88.b64`

The two **world** dependencies are no longer source-blocked. On 2026-08-24 authentic Hypnobius source archives were supplied and inspected:

- `MedievalVillageExteriorv1.0.zip`
  - SHA-256 `9283c11a67b13c7a2254e19551995d9743b8606d339890c0a268b6082fca7468`
- `Dark_Swamp_Starter_Pack_v1.0.zip`
  - SHA-256 `43cb4478dd3b4f80cf9f8e58f66bf68f4e08d37e2618f5d5ee3d9cae5dcf660e`

The original ZIPs remain outside the repository. Their raw 48px-family assets were visually inspected and mapped to the active world vocabulary. House assets are authored composites made only from supplied roof/wall/door/window pixels plus transparency; they are not represented as nonexistent vendor-prebuilt houses.

The **remaining external blocker is the Wayfarer / Iron Warden fighter atlas only**. Its source package/provenance is still unknown. Do not infer that it is Hypnobius merely because the world art is Hypnobius.

## Verified world-atlas rebuild

The source-to-runtime layout is authoritative in:

```text
docs/RUNTIME_ATLAS_REBUILD_CONTRACT.json
```

The deterministic compositor is:

```text
tools/rebuild_world_atlases_from_source_packs.py
```

Dry-run and verify the exact archives/output hashes:

```bash
python tools/rebuild_world_atlases_from_source_packs.py \
  /path/to/MedievalVillageExteriorv1.0.zip \
  /path/to/Dark_Swamp_Starter_Pack_v1.0.zip
```

Optional derived PNG previews outside the repository:

```bash
python tools/rebuild_world_atlases_from_source_packs.py \
  /path/to/MedievalVillageExteriorv1.0.zip \
  /path/to/Dark_Swamp_Starter_Pack_v1.0.zip \
  --preview-dir /tmp/bre-thiar-world-atlas-preview
```

Write only the two production-derived world caches:

```bash
python tools/rebuild_world_atlases_from_source_packs.py \
  /path/to/MedievalVillageExteriorv1.0.zip \
  /path/to/Dark_Swamp_Starter_Pack_v1.0.zip \
  --write
```

Deterministic derived PNG contracts:

| Target | Geometry | SHA-256 |
| --- | ---: | --- |
| House atlas | 578×336 | `f31ab8fb16d4511593af1023eb48e1a09b9b89b63feb095c173a31480a3a7130` |
| Props/terrain atlas | 500×294 | `8a931bc0d4a26b637e0836267689f43a8dad2f8fb021ab18fae7f8714a8bf8f9` |

The script refuses a source archive/member hash mismatch and refuses output drift from these PNG hashes. It never copies source ZIP contents into the repository.

## Fighter recovery status

`assets/runtime-v2/characters/wayfarer_iron_warden_q88.b64` is still corrupted. Reachable Git history was exhaustively checked for:

- a 256×1280 final fighter atlas
- 128×640 class/gender direction strips
- 128×160 direction frames
- historical text identifying a source package

No authentic recovery source was found. The old 192×224 mobile player sheet is different geometry and is not a substitute. The intact Mystic atlas is also not a substitute.

Use the read-only external candidate scanner if additional local backups/source packs become available:

```powershell
python tools/find_runtime_cache_recovery_candidates.py `
  C:\Projects\BreThiar `
  C:\Projects\BreThiar_Backups `
  $env:USERPROFILE\Downloads
```

An exact-geometry match is only a candidate; verify provenance and art before writing anything.

## Validation

The rebuild contract is checked against the live v4 manifest by:

```bash
python tools/validate_runtime_atlas_rebuild_contract.py
```

Before merging production recovery, all of the following must pass:

```bash
python -m pip install Pillow
python tools/validate_runtime_atlas_rebuild_contract.py
python tools/validate_hypnobius_integration.py
python tools/validate_world_continuity.py
python tools/validate_old_road_quest.py
python tools/validate_old_road_act2_contract.py
python tools/validate_old_barrow_interior_readiness.py
python tools/validate_render_profiles.py
node --check bre-thiar-world-live-v4.js
```

The GitHub Actions production-world workflow remains the final merge gate.

## Village spawn correction

The connected village intentionally has exactly two named spawn objects:

- `Player Spawn`
- `North Arrival`

`North Arrival` is required for the reciprocal Rowanwood route and must not be removed to satisfy the superseded one-spawn assumption.

## Never use these recovery shortcuts

- flattened `village.webp` / `village_front.webp`
- the old mobile `player.webp`
- screenshots or concept maps
- guessed/generated pixels
- guessed vendor crop coordinates
- padding/trimming corrupt base64 merely to silence a decoder
- disabling strict image decoding
- substituting Mystic for Wayfarer / Iron Warden
- replacing the established art family solely to make CI green

If authentic fighter source material cannot be located, keep the fighter gate red until an explicitly approved legitimate replacement/re-authoring decision is made.
