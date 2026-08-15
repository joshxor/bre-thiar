# Bré Thiar — Windows Production Client v0.7.0

This is the Windows-first production client foundation. It deliberately does **not** use the GitHub Pages/mobile renderer.

## Runtime architecture

- Godot 4 desktop client.
- Shared authoritative map JSON (`assets/maps/*.json`).
- 32×32 logical collision cells.
- 60 native outdoor ground metatiles for Bré Thiar + Rowanwood.
- Independent structure/tree back layers.
- Independent NPC/player/enemy entities.
- Separate transparent roof/canopy foreground layers.
- Native Old Barrow terrain atlas.
- Cardinal movement, camera follow, NPC interaction, combat QA, and map transitions.

## Local production bundle

The validated production bundle contains the full v0.6 asset library under `client/assets/` plus the source in this directory. The repository-side source is kept separate from the retired browser/mobile QA path.

## Open on Windows

Install Godot 4.7.x, then import `client/project.godot` and press F6/F5.

QA shortcuts: F1 Bré Thiar, F2 Rowanwood, F3 Old Barrow.

The export preset is configured for `Windows Desktop`; export templates are required to produce the standalone `.exe`.
