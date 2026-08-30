/* ============================================================================
   Wolaita Sodo Hospital — theme.js  ·  Light / Dark mode toggle
   ----------------------------------------------------------------------------
   • Loaded in <head> of every page — applies the saved theme BEFORE first
     paint (no flash of light theme).
   • Adds a sun/moon toggle button that i18n.js groups together with the
     language switcher in the topbar (or fixed top-right on auth pages).
   • Persists via localStorage key "mediq_theme" (memory fallback), supports
     ?theme=dark|light override and follows the OS preference until the user
     chooses explicitly.
   ========================================================================== */
(function () {
  "use strict";

  var LS_KEY = "mediq_theme";
  var memory = {};
  var btn = null;
  var cur = "light";

  function sGet(k) { try { return window.localStorage.getItem(k); } catch (e) { return memory[k] || null; } }
  function sSet(k, v) { try { window.localStorage.setItem(k, v); } catch (e) { memory[k] = v; } }

  function preferred() {
    var saved = sGet(LS_KEY);
    if (saved === "dark" || saved === "light") return saved;
    var q = null;
    try { q = new URLSearchParams(location.search).get("theme"); } catch (e) { /* ignore */ }
    if (q === "dark" || q === "light") return q;
    try {
      if (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches) return "dark";
    } catch (e) { /* ignore */ }
    return "light";
  }

  function apply(t) {
    cur = t === "dark" ? "dark" : "light";
    document.documentElement.setAttribute("data-theme", cur);
    document.documentElement.classList.toggle("dark", cur === "dark");
  }

  var SUN = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>';
  var MOON = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></svg>';

  function label() {
    return cur === "dark" ? "Switch to light mode" : "Switch to dark mode";
  }

  function updateBtn() {
    if (!btn) return;
    var dark = cur === "dark";
    btn.innerHTML = dark ? SUN : MOON;
    btn.setAttribute("aria-pressed", dark ? "true" : "false");
    btn.setAttribute("aria-label", "Theme / መልክ");
    btn.title = (window.t && window.t(label())) || label();
  }

  function emit() {
    try { window.dispatchEvent(new CustomEvent("theme:changed", { detail: { theme: cur } })); } catch (e) { /* ignore */ }
  }

  function setTheme(t, persist) {
    if (t === cur && persist) { /* still save */ }
    var root = document.documentElement;
    root.classList.add("theme-anim");
    apply(t);
    if (persist) sSet(LS_KEY, cur);
    updateBtn();
    emit();
    setTimeout(function () { root.classList.remove("theme-anim"); }, 300);
  }

  function toggle() { setTheme(cur === "dark" ? "light" : "dark", true); }

  function place() {
    if (!btn) return;
    if (window.I18N && typeof window.I18N.placeControls === "function") {
      window.I18N.placeControls();       // grouped with the language switcher
      var wrap = document.getElementById("appControls");
      if (wrap && btn.parentNode !== wrap) {
        wrap.appendChild(btn);           // i18n locates the button by id, so make
        window.I18N.placeControls();     // sure it is attached first, then re-arrange
      } else if (!btn.parentNode) {
        document.body.appendChild(btn);  // last resort: needs to be reachable
      }
    } else if (btn.parentNode !== document.body) {
      btn.classList.add("theme-switch-fallback");   // rare: pages without i18n
      document.body.appendChild(btn);
    }
  }

  function build() {
    if (btn || !document.body) return;
    btn = document.createElement("button");
    btn.type = "button";
    btn.id = "themeSwitch";
    btn.className = "theme-switch";
    btn.addEventListener("click", toggle);
    updateBtn();
    place();
  }

  /* ---------- boot: apply before paint ---------- */
  cur = preferred();
  apply(cur);

  document.addEventListener("DOMContentLoaded", build);

  // refresh translated tooltip when the language changes
  document.addEventListener("i18n:changed", updateBtn);
  // re-place if the shell swaps the topbar later
  document.addEventListener("i18n:rescan", function () { if (btn) place(); });

  // public API
  window.Theme = {
    toggle: toggle,
    set: setTheme,
    get: function () { return cur; }
  };

  // follow OS changes until the user picks explicitly
  try {
    if (window.matchMedia) {
      var mq = window.matchMedia("(prefers-color-scheme: dark)");
      var onOS = function (e) { if (!sGet(LS_KEY)) setTheme(e.matches ? "dark" : "light", false); };
      if (mq.addEventListener) mq.addEventListener("change", onOS);
      else if (mq.addListener) mq.addListener(onOS);
    }
  } catch (e) { /* ignore */ }

  // global shortcut Alt+⇧+T toggles the theme (works anywhere)
  document.addEventListener("keydown", function (e) {
    if (e.altKey && e.shiftKey && (e.key === "T" || e.key === "t")) {
      e.preventDefault();
      toggle();
    }
  });
})();
