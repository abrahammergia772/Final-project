/* ============================================================================
   Wolaita Sodo Hospital — i18n.js  ·  የቋንቋ መተርጎሚያ ሞተር (English / አማርኛ)
   ----------------------------------------------------------------------------
   Zero-dependency runtime translator for the whole static frontend (96 pages).

   HOW IT WORKS
   • Loads the Amharic dictionary from  i18n/am.js  (window.I18N_AM).
   • Translates every visible text node by exact match against the dictionary
     ("Doctor Dashboard" → "ሐኪም ዳሽቦርድ"), with a longest-first phrase fallback
     so dynamic strings like "12 patients" still work when "patients" is known.
   • Watches the DOM with a MutationObserver, so content rendered by page
     scripts (tables, mock data, AI results) gets translated automatically.
   • Supports explicit hooks for future use:
        <h1 data-i18n="Doctor Dashboard">          → textContent = t(key)
        <input data-i18n-placeholder="Search…">     → t() into that attribute
        window.t("Patients")                        → dictionary lookup
   • Auto-injects a language button into the topbar (or a floating chip on
     pages without one, e.g. the login page).
   • Persists the choice (guarded localStorage; falls back to memory when
     localStorage is unavailable, e.g. sandboxed iframes).
   • URL override:  ?lang=am  forces Amharic, ?lang=en forces English.

   HOW TO ADD / FIX TRANSLATIONS
   Open  i18n/am.js  and add or edit entries:
        "English source text": "የአማርኛ ትርጉም",
   Load any page with  ?i18n=debug  and watch the console — every string that
   is still English gets logged once, so you can grow the dictionary.
   ========================================================================== */
