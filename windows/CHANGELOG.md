# Bré Thiar Windows Changelog

## v0.7.2 — Persistence, inventory, and network hardening

- Character/Chronicle panel now exposes server-authoritative equipment and consumable actions.
- Effective ATK/DEF is sent by the server after equipment bonuses and displayed by Windows.
- Added all-five-Path authoritative behavior matrix plus equipment/consumable regression coverage.
- Added validated `store.json.bak` recovery and incomplete-v6 character normalization.
- Added safe-zone/position recovery for malformed or stale saves.
- Added 64 KiB WebSocket message ceiling with an oversized-frame regression test.
- Added a generous per-connection inbound action rate limit with flood-client regression coverage.
- Added native NPC progression/service markers for Maelíth, Eira, Brannoc, and Siofra from authoritative quest/civic/faith state.
- Build/protocol/content diagnostics are explicit; server version contract is now derived from `BUILD_INFO.json`.
- Added map-bounded camera assertions and inventory-control assertions to the prepared Godot headless self-check.

## v0.7.1 — Native Windows authority hardening

- Made the Godot Windows client the production path; browser/mobile remains proof-of-concept only.
- Uses the authored v0.6 environment package: 60 overworld ground metatiles, independent structures, transparent foreground layers, NPCs, enemies, Rowanwood, Bré Thiar, and Old Barrow.
- Wired the Godot client to the authoritative Node server with login/register, signed sessions, WebSocket snapshots, remote-player interpolation, chat, authoritative movement, transitions, combat, quests, civic state, and persistence.
- Added protocol/content version handshake to reject incompatible client/server combinations.
- Added directional idle, walk, and Assail presentation; authoritative boar facing/movement animation; enemy HP bars; map-bounded camera; Chronicle objective HUD.
- Added functional Character / Chronicle inventory actions: equip shortsword, Waycloak, and Stone-Knot Charm; eat bread; use Yew Draught.
- Server snapshots now report effective ATK/DEF after equipped gear bonuses.
- Fixed civic progression dead-end, early Warden quest skip, pre-farmed tusk progression, consumable feedback, death/transition input persistence, and enemy home-return collision.
- Added all-five-Path authoritative regression coverage: Cleave, Ember Bolt, Mending, Snare, Palm Strike.
- Added deterministic Godot headless world self-check (runs automatically when Godot is available).
- Added one-click Windows dev launch, editor launch, validation, and release export scripts.

### Validation currently passing without a local Godot binary

- Windows asset/map/project validation.
- Network contract validation.
- Node syntax validation.
- Real authoritative multiplayer smoke: auth/reconnect, presence/chat, movement, combat, transitions, persistence, Maelíth → Barrow → Eira progression, civic vote, faith, equipment/effective stats, consumables, all five Path skills, and death/respawn.

### Remaining local-PC gate

- Run the actual Godot 4.7.1 scene/importer and visually inspect native layer composition.
- Run `BUILD_WINDOWS_EXE.bat` after Godot 4.7.1 export templates are installed.
