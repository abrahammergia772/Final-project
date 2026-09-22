#!/usr/bin/env python3
"""One-pass modernization of mediq-pro-frontend.

- Relative asset paths (works from file:// and sub-path hosts)
- Empty sidebar/topbar placeholders filled by shell.js
- Inter font, favicon file, module stylesheet
- Inline color pairs -> tile classes
- Shared printIdCard() instead of copied printers
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "mediq-pro-frontend"
SRC = Path(__file__).resolve().parent / "page_src"
ROLES = ["admin", "manager", "doctor", "nurse", "pharmacist", "laboratory", "reception", "patient"]

STYLE_MAP = {
    "background:#fef2f2;color:#dc2626": "tile-danger",
    "background:#fef2f2;color:#b91c1c": "tile-danger",
    "background:#fbf0d3;color:#b45309": "tile-warning",
    "background:#fbf0d3;color:#d97706": "tile-warning",
    "background:#fbf0d3;color:#eab308": "tile-warning",
    "background:#fffbeb;color:#d97706": "tile-warning",
    "background:#fffbeb;color:#b45309": "tile-warning",
    "background:#e3f9ef;color:#0f9d5c": "tile-success",
    "background:#e3f9ef;color:#18bf75": "tile-success",
    "background:#ecfdf5;color:#065f46": "tile-success",
    "background:#ecfdf5;color:#047857": "tile-success",
    "background:#e1effa;color:#1a6fa8": "tile-primary",
    "background:#e3f0f9;color:#1a6fa8": "tile-primary",
    "background:#e0f4fa;color:#0891b2": "tile-info",
    "background:#f0f9ff;color:#0891b2": "tile-info",
    "background:#f5f3ff;color:#7c3aed": "tile-purple",
    "background:#f3f4f6;color:#6b7280": "tile-neutral",
    "background:#f3f4f6;color:#374151": "tile-neutral",
    "background:#e7f0e9;color:#065f46": "tile-success",
}

PRINT_CARD = """function printCard(id) {
  const list = (typeof PATS !== "undefined") ? PATS : (typeof patients !== "undefined" ? patients : []);
  const p = list && list.find ? list.find(x => x.id === id) : null;
  if (p) printIdCard(p);
  else if (id && typeof id === "object") printIdCard(id);
}"""

FONT_LINKS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com" />\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />\n'
    '<meta name="theme-color" content="#0B3A5E" />\n'
)


def prefix_for(path: Path) -> str:
    rel = path.relative_to(ROOT)
    return "../" if len(rel.parts) > 1 else ""


def fix_paths(html: str, prefix: str) -> str:
    html = html.replace('href="/assets/', f'href="{prefix}assets/')
    html = html.replace("href='/assets/", f"href='{prefix}assets/")
    html = html.replace('src="/assets/', f'src="{prefix}assets/')
    html = html.replace("src='/assets/", f"src='{prefix}assets/")
    return html


def migrate_tiles(html: str) -> str:
    def repl(m: re.Match) -> str:
        tag = m.group(0)
        sm = re.search(r'\sstyle="([^"]*)"', tag)
        if not sm:
            return tag
        key = re.sub(r"\s+", "", sm.group(1)).lower()
        cls = STYLE_MAP.get(key)
        if not cls:
            return tag
        tag = tag[: sm.start()] + tag[sm.end() :]
        if 'class="' in tag:
            tag = tag.replace('class="', f'class="{cls} ', 1)
        else:
            tag = tag[:-1] + f' class="{cls}">'
        return tag

    return re.sub(r"<[a-zA-Z][^>]*\sstyle=\"[^\"]*\"[^>]*>", repl, html)


def strip_shell(html: str) -> str:
    if re.search(r'<aside class="sidebar" id="sidebar">\s*</aside>', html):
        return html
    html, n = re.subn(
        r'<aside class="sidebar" id="sidebar">.*?</aside>',
        '<aside class="sidebar" id="sidebar"></aside>',
        html,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("failed to strip sidebar")

    def repl_header(m: re.Match) -> str:
        inner = m.group(0)
        tm = re.search(r"<h1[^>]*>(.*?)</h1>", inner, re.S)
        title = re.sub(r"<[^>]+>", "", tm.group(1)).strip() if tm else "Dashboard"
        title = title.replace('"', "&quot;")
        return f'<header class="topbar" id="topbar" data-title="{title}"></header>'

    html, n = re.subn(
        r'<header class="topbar"[^>]*>.*?</header>',
        repl_header,
        html,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit("failed to strip topbar")
    return html


def ensure_assets(html: str, prefix: str, with_shell: bool) -> str:
    if "family=Inter" not in html and "fonts.googleapis.com/css2?family=Inter" not in html:
        html = html.replace(
            '<meta name="viewport" content="width=device-width, initial-scale=1.0" />',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0" />\n' + FONT_LINKS,
            1,
        )
    dash = f'<link rel="stylesheet" href="{prefix}assets/css/dashboard.css" />'
    if "modules.css" not in html and dash in html:
        html = html.replace(dash, dash + f'\n<link rel="stylesheet" href="{prefix}assets/css/modules.css" />', 1)
    if with_shell and "icons.js" not in html:
        html = html.replace(
            f'<script src="{prefix}assets/js/config.js"></script>',
            f'<script src="{prefix}assets/js/config.js"></script>\n'
            f'<script src="{prefix}assets/js/icons.js"></script>\n'
            f'<script src="{prefix}assets/js/nav.js"></script>',
            1,
        )
    if with_shell and "shell.js" not in html:
        html = html.replace(
            f'<script src="{prefix}assets/js/utils.js"></script>',
            f'<script src="{prefix}assets/js/utils.js"></script>\n'
            f'<script src="{prefix}assets/js/shell.js"></script>',
            1,
        )
    return html


def replace_function(text: str, name: str, new_src: str) -> tuple[str, bool]:
    key = "function " + name
    i = text.find(key)
    if i < 0:
        return text, False
    # only replace the duplicated patient-card printer
    window = text[i : i + 400]
    if "PATS.find" not in window and "document.write" not in window:
        return text, False
    b = text.find("{", i)
    depth = 0
    for j in range(b, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[:i] + new_src.strip() + text[j + 1 :], True
    return text, False


def polish_login(html: str, name: str) -> str:
    html = html.replace(
        '<a href="admin-login.html" style="color:var(--primary);font-weight:600">🔐 Administrator sign in</a>',
        '<a href="admin-login.html" class="login-admin-link">'
        '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2">'
        '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> Administrator sign in</a>',
    )
    html = html.replace(
        'data-role="laboratory"><span class="dr-icon" style="background:#FEF2F2;color:#DC2626">',
        'data-role="laboratory"><span class="dr-icon tile-info">',
    )
    html = html.replace('style="color:#9CA3AF"', 'class="login-foot"')
    if name == "index.html":
        html = html.replace(
            "Wolaita Sodo Hospital v1.0 · Demo mode active",
            "Wolaita Sodo Hospital · Demo mode active",
        )
    return html


def process_file(path: Path) -> None:
    rel = path.relative_to(ROOT)
    prefix = prefix_for(path)
    role_page = len(rel.parts) > 1 and rel.parts[0] in ROLES
    html = path.read_text(encoding="utf-8")
    html = fix_paths(html, prefix)
    html = re.sub(r"\sclass=\"\"", "", html)
    html = polish_login(html, path.name)
    html = migrate_tiles(html)
    if role_page:
        html = strip_shell(html)
        html, _ = replace_function(html, "printCard", PRINT_CARD)
    html = ensure_assets(html, prefix, with_shell=role_page or path.name == "index.html")
    if not re.search(r"<html[^>]*\blang=", html):
        html = html.replace("<html>", '<html lang="en">', 1)
    path.write_text(html, encoding="utf-8")


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
<meta name="theme-color" content="#0B3A5E" />
<title>@@TITLE@@ — Wolaita Sodo Hospital</title>
<link rel="icon" type="image/png" href="../assets/images/favicon.png" />
<link rel="stylesheet" href="../assets/css/global.css" />
<link rel="stylesheet" href="../assets/css/sidebar.css" />
<link rel="stylesheet" href="../assets/css/components.css" />
<link rel="stylesheet" href="../assets/css/dashboard.css" />
<link rel="stylesheet" href="../assets/css/modules.css" />
<script src="../assets/js/theme.js"></script>
</head>
<body>
<aside class="sidebar" id="sidebar"></aside>
<div class="mobile-overlay" id="mobileOverlay"></div>
<main class="main-content" id="mainContent">
<header class="topbar" id="topbar" data-title="@@TITLE@@"></header>
<section class="page-body">
@@BODY@@
</section>
</main>
<div id="modalContainer"></div>
<div id="toastContainer"></div>
<script src="../assets/js/config.js"></script>
<script src="../assets/js/icons.js"></script>
<script src="../assets/js/nav.js"></script>
<script src="../assets/js/auth.js"></script>
<script src="../assets/js/api.js"></script>
<script src="../assets/js/utils.js"></script>
<script src="../assets/js/shell.js"></script>
<script>
document.addEventListener("DOMContentLoaded", () => {
  checkSession();
  checkRoleAccess("@@ROLE@@");
  initLayout();
  bootPage();
});
var ICONS = window.ICONS || {};
@@SCRIPT@@
</script>
<script src="../assets/js/i18n.js"></script>
</body>
</html>
"""


