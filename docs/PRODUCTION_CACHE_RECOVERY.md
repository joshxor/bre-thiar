# Production Runtime Cache Recovery

## Incident status

The production validation workflow exposed three historically corrupted text-encoded runtime image caches that predate the current Old Barrow work:

- `assets/runtime-v2/world_houses_atlas.b64`
- `assets/runtime-v2/world_props_atlas.b64`
- `assets/runtime-v2/characters/wayfarer_iron_warden_q88.b64`

The strict integration validator is correct to reject these files. Do **not** weaken base64/image validation to make CI green.

The props and fighter files contain literal omitted-text placeholders inside their encoded payloads. The houses payload contains no illegal characters but has an impossible base64 length and does not decode as an image. The fighter WebP header indicates an intended total file size far larger than the committed recoverable bytes, so the missing data cannot be reconstructed honestly from the repository text.

Reachable Git history has now been exhaustively checked in two ways:

1. exact final-atlas geometry search across all reachable refs
2. inventory of every decodable historical image blob looking for reconstructable component geometry

Neither search found a valid house atlas, props atlas, fighter atlas, 128×640 fighter direction strip, or 128×160 fighter direction frame. Historical text/provenance search also did not recover a source package name for Wayfarer / Iron Warden. Git recovery is therefore exhausted unless a previously unreachable external repository/archive is later discovered.

The old mobile village/background images are flattened or use different sprite geometry and are not acceptable recovery sources.

## Authoritative target contracts

The canonical output layouts are machine-readable in:

```text
docs/RUNTIME_ATLAS_REBUILD_CONTRACT.json
```

That file records only facts already established by the active runtime manifest: output dimensions, output cache destinations, named destination slots, and class/gender direction geometry. It deliberately leaves vendor/source filenames and source crop rectangles `unresolved` until authentic source packs are inspected. **Do not guess or infer source crops merely to fill the contract.**

CI validates this contract against the active v4 manifest with:

```bash
python tools/validate_runtime_atlas_rebuild_contract.py
```

Final derived atlas targets remain:

| Target | Format | Geometry | Derived cache destination |
| --- | --- | ---: | --- |
| House atlas | PNG | 578×336 | `assets/runtime-v2/world_houses_atlas.b64` |
| Props/terrain atlas | PNG | 500×294 | `assets/runtime-v2/world_props_atlas.b64` |
| Wayfarer/Iron Warden atlas | WebP | 256×1280 | `assets/runtime-v2/characters/wayfarer_iron_warden_q88.b64` |

The existing Mystic atlas is intact and is **not** part of this recovery incident.

## Authentic source packages currently identified

As of 2026-08-24, Hypnobius' released itch.io pages still list both current outdoor source archives and explicitly permit commercial/personal use and modification while prohibiting redistribution of the source pack:

- `MedievalVillageExteriorv1.0.zip` — 298 kB — 48×48 top-down village exterior assets, raw tilesheets included
- `Dark_Swamp_Starter_Pack_v1.0.zip` — 166 kB — 48×48 / 24×24 swamp terrain and props, raw tilesheets included

Use itch.io's normal download flow. Do not bypass the creator's download handoff, scrape protected files, or commit the original source archives to this repository.

The web-visible purchase pages expose the normal `No thanks, just take me to the downloads` flow, but the archive bytes are not exposed as a static public URL through the project tooling. This is an external source-intake boundary, not a reason to fabricate or scrape the files.

These archive names are **candidate world-art sources**, not proof of individual crop mappings. The Wayfarer / Iron Warden source provenance remains unresolved; do not label that fighter atlas as Hypnobius unless authentic source evidence establishes it.

## Inventory a freshly recovered/downloaded source pack

Before resolving any source crop mapping, run the read-only pack inventory:

```powershell
python tools/inventory_runtime_source_pack.py C:\path\to\MedievalVillageExteriorv1.0.zip
python tools/inventory_runtime_source_pack.py C:\path\to\Dark_Swamp_Starter_Pack_v1.0.zip
```

Machine-readable output:

```powershell
python tools/inventory_runtime_source_pack.py C:\path\to\source.zip --json > source-pack-inventory.json
```

The inventory reads image entries directly from ZIPs without extracting or modifying them. It reports:

- archive entry name
- image format and dimensions
- SHA-256
- byte length
- 48px / 24px grid alignment

Use this inventory plus visual inspection to resolve `sourceFile` and `sourceRect` fields in `docs/RUNTIME_ATLAS_REBUILD_CONTRACT.json`. A mapping is not verified merely because dimensions look plausible.

## Search local workspaces and backups for already-built atlas candidates

Use the read-only final-atlas scanner against likely source locations. It examines ordinary PNG/WebP files and image entries inside ZIP archives without extracting or modifying them.

PowerShell example:

```powershell
python tools/find_runtime_cache_recovery_candidates.py `
  C:\Projects\BreThiar `
  C:\Projects\BreThiar_Backups `
  $env:USERPROFILE\Downloads
```

Machine-readable output:

```powershell
python tools/find_runtime_cache_recovery_candidates.py C:\Projects\BreThiar --json > recovery-candidates.json
```

The scanner only reports geometry matches and SHA-256 hashes. A match is **not** automatically approved; visually/source-review the candidate and confirm that it is the intended independent atlas rather than a flattened preview, mobile derivative, or unrelated image with coincidental dimensions.

## Rebuild a cache only from an approved candidate

If an intact final atlas is recovered, use the guarded rebuild tool in dry-run mode first:

```powershell
python tools/rebuild_runtime_cache_from_candidate.py world_houses_atlas C:\path\to\candidate.png
```

For a candidate stored inside a ZIP:

```powershell
python tools/rebuild_runtime_cache_from_candidate.py world_props_atlas C:\path\to\source.zip --entry "path/in/archive/props.png"
```

The tool prints the candidate SHA-256. Only after verifying the art should the cache be written, and the exact hash must be supplied again:

```powershell
python tools/rebuild_runtime_cache_from_candidate.py world_houses_atlas C:\path\to\candidate.png `
  --write --expected-sha256 <verified-hash>
```

This produces only the production-derived base64 cache. It does not copy the original vendor/source package into the repository.

If only raw vendor tilesheets are recovered, first resolve the source mappings in `docs/RUNTIME_ATLAS_REBUILD_CONTRACT.json`; a deterministic compositor should then build the exact final atlas layout from those verified mappings. Do not hand-splice or eyeball the final canvas.

## Required validation after recovery

Do not merge a cache repair until all of the following pass from the repaired checkout:

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

The original integration validator also contained a stale assumption that Bré Thiar had exactly one spawn. The connected-world production map intentionally has two named spawn objects:

- `Player Spawn`
- `North Arrival`

The validator should require this exact set. `North Arrival` is the reciprocal destination used when returning from Rowanwood and must not be removed to satisfy an obsolete test.

## Never use these as recovery shortcuts

- flattened `village.webp` or `village_front.webp`
- the old mobile `player.webp` sheet, which uses different frame geometry
- screenshots or concept maps
- guessed or generated pixels
- guessed vendor crop coordinates
- base64 padding/trimming that merely silences a decoder
- disabling strict image decoding
- replacing the current art with a different asset family solely to make CI pass

If authentic source material cannot be located, leave CI red and recover/re-download the licensed/free source assets instead of fabricating the missing bytes.
