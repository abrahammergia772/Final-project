# Rebuild notes — Wolaita Sodo Hospital HMS

What changed so the thesis demo is modern, consistent, and covers a full hospital day.

## Modern UI

- Inter is loaded (system fonts remain the fallback).
- Table headers are quiet gray, not saturated blue. The accent stays on the active row and buttons.
- Stat cards keep the tinted icon and drop the extra colored bar, except danger cards.
- Badge text was darkened so 11px labels clear WCAG 4.5:1 on their tints. Dark mode keeps its own lighter text.
- Laboratory on the login screen uses info blue, not danger red. The admin link uses the shield icon instead of an emoji.
- Ctrl+K (or the topbar search) opens a command palette of the current role's pages.
- Sidebar, topbar and icons come from one place: `nav.js` + `shell.js`. Role pages no longer duplicate ~9 KB of navigation markup.

## Hospital modules that were missing

Wards and beds, blood bank, ambulance dispatch, cashier, operating theatre, and imaging. Each one runs on demo data stored in `sessionStorage` for the browser tab. Doctors register and self-approve bed requests on `doctor/beds.html`; other staff only see occupied beds. They are not a live clinical record.

## Fixes evaluators would hit first

- `config.js` no longer crashes when `localStorage` is blocked.
- Demo login shows an error if the account is rejected, instead of doing nothing.
- `DEMO_MODE` stays `true` so the frontend works offline.
- Stray `reports: 1` fields were removed from demo accounts.
- `/debug/memory` now requires a signed token.
- `resource` is imported only on Unix, so the API can start on Windows.

## Repo hygiene

- Chart PNGs that no page used were moved to `docs/model-charts/`.
- RandomForest pickles are gitignored. Render already sets `SKIP_RF_MODELS=1`. Restore them with `MODEL_DOWNLOAD_URLS` and `backend/download_models.py` if you want the ensemble.
- `VITE_API_BASE_URL` was removed from `render.yaml`. The API address is `assets/js/config.js`, overridable with `?api=`.

## How to run

```bash
cd mediq-pro-frontend
python3 -m http.server 8000
```

Open the site and use a one-click demo role. Passwords are in the README (`admin@wsh.et` / `admin123`, and the same pattern for the other roles).