def write_page(rel: str, role: str, title: str, body: str, script_name: str) -> None:
    script = (SRC / script_name).read_text(encoding="utf-8")
    html = (
        PAGE.replace("@@TITLE@@", title)
        .replace("@@ROLE@@", role)
        .replace("@@BODY@@", body)
        .replace("@@SCRIPT@@", script)
    )
    dest = ROOT / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding="utf-8")
    print("wrote", rel)


BEDS_BODY = """
<p class="page-kicker">Inpatient flow</p>
<p class="page-intro">@@INTRO@@</p>
<div class="stat-grid" id="bedStats"></div>
<div class="chip-row" id="wardFilters"></div>
<div class="bed-board" id="bedBoard"></div>
<p class="module-note">Training demo for Wolaita Sodo Hospital — this board lists occupied beds only.</p>
"""

BLOOD_BODY = """
<p class="page-kicker">Laboratory</p>
<p class="page-intro">Blood bank inventory for Wolaita Sodo Hospital — stock by group, expiry watch, reserve and issue.</p>
<div class="stat-grid" id="bloodStats"></div>
<div class="blood-grid" id="bloodGrid"></div>
<div class="panel-grid">
  <section class="panel">
    <div class="panel-header"><div><h3>Units on the shelf</h3></div></div>
    <div class="table-toolbar"><div class="filters">
      <input class="form-control" id="bloodSearch" placeholder="Search unit, donor, patient…" aria-label="Search units" style="max-width:260px">
      <select class="form-control" id="bloodType" style="max-width:160px" aria-label="Blood group"></select>
    </div></div>
    <div class="panel-body no-pad"><div class="table-wrap"><table class="data-table" id="bloodTable">
      <thead><tr><th>Unit</th><th>Group</th><th>Donor</th><th>Expires</th><th>Status</th><th>Reserved for</th><th></th></tr></thead>
      <tbody></tbody>
    </table></div></div>
  </section>
  <section class="panel">
    <div class="panel-header"><div><h3>Log a donation</h3><div class="sub">Walk-in donor, this session only</div></div></div>
    <div class="panel-body">
      <div class="form-group"><label>Donor name</label><input class="form-control" id="donName" placeholder="Full name"></div>
      <div class="form-group"><label>Blood group</label>
        <select class="form-control" id="donType"><option>O+</option><option>O-</option><option>A+</option><option>A-</option><option>B+</option><option>B-</option><option>AB+</option><option>AB-</option></select>
      </div>
      <button class="btn btn-primary" id="addDonation" type="button">Save donation</button>
      <p class="module-note">Demo stock. A live bank would screen, crossmatch and quarantine before release.</p>
    </div>
  </section>
</div>
"""

