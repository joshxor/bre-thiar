# Bré Thiar World Continuity v1

This change extends the approved Hypnobius/Tiled production world beyond the village.

## Connected world

`Bré Thiar` north exit → `Rowanwood Verge` south entry  
`Rowanwood Verge` north exit → `Old Barrow Approach` south entry

Returning south reverses those links.

## Canonical maps

- `maps/Bre_Thiar_Village_Hub_v1.tmj`
- `maps/Rowanwood_Verge_v1.tmj`
- `maps/Old_Barrow_Approach_v1.tmj`

All three use the same production-derived Hypnobius runtime assets and the same 96px world-cell contract.
Player art remains unchanged at 128×160.

## Rowanwood Verge

- wilderness connector north of Bré Thiar
- ranger lodge / path-guide staging point
- Blackwater stream and bridge
- dense tree perimeter using the existing same-family tree asset at world-appropriate scale
- north route to Old Barrow
- east/west trail hooks reserved for later expansion

## Old Barrow Approach

- darker northern exterior map in the same art family
- flooded approach and timber causeway
- actual Dark Swamp altar asset used as the barrow seal / threshold
- south return to Rowanwood
- interior is intentionally NOT switched back to legacy art; the threshold is the stopping point until the Old Barrow interior receives its own compatible environment conversion

## Runtime

`bre-thiar-world-live-v3.js` loads maps by zone, reads map-backed exits and destination spawns, persists the active zone,
and keeps Y-sorted world/NPC/player rendering. No flattened map screenshot is used.

## Permanent rule

Do not route the player from a converted production-art zone into the legacy renderer merely to make a connection look complete.
Convert the next zone first, then open the route.
