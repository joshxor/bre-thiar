# Production Map Data Repair

## Scope

GitHub Actions exposed malformed finite Tiled tile-layer array lengths in two already-active production zones. This repair changes only tile-layer data cardinality; it does not change map dimensions, object placement, collision objects, spawns, POIs, exits, or zone IDs.

## Diagnosed defects

### Rowanwood Verge

`maps/Rowanwood_Verge_v1.tmj` is an 18×14 map, so every finite tile layer must contain exactly 252 cells.

- `Ground`: 252 — valid
- `Roads`: 252 — valid
- `Swamp`: 267 — invalid

The 15 cells beyond index 251 were all zero and therefore outside the authored map extent. The repair removes only those 15 off-map zero cells.

### Old Barrow Approach

`maps/Old_Barrow_Approach_v1.tmj` is a 16×12 map, so every finite tile layer must contain exactly 192 cells.

- `Ground`: 192 — valid
- `Swamp`: 208 — invalid
- `Roads`: 176 — invalid

The extra `Swamp` row was exactly 16 zero cells beyond the map extent and is removed.

The `Roads` layer contained rows 0 through 10 only. Every existing row used the identical two-cell-wide north/south road pattern in columns 7 and 8:

```text
0 0 0 0 0 0 0 3 3 0 0 0 0 0 0 0
```

The missing row is row 11, the southern edge containing the route back toward Rowanwood. The repair restores row 11 with that same pattern so the authored road reaches the south edge consistently.

## Guarded repair utility

`tools/repair_tiled_layer_lengths.py` refuses to modify files unless they match the exact diagnosed signatures:

- Rowanwood `Swamp`: either clean 252 cells or diagnosed 267 cells with 15 trailing zeroes
- Old Barrow `Swamp`: either clean 192 cells or diagnosed 208 cells with one trailing zero row
- Old Barrow `Roads`: either clean 192 cells with the required final road row, or diagnosed 176 cells where all 11 existing rows match the established vertical-road pattern

Default execution is check-only:

```bash
python tools/repair_tiled_layer_lengths.py
```

A write requires explicit `--write`:

```bash
python tools/repair_tiled_layer_lengths.py --write
```

Production CI runs the utility in check-only mode after the repair.

## Permanent rule

Finite Tiled tile layers must contain exactly `map.width × map.height` cells. Do not rely on runtime truncation, missing-cell defaults, or out-of-bounds data. Validators must continue treating incorrect layer cardinality as a production error.