AMB_BODY = """
<p class="page-kicker">Emergency</p>
<p class="page-intro">Ambulance desk for Wolaita Sodo — dispatch a unit, then advance it from scene to hospital.</p>
<div class="stat-grid">
  <div class="stat-card color-success"><div class="stat-icon"><span class="stat-value" id="ambFree">–</span></div><div><div class="stat-label">Units free</div><div class="stat-trend text-gray">Ready in the bay</div></div></div>
  <div class="stat-card color-warning"><div class="stat-icon"><span class="stat-value" id="ambActive">–</span></div><div><div class="stat-label">Active calls</div><div class="stat-trend text-gray">En route, scene or returning</div></div></div>
</div>
<div class="fleet-grid" id="fleetGrid"></div>
<div class="panel-grid">
  <section class="panel">
    <div class="panel-header"><div><h3>New dispatch</h3></div></div>
    <div class="panel-body">
      <form id="ambForm">
        <div class="form-row">
          <div class="form-group"><label>Unit</label><select class="form-control" id="ambUnit"></select></div>
          <div class="form-group"><label>Priority</label><select class="form-control" id="ambPri"><option>Emergency</option><option>Urgent</option><option>Routine transfer</option></select></div>
        </div>
        <div class="form-group"><label>Location in Wolaita Sodo</label><select class="form-control" id="ambPlace"></select></div>
        <div class="form-group"><label>What happened</label><input class="form-control" id="ambCase" placeholder="e.g. RTA, two casualties"></div>
        <button class="btn btn-primary" type="submit">Dispatch</button>
      </form>
    </div>
  </section>
  <section class="panel">
    <div class="panel-header"><div><h3>Dispatch log</h3></div></div>
    <div class="panel-body" id="missionLog"></div>
  </section>
</div>
<p class="module-note">Demo dispatch. Real calls go through the emergency desk and radio.</p>
"""

