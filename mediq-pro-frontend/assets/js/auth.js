/* ============================================================
   Wolaita Sodo Hospital — auth.js
   Login, logout, session check, role-based access control
   ============================================================ */

// ---------- Storage (safe wrapper) ----------
// localStorage can be unavailable in sandboxed contexts (e.g. preview iframes),
// so we fall back to an in-memory store to keep the app functional.
const MemoryStore = {};
const Store = {
  get(key) {
    try { return localStorage.getItem(key); } catch (e) { return MemoryStore[key] ?? null; }
  },
  set(key, val) {
    try { localStorage.setItem(key, val); } catch (e) { MemoryStore[key] = val; }
  },
  del(key) {
    try { localStorage.removeItem(key); } catch (e) { delete MemoryStore[key]; }
  }
};

// ---------- Session helpers ----------
function getSession() {
  try {
    return JSON.parse(Store.get(STORAGE_KEY)) || null;
  } catch (e) {
    return null;
  }
}

function saveSession(data) {
  Store.set(STORAGE_KEY, JSON.stringify({
    token: data.token || "",
    role: data.role,
    user_id: data.user_id,
    name: data.name,
    email: data.email || ""
  }));
}

function clearSession() {
  Store.del(STORAGE_KEY);
}

function getUserRole() {
  const s = getSession();
  return s ? s.role : null;
}

function getUserName() {
  const s = getSession();
  return s ? s.name : "User";
}

function getUserInitials() {
  return getUserName().split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
}

// ---------- Path helpers ----------
// True when the current page lives inside a role subfolder (admin/, doctor/, …)
function inRoleFolder() {
  return /^\/(admin|manager|doctor|nurse|pharmacist|laboratory|reception|patient)\//.test(window.location.pathname);
}
function basePath() { return inRoleFolder() ? "../" : ""; }

const ROLE_DASHBOARDS = {
  admin:      "admin/dashboard.html",
  manager:    "manager/dashboard.html",
  doctor:     "doctor/dashboard.html",
  nurse:      "nurse/dashboard.html",
  pharmacist: "pharmacist/dashboard.html",
  laboratory: "laboratory/dashboard.html",
  reception:  "reception/dashboard.html",
  patient:    "patient/dashboard.html"
};

// ---------- Role → dashboard mapping ----------
function getRoleRedirect(role) {
  return basePath() + (ROLE_DASHBOARDS[role] || "index.html");
}

function getRoleLabel(role) {
  const map = {
    admin: "Administrator", manager: "General Manager", doctor: "Doctor",
    nurse: "Nurse", pharmacist: "Pharmacist", laboratory: "Laboratory",
    reception: "Receptionist", patient: "Patient"
  };
  return map[role] || role;
}

// ---------- Login ----------
async function login(email, password) {
  const res = await apiFetch(CONFIG.ENDPOINTS.LOGIN, "POST", { email, password }, { skipAuth: true });
  if (res.ok) {
    saveSession({ token: res.data.token, role: res.data.role, user_id: res.data.user_id, name: res.data.name });
    return { ok: true, session: getSession() };
  }
  return { ok: false, error: res.error || "Invalid email or password." };
}

// ---------- Session protection ----------
function checkSession() {
  const s = getSession();
  const isLoginPage = window.location.pathname.endsWith("index.html") ||
                      window.location.pathname === "/" ||
                      window.location.pathname.endsWith("/");
  // SPA mode: the shell guarantees a session; never redirect (URL stays at root)
  if (window.SPA && window.SPA.mode) return !!s;
  if (!s && !isLoginPage) {
    window.location.href = basePath() + "index.html";
    return false;
  }
  if (s && isLoginPage) {
    window.location.href = getRoleRedirect(s.role);
    return false;
  }
  return true;
}

// Redirect if the current user's role does not match the required role
function checkRoleAccess(requiredRole) {
  const role = getUserRole();
  if (!role) {
    if (window.SPA && window.SPA.mode) { window.SPA.showLogin(); return false; }
    window.location.href = basePath() + "index.html";
    return false;
  }
  if (role !== requiredRole) {
    showToast("Access denied — redirecting to your dashboard", "error");
    if (window.SPA && window.SPA.mode) {
      setTimeout(() => window.SPA.gotoDashboard(), 900);
    } else {
      setTimeout(() => { window.location.href = getRoleRedirect(role); }, 900);
    }
    return false;
  }
  return true;
}

function logout() {
  clearSession();
  showToast("Logged out successfully", "info");
  if (window.SPA && window.SPA.mode) {
    setTimeout(() => window.SPA.showLogin(), 400);
  } else {
    setTimeout(() => { window.location.href = basePath() + "index.html"; }, 400);
  }
}

