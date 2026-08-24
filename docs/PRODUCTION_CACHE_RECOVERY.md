# Production Runtime Cache Recovery

## Incident status

The production validation workflow exposed three historically corrupted text-encoded runtime image caches that predate the current Old Barrow work:

- `assets/runtime-v2/world_houses_atlas.b64`
- `assets/runtime-v2/world_props_atlas.b64`
- `assets/runtime-v2/characters/wayfarer_iron_warden_q88.b64`

The strict integration validator is correct to reject these files. Do **not** weaken base64/image validation to make CI green.

The props and fighter files contain literal omitted-text placeholders inside their encoded payloads. The houses payload contains no illegal characters but has an impossible base64 length and does not decode as an image. The fighter WebP header indicates an intended total file size far larger than the committed recoverable bytes, so the missing data cannot be reconstructed honestly from the repository text.

No intact duplicate has been found in the current repository history or the checked abandoned branches. The old mobile village/background images are flattened or use different sprite geometry and are not acceptable recovery sources.

## Authoritative target contracts

Recovery candidates must match these independent atlas contracts before they are even considered for visual review:

| Target | Format | Geometry | Derived cache destination |
| --- | --- | ---: | --- |
| House atlas | PNG | 578×336 | `assets/runtime-v2/world_houses_atlas.b64` |
| Props/terrain atlas | PNG | 500×294 | `assets/runtime-v2/world_props_atlas.b64` |
| Wayfarer/Iron Warden atlas | WebP | 256×1280 | `assets/runtime-v2/characters/wayfarer_iron_warden_q88.b64` |

The existing Mystic atlas is intact and is **not** part of this recovery incident.

## Search local workspaces and backups

Use the read-only scanner against likely source locations. It examines ordinary PNG/WebP files and image entries inside ZIP archives without extracting or modifying them.

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

After manual source/art verification, use the guarded rebuild tool in dry-run mode first:

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

## Required validation after recovery

Do not merge a cache repair until all of the following pass from the repaired checkout:

```bash
python -m pip install Pillow
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
- base64 padding/trimming that merely silences a decoder
- disabling strict image decoding
- replacing the current art with a different asset family solely to make CI pass

If authentic source material cannot be located, leave CI red and recover/re-download the licensed/free source assets instead of fabricating the missing bytes.
