/* Audio/video calling through an explicitly configured Jitsi deployment. */
(function () {
  'use strict';
  var timer = null, currentCall = null, conference = null, busy = false, lastItems = [], pollToken = null;
  var selectedPeople = new Map(), searchResult = null;
  var observer = new MutationObserver(function () {
    if (currentCall && !document.getElementById('callMeeting')) leaveMeeting();
  });
  observer.observe(document.body, {childList: true, subtree: true});
  // Start the leave request before the existing logout handler clears the token.
  document.addEventListener('click', function (event) {
    if (currentCall && event.target.closest && event.target.closest('[data-logout]')) leaveMeeting();
  }, true);

  function el(id) { return document.getElementById(id); }
  function text(node, value) { if (node) node.textContent = value; }
  function api(path, method, body) { return apiFetch('/calls' + path, method || 'GET', body || null, {quiet: true}); }
  function message(value, error) {
    var node = el('callMessage');
    if (node) { node.textContent = value || ''; node.className = error ? 'call-message is-error' : 'call-message'; }
  }
  function goToCalls() {
    var role = getUserRole();
    if (window.SPA && window.SPA.mode) window.SPA.load(role + '/calls.html');
    else location.href = 'calls.html';
  }
  function incoming(items) {
    var pending = items.filter(function (item) { return item.status === 'pending'; });
    var banner = el('incomingCallBanner');
    if (!pending.length || el('callPage')) { if (banner) banner.remove(); return; }
    if (!banner) {
      banner = document.createElement('div'); banner.id = 'incomingCallBanner';
      banner.setAttribute('role', 'status');
      banner.style.cssText = 'position:fixed;right:16px;bottom:16px;z-index:9999;padding:16px;background:#11212d;color:white;border-radius:12px;box-shadow:0 8px 30px #0004;max-width:320px;font:15px sans-serif';
      var label = document.createElement('div'); label.id = 'incomingCallText';
      var button = document.createElement('button'); button.type = 'button'; button.textContent = 'View invitation';
      button.style.cssText = 'margin-top:10px;background:white;color:#11212d;border:0;border-radius:6px;padding:8px 12px;cursor:pointer';
      button.onclick = goToCalls; banner.appendChild(label); banner.appendChild(button); document.body.appendChild(banner);
    }
    text(el('incomingCallText'), pending[0].caller_name + ' is inviting you to a ' + pending[0].mode + ' call' + (pending.length > 1 ? ' (+' + (pending.length - 1) + ' more)' : '') + '.');
  }
  async function refresh() {
    var session = getSession(), token = session && session.token;
    if (pollToken !== token) {
      pollToken = token; lastItems = []; selectedPeople.clear(); searchResult = null;
      if (el('incomingCallBanner')) el('incomingCallBanner').remove();
      if (currentCall) disposeMeeting();
      renderList();
    }
    if (busy || !token) return;
    busy = true;
    try {
      var result = await api('');
      if (!getSession() || getSession().token !== token) return;
      if (!result.ok) { if (el('callPage')) message(result.error || 'Could not load calls.', true); return; }
      lastItems = result.data.items || [];
      incoming(lastItems);
      if (currentCall && !lastItems.some(function (i) { return i.call_id === currentCall && i.status === 'accepted'; })) {
        disposeMeeting(); message('The call has ended or expired.');
      }
      renderList();
    } finally { busy = false; }
  }
  function startPolling() { if (!timer) { refresh(); timer = setInterval(refresh, 8000); } }
  function renderList() {
    var list = el('callInvitations'); if (!list) return;
    list.replaceChildren();
    if (!lastItems.length) { var empty = document.createElement('p'); empty.textContent = 'No current calls or invitations.'; list.appendChild(empty); return; }
    lastItems.forEach(function (item) {
      var row = document.createElement('div'); row.className = 'call-row';
      var detail = document.createElement('span');
      detail.textContent = (item.status === 'pending' ? 'Invitation from ' : 'Call started by ') + item.caller_name + ' · ' + item.mode;
      var actions = document.createElement('div'); actions.className = 'call-actions';
      var join = document.createElement('button'); join.className = 'btn btn-primary'; join.type = 'button'; join.textContent = item.status === 'pending' ? 'Accept & join' : 'Join';
      join.disabled = !!currentCall; join.onclick = function () { joinMeeting(item.call_id); }; actions.appendChild(join);
      if (item.status === 'pending') {
        var decline = document.createElement('button'); decline.className = 'btn btn-outline'; decline.type = 'button'; decline.textContent = 'Decline';
        decline.onclick = async function () { var r = await api('/' + encodeURIComponent(item.call_id) + '/decline', 'POST'); if (!r.ok) message(r.error, true); await refresh(); };
        actions.appendChild(decline);
      }
      row.appendChild(detail); row.appendChild(actions); list.appendChild(row);
    });
  }
  function renderDirectory() {
    var container = el('callDirectory'); if (!container) return;
    container.replaceChildren();
    var people = Array.from(selectedPeople.values());
    if (searchResult && !selectedPeople.has(searchResult.id)) people.push(searchResult);
    if (!people.length) { text(container, 'Search for a participant by email.'); return; }
    people.forEach(function (person) {
      var label = document.createElement('label'); label.className = 'call-person';
      var box = document.createElement('input'); box.type = 'checkbox'; box.checked = selectedPeople.has(person.id);
      box.onchange = function () {
        if (box.checked) selectedPeople.set(person.id, person); else selectedPeople.delete(person.id);
        renderDirectory();
      };
      var name = document.createElement('span'); name.textContent = person.name + ' · ' + person.role;
      label.appendChild(box); label.appendChild(name); container.appendChild(label);
    });
  }
  async function findPerson() {
    var input = el('callSearch'), email = input.value.trim();
    if (!input.validity.valid || !email) { message('Enter a complete account email address.', true); return; }
    message('Searching…');
    var result = await api('/directory', 'POST', {email: email});
    if (!el('callPage')) return;
    if (!result.ok) { message(result.error || 'Could not find the participant.', true); return; }
    searchResult = (result.data.items || [])[0] || null;
    renderDirectory();
    message(searchResult ? 'Select the person to add them to the call.' : 'No active account found for that email.', !searchResult);
  }
  function jitsiScript(domain) {
    return new Promise(function (resolve, reject) {
      if (window.JitsiMeetExternalAPI) { resolve(); return; }
      var script = document.createElement('script'); script.src = 'https://' + domain + '/external_api.js';
      script.onload = resolve; script.onerror = function () { script.remove(); reject(new Error('Could not load the configured Jitsi server.')); };
      document.head.appendChild(script);
    });
  }
  async function joinMeeting(id) {
    if (currentCall) { message('Leave the current call first.', true); return; }
    message('Connecting to Jitsi…');
    var result = await api('/' + encodeURIComponent(id) + '/join', 'POST');
    if (!result.ok) { message(result.error || 'Unable to join.', true); await refresh(); return; }
    var data = result.data;
    try {
      await jitsiScript(data.domain);
      var target = el('callMeeting'); if (!target) return;
      target.hidden = false; target.replaceChildren();
      currentCall = id;
      conference = new JitsiMeetExternalAPI(data.domain, {
        roomName: data.room, jwt: data.token, parentNode: target, width: '100%', height: 560,
        userInfo: {displayName: data.name},
        configOverwrite: {startWithVideoMuted: data.mode === 'audio', prejoinPageEnabled: true},
        interfaceConfigOverwrite: {MOBILE_APP_PROMO: false}
      });
      conference.addListener('readyToClose', function () { leaveMeeting(); });
      el('callEnd').hidden = false;
      message('Use the Jitsi controls to mute, turn your camera on or off, and leave.');
      renderList();
    } catch (e) { disposeMeeting(); message(e.message || 'Could not start the meeting.', true); }
  }
  function disposeMeeting() {
    var previous = conference; conference = null; currentCall = null;
    if (previous) { try { previous.dispose(); } catch (e) {} }
    if (el('callMeeting')) { el('callMeeting').replaceChildren(); el('callMeeting').hidden = true; }
    if (el('callEnd')) el('callEnd').hidden = true;
    renderList();
  }
  async function leaveMeeting() {
    var id = currentCall; if (!id) return;
    disposeMeeting();
    var result = await api('/' + encodeURIComponent(id) + '/leave', 'POST');
    message(result.ok ? 'You left the call.' : (result.error || 'Could not update the call.'), !result.ok);
    await refresh();
  }
  async function mount() {
    startPolling();
    var banner = el('incomingCallBanner'); if (banner) banner.remove();
    selectedPeople.clear(); searchResult = null; renderDirectory();
    el('callFind').onclick = findPerson;
    el('callSearch').onkeydown = function (event) { if (event.key === 'Enter') { event.preventDefault(); findPerson(); } };
    el('callStart').onclick = async function () {
      if (currentCall) { message('Leave the current call before starting another.', true); return; }
      var selected = Array.from(selectedPeople.keys());
      if (!selected.length || selected.length > 20) { message('Select between 1 and 20 participants.', true); return; }
      var button = el('callStart'); button.disabled = true; message('Sending invitations…');
      try {
        var result = await api('', 'POST', {recipients: selected, mode: el('callMode').value});
        if (!result.ok) { message(result.error || 'Could not start the call.', true); return; }
        await refresh(); await joinMeeting(result.data.call_id);
      } finally { if (button.isConnected) button.disabled = false; }
    };
    el('callEnd').onclick = leaveMeeting;
    await refresh(); renderList();
  }
  window.HospitalCalls = {mount: mount, startPolling: startPolling};
})();
