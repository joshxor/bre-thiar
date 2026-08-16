# Bré Thiar Windows Changelog

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
