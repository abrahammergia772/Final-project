/* ============================================================
   MedIQ Pro — app.js  (single-page shell)
   The whole system runs from the root URL (index.html). Pages are
   loaded into #spaBody with fetch() and swapped in place, so the
   browser URL never changes from the domain root. Every static
   page still works standalone when opened directly.
   ============================================================ */
window.SPA = { mode: true, current: "" };

(function () {
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));

  // ---------- resolve an internal link to a page path ----------
  function resolveHref(href) {
    if (!href || href.startsWith("#") || href.startsWith("//")) return null;
    if (/^[a-z]+:/i.test(href)) return null; // external (http, mailto, tel…)
    const clean = href.split("?")[0].split("#")[0];
    if (!clean.endsWith(".html")) return null;
    if (clean.startsWith("/")) return clean.slice(1);
    const cur = SPA.current || "";
    const dir = cur.includes("/") ? cur.slice(0, cur.lastIndexOf("/") + 1) : "";
    const segs = (dir + clean).split("/");
    const out = [];
    for (const seg of segs) {
      if (seg === "" || seg === ".") continue;
      if (seg === "..") out.pop();
      else out.push(seg);
    }
    return out.join("/");
  }

  // ---------- mark the active nav link ----------
  function markActive(path) {
    const file = path.split("/").pop();
    $$(".nav-link").forEach(a => a.classList.toggle("active", a.getAttribute("href").split("?")[0].split("#")[0].split("/").pop() === file));
  }

  // ---------- page script execution ----------
  const origAdd = EventTarget.prototype.addEventListener;
  let evalGuard = false;
  EventTarget.prototype.addEventListener = function (type, fn, opts) {
    if (type === "DOMContentLoaded" && evalGuard && typeof fn === "function") {
      try { fn(); } catch (e) { console.error("page init error:", e); }
      return;
    }
    return origAdd.call(this, type, fn, opts);
  };

  function runPageScript(code) {
    if (!code) return;
    // top-level const/let -> var so re-declaration across pages is harmless
    const lines = code.split("\n").map(line => {
      if (/^(const|let)\s+[A-Za-z_$][\w$]*\b/.test(line)) {
        return line.replace(/^(const|let)\s+/, "var ");
      }
      return line;
    });
    evalGuard = true;
    try {
      (0, eval)(lines.join("\n"));
    } catch (e) {
      console.error("SPA page script error:", e);
    } finally {
      evalGuard = false;
    }
  }

  // ---------- load a page into the shell ----------
  async function load(path) {
    if (!path || SPA.loading === path) return;
    SPA.loading = path;
    showLoading("Loading…");
    try {
      const res = await fetch(path, { cache: "no-store" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const html = await res.text();
      const doc = new DOMParser().parseFromString(html, "text/html");
      const body = doc.querySelector(".page-body");
      const scripts = doc.querySelectorAll("script");
      let inline = "";
      for (const s of scripts) if (!s.getAttribute("src")) inline = s.textContent || "";
      $("#spaBody").innerHTML = body ? body.innerHTML : "";
      const title = doc.querySelector(".page-title");
      if (title) {
        const tt = $("#topbarTitle");
        if (tt) tt.textContent = title.textContent;
      }
      document.title = (doc.title || "MedIQ Pro") + " — MedIQ Pro";
      SPA.current = path.split("?")[0].split("#")[0];
      markActive(SPA.current);
      document.body.classList.remove("mobile-menu-open");
      window.scrollTo(0, 0);
      runPageScript(inline);
    } catch (e) {
      console.error("SPA load error:", e);
      $("#spaBody").innerHTML = '<div class="alert alert-danger"><span>' + (window.ICONS ? window.ICONS.alert : "") + '</span><div class="alert-body"><strong>Could not open this page.</strong> Please try again.</div></div>';
    } finally {
      SPA.loading = "";
      hideLoading();
    }
  }

  // ---------- shell (sidebar + topbar) ----------
  function buildShell(role) {
    const cfg = (window.NAV_ROLES || {})[role] || { label: role, nav: [] };
    // Sidebar
    let sb = '<button class="sidebar-toggle" id="sidebarToggle" title="Collapse menu">' + (window.ICONS ? window.ICONS["chevron-left"] : "") + '</button>';
    sb += '<div class="sidebar-logo"><img src="assets/images/logo.png" alt="MedIQ Pro logo"><div class="logo-text"><div class="brand">MedIQ Pro</div><div class="tag">Hospital Management</div></div></div>';
    sb += '<nav class="sidebar-nav">';
    const perm = (window.NAV_PERM_MAP || {})[role] || {};
    cfg.nav.forEach(([section, items]) => {
      sb += '<div class="nav-section-label">' + section + "</div>";
      items.forEach(([href, label, ic]) => {
        const p = perm[href] || "";
        sb += '<a class="nav-link" href="' + href + '"' + (p ? ' data-perm="' + p + '"' : "") + ' data-close-menu>' + (window.ICONS[ic] || "") + '<span class="nav-label">' + label + "</span></a>";
      });
    });
    sb += '<div class="nav-section-label">MESSAGES</div>';
    sb += '<a class="nav-link" href="messages.html" data-perm="messages" data-close-menu>' + (window.ICONS.mail || "") + '<span class="nav-label">Messages</span></a>';
    sb += '<div class="nav-section-label">ACCOUNT</div>';
    sb += '<a class="nav-link" href="settings.html" data-perm="settings" data-close-menu>' + (window.ICONS.settings || "") + '<span class="nav-label">Settings</span></a>';
    sb += "</nav>";
    sb += '<div class="sidebar-footer"><div class="user-box"><span class="avatar" data-user-initials>…</span><div class="u-meta"><div class="u-name" data-user-name>Loading…</div><div class="u-role" data-user-role></div></div><button class="btn-icon u-logout" data-logout title="Log out" style="color:#fff">' + (window.ICONS.logout || "") + "</button></div></div>";
    $("#sidebar").innerHTML = sb;
    // Topbar
    let tb = '<div class="topbar-left"><button class="hamburger" id="hamburger">' + (window.ICONS.menu || "") + "</button><h1 class=\"page-title\" id=\"topbarTitle\">Dashboard</h1></div>";
    tb += '<div class="topbar-right">';
    tb += '<div class="topbar-search">' + (window.ICONS.search || "") + '<input class="form-control" placeholder="Search…" aria-label="Search"></div>';
    tb += '<div class="dropdown"><button class="icon-btn" data-dropdown-toggle="#notifMenu" aria-label="Notifications">' + (window.ICONS.bell || "") + '<span class="notif-dot"></span></button><div class="dropdown-menu" id="notifMenu"><div class="dd-header">Notifications</div></div></div>';
    tb += '<div class="dropdown"><button class="topbar-avatar" data-dropdown-toggle="#profileMenu"><span class="avatar" data-user-initials>…</span><div class="hide-sm"><div class="t-name" data-user-name>Loading…</div><div class="t-role" data-user-role></div></div></button><div class="dropdown-menu" id="profileMenu" style="min-width:210px"><div class="dd-header">Account</div><div class="dd-item" data-logout>' + (window.ICONS.logout || "") + "<span>Log out</span></div></div></div>";
    tb += "</div>";
    $("#topbar").innerHTML = tb;
  }

  // ---------- enter / exit the app ----------
  function enterApp() {
    const role = getUserRole();
    if (!role) return showLogin();
    $("#loginView").classList.add("hidden");
    $("#appView").classList.remove("hidden");
    buildShell(role);
    load(getRoleRedirect(role));
  }
  function showLogin() {
    clearSession();
    $("#appView").classList.add("hidden");
    $("#loginView").classList.remove("hidden");
    $("#spaBody").innerHTML = "";
    document.title = "Login — MedIQ Pro";
  }
  SPA.load = load;
  SPA.gotoDashboard = () => load(getRoleRedirect(getUserRole()));
  SPA.showLogin = showLogin;
  SPA.enterApp = enterApp;

  // ---------- global link interception (in-app pages load into the shell) ----------
  // Skips the login screen so its public links (signup / forgot / admin) navigate
  // normally; every other internal .html link (including inside modals) is swapped
  // in place so the URL stays at the root.
  document.addEventListener("click", (e) => {
    const lv = $("#loginView");
    if (lv && !lv.classList.contains("hidden")) return; // login screen → normal nav
    const a = e.target.closest("a[href]");
    if (!a) return;
    if (a.target === "_blank" || a.hasAttribute("download")) return;
    const path = resolveHref(a.getAttribute("href"));
    if (path) { e.preventDefault(); load(path); }
  });

  // ---------- init ----------
  document.addEventListener("DOMContentLoaded", () => {
    // Login form
    const form = $("#loginForm");
    if (form) {
      form.addEventListener("submit", (ev) => {
        ev.preventDefault();
        const btn = $("#loginBtn");
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner sm white"></span> Signing in…';
        login($("#loginEmail").value.trim(), $("#loginPassword").value).then(res => {
          if (res.ok) {
            showToast("Welcome back, " + getUserName() + "!", "success");
            enterApp();
          } else {
            const box = $("#loginError");
            $("#loginErrorText").textContent = res.error || "Login failed.";
            box.classList.add("show");
            btn.disabled = false;
            btn.innerHTML = "Sign In";
          }
        });
      });
      $$(".demo-role").forEach(b => b.addEventListener("click", () => {
        const role = b.dataset.role;
        login(role + "@mediq.pro", (CONFIG.DEMO_ACCOUNTS[role] || {}).password).then(res => {
          if (res.ok) enterApp();
        });
      }));
    }
    // Browsing the site root ALWAYS shows the login page — even if a previous
    // session exists in localStorage (fresh login each visit).
    // The only exception is a one-shot auto-enter flag set by admin-login.html,
    // so the Administrator portal can drop you straight into the admin dashboard.
    let autoEnter = false;
    try { autoEnter = sessionStorage.getItem("mediq_autoenter") === "1"; sessionStorage.removeItem("mediq_autoenter"); } catch (e) {}
    if (autoEnter && getSession()) enterApp(); else showLogin();
  });
})();