BILL_BODY = """
<p class="page-kicker">Cashier</p>
<p class="page-intro">Front-desk billing in ETB — raise an invoice, collect cash, Telebirr, CBE Birr or insurance, and print a receipt.</p>
<div class="stat-grid" id="billStats"></div>
<div class="panel-grid">
  <section class="panel">
    <div class="panel-header"><div><h3>Invoices</h3></div>
      <input class="form-control" id="billSearch" placeholder="Search patient or invoice…" aria-label="Search invoices" style="max-width:240px">
    </div>
    <div class="panel-body no-pad"><div class="table-wrap"><table class="data-table" id="billTable">
      <thead><tr><th>Invoice</th><th>Patient</th><th>Service</th><th>Amount</th><th>Due</th><th>Status</th><th></th></tr></thead>
      <tbody></tbody>
    </table></div></div>
  </section>
  <section class="panel">
    <div class="panel-header"><div><h3>New invoice</h3></div></div>
    <div class="panel-body">
      <div class="form-group"><label>Patient</label><input class="form-control" id="invPatient" placeholder="Full name"></div>
      <div class="form-group"><label>Service</label><input class="form-control" id="invService" placeholder="e.g. Consultation + lab"></div>
      <div class="form-group"><label>Amount (ETB)</label><input class="form-control" id="invAmount" type="number" min="1" step="0.01" placeholder="0.00"></div>
      <button class="btn btn-primary" id="newInv" type="button">Create invoice</button>
      <p class="module-note">Demo cashier. A live deployment would post to finance and the patient's bill.</p>
    </div>
  </section>
</div>
"""

