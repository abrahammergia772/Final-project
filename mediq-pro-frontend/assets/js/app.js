/* ============================================================
   Wolaita Sodo Hospital — app.js  (single-page shell)
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
  let pendingInit = [];
  EventTarget.prototype.addEventListener = function (type, fn, opts) {
    if (type === "DOMContentLoaded" && evalGuard && typeof fn === "function") {
      // Defer until the page script has finished evaluating — a real browser
      // also fires DOMContentLoaded only after the whole script has run, so
      // declarations placed after the registration must already exist.
      pendingInit.push(fn);
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
      if (/^(const|let)\s+[\[{]/.test(line)) {
        console.warn("SPA: destructuring declaration may not survive page swaps:", line.trim().slice(0, 90));
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
      const inits = pendingInit;
      pendingInit = [];
      for (const fn of inits) {
        try { fn(); } catch (e) { console.error("page init error:", e); }
      }
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
      const titled = doc.querySelector("header.topbar[data-title], [data-title]");
      const title = doc.querySelector(".page-title");
      const label = (titled && titled.getAttribute("data-title")) || (title && title.textContent) || "";
      if (label) {
        const tt = $("#topbarTitle");
        if (tt) tt.textContent = label.trim();
      }
      const base = (doc.title || "Wolaita Sodo Hospital").replace(/\s*—\s*(Wolaita Sodo Hospital|MedIQ Pro)\s*$/, "");
      document.title = base + " — Wolaita Sodo Hospital";
      SPA.current = path.split("?")[0].split("#")[0];
      markActive(SPA.current);
      if (typeof closeMobileMenu === "function") closeMobileMenu(); else document.body.classList.remove("mobile-menu-open");
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

  // Sidebar + topbar are built by shell.js (window.buildShell).

    // ---------- enter / exit the app ----------
  function enterApp() {
    const role = getUserRole();
    if (!role) return showLogin();
    $("#loginView").classList.add("hidden");
    $("#appView").classList.remove("hidden");
    if (typeof window.buildShell === "function") window.buildShell(role);
    else console.error("shell.js did not load — navigation cannot be built");
    // Wire up hamburger / profile dropdown / notifications / permissions
    // for the freshly-built shell (delegated handlers in initAuthUI ensure
    // the listeners survive future DOM rebuilds too).
    window.__spaLayoutDone = false; // force re-wire for the new shell
    initLayout();
    load(getRoleRedirect(role));
  }
  function showLogin() {
    clearSession();
    $("#appView").classList.add("hidden");
    $("#loginView").classList.remove("hidden");
    $("#spaBody").innerHTML = "";
    document.title = "Login — Wolaita Sodo Hospital";
    // Reset one-shot flags so a future login re-initialises notifs/layout.
    window.__notifsBound = false;
    window.__spaLayoutDone = false;
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
        }).catch(() => {
          const box = $("#loginError");
          $("#loginErrorText").textContent = "Cannot reach the server. Please try again.";
          box.classList.add("show");
          btn.disabled = false;
          btn.innerHTML = "Sign In";
        });
      });
      $$(".demo-role").forEach(b => b.addEventListener("click", () => {
        const role = b.dataset.role;
        const acct = CONFIG.DEMO_ACCOUNTS[role] || {};
        login(role + "@wsh.et", acct.password).then(res => {
          if (res.ok) enterApp();
          else {
            const box = $("#loginError");
            $("#loginErrorText").textContent = res.error || "Login failed.";
            if (box) box.classList.add("show");
          }
        }).catch(() => showToast("Login service unavailable.", "error"));
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
