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

  function signedIn() {
    try { return typeof getSession === "function" && !!getSession(); }
    catch (e) { return false; }
  }

  function loginHref() {
    if (window.SPA && window.SPA.mode) return "index.html";
    if (roleFromPath() === "admin") return "../admin-login.html";
    return "../index.html";
  }

  function authControl() {
    if (signedIn()) {
      return '<button type="button" class="auth-corner" data-logout><span data-i18n="Log out">Log out</span></button>';
    }
    return '<a class="auth-corner" href="' + loginHref() + '"><span data-i18n="Log in">Log in</span></a>';
  }

  function navLink(href, label, ic, perm, spa, cur, cls) {
    var p = perm[href] || (href === "messages.html" ? "messages" : href === "settings.html" ? "settings" : "");
    var file = String(href).split("?")[0].split("/").pop();
    var active = !spa && cur === file ? " active" : "";
    var withIcon = cls !== "bar-link";
    return '<a class="' + (cls || "nav-link") + active + '" href="' + href + '"' +
      (p ? ' data-perm="' + p + '"' : "") + ' data-close-menu>' +
      (withIcon ? icon(ic) : "") + '<span class="nav-label" data-i18n="' + label + '">' + label + "</span></a>";
  }

  function navMenuHtml(cfg, perm, spa, cur) {
    var html = "";
    (cfg.nav || []).forEach(function (section) {
      html += '<div class="home-col"><div class="nav-section-label">' + section[0] + "</div>";
      (section[1] || []).forEach(function (item) {
        html += navLink(item[0], item[1], item[2], perm, spa, cur);
      });
      html += "</div>";
    });
    html += '<div class="home-col"><div class="nav-section-label">MESSAGES</div>';
    html += navLink("messages.html", "Messages", "mail", perm, spa, cur);
    html += '<div class="nav-section-label">ACCOUNT</div>';
    html += navLink("settings.html", "Settings", "settings", perm, spa, cur);
    html += '<div class="nav-section-label">CONTACT</div>';
    html += navLink("contact.html", "Contact us", "phone", perm, spa, cur);
    html += "</div>";
    return html;
  }

  function topLinksHtml(role, perm, spa, cur) {
    var items = (window.NAV_TOP || {})[role] || [];
    return items.map(function (item) {
      return navLink(item[0], item[1], item[2], perm, spa, cur, "bar-link");
    }).join("");
  }

  function buildAuthFoot() {
    var old = document.getElementById("roleTaskbar");
    if (old) old.remove();
    document.body.classList.remove("has-taskbar");
    var foot = document.getElementById("authFoot");
    if (!foot) {
      foot = document.createElement("div");
      foot.id = "authFoot";
      foot.className = "auth-foot";
      var host = document.getElementById("appView") || document.body;
      host.appendChild(foot);
    }
    foot.innerHTML = '<span class="auth-foot-note"><span data-user-role></span></span>' + authControl();
    document.body.classList.add("has-auth-foot");
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
    document.body.classList.add("home-shell");
    sb.innerHTML = "";
    sb.setAttribute("hidden", "hidden");

    var title = pageTitle();
    var top = '<div class="topbar-main">';
    top += '<a class="brand-lockup" href="dashboard.html"><img src="' + asset("assets/images/logo-mark.png") + '" alt=""><span data-i18n="Wolaita Sodo Hospital">Wolaita Sodo Hospital</span></a>';
    top += '<div class="top-center">';
    top += '<div class="dropdown home-drop"><button class="home-trigger" id="homeTrigger" type="button" aria-haspopup="true" aria-expanded="false" aria-controls="homeMenu">';
    top += '<span data-i18n="Home">Home</span>' + icon("chevron-down") + "</button>";
    top += '<div class="dropdown-menu home-menu" id="homeMenu" role="menu"><div class="home-menu-grid">' + navMenuHtml(cfg, perm, spa, cur) + "</div></div></div>";
    top += '<nav class="top-nav" aria-label="Primary">' + topLinksHtml(role, perm, spa, cur) + "</nav></div>";
    top += '<div class="topbar-right"><div class="dropdown more-drop">';
    top += '<button class="more-trigger" type="button" data-dropdown-toggle="#moreMenu" aria-label="More" aria-haspopup="true" aria-expanded="false" title="More">';
    top += '<span></span><span></span><span></span><i class="notif-dot" hidden></i></button>';
    top += '<div class="dropdown-menu more-menu" id="moreMenu" role="menu">';
    top += '<div class="more-name" data-user-name></div>';
    top += '<div id="moreControls"></div>';
    top += '<button class="more-row" id="cmdOpen" type="button">' + icon("search") + '<span data-i18n="Search pages">Search pages</span></button>';
    top += '<div class="more-notes" id="notifMenu" role="group" aria-label="Notifications"><div class="dd-header">Notifications</div><div class="empty-state" style="padding:16px">Loading notifications…</div></div>';
    top += authControl();
    top += "</div></div></div></div>";
    top += '<h1 class="page-title" id="topbarTitle">' + title + "</h1>";
    tb.innerHTML = top;
    tb.setAttribute("data-title", title);

    buildAuthFoot();
    ensurePalette();
    try { document.dispatchEvent(new CustomEvent("i18n:rescan")); } catch (e) {}
    if (typeof initAuthUI === "function") initAuthUI();
    if (typeof window.refreshNotifications === "function") window.refreshNotifications();
  }

  function buildTaskbar(role, perm, spa, cur) {
    var items = (window.NAV_TASKBAR || {})[role] || [];
    var bar = document.getElementById("roleTaskbar");
    if (!items.length) {
      if (bar) bar.remove();
      document.body.classList.remove("has-taskbar");
      return;
    }
    if (!bar) {
      bar = document.createElement("nav");
      bar.id = "roleTaskbar";
      bar.className = "role-taskbar";
      bar.setAttribute("aria-label", "Quick tasks");
      var host = document.getElementById("appView") || document.body;
      host.appendChild(bar);
    }
    bar.innerHTML = items.map(function (item) {
      var href = item[0], label = item[1], ic = item[2];
      var file = String(href).split("?")[0].split("/").pop();
      var active = !spa && cur === file ? " active" : "";
      var p = perm[href] || (href === "messages.html" ? "messages" : "");
      return '<a class="taskbar-link' + active + '" href="' + href + '"' +
        (p ? ' data-perm="' + p + '"' : "") + ' data-close-menu>' +
        icon(ic) + '<span data-i18n="' + label + '">' + label + "</span></a>";
    }).join("");
    document.body.classList.add("has-taskbar");
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
    out.push({ href: "contact.html", label: "Contact us", icon: "phone", section: "CONTACT" });
    return out.filter(function (item) {
      return typeof pageAllowed !== "function" || pageAllowed(item.href);
    });
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
      var more = document.getElementById("moreMenu");
      if (more) more.classList.remove("show");
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

  function placeHomeMenu(btn, menu) {
    var box = btn.getBoundingClientRect();
    var width = Math.min(640, window.innerWidth - 16);
    var left = Math.max(8, Math.min(box.left, window.innerWidth - width - 8));
    menu.style.position = "fixed";
    menu.style.top = Math.round(box.bottom + 8) + "px";
    menu.style.left = Math.round(left) + "px";
    menu.style.right = "auto";
    menu.style.width = Math.round(width) + "px";
    menu.style.zIndex = "4000";
    menu.style.display = "block";
  }

  function closeHomeMenu() {
    var menu = document.getElementById("homeMenu");
    var btn = document.querySelector(".home-trigger");
    if (menu) {
      menu.classList.remove("show");
      menu.style.display = "";
    }
    if (btn) btn.setAttribute("aria-expanded", "false");
  }

  document.addEventListener("click", function (e) {
    var trigger = e.target.closest && e.target.closest(".home-trigger");
    if (trigger) {
      e.preventDefault();
      var menu = document.getElementById("homeMenu");
      if (!menu) return;
      var open = !menu.classList.contains("show");
      document.querySelectorAll(".dropdown-menu.show").forEach(function (m) {
        if (m !== menu) m.classList.remove("show");
      });
      menu.classList.toggle("show", open);
      trigger.setAttribute("aria-expanded", open ? "true" : "false");
      if (open) placeHomeMenu(trigger, menu);
      else menu.style.display = "";
      return;
    }
    var link = e.target.closest && e.target.closest("#homeMenu a");
    if (link) {
      closeHomeMenu();
      return;
    }
    if (!e.target.closest || !e.target.closest("#homeMenu, .home-trigger")) closeHomeMenu();
  });

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", auto);
  else auto();
})();
