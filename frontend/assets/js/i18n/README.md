# 🌐 Multi-language system — English / አማርኛ

The whole frontend (all 96 pages) can be switched **between English and Amharic
at runtime** — no page rewrites needed.

| File | Role |
|---|---|
| `assets/js/i18n.js` | Runtime engine (dictionary loader, DOM translator, language switcher, persistence, font support) |
| `assets/js/i18n/am.js` | The Amharic dictionary — **this is where you add translations** |
| `assets/js/i18n/README.md` | This guide |

## Using it

- **Switch language:** a segmented **`EN | አማ`** control (with a globe icon) sits in the
  **topbar-right, next to the notification bell** on every role page, and in the
  **top-right corner** of pages without a topbar (login, signup, admin login, forgot password).
  It sits together with the **dark-mode toggle** in a single control group.
- **Shortcut:** `Alt + Shift + L` toggles the language anywhere; `Alt + Shift + T` toggles the theme.
- **Persistence:** the choice is saved (`localStorage` → key `mediq_lang`, with a
  memory fallback) and applied on every page. It also survives login.
- **URL override:** `?lang=am` or `?lang=en` forces a language for that visit.
- **Auto-detect:** browsers set to Amharic (`navigator.language` = `am`) default to Amharic.

## How translation works

1. `i18n.js` is loaded on every page (injected before `</body>`).
2. It loads the dictionary from `i18n/am.js` (`window.I18N_AM`).
3. It walks the DOM and replaces every visible text node whose text matches a
   dictionary key — exact match first, then a **longest-first phrase pass**, so
   dynamic strings like `"14 patients"` become `"14 ታካሚዎች"` as long as
   `patients` is in the dictionary.
4. `placeholder`, `title`, `aria-label` and `alt` attributes are translated too.
5. A `MutationObserver` re-scans the DOM, so content rendered later by page
   scripts (tables, mock data, AI results, the SPA shell) is translated too.
6. Numbers, dates, codes, names and unit strings are never modified
   (only strings containing Latin letters are considered).

## Adding / fixing translations

Open `assets/js/i18n/am.js` and add a line:

```js
"English source text": "የአማርኛ ትርጉም",
```

**Find what's untranslated:** load any page with `?i18n=debug` and open the
browser console — every string still in English is printed once, ready to paste.

**Explicit hooks (for page authors):**

```html
<h1 data-i18n="Doctor Dashboard">Doctor Dashboard</h1>   <!-- locked translation -->
<input data-i18n-placeholder="Search…">                   <!-- placeholder via dict -->
```

**From JS:** `window.t("Patients")` returns `"ታካሚዎች"` (English when unknown);
`window.I18N.setLang("am")` switches programmatically. An `i18n:changed` event
fires with `{lang}` after every switch.

## Notes & caveats

- The dictionary is **UI-focused** (~750 entries). Patient-generated content,
  free-text notes and AI responses stay in their original language — add keys
  for repeated AI phrases if you want them localized.
- Amharic text renders with **Noto Sans Ethiopic** (loaded from Google Fonts
  when Amharic is active; falls back to Nyala / Ebrima / Abyssinica SIL on
  offline systems).
- Translations are looked up on normalized (whitespace-collapsed) text, so
  formatting differences in HTML don't break matching.
- To extend to a 3rd language: copy `am.js`, translate the keys, and load it
  the same way (the engine supports arbitrary codes — `lang` is stored as-is).

## Light / Dark mode

`assets/js/theme.js` (loaded in the `<head>` of every page) provides the sun/moon
toggle and applies the saved theme **before first paint** (no flash):

- Persisted in localStorage (`mediq_theme`); `?theme=dark|light` forces a visit;
  follows the OS `prefers-color-scheme` until you choose explicitly.
- Dark colors are declared once in `global.css` under `html[data-theme="dark"]`
  (variable re-mapping + a few targeted overrides for hardcoded light values).
- API: `window.Theme.get() / .set("dark") / .toggle()` — and the `theme:changed`
  event fires with `{theme}` after every switch.
