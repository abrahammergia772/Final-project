/* Wolaita Sodo Hospital — navigation (single source of truth) */
window.NAV_ROLES = {
  admin: {
    label: "Administrator",
    nav: [["MAIN", [
      ["dashboard.html", "Dashboard", "grid"],
      ["users.html", "Users", "users"],
      ["roles.html", "Roles & Permissions", "shield"],
      ["wards.html", "Wards & Beds", "bed"],
      ["announcements.html", "Announcements", "megaphone"],
      ["audit-logs.html", "Audit Logs", "list"],
      ["shifts.html", "Shifts & Attendance", "clock"],
      ["documents.html", "Documents", "file-text"],
      ["reports.html", "Reports", "chart"],
      ["patients.html", "Patients", "users"],
      ["settings.html", "Settings", "settings"]
    ]], ["SYSTEM & AI", [
      ["ai-config.html", "AI Configuration", "cpu"]
    ]]]
  },
  manager: {
    label: "General Manager",
    nav: [["MAIN", [
      ["dashboard.html", "Dashboard", "grid"],
      ["departments.html", "Departments", "building"],
      ["staff.html", "Staff", "briefcase"],
      ["wards.html", "Wards & Beds", "bed"],
      ["reports.html", "Reports", "chart"],
      ["finance.html", "Finance", "wallet"],
      ["complaints.html", "Complaints", "alert"],
      ["shifts.html", "Shifts & Attendance", "clock"],
      ["documents.html", "Documents", "file-text"],
      ["patients.html", "Patients", "users"]
    ]], ["AI TOOLS", [
      ["ai-insights.html", "AI Insights", "sparkles"]
    ]]]
  },
  doctor: {
    label: "Doctor",
    nav: [["MAIN", [
      ["dashboard.html", "Dashboard", "grid"],
      ["patients.html", "Patients", "users"],
      ["beds.html", "Bed requests", "bed"],
      ["consultation.html", "Consultation", "stethoscope"],
      ["prescriptions.html", "Prescriptions", "file-text"],
      ["appointments.html", "Appointments", "calendar"],
      ["referrals.html", "Referrals", "share"],
      ["theatre.html", "Operating Theatre", "activity"],
      ["imaging.html", "Imaging", "eye"],
      ["shifts.html", "Shifts & Attendance", "clock"],
      ["documents.html", "Documents", "file-text"],
      ["reports.html", "Reports", "chart"]
    ]], ["AI TOOLS", [
      ["ai-diagnosis.html", "AI Diagnosis", "brain"],
      ["clinical-decision.html", "Clinical Decision", "clipboard"],
      ["videos.html", "Health Videos", "play"]
    ]]]
  },
  nurse: {
    label: "Nurse",
    nav: [["MAIN", [
      ["dashboard.html", "Dashboard", "grid"],
      ["beds.html", "Wards & Beds", "bed"],
      ["vitals.html", "Vitals", "thermometer"],
      ["observations.html", "Observations", "activity"],
      ["medications.html", "Medications", "pill"],
      ["care-plans.html", "Care Plans", "clipboard"],
      ["shifts.html", "Shifts & Attendance", "clock"],
      ["documents.html", "Documents", "file-text"],
      ["reports.html", "Reports", "chart"],
      ["patients.html", "Patients", "users"]
    ]]]
  },
  pharmacist: {
    label: "Pharmacist",
    nav: [["MAIN", [
      ["dashboard.html", "Dashboard", "grid"],
      ["prescriptions.html", "Prescriptions", "file-text"],
      ["inventory.html", "Inventory", "package"],
      ["suppliers.html", "Suppliers & POs", "truck"],
      ["shifts.html", "Shifts & Attendance", "clock"],
      ["documents.html", "Documents", "file-text"],
      ["reports.html", "Reports", "chart"],
      ["patients.html", "Patients", "users"]
    ]], ["AI TOOLS", [
      ["ai-interaction.html", "AI Interaction", "zap"],
      ["ai-forecast.html", "AI Forecast", "chart"]
    ]]]
  },
  laboratory: {
    label: "Laboratory",
    nav: [["MAIN", [
      ["dashboard.html", "Dashboard", "grid"],
      ["test-requests.html", "Test Requests", "flask"],
      ["samples.html", "Sample Tracking", "barcode"],
      ["blood-bank.html", "Blood Bank", "droplet"],
      ["results.html", "Results", "file-text"],
      ["shifts.html", "Shifts & Attendance", "clock"],
      ["documents.html", "Documents", "file-text"],
      ["reports.html", "Reports", "chart"],
      ["patients.html", "Patients", "users"]
    ]], ["AI TOOLS", [
      ["ai-analyzer.html", "AI Analyzer", "brain"]
    ]]]
  },
  reception: {
    label: "Receptionist",
    nav: [["MAIN", [
      ["dashboard.html", "Dashboard", "grid"],
      ["registration.html", "Registration", "users"],
      ["admissions.html", "Admissions & Beds", "bed"],
      ["appointments.html", "Appointments", "calendar"],
      ["queue.html", "Queue", "list"],
      ["ambulance.html", "Ambulance", "truck"],
      ["billing.html", "Cashier", "receipt"],
      ["insurance.html", "Insurance", "shield"],
      ["shifts.html", "Shifts & Attendance", "clock"],
      ["documents.html", "Documents", "file-text"],
      ["reports.html", "Reports", "chart"],
      ["patients.html", "Patients", "users"]
    ]]]
  },
  patient: {
    label: "Patient",
    nav: [["MAIN", [
      ["dashboard.html", "Dashboard", "grid"],
      ["appointments.html", "Appointments", "calendar"],
      ["records.html", "Medical Records", "book"],
      ["bills.html", "Bills", "wallet"],
      ["complaints.html", "Complaints", "alert"],
      ["health-card.html", "Health Card", "card"]
    ]], ["AI ASSISTANT", [
      ["ai-chatbot.html", "AI Chatbot", "chat"],
      ["videos.html", "Health Videos", "play"]
    ]]]
  }
};