(function () {
  "use strict";

  var LS_KEY = "mediq_lang";
  var dict = {};        // normalized English -> Amharic
  var keys = [];        // sorted by length desc (phrase fallback)
  var lang = "en";
  var timer = null;
  var busy = false;

  // original values for switching back to English
  var enText = typeof WeakMap === "function" ? new WeakMap() : null;
  var enAttr = typeof WeakMap === "function" ? new WeakMap() : null;

  /* ---------------- storage (localStorage-safe) ---------------- */
  var memory = {};
  function sGet(k) { try { return window.localStorage.getItem(k); } catch (e) { return memory[k] || null; } }
  function sSet(k, v) { try { window.localStorage.setItem(k, v); } catch (e) { memory[k] = v; } }

  /* ---------------- dict loading ---------------- */
  function baseDir() {
    try {
      if (document.currentScript && document.currentScript.src) {
        return document.currentScript.src.replace(/[^/]*$/, "");
      }
    } catch (e) { /* fall through */ }
    var scripts = document.getElementsByTagName("script");
    for (var i = scripts.length - 1; i >= 0; i--) {
      var src = scripts[i].src || "";
      if (/i18n\.js/.test(src)) return src.replace(/[^/]*$/, "");
    }
    return "/assets/js/";
  }

  function loadDict() {
    return new Promise(function (resolve) {
      var s = document.createElement("script");
      s.src = baseDir() + "i18n/am.js";
      s.onload = function () {
        if (window.I18N_AM && typeof window.I18N_AM === "object") {
          for (var k in window.I18N_AM) {
            if (Object.prototype.hasOwnProperty.call(window.I18N_AM, k)) dict[k] = window.I18N_AM[k];
          }
          keys = Object.keys(dict).sort(function (a, b) { return b.length - a.length; });
        }
        resolve();
      };
      s.onerror = resolve; // dictionary optional — app stays English
      document.head.appendChild(s);
    });
  }

  /* ---------------- translation core ---------------- */
  function norm(s) { return String(s == null ? "" : s).replace(/\s+/g, " ").trim(); }
  function hasKey(s) { return Object.prototype.hasOwnProperty.call(dict, norm(s)); }
  function t(key) {
    var k = norm(key);
    if (lang === "am" && Object.prototype.hasOwnProperty.call(dict, k)) return dict[k];
    return key;
  }

  function wordRegex(phrase) {
    // word-boundary-ish match so "On" never hits "Once"
    try {
      var esc = phrase.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      return new RegExp("(?<![A-Za-z])" + esc + "(?![A-Za-z])", "g");
    } catch (e) {
      return null;
    }
  }

  function translateText(s, recordOriginals) {
    if (lang !== "am" || !dict || !s) return s;
    var k = norm(s);
    if (!/[A-Za-z]{2,}/.test(k)) return s; // numbers, codes, dates — leave alone
    var hit = dict[k];
    if (hit !== undefined) return hit;
    // phrase-level fallback: longest keys first
    var out = s;
    for (var i = 0; i < keys.length; i++) {
      var key = keys[i];
      if (key.length < 3 || key.length > s.length) continue;
      var re = wordRegex(key);
      if (!re) continue;
      re.lastIndex = 0;
      if (re.test(out)) { re.lastIndex = 0; out = out.replace(re, dict[key]); }
    }
    return out === s ? s : out;
  }

  var SKIP_TAGS = {
    SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, TEXTAREA: 1, INPUT: 1, SELECT: 1,
    OPTION: 1, CODE: 1, PRE: 1, KBD: 1, SVG: 1, TEMPLATE: 1
  };

  function translateNode(node) {
    if (node.nodeType === 1) { // element
      var tag = node.tagName;
      if (SKIP_TAGS[tag]) return;
      if (node.hasAttribute && node.hasAttribute("data-i18n")) {
        var key = node.getAttribute("data-i18n");
        if (enText && !enText.has(node)) enText.set(node, node.textContent);
        node.textContent = t(key);
        return;
      }
      // attributes
      ["placeholder", "title", "aria-label", "alt"].forEach(function (attr) {
        if (!node.hasAttribute || !node.hasAttribute(attr)) return;
        var val = node.getAttribute(attr);
        if (lang === "am" && hasKey(val)) {
          if (enAttr && !enAttr.has(node)) { enAttr.set(node, {}); }
          if (enAttr) {
            var mem = enAttr.get(node) || {};
            if (!(attr in mem)) mem[attr] = val;
          }
          node.setAttribute(attr, dict[norm(val)]);
        }
      });
      // child text nodes (only leaf text, skip nested structure)
      for (var c = node.firstChild; c; c = c.nextSibling) {
        if (c.nodeType === 3) translateTextNode(c);
        else translateNode(c);
      }
    } else if (node.nodeType === 3) {
      translateTextNode(node);
    }
  }

  function translateTextNode(node) {
    var v = node.nodeValue;
    if (!v || !/[A-Za-z]{2,}/.test(v)) return;
    var out = translateText(v);
    if (out !== v) {
      if (enText && !enText.has(node)) enText.set(node, v);
      node.nodeValue = out;
    }
  }

  function restoreNode(node) {
    if (node.nodeType === 1) {
      if (SKIP_TAGS[node.tagName]) return;
      if (enText && enText.has(node)) { node.textContent = enText.get(node); enText.delete(node); }
      if (enAttr && enAttr.has(node)) {
        var mem = enAttr.get(node);
        for (var attr in mem) if (mem.hasOwnProperty(attr)) node.setAttribute(attr, mem[attr]);
        enAttr.delete(node);
      }
      for (var c = node.firstChild; c; c = c.nextSibling) restoreNode(c);
    } else if (node.nodeType === 3) {
      if (enText && enText.has(node)) { node.nodeValue = enText.get(node); enText.delete(node); }
    }
  }

  /* ---------------- language switcher ---------------- */
  var btn = null;

  function switchLabel() {
    if (!btn) return;
    btn.innerHTML = lang === "am"
      ? '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'
      + ' <b>አማ</b> · English'
      : '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>'
      + ' English · <b>አማርኛ</b>';
    btn.setAttribute("title", lang === "am" ? "Switch to English" : "ወደ አማርኛ ቀይር");
    btn.setAttribute("aria-label", lang === "am" ? "Switch language to English" : "ቋንቋውን ወደ አማርኛ ይቀይሩ");
  }

  function placeSwitcher() {
    if (!btn) {
      btn = document.createElement("button");
      btn.type = "button";
      btn.id = "langSwitch";
      btn.className = "lang-switch";
      btn.addEventListener("click", function () { setLang(lang === "am" ? "en" : "am"); });
    }
    var bar = document.querySelector(".topbar");
    var visible = bar && bar.offsetParent !== null && !bar.classList.contains("hidden");
    if (visible) {
      btn.classList.remove("lang-switch-fixed");
      if (btn.parentNode !== bar) bar.insertBefore(btn, bar.firstChild);
    } else {
      btn.classList.add("lang-switch-fixed");
      if (btn.parentNode !== document.body) document.body.appendChild(btn);
    }
    switchLabel();
  }

  /* ---------------- observer ---------------- */
  var mo = null;
  function schedule() {
    if (timer) return;
    timer = setTimeout(function () {
      timer = null;
      if (busy) { schedule(); return; }
      busy = true;
      try {
        if (lang === "am") translateNode(document.body);
        placeSwitcher();
      } finally { busy = false; }
    }, 120);
  }

  function startObserver() {
    if (!window.MutationObserver || mo) return;
    mo = new MutationObserver(function (muts) {
      if (busy) return;
      for (var i = 0; i < muts.length; i++) {
        var m = muts[i];
        if (m.type === "attributes") {
          var el = m.target;
          var attr = m.attributeName;
          if (el.nodeType === 1 && lang === "am" &&
              (attr === "placeholder" || attr === "title" || attr === "aria-label")) {
            var val = el.getAttribute && el.getAttribute(attr);
            if (val && hasKey(val)) el.setAttribute(attr, dict[norm(val)]);
          }
        } else if (m.type === "characterData") {
          if (lang === "am") translateTextNode(m.target);
        } else if (m.addedNodes && m.addedNodes.length) {
          schedule();
        }
      }
    });
    mo.observe(document.body, {
      childList: true, subtree: true, characterData: true,
      attributes: true, attributeFilter: ["placeholder", "title", "aria-label", "data-i18n"]
    });
  }

  /* ---------------- fonts / setup ---------------- */
  function applyFonts() {
    var id = "langFontLink", cssId = "langFontCss";
    var link = document.getElementById(id);
    if (lang === "am") {
      if (!link) {
        link = document.createElement("link");
        link.id = id; link.rel = "stylesheet"; link.href = "https://fonts.googleapis.com/css2?family=Noto+Sans+Ethiopic:wght@400;500;600;700&display=swap";
        document.head.appendChild(link);
      }
      if (!document.getElementById(cssId)) {
        var st = document.createElement("style");
        st.id = cssId;
        st.textContent = "html[lang=\"am\"] body, html[lang=\"am\"] .sidebar, html[lang=\"am\"] .topbar, " +
          "html[lang=\"am\"] button, html[lang=\"am\"] input, html[lang=\"am\"] select, html[lang=\"am\"] textarea, " +
          "html[lang=\"am\"] th, html[lang=\"am\"] td, html[lang=\"am\"] .btn, html[lang=\"am\"] table, html[lang=\"am\"] .stat-card, html[lang=\"am\"] .panel {" +
          "font-family: 'Noto Sans Ethiopic','Noto Sans','Nyala','Ebrima','Abyssinica SIL','Kefa',system-ui,'Segoe UI',Arial,sans-serif; }";
        document.head.appendChild(st);
      }
    }
  }

  function setLang(l, silent) {
    var next = (l === "am") ? "am" : "en";
    lang = next;
    sSet(LS_KEY, lang);
    document.documentElement.lang = lang;
    document.documentElement.classList.toggle("lang-am", lang === "am");
    busy = true;
    try {
      if (lang === "am") translateNode(document.body);
      else restoreNode(document.body);
      applyFonts();
      placeSwitcher();
    } finally { busy = false; }
    if (!silent) {
      try { window.dispatchEvent(new CustomEvent("i18n:changed", { detail: { lang: lang } })); } catch (e) {}
    }
  }

  /* ---------------- boot ---------------- */
  function missingReport() {
    if (!/i18n=debug/.test(location.search)) return;
    var missing = [];
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        var p = n.parentNode;
        while (p && p.parentNode) {
          if (SKIP_TAGS[p.tagName]) return NodeFilter.FILTER_REJECT;
          p = p.parentNode;
        }
        return /[A-Za-z]{2,}/.test(n.nodeValue) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });
    while (walker.nextNode()) {
      var k = norm(walker.currentNode.nodeValue);
      if (k && !dict[k] && !(window.I18N_MISSING || (window.I18N_MISSING = {})).hasOwnProperty(k)) {
        missing.push(dict[k] === undefined ? k : null);
      }
    }
    var uniq = [];
    for (var i = 0; i < missing.length; i++) {
      if (missing[i] && uniq.indexOf(missing[i]) === -1) uniq.push(missing[i]);
    }
    if (uniq.length) {
      window.I18N = window.I18N || {};
      window.I18N.missing = uniq;
      console.log("[i18n:debug] " + uniq.length + " untranslated strings — add them to assets/js/i18n/am.js:\n" +
        uniq.slice(0, 120).map(function (s) { return '    "' + s.replace(/"/g, '\\"') + '": "",'; }).join("\n"));
    }
  }

  function detectLang() {
    var q = null;
    try { q = new URLSearchParams(location.search).get("lang"); } catch (e) {}
    if (q === "am" || q === "en") return q;
    var stored = sGet(LS_KEY);
    return stored === "am" || stored === "en" ? stored : (navigator.language && navigator.language.indexOf("am") === 0 ? "am" : "en");
  }

  function boot() {
    lang = "en"; // let loadDict run async; apply after
    loadDict().then(function () {
      var pref = detectLang();
      lang = pref === "am" ? "am" : "en";
      document.documentElement.lang = lang;
      document.documentElement.classList.toggle("lang-am", lang === "am");
      document.title = t(document.title);
      busy = true;
      try {
        if (lang === "am") {
          translateNode(document.body);
          mo && mo.disconnect();
        }
        applyFonts();
        placeSwitcher();
        startObserver();
      } finally { busy = false; }
      missingReport();
      try { window.dispatchEvent(new CustomEvent("i18n:ready", { detail: { lang: lang } })); } catch (e) {}
    });
  }

  function injectStyles() {
    if (document.getElementById("langSwitchCss")) return;
    var st = document.createElement("style");
    st.id = "langSwitchCss";
    st.textContent =
      ".lang-switch{border:1px solid #cbd5e1;background:#fff;color:#334155;border-radius:999px;" +
      "padding:7px 13px;font-size:12.5px;font-weight:600;cursor:pointer;display:inline-flex;" +
      "align-items:center;gap:7px;white-space:nowrap;transition:border-color .15s,color .15s;margin-right:8px}" +
      ".lang-switch:hover{border-color:#2563eb;color:#2563eb}" +
      ".lang-switch b{color:#2563eb}" +
      ".lang-switch-fixed{position:fixed;right:16px;bottom:16px;z-index:99999;background:#fff;" +
      "box-shadow:0 6px 22px rgba(0,0,0,.22);border:1px solid #e2e8f0}" +
      "@media(max-width:768px){.lang-switch{padding:6px 10px;font-size:11.5px;margin-right:4px}}" +
      ".topbar .lang-switch{order:-1}";
    document.head.appendChild(st);
  }

  /* API for page scripts */
  window.I18N = {
    t: t,
    translate: function (s) { return translateText(s); },
    setLang: setLang,
    getLang: function () { return lang; },
    dict: function () { return dict; }
  };
  window.t = t;

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { injectStyles(); boot(); });
  } else {
    injectStyles(); boot();
  }

  // global shortcut Alt+⇧+L toggles the language (works anywhere)
  document.addEventListener("keydown", function (e) {
    if (e.altKey && e.shiftKey && (e.key === "L" || e.key === "l")) {
      e.preventDefault();
      setLang(lang === "am" ? "en" : "am");
    }
  });

  // keep the switcher in place when SPA shell swaps the topbar
  document.addEventListener("i18n:rescan", function () { schedule(); });
})();
