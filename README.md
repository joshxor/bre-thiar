# Bré Thiar

Bré Thiar is a separate, original top-down social fantasy MMO prototype inspired by the social depth and four-direction readability of classic online RPGs while using its own world, art, systems, and identity.

## Private mobile test

The repository stays private.

**Launch the current private mobile QA build:**

https://codespaces.new/joshxor/bre-thiar

Create the codespace from `main`. The checked-in dev-container automatically starts the preview server on port `8000`; the repository root redirects to the current `play.html` production-art QA slice.

## Current baseline

- Authoritative Node.js game-server foundation
- Browser/Canvas client
- Map-backed collision and movement
- Independent player, NPC, enemy, and prop entities
- Layered foreground occlusion
- Bré Thiar village, Rowanwood, and Old Barrow production work retained in the standalone project
- Full-quality mobile/web presentation uses the same production visual language as desktop

## Current private QA runtime

`play.html` is the current phone QA entry point. It uses the production-derived Bré Thiar village art, live NPC entities, authoritative collision data, touch movement, interaction, local position saving, movement-distance animation timing, and production-pixel roof/tree occlusion.

The village render cache is reconstructed from verified text chunks stored directly on `main`; it no longer depends on unauthenticated `raw.githubusercontent.com` access, so the repository may remain private. Player art is likewise reconstructed from its checked-in text cache before falling back to the legacy binary copy.

## Project rules

- Bré Thiar remains completely separate from Ebonmere, Ember & Oak, Coolinator Wrath, Greenhollow, and all other projects.
- Do not ship a lower-quality "mobile-lite" art fork.
- Mobile/web optimization may use production-derived render caches for preview delivery, but canonical world/collision data remains map-backed rather than treating flattened images as the map source.
- NPCs and monsters are entities, never painted into canonical environment art.
- Collision must remain derived from authoritative map data.
- Programmer-art/debug-looking maps are not acceptable as finished content.
- Do not change repository visibility merely to enable testing.
