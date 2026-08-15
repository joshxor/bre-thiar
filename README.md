# Bré Thiar

Bré Thiar is a separate, original top-down social fantasy MMO prototype inspired by the social depth and four-direction readability of classic online RPGs while using its own world, art, systems, and identity.

## Current baseline

- Authoritative Node.js game server
- Browser/Canvas client
- Real map-backed collision and movement
- Independent player, NPC, enemy, and prop entities
- Layered foreground occlusion
- Bré Thiar village, Rowanwood, and Old Barrow test content
- Full-quality mobile/web presentation must use the same production visual language as desktop

## Mobile QA

`play.html` is the current phone QA entry point. It uses the production-derived v0.6 Bré Thiar village art, live NPC entities, the authoritative collision grid, touch movement, interaction, local position saving, and production-pixel roof/tree occlusion.

The historical image chunks referenced by `play.html` are pinned to Bré Thiar's own repository history. They are not hosted in or dependent on Coolinator Wrath, Ebonmere, Ember & Oak, or any unrelated project.

Rowanwood and Old Barrow will be added behind the same mobile client after the village presentation passes visual QA.

## Project rules

- Bré Thiar remains completely separate from Ebonmere, Ember & Oak, Coolinator Wrath, Greenhollow, and all other projects.
- Do not ship a lower-quality "mobile-lite" art fork.
- Mobile/web optimization should use caching, chunking, responsive controls, and production-derived render caches—not downgraded replacement art.
- NPCs and monsters are entities, never painted into canonical environment art.
- Collision must remain derived from authoritative map data.
- Programmer-art/debug-looking maps are not acceptable as finished content.
