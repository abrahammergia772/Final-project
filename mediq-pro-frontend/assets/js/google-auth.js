/* Continue with Google. The client id stays on the backend. */
function mountGoogleContinue(opts) {
  var button = document.getElementById(opts.buttonId);
  if (!button) return;
  button.addEventListener("click", function () {
    if (opts.before && opts.before() === false) return;
    button.disabled = true;
    loadGoogleClient().then(function (clientId) {
      if (!clientId) {
        button.disabled = false;
        opts.onError("Google sign-in is not connected yet.");
        return;
      }
      return loadGoogleScript().then(function () {
        openGoogleAccount(clientId, opts, button);
      });
    }).catch(function () {
      button.disabled = false;
      opts.onError("Cannot reach the server. Please try again.");
    });
  });
}

function loadGoogleClient() {
  return fetch(CONFIG.API_BASE_URL + "/auth/google-client", { headers: { "Accept": "application/json" } })
    .then(function (res) { return res.json(); })
    .then(function (data) { return (data && data.client_id) || ""; });
}

function loadGoogleScript() {
  if (window.google && window.google.accounts && window.google.accounts.id) {
    return Promise.resolve();
  }
  return new Promise(function (resolve, reject) {
    var existing = document.getElementById("googleGsi");
    if (existing) {
      existing.addEventListener("load", function () { resolve(); });
      existing.addEventListener("error", function () { reject(new Error("script")); });
      return;
    }
    var script = document.createElement("script");
    script.id = "googleGsi";
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.onload = function () { resolve(); };
    script.onerror = function () { reject(new Error("script")); };
    document.head.appendChild(script);
  });
}

function openGoogleAccount(clientId, opts, button) {
  var host = document.getElementById(opts.hostId);
  if (!host) {
    host = document.createElement("div");
    host.id = opts.hostId;
    host.className = "google-host";
    host.setAttribute("aria-hidden", "true");
    document.body.appendChild(host);
  }
  window.google.accounts.id.initialize({
    client_id: clientId,
    callback: function (response) {
      button.disabled = false;
      if (!response || !response.credential) {
        opts.onError("Google did not return an account.");
        return;
      }
      opts.onCredential(response.credential);
    },
    auto_select: false,
    cancel_on_tap_outside: true,
    use_fedcm_for_prompt: false
  });
  host.innerHTML = "";
  window.google.accounts.id.renderButton(host, {
    type: "standard",
    theme: "outline",
    size: "large",
    text: "continue_with",
    shape: "rectangular",
    width: 320
  });
  window.setTimeout(function () {
    var inner = host.querySelector("[role='button']");
    if (inner) inner.click();
    else window.google.accounts.id.prompt();
    button.disabled = false;
  }, 60);
}

function saveGoogleSession(data) {
  saveSession({
    token: data.token,
    role: data.role,
    user_id: data.user_id,
    name: data.name,
    email: data.email,
    health_card: data.health_card && data.health_card.id,
    portal: ""
  });
}
