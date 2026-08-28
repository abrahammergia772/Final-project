# MedIQ Pro — Full Audit & Corrections

**Scope:** `mediq-pro-frontend/` (92 HTML pages + CSS/JS) and `backend/`
**Method:** static analysis, link/permission-map validation, JS syntax check, WCAG contrast math on the actual color pairs used.

---

## ✅ What is already good (keep it)

- CSS architecture is genuinely solid: design tokens in `global.css` (`:root` variables), consistent radius/shadow/spacing scale, utility classes, responsive breakpoints, `body.compact` density mode.
- `components.css` covers buttons, badges, modals, toasts, tables, skeletons — most things are built once and reused.
- Backend layout is clean and modular: `routers/` (9 routers), `model_loader.py`, `security.py` (signed tokens), `config.py` (env-driven), lazy-loading + low-memory mode for Render free tier.
- SPA shell (`app.js`) with graceful fallback to standalone pages; delegated event handlers so dropdowns survive DOM swaps.
- No broken internal links; all `nav.js` targets exist; all JS files pass syntax check; no `console.log` leftovers, no `alert()/prompt()`.

The problems below are mostly **consistency and duplication** — classic symptoms of generated/copied pages.

---

## 1. 🔴 ERRORS — with corrections

### 1.1 `config.js` crashes in sandboxed iframes (real bug)
`assets/js/config.js` → `API_BASE_URL` IIFE:
```js
var override = urlParams.get('api') || localStorage.getItem('mediq_api_base');
```
`localStorage` access **throws** `SecurityError` in sandboxed iframes/private contexts. `auth.js` already defends against this with its `MemoryStore` wrapper — `config.js` does not, and it loads *first*, so the whole app dies with `CONFIG is not defined`.

**Correction:**
```js
API_BASE_URL: (function() {
  var urlParams = new URLSearchParams(window.location.search);
  var saved = null;
  try { saved = localStorage.getItem('mediq_api_base'); } catch (e) {}
  return urlParams.get('api') || saved || "https://final-project-bo4l.onrender.com";
})(),
```

### 1.2 One-click demo login fails silently
`assets/js/app.js` (DOMContentLoaded handler):
```js
$$(".demo-role").forEach(b => b.addEventListener("click", () => {
  const role = b.dataset.role;
  login(role + "@mediq.pro", (CONFIG.DEMO_ACCOUNTS[role] || {}).password).then(res => {
    if (res.ok) enterApp();          // ← no else, no catch
  });
}));
```
With `DEMO_MODE: false`, login goes to the Render free tier — which sleeps after 15 min and takes ~50 s to wake. During that window the buttons do **nothing visible**. The login form has the same gap (no `.catch` — spinner button can hang disabled).

**Correction:**
```js
login(role + "@mediq.pro", CONFIG.DEMO_ACCOUNTS[role].password).then(res => {
  if (res.ok) enterApp();
  else showToast(res.error || "Login failed", "error");
}).catch(() => showToast("Backend unreachable — is the API awake?", "error"));
```

### 1.3 `DEMO_MODE: false` contradicts the UI and README
- Login page footer literally prints **“Demo mode active”**.
- README says the frontend is “fully functional right now using built-in demo data”.
- `DEMO_MODE: false` means every action depends on the sleeping Render service.

**Correction (pick one, deliberately):**
- Thesis demo/presentation → `DEMO_MODE: true` (works offline, always).
- Real backend → keep `false` but fix the login footer text to “Connected to live API”.

### 1.4 Broken config data in `DEMO_ACCOUNTS`
```js
admin: { reports: 1, password: "admin123", ... },   // stray "reports: 1"
nurse:  { reports: 1, password: "nurse123", ... },  // same copy-paste artifact
```
**Correction:** delete both `reports: 1` properties — every account object should have the same shape (`password`, `name`, `role`).

### 1.5 11 pages missing `lang` attribute
These pages were regenerated separately (they carry the print-ID-card script) and start with a bare `<html>`:
`admin/patients.html`, `doctor/prescriptions.html`, `laboratory/{ai-analyzer,patients,results}.html`, `manager/patients.html`, `nurse/patients.html`, `patient/{bills,health-card}.html`, `pharmacist/patients.html`, `reception/patients.html`

**Correction:** `<html>` → `<html lang="en">` (screen readers rely on it).

### 1.6 SPA script execution is a fragile `eval` hack
`app.js → runPageScript()` rewrites top-level `const/let` → `var` **line by line** and monkey-patches `EventTarget.prototype.addEventListener` globally. It breaks on:
- destructuring (`const {a, b} = obj` — regex misses it),
- declarations split across lines.

