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
    email: data.email || "",
    health_card: data.health_card || "",
    portal: data.portal || ""
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
async function login(email, password, portal) {
  const body = { email: email, password: password };
  if (portal) body.portal = portal;
  const res = await apiFetch(CONFIG.ENDPOINTS.LOGIN, "POST", body, { skipAuth: true });
  if (!res.ok) return { ok: false, error: res.error || "Invalid email or password." };
  const role = res.data && res.data.role;
  if (portal === "admin" && role !== "admin") {
    return { ok: false, error: "This portal is for administrators only. Use the main login for other roles." };
  }
  if (portal !== "admin" && role === "admin") {
    return { ok: false, error: "Administrators sign in only through the administrator portal." };
  }
  saveSession({ token: res.data.token, role: role, user_id: res.data.user_id, name: res.data.name, email: res.data.email || email, health_card: res.data.health_card && res.data.health_card.id, portal: portal || "" });
  return { ok: true, session: getSession() };
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
  if (role === "admin" && getSession().portal !== "admin") {
    clearSession();
    window.location.href = basePath() + "admin-login.html";
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
  const role = getUserRole();
  clearSession();
  showToast("Logged out successfully", "info");
  const dest = basePath() + (role === "admin" ? "admin-login.html" : "index.html");
  if (window.SPA && window.SPA.mode && role !== "admin") {
    setTimeout(() => window.SPA.showLogin(), 400);
  } else {
    setTimeout(() => { window.location.href = dest; }, 400);
  }
}

// ---------- Permissions (tab access per role) ----------
// Saved by the administrator in Supabase. A turned-off permission hides the
// page and the API refuses the related action. Defaults apply until a row exists.
let _permCache = null;
let _permReady = false;
let _permState = "";
let _permPromise = null;
const PERM_UNLOCKS = {
  users: ["users"], announcements: ["announcements"], audit: ["audit_logs"],
  shifts: ["shifts", "roster", "attendance"], documents: ["documents"], records: ["documents"],
  patients: ["patients"], registration: ["patients"], wards: ["beds"], beds: ["beds"], admissions: ["beds"],
  bedrequests: ["bed_requests"], messages: ["messages"], departments: ["departments"], staff: ["staff"],
  finance: ["finance"], complaints: ["complaints"], prescriptions: ["prescriptions"], appointments: ["appointments"],
  referrals: ["referrals"], theatre: ["theatre_cases"], imaging: ["imaging_studies"], videos: ["videos"],
  vitals: ["vitals"], observations: ["observations"], medications: ["medications"], careplans: ["care_plans"],
  inventory: ["inventory"], suppliers: ["suppliers", "purchase_orders"], testrequests: ["lab_requests"],
  samples: ["samples"], bloodbank: ["blood_units"], results: ["lab_results"], insurance: ["insurance"],
  queue: ["queue"], ambulance: ["ambulances", "ambulance_missions"], billing: ["cashier_invoices", "bills"],
  bills: ["bills", "cashier_invoices"]
};

function seedPermissions() {
  if (_permPromise) return _permPromise;
  if (typeof apiFetch !== "function") {
    _permReady = true;
    _permState = "defaults";
    return Promise.resolve(loadPermissions());
  }
  _permPromise = apiFetch(CONFIG.ENDPOINTS.APP_SETTINGS).then(function (res) {
    if (res && res.ok) {
      const items = (res.data && res.data.items) || [];
      const row = items.find(function (item) { return item && item.id === "permissions"; });
      let value = row && row.value;
      if (typeof value === "string") {
        try { value = JSON.parse(value); } catch (e) { value = null; }
      }
      if (value && typeof value === "object") {
        _permCache = value;
        _permState = "saved";
        if (typeof markKnown === "function") markKnown(CONFIG.ENDPOINTS.APP_SETTINGS, [row]);
      } else {
        _permCache = null;
        _permState = "defaults";
      }
    } else {
      _permCache = null;
      _permState = "error";
    }
    _permReady = true;
    if (typeof applyPermissions === "function") applyPermissions();
    if (typeof enforceCurrentPage === "function") enforceCurrentPage();
    return loadPermissions();
  }).catch(function () {
    _permCache = null;
    _permState = "error";
    _permReady = true;
    if (typeof applyPermissions === "function") applyPermissions();
    return loadPermissions();
  });
  return _permPromise;
}

function loadPermissions() {
  return (_permCache && typeof _permCache === "object") ? _permCache : CONFIG.PERMISSIONS;
}

function granted(role, key) {
  if (role === "admin" && key === "roles") return true;
  const savedRole = _permCache && _permCache[role];
  if (savedRole && Object.prototype.hasOwnProperty.call(savedRole, key)) {
    return savedRole[key] === 1 || savedRole[key] === true;
  }
  const defaults = (CONFIG.PERMISSIONS && CONFIG.PERMISSIONS[role]) || {};
  return defaults[key] === 1;
}

function canAccess(role, permKey) {
  if (!permKey) return true;
  if (!role) return false;
  if (!_permReady) return false;
  return granted(role, permKey);
}

function resourceAllowed(role, resource) {
  if (!resource || resource === "app_settings" || resource === "notifications") return true;
  const defaults = (CONFIG.PERMISSIONS && CONFIG.PERMISSIONS[role]) || {};
  const savedRole = _permCache && _permCache[role];
  const known = {};
  Object.keys(defaults).forEach(function (key) { known[key] = 1; });
  if (savedRole) Object.keys(savedRole).forEach(function (key) { known[key] = 1; });
  const governors = Object.keys(known).filter(function (key) {
    return (PERM_UNLOCKS[key] || []).indexOf(resource) >= 0;
  });
  if (!governors.length) return true;
  return governors.some(function (key) { return granted(role, key); });
}

function endpointAllowed(endpoint) {
  if (!_permReady || !getUserRole()) return true;
  const role = getUserRole();
  const path = String(endpoint || "").split("?")[0];
  if (path.indexOf("/auth/") === 0) {
    if (path.indexOf("/auth/health-card") === 0) return canAccess(role, "healthcard");
    return true;
  }
  if (path.indexOf("/ai/") === 0) return canAccess(role, "ai");
  const resource = path.replace(/^\//, "").split("/")[0];
  return resourceAllowed(role, resource);
}

function pageFileOf(path) {
  return String(path || "").split("?")[0].split("#")[0].split("/").pop();
}

function permKeyFor(path) {
  const file = pageFileOf(path);
  if (!file || file === "dashboard.html" || file === "index.html") return "";
  const role = getUserRole();
  const map = (window.NAV_PERM_MAP || {})[role] || {};
  if (map[file]) return map[file];
  if (file === "messages.html") return "messages";
  if (file === "settings.html") return "settings";
  return "";
}

function pageAllowed(path) {
  const key = permKeyFor(path);
  if (!key || !_permReady) return true;
  return canAccess(getUserRole(), key);
}

function permissionDeniedHtml() {
  return '<div class="alert alert-danger" style="margin:16px"><div class="alert-body"><strong>Permission required.</strong> An administrator has not given your role access to this page.</div></div>';
}

function savePermissions(role, map) {
  if (_permState === "error") {
    return Promise.resolve({ ok: false, error: "Could not load saved permissions, so nothing was changed." });
  }
  const all = JSON.parse(JSON.stringify(loadPermissions()));
  all[role] = map;
  const row = { id: "permissions", value: all };
  function finish(res) {
    if (res && res.ok) {
      _permCache = all;
      _permReady = true;
      _permState = "saved";
      if (typeof markKnown === "function") markKnown(CONFIG.ENDPOINTS.APP_SETTINGS, [row]);
      if (typeof applyPermissions === "function") applyPermissions();
    }
    return res || { ok: false, error: "Could not save permissions" };
  }
  return apiFetch(CONFIG.ENDPOINTS.APP_SETTINGS, "POST", row).then(function (res) {
    if (res && res.ok) return finish(res);
    return apiFetch(CONFIG.ENDPOINTS.APP_SETTINGS + "/permissions", "PUT", row).then(finish);
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
let _profileAvatar = "";
function applyProfilePhoto(url) {
  if (!url) return;
  _profileAvatar = url;
  const safe = String(url).replace(/\\/g, "\\\\").replace(/"/g, "%22");
  document.querySelectorAll("[data-user-initials]").forEach(function (el) {
    el.style.backgroundImage = "url(\"" + safe + "\")";
    el.style.backgroundSize = "cover";
    el.style.backgroundPosition = "center";
    el.style.backgroundRepeat = "no-repeat";
    el.style.color = "transparent";
    el.style.overflow = "hidden";
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
    const avatar = (_userDetails.profile && _userDetails.profile.avatar) || "";
    if (avatar) applyProfilePhoto(avatar);
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
  if (typeof ensureHealthCard === "function") ensureHealthCard();

  // --- Populate user name / role / initials everywhere currently in DOM ---
  const nameEl = document.querySelector("[data-user-name]");
  const roleEl = document.querySelector("[data-user-role]");
  const role = getUserRole();
  if (nameEl) nameEl.textContent = getUserName();
  if (roleEl && role) roleEl.textContent = getRoleLabel(role);
  document.querySelectorAll("[data-user-initials]").forEach((el) => {
    el.textContent = getUserInitials();
  });
  if (_profileAvatar) applyProfilePhoto(_profileAvatar);

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
