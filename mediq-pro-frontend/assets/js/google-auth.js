/* Continue with Google. The client id stays on the backend. */
function mountGoogleContinue(opts) {
  var button = document.getElementById(opts.buttonId);
  if (!button) return;
  var picker = null;
  var ready = prepareGooglePicker(opts, button).then(function (client) {
    picker = client;
    return client;
  });
  button.addEventListener("click", function () {
    if (opts.before && opts.before() === false) return;
    if (picker) {
      picker.requestAccessToken({ prompt: "select_account" });
      return;
    }
    button.disabled = true;
    ready.then(function (client) {
      button.disabled = false;
      if (!client) {
        opts.onError("Google sign-in is not connected yet.");
        return;
      }
      client.requestAccessToken({ prompt: "select_account" });
    }).catch(function () {
      button.disabled = false;
      opts.onError("Cannot reach the server. Please try again.");
    });
  });
}

function prepareGooglePicker(opts, button) {
  return loadGoogleClient().then(function (clientId) {
    if (!clientId) return null;
    return loadGoogleScript().then(function () {
      return window.google.accounts.oauth2.initTokenClient({
        client_id: clientId,
        scope: "openid email profile",
        callback: function (response) {
          button.disabled = false;
          if (!response || response.error || !response.access_token) {
            if (response && (response.error === "popup_closed" || response.error === "access_denied")) {
              opts.onError("Choose a Google account to continue.");
              return;
            }
            opts.onError("Google did not return an account.");
            return;
          }
          opts.onAccessToken(response.access_token);
        },
        error_callback: function (error) {
          button.disabled = false;
          if (error && error.type === "popup_failed_to_open") {
            opts.onError("Allow popups to see the Google accounts on this device.");
            return;
          }
          opts.onError("Choose a Google account to continue.");
        }
      });
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