**Correction (minimum):** extend the regex to `const\s+[\[{]` and warn in console when a page script throws. **(Better):** standardize every page on `document.addEventListener("DOMContentLoaded", initPage)` + `window.MedIQPages = { pagename: initFn }` called explicitly by the shell — no `eval`, no patching.

### 1.7 Wrong/duplicate icon: “AI Forecast” uses the truck icon
`assets/js/nav.js` → pharmacist nav: `"Suppliers & POs" = "truck"` **and** `"AI Forecast" = "truck"`. Copy-paste error.
**Correction:** use `chart` or `activity` for AI Forecast (both exist in `icons.js`).

### 1.8 SPA notification dropdown is empty
Static pages ship 3 demo notifications; `buildShell()` in `app.js` renders `#notifMenu` with only a header — users see an empty white box in SPA mode.
**Correction:** render the same 3 demo items in `buildShell()`, or fetch from `/notifications` when live.

### 1.9 `resource` import breaks Windows dev machines
`backend/main.py` imports `resource` (Unix-only) unconditionally — the backend won’t even start on Windows.
**Correction:**
```python
try:
    import resource
except ImportError:      # Windows
    resource = None
```
and guard `_log_memory()` / `/debug/memory` accordingly.

### 1.10 Security notes to state in the thesis (not code bugs)
- Role checks (`checkRoleAccess`) are client-side only — fine, because the backend enforces signed tokens (`security.py`) on all AI/data routers. **Say this explicitly in the report**; reviewers will look for it.
- `CORS_ALLOW_ALL=1` and the public `/debug/memory` endpoint must be disabled/protected before any real deployment.
- Demo passwords in `config.js` are acceptable **only** in demo mode — never reuse them with `DEMO_MODE: false`.

---

## 2. 🏗️ STRUCTURE — corrections

### 2.1 ⚠️ Biggest issue: the app shell exists twice (862 KB of duplicated markup)
- Every one of the 92 role pages hardcodes the full sidebar + topbar (**9.4 KB per page, 862 KB total**).
- `app.js → buildShell()` *regenerates* the identical shell from `nav.js` at runtime.

Two sources of truth for the same UI. Your own last commit — *“fix(frontend): hamburger menu + profile dropdown not working in SPA mode”* — is exactly the class of bug this duplication produces: fix it in one copy, it stays broken in the other.

**Correction (single source of truth, no build tools needed):**
1. In each static page replace the whole `<aside>…</aside>` + `<header>…</header>` with placeholders:
   ```html
   <aside class="sidebar" id="sidebar"></aside>
   ...
   <header class="topbar" id="topbar"></header>
   ```
2. Extract `buildShell()` from `app.js` into `assets/js/shell.js` and call it on every page load (standalone *and* SPA).
3. Sidebar definition lives **only** in `nav.js`. One edit → all 92 pages update.
   Net effect: ~860 KB less markup, ~40 % smaller pages, and the SPA/standalone divergence disappears.

### 2.2 Mixed absolute/relative asset paths (829 absolute refs)
Pages use `/assets/css/...` (server-root absolute — breaks under `file://` and under sub-path hosting such as GitHub Pages `/Final-project/`), while `buildShell()` uses relative `assets/...`. Two conventions in one codebase.

**Correction:** since all pages live either at root (`index.html`) or one folder deep (`doctor/…`), use `../assets/...` in role pages and `assets/...` at root — the helper `basePath()` in `auth.js` already proves the pattern. Then it works from `file://`, any sub-path, and Render.

### 2.3 The ID-card printer is copy-pasted into 6+ pages
The identical `document.write(...)` print-card routine (with ~15 lines of inline CSS) is duplicated in `admin|manager|nurse|pharmacist|laboratory|reception/patients.html` (+ variants in `bills.html`, `health-card.html`).
**Correction:** one `printIdCard(patient)` function in `utils.js`; each page calls it. The print window keeps its inline styles (it’s a separate document) but the *source* exists once.

### 2.4 Backend — fine as is; two tweaks
- `db.py` (231 lines) + `routers/data.py`: verify no SQL string concatenation (use parameterized Supabase/PostgREST queries) — stated for the thesis defense.
- Add a 10-line `tests/test_smoke.py` (`TestClient` hits `/`, `/health`) — universities love it, costs nothing.

### 2.5 Repo layout suggestion
```
Final-project/
├── backend/            ✅ good
├── mediq-pro-frontend/ ✅ good
├── docs/               ← ADD: move the 23 EDA/model PNGs here (out of backend/models/)
└── render.yaml
```

---

## 3. 🎨 DESIGN — corrections

