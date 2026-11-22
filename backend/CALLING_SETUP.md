# Audio and video calling setup

The application includes Jitsi-based one-to-one and group calls for all eight roles. Users find participants by their exact account email, select up to 20 people, and start an audio or video call. Invitations are polled about every eight seconds while the recipient is signed in with the app open. They can accept or decline on the Calls page. Audio calls start with the camera muted; users can control audio/video in Jitsi. The caller leaving ends invitations for the whole group; other participants leaving only removes their own invitation. Invitations expire after one hour. There is no offline push notification or call recording built into this app.

## Required deployment

1. Run `sql/call_invites.sql` in the Supabase SQL editor. It enables RLS and revokes browser access. Keep the Supabase service-role key on the backend only.
2. Deploy a **private, HTTPS Jitsi Meet server** with JWT authentication enabled and anonymous/guest room access disabled. Configure its accepted issuer, audience and domain to match the settings below; test that it rejects missing, invalid, expired, and wrong-room tokens. Use a Jitsi deployment compatible with HS256 JWT authentication and Jitsi's external iframe API. Configure TURN for restrictive networks and set the appropriate iframe/permissions policies for camera and microphone.
3. Set these backend environment variables, then redeploy the API:
   - `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` — existing database URL and server-only service-role key.
   - `JITSI_DOMAIN` — Jitsi host, optionally with port, **without** `https://` or a path, for example `meet.example.org`.
   - `JITSI_APP_ID` — accepted Jitsi JWT issuer.
   - `JITSI_APP_SECRET` — strong shared secret used by the Jitsi JWT verifier; never put it in browser files or the repository.
4. Serve the frontend over HTTPS, point `CONFIG.API_BASE_URL` at the updated API, and configure backend CORS for the frontend origin. Redeploy the frontend. Camera and microphone permission must be allowed in the browser.
5. Sign in as two different users in separate browsers, open the app for both, and test an individual call, a group call, audio-only, decline, leaving and ending. Verify that a non-invited account and a direct room URL without a valid token cannot join. Check restrictive-network connectivity.

The backend rejects call creation and joining when the Jitsi settings are absent; it does not silently fall back to a public Jitsi service. Once configured, the app generates random room names and short-lived, room-scoped signed Jitsi JWTs only for invited active accounts. Tokens expire within 30 minutes (or sooner if the invitation expires).

## Safety and operational limitations

**This integration is not yet approved or verified for real patient information.** Jitsi must actually enforce JWT validation and room restrictions: the API alone cannot secure an anonymously accessible Jitsi server. The meeting service receives participant names and media. TLS in transit does not by itself provide end-to-end encryption or regulatory compliance. The hospital must assess hosting, privacy, consent, recording, retention, audit, access policies, role/relationship restrictions, account security, and applicable laws before clinical use. Jitsi scripts are loaded from the configured server, which must be trusted and maintained.

Exact-email lookup limits casual browsing of the user directory but is not a complete defense against account enumeration; add rate limiting and relationship-based authorization before production. An issued JWT cannot be revoked by the API once delivered; ending a call updates app invitations and connected app clients leave on their next poll, but cannot guarantee immediate removal of a copied token or an external Jitsi client. Configure Jitsi-side moderation and revocation controls if needed. If a host closes the tab without leaving, invitations may remain active until expiry. Clean up expired records on a schedule according to the hospital's retention policy. Test the complete deployed system, including Jitsi token validation and both browsers, before relying on it.
