# Private mobile access

The repository stays **private**. Do not change its visibility just to test the mobile build.

## One-click private test

Open:

https://codespaces.new/joshxor/bre-thiar

Create the codespace from `main`. The repository's `.devcontainer/devcontainer.json` starts a small HTTP server on port `8000` and forwards that port automatically. GitHub Codespaces forwarded ports are private by default, so the preview remains tied to the authenticated codespace owner.

The preview root redirects to `play.html`, which is the current production-art Bré Thiar mobile QA slice.

If the browser does not open the preview automatically, open the **PORTS** tab in the codespace and tap the globe/open-in-browser icon for port `8000`.

## Current runtime path

- `index.html` → `play.html`
- `play.html` → `village-live.js`
- Village background is reconstructed from the verified `mobile/vb_00.txt` … `mobile/vb_06.txt` cache pieces stored on `main`.
- Player art loads from `mobile/player_q85.b64` first, avoiding the connector-truncated binary copy.
- NPCs remain independent runtime entities.

## Privacy rule

Do not publish a GitHub Pages site or change repository visibility unless the owner explicitly requests it later.