### 3.1 Font declared but never loaded
`--font-main: 'Inter', …` — there is no `<link>` to Inter anywhere, so everyone sees Segoe UI/system fallback.
**Correction:** add to `<head>` (or drop `'Inter'` from the stack):
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### 3.2 Table headers: heavy saturated blue
`.data-table thead th { background: var(--primary); color: #fff }` — every table shouts. This is the single most “2015 Bootstrap admin” element in an otherwise modern UI.
**Correction (calmer, modern):**
```css
.data-table thead th {
  background: #F9FAFB; color: #374151;
  border-bottom: 2px solid var(--border);
}
```
Keep the blue for active sort state only.

### 3.3 Stat cards carry three competing color signals
4 px colored left bar **+** colored icon tile **+** colored trend text on every card makes dashboards noisy.
**Correction:** keep the icon tint + trend color, drop the `::before` bar (or keep the bar only for alert-state cards, e.g. `color-danger`).

### 3.4 Emoji mixed with the SVG icon system
`index.html`: `🔐 Administrator sign in` — you maintain a 76-icon SVG set (`icons.js`); mixing emoji breaks visual consistency across OSes.
**Correction:** replace with `ICONS.shield` / `ICONS["user-check"]`.

### 3.5 Accessibility gaps (quick wins)
| Where | Issue | Correction |
|---|---|---|
| `<button class="hamburger">` (all 92 pages + `buildShell`) | no accessible name | `aria-label="Open menu"` |
| Dropdowns | no keyboard close | add `keydown` Escape → close `.dropdown-menu.show` |
| `.modal-overlay` | no focus trap, no Escape | trap focus, close on Escape (utils.js `showModal`) |
| Login footer `#9CA3AF` text | 2.31:1 contrast | use `var(--gray)` (4.8:1) |
| Form placeholders | 2.54:1 (`#9CA3AF`) | placeholders are hints only — but the login page relies on them; darken to `#6B7280` |

### 3.6 Small inconsistencies
- SPA topbar shows page title from fetched `<title>` — but `document.title` becomes **“Doctor Dashboard — MedIQ Pro — MedIQ Pro”** (app.js appends “ — MedIQ Pro” to a title that already ends with it). Strip the suffix before appending.
- `buildShell()` hamburger/sidebar-toggle lack the `title`/`aria-label` the static versions have.
- 96 pages embed the same ~800-byte favicon data-URI — replace with one `assets/images/favicon.ico` + `<link rel="icon" href="…">` (also makes rebranding a one-file change).

---

## 4. 🌈 COLOR COMBINATIONS — corrections

### 4.1 The palette is coherent but **bypassed by inline styles**
52 unique hex values are hardcoded across HTML/JS, while a proper token set exists in `global.css`. Top offenders: `#6B7280` ×210, `#065F46` ×125, `#ECFDF5` ×124, `#FFFBEB` ×123, `#D97706` ×122, `#DC2626` ×118 — **1,554 inline `style=""` attributes** total, mostly re-creating `.badge-*`, `.avatar-sm.*`, `.feed-icon` and `.qa-icon` classes that already exist.

**Correction:** replace inline color pairs with the existing classes, and add the two missing utility groups to `components.css`:
```css
/* icon tiles currently done inline ~500× */
.tile-info    { background: var(--info-bg);    color: var(--info); }
.tile-success { background: var(--success-bg); color: var(--success); }
.tile-warning { background: var(--warning-bg); color: var(--warning); }
.tile-danger  { background: var(--danger-bg);  color: var(--danger); }
.tile-purple  { background: #F5F3FF;           color: #7C3AED; }
```
Then `style="background:#FEF2F2;color:#DC2626"` → `class="tile-danger"`. A one-time sed/script pass fixes all 92 pages (I can run it for you).

### 4.2 Near-duplicate hues — consolidate
| Currently used | Used for | Keep / change |
|---|---|---|
| `#065F46` `#047857` `#10B981` | success text, shift-day, health-dot | keep `#065F46` (token) + `#10B981` (dot only); drop `#047857` |
| `#0369A1` `#0891B2` | info, shift-half | keep `#0369A1` (token); change shift-half to it |
| `#BE123C` `#0F766E` | settings pages only | replace with `--danger` / `--info` |
| `#E7F0E9` | patient demo icon bg | use `--success-bg` (`#ECFDF5`) |

### 4.3 WCAG contrast failures (measured on the real pairs)
Badges are **11 px text → need 4.5:1**.

