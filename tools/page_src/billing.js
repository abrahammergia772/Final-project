const KEY = "wsh_bills_v1";
function seedBills() {
  return [
    { id: "INV-2401", patient: "Abel Mekonnen", service: "Inpatient day · Medical", amount: 1850, paid: 0, method: "" },
    { id: "INV-2402", patient: "Selamawit Tadesse", service: "C-section package", amount: 12600, paid: 6000, method: "Insurance" },
    { id: "INV-2403", patient: "Yonas Girma", service: "Appendectomy + ward", amount: 8400, paid: 8400, method: "Cash" },
    { id: "INV-2404", patient: "Liya Hailu", service: "ER visit + X-ray", amount: 960, paid: 0, method: "" },
    { id: "INV-2405", patient: "Kidus Haile", service: "Pediatrics overnight", amount: 1420, paid: 500, method: "Telebirr" },
    { id: "INV-2406", patient: "Hanna Bekele", service: "Lab panel + consult", amount: 740, paid: 0, method: "" }
  ];
}
let bills = [];
function loadB() { try { const r = sessionStorage.getItem(KEY); if (r) { bills = JSON.parse(r); return; } } catch (e) {} bills = seedBills(); }
function saveB() { try { sessionStorage.setItem(KEY, JSON.stringify(bills)); } catch (e) {} }
function due(b) { return Math.max(0, b.amount - b.paid); }
function billStatus(b) {
  if (due(b) === 0) return badge("paid", "success");
  if (b.paid > 0) return badge("partial", "warning");
  return badge("unpaid", "danger");
}
function renderBills() {
  const outstanding = bills.reduce((s, b) => s + due(b), 0);
  const collected = bills.reduce((s, b) => s + b.paid, 0);
  document.getElementById("billStats").innerHTML = `
    <div class="stat-card"><div class="stat-icon tile-primary">${ICONS.receipt}</div><div><div class="stat-value">${bills.length}</div><div class="stat-label">Open invoices</div></div></div>
    <div class="stat-card color-danger"><div class="stat-icon">${ICONS.alert}</div><div><div class="stat-value">${formatCurrency(outstanding, false)}</div><div class="stat-label">Outstanding ETB</div></div></div>
    <div class="stat-card color-success"><div class="stat-icon">${ICONS.check}</div><div><div class="stat-value">${formatCurrency(collected, false)}</div><div class="stat-label">Collected ETB</div></div></div>
    <div class="stat-card color-info"><div class="stat-icon">${ICONS.wallet}</div><div><div class="stat-value">${bills.filter(b => due(b) === 0).length}</div><div class="stat-label">Fully paid</div></div></div>`;
  const q = (document.getElementById("billSearch").value || "").toLowerCase();
  const rows = bills.filter(b => !q || (b.id + b.patient + b.service).toLowerCase().includes(q));
  document.querySelector("#billTable tbody").innerHTML = rows.map(b => `<tr>
    <td>${esc(b.id)}</td><td>${esc(b.patient)}</td><td>${esc(b.service)}</td>
    <td>${formatCurrency(b.amount)}</td><td>${formatCurrency(due(b))}</td><td>${billStatus(b)}</td>
    <td class="actions">
      ${due(b) ? `<button class="btn btn-primary btn-sm" data-pay="${esc(b.id)}">Collect</button>` : ""}
      <button class="btn btn-secondary btn-sm" data-rcpt="${esc(b.id)}">Receipt</button>
    </td></tr>`).join("") || emptyRow(7, "No invoices.");
  document.querySelectorAll("[data-pay]").forEach(b => b.onclick = () => collect(b.dataset.pay));
  document.querySelectorAll("[data-rcpt]").forEach(b => b.onclick = () => receipt(b.dataset.rcpt));
}
function collect(id) {
  const b = bills.find(x => x.id === id);
  openModal({
    title: "Collect payment · " + id,
    body: `<p class="mb-3">Balance due <strong>${formatCurrency(due(b))}</strong> for ${esc(b.patient)}.</p>
      <div class="form-group"><label>Amount (ETB)</label><input class="form-control" id="payAmt" type="number" min="1" step="0.01" value="${due(b)}"></div>
      <div class="form-group"><label>Method</label><div class="pay-methods">
        ${["Cash", "Telebirr", "CBE Birr", "Insurance"].map((m, i) => `<label><input type="radio" name="paym" value="${m}" ${i === 0 ? "checked" : ""}> ${m}</label>`).join("")}
      </div></div>`,
    footer: `<button class="btn btn-secondary" data-close>Cancel</button><button class="btn btn-primary" id="payOk">Record payment</button>`
  }, { onMount(ov) {
    ov.querySelector("#payOk").onclick = () => {
      const amt = Number(ov.querySelector("#payAmt").value);
      const method = (ov.querySelector("input[name=paym]:checked") || {}).value || "Cash";
      if (!amt || amt <= 0) { showToast("Enter an amount", "warning"); return; }
      b.paid = Math.min(b.amount, b.paid + amt);
      b.method = method;
      saveB(); closeModal(ov); renderBills();
      showToast("Payment recorded · " + method, "success");
    };
  }});
}
function receipt(id) {
  const b = bills.find(x => x.id === id);
  const w = window.open("", "_blank", "noopener,width=480,height=640");
  if (!w) { showToast("Allow pop-ups to print the receipt", "warning"); return; }
  w.document.write(`<!DOCTYPE html><html><head><title>${esc(b.id)}</title><style>
    body{font-family:Inter,Segoe UI,Arial,sans-serif;padding:28px;color:#111} h1{font-size:18px;margin:0}
    .sub{color:#64748B;font-size:12px;margin-bottom:16px} table{width:100%;border-collapse:collapse;font-size:14px}
    td{padding:8px 0;border-bottom:1px solid #e5e7eb} .tot{font-weight:700;font-size:16px}
  </style></head><body>
    <h1>Wolaita Sodo Hospital</h1><div class="sub">Cashier receipt · ${esc(b.id)} · ${esc(todayStr())}</div>
    <table>
      <tr><td>Patient</td><td>${esc(b.patient)}</td></tr>
      <tr><td>Service</td><td>${esc(b.service)}</td></tr>
      <tr><td>Amount</td><td>${formatCurrency(b.amount)}</td></tr>
      <tr><td>Paid</td><td>${formatCurrency(b.paid)} ${b.method ? "(" + esc(b.method) + ")" : ""}</td></tr>
      <tr><td class="tot">Balance</td><td class="tot">${formatCurrency(due(b))}</td></tr>
    </table>
    <p class="sub">Demo receipt — not a fiscal invoice.</p>
    <script>window.onload=function(){setTimeout(function(){window.print()},300)}<\/script>
  </body></html>`);
  w.document.close();
}
function bootPage() {
  const ICONS = window.ICONS || {};
  window.ICONS = ICONS;
  loadB();
  document.getElementById("billSearch").oninput = debounce(renderBills, 200);
  document.getElementById("newInv").onclick = () => {
    const patient = document.getElementById("invPatient").value.trim();
    const service = document.getElementById("invService").value.trim();
    const amount = Number(document.getElementById("invAmount").value);
    if (!patient || !service || !amount) { showToast("Patient, service and amount are required", "warning"); return; }
    bills.unshift({ id: "INV-" + (2500 + bills.length), patient, service, amount, paid: 0, method: "" });
    saveB(); renderBills();
    showToast("Invoice created", "success");
    document.getElementById("invPatient").value = "";
    document.getElementById("invService").value = "";
    document.getElementById("invAmount").value = "";
  };
  renderBills();
}
