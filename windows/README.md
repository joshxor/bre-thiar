# Bré Thiar — Windows Production Client v0.7.1

Bré Thiar is now a Windows-first native Godot MMO client. The earlier browser/mobile build remains a proof-of-concept only and is not part of the production runtime.

## What is in this package

- Godot 4.7.1 desktop client using the authored v0.6 visual/world package.
- Shared authoritative map JSON (`client/assets/maps/*.json`) with 32×32 logical collision cells.
- 60 authored native overworld metatiles for Bré Thiar + Rowanwood; no scene-sized stretched map screenshot.
- Independent buildings, trees, props, NPCs, monsters, player entities, and transparent roof/canopy foreground layers.
- Native Old Barrow terrain/props and Stonebound Warden encounter.
- Directional idle/walk/Assail player presentation, authoritative boar movement/facing, enemy HP bars, map-bounded camera.
- Authoritative Node 22+ server with accounts, persistence, WebSocket snapshots, multiplayer presence/chat, movement, combat, quests, Path progression, religion, civic voting, inventory/equipment, consumables, death/respawn, and transitions.
- Functional Character / Chronicle panel with equippable gear and usable bread/draught items.
- Protocol/content version handshake so incompatible client/server versions fail clearly instead of corrupting state.

## Fastest Windows test

1. Have **Godot 4.7.1** and **Node.js 22+** available.
2. Double-click `RUN_WINDOWS_DEV.bat`.

The launcher finds Godot, starts the authoritative server on a free localhost port, waits for health, supplies the server URLs to the Godot client, opens a local dev session, and stops the server when the game closes.

## Other one-click tools

- `OPEN_WINDOWS_EDITOR.bat` — opens the Godot project.
- `VALIDATE_WINDOWS.bat` — runs asset/map validation, network-contract checks, Node syntax, the full authoritative multiplayer/progression smoke test, and the Godot headless self-check when Godot is available.
- `BUILD_WINDOWS_EXE.bat` — validates, then exports `BreThiar.exe` and creates a checksummed `BreThiar-Windows-v0.7.1.zip`. Godot 4.7.1 export templates must be installed first.

## Controls

- WASD / Arrow keys — move
- E / Space — interact
- 1 / F / J — Assail
- 2 — Focus
- 3 — learned Path skill
- 4 — Yew Draught
- Enter — local chat
- C / I — Character / Chronicle / inventory
- F1 / F2 / F3 — offline QA jumps to Bré Thiar / Rowanwood / Old Barrow

## Current validation status

Automated non-Godot validation is green, including a real server/WebSocket smoke covering registration/auth/reconnect, remote presence, chat, authoritative movement/combat/transitions/persistence, Maelíth → Old Barrow → Eira progression, civic voting, shrine faith, equipment/effective stats, bread/draught use, all five Path skills, and authoritative death/respawn.

The remaining hard gate is the first real **Godot 4.7.1 runtime/import + visual pass** on a machine where Godot can execute. `client/tests/headless_world_self_check.gd` is already prepared to automate most of that validation.

See `CHANGELOG.md` and `docs/WINDOWS_DIRECTION.md` for the current production rules.