// ---------- Permissions (tab access per role) ----------
// Admin grants/revokes from Roles & Permissions; changes are stored here and
// each role page applies them when the sidebar renders — so a granted tab
// appears automatically, a revoked one disappears.
let _permCache = null;
let _permRequested = false;
function seedPermissions() {
  if (!_permCache) _permCache = JSON.parse(JSON.stringify(CONFIG.PERMISSIONS));
  if (_permRequested || typeof apiFetch !== "function") return;
  _permRequested = true;
  apiFetch(CONFIG.ENDPOINTS.APP_SETTINGS).then(function (res) {
    if (!res.ok) return;
    const row = (res.data.items || []).find(function (item) { return item.id === "permissions"; });
    if (row && row.value) {
      _permCache = row.value;
      markKnown(CONFIG.ENDPOINTS.APP_SETTINGS, [row]);
      applyPermissions();
    }
  });
}

function loadPermissions() {
  return _permCache || CONFIG.PERMISSIONS;
}

// canAccess(role, permKey) — true when the tab should be visible
function canAccess(role, permKey) {
  if (!permKey || !role) return true;
  const map = loadPermissions()[role] || CONFIG.PERMISSIONS[role] || {};
  return map[permKey] === 1;
}

function savePermissions(role, map) {
  const all = Object.assign({}, loadPermissions());
  all[role] = map;
  _permCache = all;
  const row = { id: "permissions", value: all };
  apiFetch(CONFIG.ENDPOINTS.APP_SETTINGS, "POST", row).then(function (res) {
    if (!res.ok) persistUpdate(CONFIG.ENDPOINTS.APP_SETTINGS, "permissions", { value: all });
    else markKnown(CONFIG.ENDPOINTS.APP_SETTINGS, [row]);
  });
}

let _userPrefs = {};
function getSetting(k) { return _userPrefs[k]; }
function setSetting(k, v) {
  _userPrefs[k] = v;
  const s = getSession();
  if (s && s.user_id) persistUpdate(CONFIG.ENDPOINTS.USERS, s.user_id, { details: { prefs: _userPrefs } });
}
function loadMyPrefs(done) {
  apiFetch(CONFIG.ENDPOINTS.ME).then(function (res) {
    const prefs = (res.ok && res.data && res.data.details && res.data.details.prefs) || {};
    _userPrefs = prefs;
    if (prefs.theme && window.Theme) window.Theme.set(prefs.theme, false);
    if (prefs.lang && window.I18N) window.I18N.setLang(prefs.lang, true);
    if (done) done(prefs);
  });
}
window.saveUserPref = function (key, value) {
  const name = key === "mediq_theme" ? "theme" : key === "mediq_lang" ? "lang" : key;
  setSetting(name, value);
};

// ---------- Wire up UI bits ----------
// Uses event delegation so dropdowns/hamburger/logout work even when elements
// are added dynamically (e.g. by the SPA shell after login, or after page
// swaps). Safe to call multiple times — the global delegated listeners are
// only attached once.
let _authUI_bound = false;
function initAuthUI() {
  if (getSession()) loadMyPrefs();

  // --- Populate user name / role / initials everywhere currently in DOM ---
  const nameEl = document.querySelector("[data-user-name]");
  const roleEl = document.querySelector("[data-user-role]");
  const role = getUserRole();
  if (nameEl) nameEl.textContent = getUserName();
  if (roleEl && role) roleEl.textContent = getRoleLabel(role);
  document.querySelectorAll("[data-user-initials]").forEach((el) => {
    el.textContent = getUserInitials();
  });

  // --- One-time global delegated handlers ---
  if (_authUI_bound) return;
  _authUI_bound = true;

  // Dropdown toggles (profile, notifications, etc.) — works for dynamically
  // inserted buttons because we listen on document.
  document.addEventListener("click", (e) => {
    const toggle = e.target.closest("[data-dropdown-toggle]");
    if (toggle) {
      e.stopPropagation();
      const sel = toggle.getAttribute("data-dropdown-toggle");
      const menu = sel ? document.querySelector(sel) : null;
      if (!menu) return;
      const isOpen = menu.classList.contains("show");
      // close all other dropdowns
      document.querySelectorAll(".dropdown-menu.show").forEach((m) => {
        if (m !== menu) m.classList.remove("show");
      });
      menu.classList.toggle("show", !isOpen);
      return;
    }
    // Click outside any dropdown → close all
    if (!e.target.closest(".dropdown")) {
      document.querySelectorAll(".dropdown-menu.show").forEach((m) => m.classList.remove("show"));
    }
    // Logout buttons (anywhere, even in dynamically-rendered shell)
    const logoutBtn = e.target.closest("[data-logout]");
    if (logoutBtn) {
      e.preventDefault();
      logout();
    }
  });
}