window.NAV_PERM_MAP = {
  admin: {
    "users.html": "users", "roles.html": "roles", "announcements.html": "announcements",
    "audit-logs.html": "audit", "settings.html": "settings", "shifts.html": "shifts",
    "ai-config.html": "ai", "documents.html": "documents", "patients.html": "patients",
    "wards.html": "wards", "reports.html": "reports"
  },
  manager: {
    "departments.html": "departments", "staff.html": "staff", "reports.html": "reports",
    "finance.html": "finance", "complaints.html": "complaints", "shifts.html": "shifts",
    "ai-insights.html": "ai", "settings.html": "settings", "documents.html": "documents",
    "patients.html": "patients", "wards.html": "wards"
  },
  doctor: {
    "patients.html": "patients", "beds.html": "bedrequests", "consultation.html": "consultation", "prescriptions.html": "prescriptions",
    "appointments.html": "appointments", "referrals.html": "referrals", "shifts.html": "shifts",
    "videos.html": "videos", "ai-diagnosis.html": "ai", "clinical-decision.html": "ai", "settings.html": "settings",
    "documents.html": "documents", "theatre.html": "theatre", "imaging.html": "imaging",
    "reports.html": "reports"
  },
  nurse: {
    "vitals.html": "vitals", "observations.html": "observations", "medications.html": "medications",
    "care-plans.html": "careplans", "shifts.html": "shifts", "settings.html": "settings",
    "documents.html": "documents", "patients.html": "patients", "beds.html": "beds",
    "reports.html": "reports"
  },
  pharmacist: {
    "prescriptions.html": "prescriptions", "inventory.html": "inventory", "suppliers.html": "suppliers",
    "shifts.html": "shifts", "ai-interaction.html": "ai", "ai-forecast.html": "ai",
    "settings.html": "settings", "documents.html": "documents", "patients.html": "patients",
    "reports.html": "reports"
  },
  laboratory: {
    "test-requests.html": "testrequests", "samples.html": "samples", "results.html": "results",
    "shifts.html": "shifts", "ai-analyzer.html": "ai", "settings.html": "settings",
    "documents.html": "documents", "patients.html": "patients", "blood-bank.html": "bloodbank",
    "reports.html": "reports"
  },
  reception: {
    "registration.html": "registration", "appointments.html": "appointments", "insurance.html": "insurance",
    "queue.html": "queue", "shifts.html": "shifts", "settings.html": "settings",
    "documents.html": "documents", "patients.html": "patients", "admissions.html": "admissions",
    "ambulance.html": "ambulance", "billing.html": "billing", "reports.html": "reports"
  },
  patient: {
    "appointments.html": "appointments", "records.html": "records", "bills.html": "bills",
    "complaints.html": "complaints", "videos.html": "videos", "ai-chatbot.html": "ai",
    "settings.html": "settings", "health-card.html": "healthcard"
  }
};

/* Five daily actions pinned to the bottom taskbar. The sidebar keeps the rest. */
window.NAV_TASKBAR = {
  admin: [
    ["dashboard.html", "Home", "grid"],
    ["users.html", "Users", "users"],
    ["patients.html", "Patients", "users"],
    ["wards.html", "Wards", "bed"],
    ["messages.html", "Messages", "mail"]
  ],
  manager: [
    ["dashboard.html", "Home", "grid"],
    ["staff.html", "Staff", "briefcase"],
    ["finance.html", "Finance", "wallet"],
    ["reports.html", "Reports", "chart"],
    ["messages.html", "Messages", "mail"]
  ],
  doctor: [
    ["dashboard.html", "Home", "grid"],
    ["patients.html", "Patients", "users"],
    ["consultation.html", "Consult", "stethoscope"],
    ["prescriptions.html", "Rx", "file-text"],
    ["messages.html", "Messages", "mail"]
  ],
  nurse: [
    ["dashboard.html", "Home", "grid"],
    ["vitals.html", "Vitals", "thermometer"],
    ["beds.html", "Beds", "bed"],
    ["medications.html", "Meds", "pill"],
    ["messages.html", "Messages", "mail"]
  ],
  pharmacist: [
    ["dashboard.html", "Home", "grid"],
    ["prescriptions.html", "Rx", "file-text"],
    ["inventory.html", "Stock", "package"],
    ["ai-interaction.html", "Interact", "zap"],
    ["messages.html", "Messages", "mail"]
  ],
  laboratory: [
    ["dashboard.html", "Home", "grid"],
    ["test-requests.html", "Tests", "flask"],
    ["samples.html", "Samples", "barcode"],
    ["results.html", "Results", "file-text"],
    ["messages.html", "Messages", "mail"]
  ],
  reception: [
    ["dashboard.html", "Home", "grid"],
    ["registration.html", "Register", "users"],
    ["appointments.html", "Appts", "calendar"],
    ["queue.html", "Queue", "list"],
    ["messages.html", "Messages", "mail"]
  ],
  patient: [
    ["dashboard.html", "Home", "grid"],
    ["appointments.html", "Appts", "calendar"],
    ["records.html", "Records", "book"],
    ["health-card.html", "Card", "card"],
    ["messages.html", "Messages", "mail"]
  ]
};