OT_BODY = """
<p class="page-kicker">Surgery</p>
<p class="page-intro">Operating theatre list — three rooms, today's cases, and a slot you can book from the ward.</p>
<div class="ot-grid" id="otGrid"></div>
<div class="panel-grid">
  <section class="panel">
    <div class="panel-header"><div><h3>Today's list</h3></div></div>
    <div class="panel-body no-pad"><div class="table-wrap"><table class="data-table" id="otTable">
      <thead><tr><th>Time</th><th>Theatre</th><th>Patient</th><th>Procedure</th><th>Surgeon</th><th>Status</th><th></th></tr></thead>
      <tbody></tbody>
    </table></div></div>
  </section>
  <section class="panel">
    <div class="panel-header"><div><h3>Book a slot</h3></div></div>
    <div class="panel-body">
      <form id="otForm">
        <div class="form-group"><label>Patient</label><input class="form-control" id="otPatient" placeholder="Full name"></div>
        <div class="form-group"><label>Procedure</label><input class="form-control" id="otProc" placeholder="e.g. C-section"></div>
        <div class="form-row">
          <div class="form-group"><label>Theatre</label><select class="form-control" id="otRoom"><option>OT-1</option><option>OT-2</option><option>Maternity OT</option></select></div>
          <div class="form-group"><label>Time</label><input class="form-control" id="otTime" type="time" value="16:00"></div>
        </div>
        <div class="form-group"><label>Surgeon</label><input class="form-control" id="otSurg" placeholder="Dr. name"></div>
        <button class="btn btn-primary" type="submit">Book theatre</button>
      </form>
      <p class="module-note">Demo list. Confirm consent, blood and anaesthesia before the patient leaves the ward.</p>
    </div>
  </section>
</div>
"""

IMG_BODY = """
<p class="page-kicker">Diagnostics</p>
<p class="page-intro">Imaging worklist — X-ray, ultrasound and CT requests, with emergency studies highlighted.</p>
<div class="stat-grid" id="imgStats"></div>
<div class="panel-grid">
  <section class="panel">
    <div class="panel-header"><div><h3>Worklist</h3></div>
      <select class="form-control" id="imgFilter" style="max-width:180px" aria-label="Filter studies">
        <option value="">All studies</option>
        <option value="scheduled">Scheduled</option>
        <option value="in-progress">In progress</option>
        <option value="reported">Reported</option>
        <option value="x-ray">X-ray</option>
        <option value="ultrasound">Ultrasound</option>
        <option value="ct">CT</option>
      </select>
    </div>
    <div class="panel-body no-pad"><div class="table-wrap"><table class="data-table" id="imgTable">
      <thead><tr><th>ID</th><th>Patient</th><th>Study</th><th>Priority</th><th>Status</th><th>Note</th><th></th></tr></thead>
      <tbody></tbody>
    </table></div></div>
  </section>
  <section class="panel">
    <div class="panel-header"><div><h3>Request a study</h3></div></div>
    <div class="panel-body">
      <form id="imgForm">
        <div class="form-group"><label>Patient</label><input class="form-control" id="imgPatient" placeholder="Full name"></div>
        <div class="form-group"><label>Study</label>
          <select class="form-control" id="imgStudy">
            <option>Chest X-ray</option><option>Abdominal ultrasound</option><option>Pelvis X-ray</option>
            <option>CT head</option><option>Obstetric ultrasound</option>
          </select>
        </div>
        <div class="form-group"><label>Priority</label>
          <select class="form-control" id="imgPri"><option>Routine</option><option>Urgent</option><option>Emergency</option></select>
        </div>
        <button class="btn btn-primary" type="submit">Send request</button>
      </form>
      <p class="module-note">Demo worklist — not a diagnostic report. Release notes are visible to the requesting clinician in this session.</p>
    </div>
  </section>
</div>
"""


