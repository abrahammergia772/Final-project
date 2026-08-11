# -*- coding: utf-8 -*-
"""MedIQ Pro frontend builder — assembles every role page from the shared shell.
Run:  python3 tools/build_frontend.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frontend_lib import FRONT, ICON_PATHS, FAVICON, icon
from bodies_a import A
from bodies_b import B
from bodies_c import C
from bodies_d import D
from bodies_manager import M

# ---------------------------------------------------------------------------
# Role navigation definitions
# ---------------------------------------------------------------------------
ROLES = {
    "admin": {
        "label": "Administrator",
        "nav": [
            ("MAIN", [
                ("dashboard.html", "Dashboard", "grid"),
                ("users.html", "Users", "users"),
                ("roles.html", "Roles & Permissions", "shield"),
                ("audit-logs.html", "Audit Logs", "list"),
                ("settings.html", "Settings", "settings"),
            ]),
            ("SYSTEM & AI", [
                ("ai-config.html", "AI Configuration", "cpu"),
            ]),
        ],
    },
    "manager": {
        "label": "General Manager",
        "nav": [
            ("MAIN", [
                ("dashboard.html", "Dashboard", "grid"),
                ("departments.html", "Departments", "building"),
                ("staff.html", "Staff", "briefcase"),
                ("reports.html", "Reports", "chart"),
            ]),
            ("AI TOOLS", [
                ("ai-insights.html", "AI Insights", "sparkles"),
            ]),
        ],
    },
    "doctor": {
        "label": "Doctor",
        "nav": [
            ("MAIN", [
                ("dashboard.html", "Dashboard", "grid"),
                ("patients.html", "Patients", "users"),
                ("consultation.html", "Consultation", "stethoscope"),
                ("prescriptions.html", "Prescriptions", "file-text"),
                ("appointments.html", "Appointments", "calendar"),
            ]),
            ("AI TOOLS", [
                ("ai-diagnosis.html", "AI Diagnosis", "brain"),
            ]),
        ],
    },
    "nurse": {
        "label": "Nurse",
        "nav": [
            ("MAIN", [
                ("dashboard.html", "Dashboard", "grid"),
                ("vitals.html", "Vitals", "thermometer"),
                ("medications.html", "Medications", "pill"),
                ("care-plans.html", "Care Plans", "clipboard"),
            ]),
        ],
    },
    "pharmacist": {
        "label": "Pharmacist",
        "nav": [
            ("MAIN", [
                ("dashboard.html", "Dashboard", "grid"),
                ("prescriptions.html", "Prescriptions", "file-text"),
                ("inventory.html", "Inventory", "package"),
            ]),
            ("AI TOOLS", [
                ("ai-interaction.html", "AI Interaction", "zap"),
                ("ai-forecast.html", "AI Forecast", "truck"),
            ]),
        ],
    },
    "laboratory": {
        "label": "Laboratory",
        "nav": [
            ("MAIN", [
                ("dashboard.html", "Dashboard", "grid"),
                ("test-requests.html", "Test Requests", "flask"),
                ("results.html", "Results", "file-text"),
            ]),
            ("AI TOOLS", [
                ("ai-analyzer.html", "AI Analyzer", "brain"),
            ]),
        ],
    },
    "reception": {
        "label": "Receptionist",
        "nav": [
            ("MAIN", [
                ("dashboard.html", "Dashboard", "grid"),
                ("registration.html", "Registration", "users"),
                ("appointments.html", "Appointments", "calendar"),
                ("queue.html", "Queue", "list"),
            ]),
        ],
    },
    "patient": {
        "label": "Patient",
        "nav": [
            ("MAIN", [
                ("dashboard.html", "Dashboard", "grid"),
                ("appointments.html", "Appointments", "calendar"),
                ("records.html", "Medical Records", "book"),
                ("results.html", "Lab Results", "flask"),
                ("bills.html", "Bills", "wallet"),
            ]),
            ("AI ASSISTANT", [
                ("ai-chatbot.html", "AI Chatbot", "chat"),
            ]),
        ],
    },
}

PAGES = {}
for d in (A, B, C, D, M):
    for role, pages in d.items():
        PAGES.setdefault(role, {}).update(pages)

# ---------------------------------------------------------------------------
# JS inline icon library injected into every page
# ---------------------------------------------------------------------------
def js_icons():
    parts = []
    for name, paths in ICON_PATHS.items():
        svg = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
               'stroke-linecap="round" stroke-linejoin="round">' + paths + "</svg>")
        parts.append('"%s": "%s"' % (name, svg.replace('"', '\\"')))
    return "const ICONS = {" + ",\n".join(parts) + "};"


# ---------------------------------------------------------------------------
# Sidebar + topbar shell
# ---------------------------------------------------------------------------
def sidebar_html(role, active_file):
    out = [
        '<aside class="sidebar" id="sidebar">',
        '<button class="sidebar-toggle" id="sidebarToggle" title="Collapse menu">' + icon("chevron-left") + "</button>",
        '<div class="sidebar-logo"><img src="../assets/images/logo.png" alt="MedIQ Pro logo">'
        '<div class="logo-text"><div class="brand">MedIQ Pro</div><div class="tag">Hospital Management</div></div></div>',
        '<nav class="sidebar-nav">',
    ]
    for section, items in ROLES[role]["nav"]:
        out.append('<div class="nav-section-label">%s</div>' % section)
        for href, label, ic in items:
            active = ' active' if href == active_file else ""
            out.append('<a class="nav-link%s" href="%s" data-close-menu>%s<span class="nav-label">%s</span></a>'
                       % (active, href, icon(ic), label))
    out += [
        "</nav>",
        '<div class="sidebar-footer"><div class="user-box">'
        '<span class="avatar" data-user-initials>…</span>'
        '<div class="u-meta"><div class="u-name" data-user-name>Loading…</div><div class="u-role" data-user-role></div></div>'
        '<button class="btn-icon u-logout" data-logout title="Log out" style="color:#fff">' + icon("logout") + "</button>"
        "</div></div></aside>",
        '<div class="mobile-overlay" id="mobileOverlay"></div>',
    ]
    return "\n".join(out)


def topbar_html(title):
    notif_items = [
        ('<div class="dd-item"><div class="feed-icon" style="background:#FEF2F2;color:#DC2626">' + icon("alert") + "</div>"
         '<div class="feed-text"><div class="dd-title">3 critical patient alerts</div><div class="dd-sub">Flagged by the vitals AI</div></div></div>'),
        ('<div class="dd-item"><div class="feed-icon" style="background:#FFFBEB;color:#D97706">' + icon("package") + "</div>"
         '<div class="feed-text"><div class="dd-title">4 items low in stock</div><div class="dd-sub">Pharmacy reorder suggested</div></div></div>'),
        ('<div class="dd-item"><div class="feed-icon" style="background:#ECFDF5;color:#065F46">' + icon("check") + "</div>"
         '<div class="feed-text"><div class="dd-title">AI modules online</div><div class="dd-sub">All 7 modules passed health check</div></div></div>'),
    ]
    return (
        '<header class="topbar"><div class="topbar-left">'
        '<button class="hamburger" id="hamburger">' + icon("menu") + "</button>"
        '<h1 class="page-title">' + title + "</h1></div>"
        '<div class="topbar-right">'
        '<div class="topbar-search">' + icon("search") + '<input class="form-control" placeholder="Search…" aria-label="Search"></div>'
        '<div class="dropdown"><button class="icon-btn" data-dropdown-toggle="#notifMenu" aria-label="Notifications">' + icon("bell")
        + '<span class="notif-dot"></span></button>'
        '<div class="dropdown-menu" id="notifMenu"><div class="dd-header">Notifications</div>'
        + "".join(notif_items)
        + '<div class="dd-footer"><a href="#" onclick="event.preventDefault();showToast(\'No more notifications\',\'info\')">View all</a></div></div></div>'
        '<div class="dropdown"><button class="topbar-avatar" data-dropdown-toggle="#profileMenu">'
        '<span class="avatar" data-user-initials>…</span>'
        '<div class="hide-sm"><div class="t-name" data-user-name>Loading…</div><div class="t-role" data-user-role></div></div></button>'
        '<div class="dropdown-menu" id="profileMenu" style="min-width:210px"><div class="dd-header">Account</div>'
        '<div class="dd-item" data-logout>' + icon("logout") + '<span>Log out</span></div></div></div>'
        "</div></header>"
    )


# ---------------------------------------------------------------------------
# Page renderer
# ---------------------------------------------------------------------------
def render_page(role, filename, page):
    title = page["title"]
    nav = sidebar_html(role, filename)
    topbar = topbar_html(title)
    body = page["body"]
    script = page["script"]

    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>__TITLE__ — MedIQ Pro</title>
<link rel="icon" href="__FAVICON__" />
<link rel="stylesheet" href="../assets/css/global.css" />
<link rel="stylesheet" href="../assets/css/sidebar.css" />
<link rel="stylesheet" href="../assets/css/components.css" />
<link rel="stylesheet" href="../assets/css/dashboard.css" />
</head>
<body>
__NAV__
<main class="main-content" id="mainContent">
__TOPBAR__
<section class="page-body">
__BODY__
</section>
</main>
<div id="modalContainer"></div>
<div id="toastContainer"></div>
<script src="../assets/js/config.js"></script>
<script src="../assets/js/auth.js"></script>
<script src="../assets/js/api.js"></script>
<script src="../assets/js/utils.js"></script>
<script>
__ICONS__
__SCRIPT__
</script>
</body>
</html>
""".replace("__TITLE__", title).replace("__FAVICON__", FAVICON).replace("__NAV__", nav) \
        .replace("__TOPBAR__", topbar).replace("__BODY__", body).replace("__ICONS__", js_icons()) \
        .replace("__SCRIPT__", script)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    built = 0
    missing = []
    for role in ROLES:
        role_dir = os.path.join(FRONT, role)
        os.makedirs(role_dir, exist_ok=True)
        for filename in sorted(PAGES.get(role, {}).keys()):
            page = PAGES[role][filename]
            html = render_page(role, filename, page)
            path = os.path.join(role_dir, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            built += 1
        # pages defined but not in nav → warn
        nav_files = {href for _, items in ROLES[role]["nav"] for href, _, _ in items}
        for filename in PAGES.get(role, {}):
            if filename not in nav_files:
                missing.append(role + "/" + filename)
    print("Built %d pages into %s" % (built, FRONT))
    if missing:
        print("WARNING — pages not linked in nav:", ", ".join(missing))


if __name__ == "__main__":
    main()
