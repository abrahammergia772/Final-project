/* ============================================================
   Wolaita Sodo Hospital — shell.js
   Single source of truth for the sidebar, topbar and command
   palette. Standalone role pages and the SPA (app.js) both
   call buildShell(), so navigation is defined only in nav.js.
   ============================================================ */
(function () {
  "use strict";

  function icon(name) {
    var I = window.ICONS || {};
    return I[name] || "";
  }

  function asset(path) {
    var base = (typeof basePath === "function") ? basePath() : "";
    return base + path;
  }

  function roleFromPath() {
    var m = (location.pathname || "").match(/\/(admin|manager|doctor|nurse|pharmacist|laboratory|reception|patient)\//);
    if (m) return m[1];
    return (typeof getUserRole === "function") ? getUserRole() : null;
  }

  function pageFile() {
    return (location.pathname || "").split("/").pop() || "";
  }

  function pageTitle() {
    var tb = document.getElementById("topbar");
    if (tb && tb.getAttribute("data-title")) return tb.getAttribute("data-title");
    var h = document.querySelector("h1.page-title");
    if (h && h.textContent.trim() && h.id !== "topbarTitle") return h.textContent.trim();
    return (document.title || "Dashboard").replace(/\s*[—-]\s*(Wolaita Sodo Hospital|MedIQ Pro)\s*$/, "") || "Dashboard";
  }

  function loginVisible() {
    var lv = document.getElementById("loginView");
    return !!(lv && !lv.classList.contains("hidden"));
  }

  var DEMO_NOTIFS = [
    { icon: "alert", cls: "tile-danger", title: "3 critical patient alerts", sub: "Flagged by the vitals AI" },
    { icon: "package", cls: "tile-warning", title: "4 items low in stock", sub: "Pharmacy reorder suggested" },
    { icon: "check", cls: "tile-success", title: "AI modules online", sub: "All 7 modules passed health check" }
  ];

  function notifHtml() {
    return DEMO_NOTIFS.map(function (n) {
      return '<div class="dd-item"><div class="feed-icon ' + n.cls + '">' + icon(n.icon) +
        '</div><div class="feed-text"><div class="dd-title">' + n.title + '</div><div class="dd-sub">' + n.sub + "</div></div></div>";
    }).join("");
  }

  function buildShell(role) {
    role = role || roleFromPath() || "";
    var cfg = (window.NAV_ROLES || {})[role] || { label: role, nav: [] };
    var perm = (window.NAV_PERM_MAP || {})[role] || {};
    var sb = document.getElementById("sidebar");
    var tb = document.getElementById("topbar");
    if (!sb || !tb) return;

    var spa = window.SPA && window.SPA.mode;
    var cur = pageFile();
    var html = '<button class="sidebar-toggle" id="sidebarToggle" type="button" title="Collapse menu" aria-label="Collapse menu">' + icon("chevron-left") + "</button>";
    html += '<div class="sidebar-logo"><img src="' + asset("assets/images/logo-mark.png") + '" alt="Wolaita Sodo Hospital"><div class="logo-text"><div class="brand">Wolaita Sodo Hospital</div><div class="tag">Management System</div></div></div>';
    html += '<nav class="sidebar-nav" aria-label="Primary">';
    (cfg.nav || []).forEach(function (section) {
      html += '<div class="nav-section-label">' + section[0] + "</div>";
      (section[1] || []).forEach(function (item) {
        var href = item[0], label = item[1], ic = item[2];
        var p = perm[href] || "";
        var file = String(href).split("?")[0].split("/").pop();
        var active = !spa && cur === file ? " active" : "";
        html += '<a class="nav-link' + active + '" href="' + href + '"' +
          (p ? ' data-perm="' + p + '"' : "") + ' data-close-menu>' +
          icon(ic) + '<span class="nav-label">' + label + "</span></a>";
      });
    });
    html += '<div class="nav-section-label">MESSAGES</div>';
    html += '<a class="nav-link" href="messages.html" data-perm="messages" data-close-menu>' + icon("mail") + '<span class="nav-label">Messages</span></a>';
    html += '<div class="nav-section-label">ACCOUNT</div>';
    html += '<a class="nav-link" href="settings.html" data-perm="settings" data-close-menu>' + icon("settings") + '<span class="nav-label">Settings</span></a>';
    html += "</nav>";
    html += '<div class="sidebar-footer"><div class="user-box"><span class="avatar" data-user-initials>…</span><div class="u-meta"><div class="u-name" data-user-name>Loading…</div><div class="u-role" data-user-role></div></div>' +
      '<button class="btn-icon u-logout" type="button" data-logout title="Log out" aria-label="Log out">' + icon("logout") + '<span class="u-logout-label">Log out</span></button></div></div>';
    sb.innerHTML = html;

    var title = pageTitle();
    var top = '<div class="topbar-left"><button class="hamburger" id="hamburger" type="button" aria-label="Open menu" aria-controls="sidebar" aria-expanded="false">' +
      icon("menu") + '</button><h1 class="page-title" id="topbarTitle">' + title + "</h1></div>";
    top += '<div class="topbar-right">';
    top += '<button class="icon-btn cmd-btn" id="cmdOpen" type="button" aria-label="Search pages" title="Search pages (Ctrl K)">' + icon("search") + "</button>";
    top += '<div class="topbar-search"><button type="button" class="search-trigger" id="searchTrigger" aria-label="Search pages">' +
      icon("search") + "<span>Search pages</span><kbd>Ctrl K</kbd></button></div>";
    top += '<div class="dropdown"><button class="icon-btn" type="button" data-dropdown-toggle="#notifMenu" aria-label="Notifications" aria-haspopup="true" aria-expanded="false">' +
      icon("bell") + '<span class="notif-dot"></span></button><div class="dropdown-menu" id="notifMenu" role="menu"><div class="dd-header">Notifications</div>' +
      notifHtml() + '<div class="dd-footer"><a href="#" onclick="event.preventDefault();if(window.showToast)showToast(\'All notifications shown\',\'info\')">View all</a></div></div></div>';
    top += '<div class="dropdown"><button class="topbar-avatar" type="button" data-dropdown-toggle="#profileMenu" aria-label="Account menu" aria-haspopup="true">' +
      '<span class="avatar" data-user-initials>…</span><div class="hide-sm"><div class="t-name" data-user-name>Loading…</div><div class="t-role" data-user-role></div></div></button>' +
      '<div class="dropdown-menu" id="profileMenu" role="menu"><div class="dd-header">Account</div><div class="dd-item" data-logout>' +
      icon("logout") + "<span>Log out</span></div></div></div>";
    top += "</div>";
    tb.innerHTML = top;
    tb.setAttribute("data-title", title);

    ensurePalette();
    try { document.dispatchEvent(new CustomEvent("i18n:rescan")); } catch (e) {}
    if (typeof initAuthUI === "function") initAuthUI();
  }

  window.buildShell = buildShell;
  window.MedIQShell = { build: buildShell, openPalette: function () { openPalette(); } };

  /* ---------- Command palette ---------- */
  var palette = null, input = null, list = null, items = [], active = 0;

  function collectItems() {
    var role = (typeof getUserRole === "function" && getUserRole()) || roleFromPath();
    var cfg = (window.NAV_ROLES || {})[role] || { nav: [] };
    var out = [];
    (cfg.nav || []).forEach(function (section) {
      (section[1] || []).forEach(function (item) {
        out.push({ href: item[0], label: item[1], icon: item[2], section: section[0] });
      });
    });
    out.push({ href: "messages.html", label: "Messages", icon: "mail", section: "MESSAGES" });
    out.push({ href: "settings.html", label: "Settings", icon: "settings", section: "ACCOUNT" });
    return out;
  }

  function ensurePalette() {
    if (document.getElementById("cmdPalette")) {
      palette = document.getElementById("cmdPalette");
      input = document.getElementById("cmdInput");
      list = document.getElementById("cmdList");
      return;
    }
    var el = document.createElement("div");
    el.id = "cmdPalette";
    el.className = "cmd-overlay";
    el.hidden = true;
    el.innerHTML = '<div class="cmd-modal" role="dialog" aria-modal="true" aria-label="Search pages">' +
      '<div class="cmd-input-wrap">' + icon("search") +
      '<input id="cmdInput" class="cmd-input" placeholder="Jump to a page…" autocomplete="off" aria-label="Search pages" />' +
      '<kbd class="cmd-esc">Esc</kbd></div><div class="cmd-list" id="cmdList" role="listbox"></div>' +
      '<div class="cmd-foot"><span>↑↓ navigate</span><span>Enter open</span><span>Esc close</span></div></div>';
    document.body.appendChild(el);
    palette = el;
    input = el.querySelector("#cmdInput");
    list = el.querySelector("#cmdList");
    el.addEventListener("click", function (e) { if (e.target === el) closePalette(); });
    input.addEventListener("input", function () { active = 0; renderList(); });
    input.addEventListener("keydown", onInputKey);
  }

  function canPalette() {
    if (loginVisible()) return false;
    return !!(document.getElementById("sidebar") || (window.SPA && window.SPA.mode));
  }

  function openPalette() {
    if (!canPalette()) return;
    ensurePalette();
    items = collectItems();
    active = 0;
    input.value = "";
    palette.hidden = false;
    document.body.classList.add("cmd-open");
    renderList();
    setTimeout(function () { input.focus(); }, 30);
  }

  function closePalette() {
    if (!palette) return;
    palette.hidden = true;
    document.body.classList.remove("cmd-open");
  }

  function renderList() {
    if (!list) return;
    var q = (input.value || "").toLowerCase().trim();
    var shown = items.filter(function (it) {
      return !q || it.label.toLowerCase().indexOf(q) >= 0 || String(it.section).toLowerCase().indexOf(q) >= 0;
    });
    if (active >= shown.length) active = 0;
    list._shown = shown;
    if (!shown.length) {
      list.innerHTML = '<div class="cmd-empty">No matching pages</div>';
      return;
    }
    list.innerHTML = shown.map(function (it, i) {
      return '<button type="button" class="cmd-item' + (i === active ? " active" : "") + '" data-i="' + i + '" role="option" aria-selected="' + (i === active) + '">' +
        icon(it.icon) + '<span class="cmd-label">' + it.label + '</span><span class="cmd-sec">' + it.section + "</span></button>";
    }).join("");
    var activeEl = list.querySelector(".cmd-item.active");
    if (activeEl && activeEl.scrollIntoView) activeEl.scrollIntoView({ block: "nearest" });
  }

  function go(href) {
    closePalette();
    if (window.SPA && window.SPA.mode && typeof window.SPA.load === "function") {
      var cur = window.SPA.current || "";
      var dir = cur.indexOf("/") >= 0 ? cur.slice(0, cur.lastIndexOf("/") + 1) : "";
      var path = href;
      if (href.indexOf("..") !== 0 && href.charAt(0) !== "/") path = dir + href;
      window.SPA.load(path.replace(/^\//, ""));
    } else {
      location.href = href;
    }
  }

  function onInputKey(e) {
    var shown = (list && list._shown) || [];
    if (e.key === "ArrowDown") {
      e.preventDefault();
      active = Math.min(Math.max(shown.length - 1, 0), active + 1);
      renderList();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      active = Math.max(0, active - 1);
      renderList();
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (shown[active]) go(shown[active].href);
    } else if (e.key === "Escape") {
      e.preventDefault();
      closePalette();
    }
  }

  document.addEventListener("click", function (e) {
    var item = e.target.closest && e.target.closest(".cmd-item");
    if (item && list && list._shown) {
      var it = list._shown[+item.getAttribute("data-i")];
      if (it) go(it.href);
      return;
    }
    if (e.target.closest && e.target.closest("#cmdOpen, #searchTrigger")) {
      e.preventDefault();
      openPalette();
    }
  });

  document.addEventListener("keydown", function (e) {
    if ((e.ctrlKey || e.metaKey) && (e.key === "k" || e.key === "K")) {
      if (!canPalette() && loginVisible()) return;
      if (!canPalette()) return;
      e.preventDefault();
      if (palette && !palette.hidden) closePalette();
      else openPalette();
    } else if (e.key === "Escape" && palette && !palette.hidden) {
      closePalette();
    }
  });

  function auto() {
    if (window.SPA && window.SPA.mode) return;
    var sb = document.getElementById("sidebar");
    if (!sb || sb.children.length) return;
    buildShell(roleFromPath());
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", auto);
  else auto();
})();