def write_new_pages() -> None:
    intros = {
        "nurse": "Occupied beds only. Empty, cleaning and reserved beds stay hidden. A doctor registers and approves anyone who needs a bed.",
        "admin": "Occupied beds for administration. Free beds and new requests are handled by the doctor, not from this board.",
        "manager": "Occupied beds across the hospital. Empty beds are not shown. Doctors approve new admissions themselves.",
        "reception": "Occupied beds only. Registering and approving a patient who needs a bed is done by the doctor.",
    }
    write_page("nurse/beds.html", "nurse", "Wards & Beds", BEDS_BODY.replace("@@INTRO@@", intros["nurse"]), "beds.js")
    write_page("admin/wards.html", "admin", "Wards & Beds", BEDS_BODY.replace("@@INTRO@@", intros["admin"]), "beds.js")
    write_page("manager/wards.html", "manager", "Wards & Beds", BEDS_BODY.replace("@@INTRO@@", intros["manager"]), "beds.js")
    write_page("reception/admissions.html", "reception", "Admissions & Beds", BEDS_BODY.replace("@@INTRO@@", intros["reception"]), "beds.js")
    write_page("laboratory/blood-bank.html", "laboratory", "Blood Bank", BLOOD_BODY, "blood.js")
    write_page("reception/ambulance.html", "reception", "Ambulance", AMB_BODY, "ambulance.js")
    write_page("reception/billing.html", "reception", "Cashier", BILL_BODY, "billing.js")
    write_page("doctor/theatre.html", "doctor", "Operating Theatre", OT_BODY, "theatre.js")
    write_page("doctor/imaging.html", "doctor", "Imaging", IMG_BODY, "imaging.js")


def patch_labels() -> None:
    path = ROOT / "admin" / "roles.html"
    text = path.read_text(encoding="utf-8")
    needle = 'records:"Medical Records", bills:"Bills"'
    extra = ', wards:"Wards & Beds", beds:"Wards & Beds", admissions:"Admissions & Beds", bloodbank:"Blood Bank", ambulance:"Ambulance Dispatch", billing:"Cashier", theatre:"Operating Theatre", imaging:"Imaging"'
    if needle in text and "bloodbank:" not in text:
        text = text.replace(needle, needle + extra, 1)
        path.write_text(text, encoding="utf-8")
        print("patched PAGE_LABELS")
    am = ROOT / "assets" / "js" / "i18n" / "am.js"
    blob = am.read_text(encoding="utf-8")
    addition = """
"Wards & Beds": "ዋርዶች እና አልጋዎች",
"Admissions & Beds": "መግቢያ እና አልጋዎች",
"Blood Bank": "የደም ባንክ",
"Ambulance": "አምቡላንስ",
"Cashier": "ገንዘብ ተቀባይ",
"Operating Theatre": "የቀዶ ጥገና ክፍል",
"Imaging": "ምስል ምርመራ",
"Administrator sign in": "የአስተዳዳሪ መግቢያ",
"Search pages": "ገጾችን ፈልግ",
"Jump to a page…": "ወደ ገጽ ዝለል…",
"Waiting for a bed": "አልጋ በመጠባበቅ ላይ",
"Demo mode active": "የሙከራ ሁነታ ንቁ",
"""
    if '"Blood Bank"' not in blob:
        blob = blob.rstrip()
        if blob.endswith("};"):
            blob = blob[:-2] + addition + "};\n"
            am.write_text(blob, encoding="utf-8")
            print("patched am.js")


def main() -> None:
    pages = list(ROOT.rglob("*.html"))
    for p in pages:
        process_file(p)
        print("updated", p.relative_to(ROOT))
    write_new_pages()
    patch_labels()
    # sanity
    broken = []
    for p in (ROOT).rglob("*.html"):
        t = p.read_text(encoding="utf-8")
        rel = p.relative_to(ROOT)
        if len(rel.parts) > 1 and rel.parts[0] in ROLES:
            if 'id="sidebar">' in t and not re.search(r'<aside class="sidebar" id="sidebar">\s*</aside>', t):
                broken.append(str(rel) + " sidebar not empty")
            if "shell.js" not in t:
                broken.append(str(rel) + " missing shell.js")
            if 'src="/assets/' in t or 'href="/assets/' in t:
                broken.append(str(rel) + " absolute asset")
    if broken:
        raise SystemExit("sanity failed:\\n" + "\\n".join(broken))
    print("ok", len(list(ROOT.rglob('*.html'))), "html files")


if __name__ == "__main__":
    main()
