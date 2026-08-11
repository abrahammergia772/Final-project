/* ============================================================
   MedIQ Pro — auth.js
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
    token: data.token || "demo-token",
    role: data.role,
    user_id: data.user_id,
    name: data.name
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
  if (CONFIG.DEMO_MODE) {
    // Demo: accept demo accounts by email (e.g. admin@mediq.pro) or role name
    const roleKey = (email || "").toLowerCase().split("@")[0];
    const account = CONFIG.DEMO_ACCOUNTS[roleKey];
    if (account && account.password === password) {
      const session = {
        token: "demo-token-" + roleKey,
        role: account.role,
        user_id: roleKey + "-001",
        name: account.name
      };
      saveSession(session);
      return { ok: true, session };
    }
    return { ok: false, error: "Invalid email or password. Try a demo account (e.g. admin@mediq.pro / admin123)." };
  }

  // Production: call FastAPI
  const res = await apiFetch(CONFIG.ENDPOINTS.LOGIN, "POST", { email, password }, { skipAuth: true });
  if (res.ok) {
    saveSession({ token: res.data.token, role: res.data.role, user_id: res.data.user_id, name: res.data.name });
    return { ok: true };
  }
  return { ok: false, error: res.error || "Login failed. Please try again." };
}

// ---------- Session protection ----------
function checkSession() {
  const s = getSession();
  const isLoginPage = window.location.pathname.endsWith("index.html") ||
                      window.location.pathname === "/" ||
                      window.location.pathname.endsWith("/");
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
  if (!role) { window.location.href = basePath() + "index.html"; return false; }
  if (role !== requiredRole) {
    showToast("Access denied — redirecting to your dashboard", "error");
    setTimeout(() => { window.location.href = getRoleRedirect(role); }, 900);
    return false;
  }
  return true;
}

function logout() {
  clearSession();
  showToast("Logged out successfully", "info");
  setTimeout(() => { window.location.href = basePath() + "index.html"; }, 400);
}

// ---------- Wire up UI bits ----------
function initAuthUI() {
  // Logout buttons anywhere (data-action="logout")
  document.querySelectorAll("[data-logout]").forEach(btn => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      logout();
    });
  });

  // Sidebar profile
  const nameEl = document.querySelector("[data-user-name]");
  const roleEl = document.querySelector("[data-user-role]");
  const initialsEl = document.querySelectorAll("[data-user-initials]");
  const role = getUserRole();

  if (nameEl) nameEl.textContent = getUserName();
  if (roleEl && role) roleEl.textContent = getRoleLabel(role);
  initialsEl.forEach(el => { el.textContent = getUserInitials(); });

  // Topbar dropdowns (profile / notifications)
  document.querySelectorAll("[data-dropdown-toggle]").forEach(toggle => {
    toggle.addEventListener("click", (e) => {
      e.stopPropagation();
      const menu = document.querySelector(toggle.dataset.dropdownToggle);
      if (!menu) return;
      const wasOpen = menu.classList.contains("show");
      document.querySelectorAll(".dropdown-menu").forEach(m => m.classList.remove("show"));
      if (!wasOpen) menu.classList.add("show");
    });
  });
  document.addEventListener("click", () => {
    document.querySelectorAll(".dropdown-menu").forEach(m => m.classList.remove("show"));
  });
}
