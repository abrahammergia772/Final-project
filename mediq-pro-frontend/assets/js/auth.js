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
    saveSession({ token: res.data.token, role: res.data.role, user_id: res.data.user_id, name: res.data.name, email: res.data.email || email });
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
let _userDetails = {};
let _prefTimer = null;
function getSetting(k) { return _userPrefs[k]; }
function setSetting(k, v) {
  _userPrefs[k] = v;
  _userDetails.prefs = _userPrefs;
  const s = getSession();
  if (!s || !s.user_id) return Promise.resolve({ ok: false });
  clearTimeout(_prefTimer);
  return new Promise(function (resolve) {
    _prefTimer = setTimeout(function () {
      apiFetch(CONFIG.ENDPOINTS.PROFILE, "POST", { details_patch: { prefs: _userPrefs } }).then(function (res) {
        if (!res.ok) showToast(res.error || "Could not save settings", "error");
        resolve(res);
      });
    }, 40);
  });
}
function fillSettingsForm() {
  return apiFetch(CONFIG.ENDPOINTS.ME).then(function (res) {
    if (!res.ok || !res.data) return res;
    const u = res.data;
    const s = getSession() || {};
    s.name = u.name || s.name || "";
    s.email = u.email || s.email || "";
    if (u.id) s.user_id = u.id;
    saveSession(s);
    const set = function (id, value) {
      const el = document.getElementById(id);
      if (el && value != null) el.value = value;
    };
    set("stName", u.name || "");
    set("stEmail", u.email || "");
    set("stPhone", u.phone || "");
    const profile = (u.details && u.details.profile) || {};
    const extra1 = document.getElementById("stExtra1");
    const extra2 = document.getElementById("stExtra2");
    if (extra1) extra1.value = profile.extra1 || (getUserRole() === "patient" ? (u.emergency_contact || "") : "");
    if (extra2) {
      const blood = profile.extra2 || (getUserRole() === "patient" ? (u.blood || "") : "");
      if (extra2.tagName === "SELECT") { if (blood) extra2.value = blood; }
      else extra2.value = blood;
      if (getUserRole() === "patient") extra2.disabled = false;
    }
    if (profile.avatar) applyProfilePhoto(profile.avatar);
    document.querySelectorAll("[data-user-name]").forEach(function (el) { el.textContent = u.name || ""; });
    return res;
  });
}
function applyProfilePhoto(url) {
  document.querySelectorAll("[data-user-initials]").forEach(function (el) {
    el.style.backgroundImage = "url(" + url + ")";
    el.style.backgroundSize = "cover";
    el.style.color = "transparent";
  });
}
function onProfilePhoto(input) {
  const file = input.files && input.files[0];
  if (!file) return;
  readUploadFile(file, 300000).then(function (packed) {
    return apiFetch(CONFIG.ENDPOINTS.PROFILE, "POST", { details_patch: { profile: { avatar: packed.data } } });
  }).then(function (res) {
    if (!res || !res.ok) { showToast((res && res.error) || "Could not save the photo", "error"); return; }
    const avatar = res.data && res.data.user && res.data.user.details && res.data.user.details.profile && res.data.user.details.profile.avatar;
    if (avatar) applyProfilePhoto(avatar);
    showToast("Profile photo saved", "success");
  }).catch(function (err) { showToast(err.message || "Could not read the photo", "error"); });
}
function saveProfileForm() {
  const nameEl = document.getElementById("stName");
  const name = nameEl ? nameEl.value.trim() : "";
  if (!name) { showToast("Name is required", "error"); return; }
  const email = (document.getElementById("stEmail") || {}).value || "";
  const phone = (document.getElementById("stPhone") || {}).value || "";
  const extra1 = document.getElementById("stExtra1");
  const extra2 = document.getElementById("stExtra2");
  const payload = {
    name: name,
    email: email.trim(),
    phone: phone.trim(),
    details_patch: { profile: { extra1: extra1 ? extra1.value : "", extra2: extra2 ? extra2.value : "" } }
  };
  if (getUserRole() === "patient") {
    payload.emergency_contact = extra1 ? extra1.value.trim() : "";
    payload.blood = extra2 ? extra2.value.trim() : "";
  }
  apiFetch(CONFIG.ENDPOINTS.PROFILE, "POST", payload).then(function (res) {
    if (!res.ok) { showToast(res.error || "Could not save the profile", "error"); return; }
    const s = getSession() || {};
    s.name = name;
    s.email = email.trim();
    saveSession(s);
    document.querySelectorAll("[data-user-name]").forEach(function (el) { el.textContent = name; });
    document.querySelectorAll("[data-user-initials]").forEach(function (el) {
      if (!el.style.backgroundImage) el.textContent = initialsOf(name);
    });
    showToast("Profile saved", "success");
  });
}
function savePrefsForm() {
  const prefs = Object.assign({}, _userPrefs);
  document.querySelectorAll("[data-pref]").forEach(function (box) {
    prefs["notify_" + box.getAttribute("data-pref")] = box.checked ? 1 : 0;
  });
  _userPrefs = prefs;
  _userDetails.prefs = prefs;
  return apiFetch(CONFIG.ENDPOINTS.PROFILE, "POST", { details_patch: { prefs: prefs } }).then(function (res) {
    if (res.ok) showToast("Notification preferences saved", "success");
    else showToast(res.error || "Could not save settings", "error");
    return res;
  });
}
function saveAppearanceForm() {
  const accent = document.getElementById("stAccent");
  const compact = document.getElementById("stCompact");
  if (accent) {
    _userPrefs.accent = accent.value;
    if (typeof applyAccent === "function") applyAccent(accent.value);
  }
  if (compact) {
    _userPrefs.compact = compact.checked ? 1 : 0;
    document.body.classList.toggle("compact", compact.checked);
  }
  _userDetails.prefs = _userPrefs;
  return apiFetch(CONFIG.ENDPOINTS.PROFILE, "POST", { details_patch: { prefs: _userPrefs } }).then(function (res) {
    if (res.ok) showToast("Appearance saved", "success");
    else showToast(res.error || "Could not save appearance", "error");
    return res;
  });
}
function applyNotifyPrefs() {
  document.querySelectorAll("[data-pref]").forEach(function (box) {
    const saved = _userPrefs["notify_" + box.getAttribute("data-pref")];
    if (saved != null) box.checked = !!saved;
  });
}
function loadMyPrefs(done) {
  apiFetch(CONFIG.ENDPOINTS.ME).then(function (res) {
    _userDetails = (res.ok && res.data && res.data.details) || {};
    if (typeof _userDetails !== "object" || !_userDetails) _userDetails = {};
    const prefs = _userDetails.prefs || {};
    _userPrefs = prefs;
    _userDetails.prefs = _userPrefs;
    if (prefs.theme && window.Theme) window.Theme.set(prefs.theme, false);
    if (prefs.lang && window.I18N) window.I18N.setLang(prefs.lang, true);
    applyNotifyPrefs();
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