| Pair | Ratio | Verdict | Fix |
|---|---|---|---|
| `#D97706` on `#FFFBEB` (badge-warning, shift-evening, avatar-sm.warn) | **3.07** | ✗ | text → `#B45309` (4.95:1) |
| `#DC2626` on `#FEF2F2` (badge-danger, shift-custom) | **4.41** | ✗ (marginal) | text → `#B91C1C` (5.94:1) |
| `#6B7280` on `#F3F4F6` (badge-neutral) | **4.39** | ✗ (marginal) | text → `#374151` |
| `#0891B2` on `#F0F9FF` (shift-half) | **3.45** | ✗ | text → `#0E7490`, or reuse `--info` |
| `#9CA3AF` on `#F3F4F6` (login footer) | **2.31** | ✗✗ | → `var(--gray)` |

Good news: success (7.29), info (5.57), primary (5.68), night (5.20), table header (6.18) all pass — only the warm/neutral pairs need darkening.

### 4.4 Semantic color misuse
- **Red is danger** — but it’s also the *Laboratory role* icon (login demo buttons) and *“custom shift”* chip. Reserve red for critical/alert only → Laboratory → `--info` blue (flask = lab = science); shift-custom → neutral gray.
- **Purple `#7C3AED`** is doing 3 unrelated jobs: avatar gradient, night shift, pharmacist demo icon. Pick one meaning (suggest: night shift only); avatar → solid `var(--primary)`.
- Six categorical shift colors is too many; 4 + neutral reads cleaner: morning=blue, evening=amber, night=purple, day=green, half/custom=neutral gray chips.

### 4.5 One-off tints
`badge-default` hardcodes `#E5E7EB/#374151` instead of `var(--border)`/`#374151→token`. Add `--text-strong: #374151` token and use vars everywhere in CSS too (CSS itself is ~95 % tokenized — finish the job).

---

## 5. 🗑️ UNNECESSARY THINGS — remove / relocate

| # | Item | Size | Why |
|---|---|---|---|
| 1 | RandomForest `.pkl` models (`vitals_rf` 25 MB, `clinical rf` 17 MB, `symptom rf` 13 MB, `lab rf` 6.2 MB, `drug rf` 0.4 MB) | **~62 MB** | `render.yaml` sets `SKIP_RF_MODELS=1` — they are *never loaded* in the deployed config. Keep XGBoost only; move RFs to a Google Drive/release asset link (you already have `download_models.py` for exactly this) |
| 2 | 23 EDA/chart PNGs inside `backend/models/**` (incl. 1.4 MB wordcloud) | ~5 MB | Never referenced by frontend or backend; they’re thesis-report artifacts → `docs/` |
| 3 | `VITE_API_BASE_URL` in `render.yaml` | — | Static site with **no build step** — Vite env vars are never injected. Dead config; the real URL is hardcoded in `config.js`. Remove it (or add a real rewrite step) |
| 4 | 2,117 empty `class=""` attributes | ~30 KB + noise | Generator artifact; strip in one pass |
| 5 | Duplicated ID-card print CSS/JS ×6 | ~10 KB | → one `printIdCard()` in `utils.js` (see 2.3) |
| 6 | `reports: 1` stray props in DEMO_ACCOUNTS | — | See 1.4 |
| 7 | Favicon data-URI ×96 pages | ~75 KB total | → single favicon file (see 3.6) |
| 8 | Empty `SUPABASE_URL/KEY` in frontend `config.js` | — | Dead until set; keep but comment out or gate behind a flag to avoid confusion |
| 9 | `/debug/memory` endpoint | — | Publicly exposes runtime internals; protect with token or remove before production |
| 10 | `admin-login.html` (5.4 KB duplicate of the login form) | optional | Could be `index.html?admin=1`, but as a separate page it’s defensible — your call |

Repo shrinks from **~85 MB → ~20 MB** with items 1–2 alone, and Render deploys get much faster.

---

## 6. Priority order (what I’d fix first)

1. 🔴 `config.js` localStorage crash (1.1) — 3 lines, app-killing bug.
2. 🔴 Silent demo-login failure + `DEMO_MODE` decision (1.2, 1.3) — this is what evaluators will hit first.
3. 🔴 `lang` attribute ×11 (1.5) and stray config props (1.4) — 2-minute fixes.
4. 🏗️ Single-source sidebar (`shell.js`) (2.1) — biggest structural win, kills the whole bug-class of your last commit.
5. 🌈 Badge contrast fixes (4.3) — 5 CSS lines, accessibility win you can show in the thesis.
6. 🌈 Inline-color → class migration + tile utilities (4.1) — one scripted pass.
7. 🗑️ Move RF models + EDA PNGs out of the repo (5.1, 5.2).
8. 🎨 Table header restyle (3.2), Inter font link (3.1), hamburger aria-label (3.5).
