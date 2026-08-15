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

## Project rules

- Bré Thiar remains completely separate from Ebonmere, Ember & Oak, Coolinator Wrath, Greenhollow, and all other projects.
- Do not ship a lower-quality "mobile-lite" art fork.
- Mobile/web optimization should use caching, chunking, responsive controls, and render caches—not downgraded replacement art.
- NPCs and monsters are entities, never painted into canonical environment art.
- Collision must remain derived from authoritative map data.
- Programmer-art/debug-looking maps are not acceptable as finished content.

## Mobile QA

The temporary mobile QA client is designed to use render caches generated from the real v0.6 production layers while keeping player/NPC/enemy entities, collision, movement, interaction, and foreground occlusion live. The render caches are an optimization only; the canonical world remains layered map data.
