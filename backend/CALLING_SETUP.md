# Audio and video calling setup

The app supports authenticated one-to-one and group calls for all roles. It supports either Jitsi as a Service (JaaS) or a separately deployed private JWT-authenticated Jitsi server. It does not support authenticating JaaS calls through `meet.jit.si`.

Users find participants by exact account email, select up to 20 people, and choose audio or video. Invitations appear while recipients are signed in with the app open, normally within eight seconds. No offline push is provided. The caller leaving ends invitations; invitations expire after one hour. Audio calls start with the camera muted.

## 1. Database and web prerequisites

- Run `sql/call_invites.sql` in your Supabase SQL editor. Existing installations that already ran it do not need to run it again.
- Set `SUPABASE_URL`, `SUPABASE_KEY`, and `SUPABASE_SERVICE_KEY` on the backend. The service-role key must stay on the backend.
- Use HTTPS for the frontend and ensure backend CORS allows its exact origin. Browser camera/microphone permissions must be granted.

## 2. Configure Jitsi as a Service (JaaS)

The public `meet.jit.si` site is not the JaaS service. JaaS uses `8x8.vc` and a room path prefixed by the application's AppID. The backend generates a separate, room-scoped RS256 JWT for each invited participant; only the call creator is given the moderator claim.

1. In the [JaaS console](https://jaas.8x8.vc/), open **API Keys**. Create or add an RSA key pair and keep the private key securely. If you lost a generated private key, create a replacement key pair in the console; it cannot be recovered there. See [JaaS API keys](https://developer.8x8.com/jaas/docs/jaas-console-api-keys/).
2. On the Render **backend web service** (not the frontend), set these environment variables:
   - `CALL_PROVIDER`: `jaas`
   - `JAAS_APP_ID`: the full JaaS AppID, beginning `vpaas-magic-cookie-`.
   - `JAAS_KEY_ID`: the full key ID (`kid`) shown for the uploaded public key, including the AppID and slash.
   - `JAAS_PRIVATE_KEY`: the corresponding RSA private key in PEM format. Use a multiline secret value, or a single line with literal `\n` where each line break belongs. Use an unencrypted RSA key of at least 2048 bits.
3. Save and redeploy the backend so it installs the updated requirements and reads these settings. Redeploy the frontend too. Refresh your browser and start a **new** call.
4. Test with two different accounts. The caller must join as moderator and the recipient must accept their invitation. Verify unauthorized users and tokens for another room cannot join. Review your JaaS account's security and access settings separately.

Never paste the private key, JWT, service-role key, or meeting links into a chat, public issue, frontend file, or repository. `JITSI_DOMAIN` and `JITSI_APP_SECRET` are for the private-server mode and are not used when `CALL_PROVIDER=jaas`. Merely changing the domain to `8x8.vc` without the code and settings above will not work.

## 3. Alternative: private Jitsi server

To use an independent server instead of JaaS, set `CALL_PROVIDER=private` (or omit it), `JITSI_DOMAIN` to the server's HTTPS hostname without `https://` or a path, `JITSI_APP_ID` to its JWT issuer, and `JITSI_APP_SECRET` to the server-only shared secret. The private Jitsi server must require and validate HS256 tokens, accept audience `jitsi` and the configured issuer, and validate the subject (the configured hostname) and room. Disable anonymous room access. Configure TURN and required network ports. The API cannot enforce who enters a meeting on an anonymously accessible Jitsi server. Verify missing, invalid, expired, and wrong-room JWTs are rejected.

## Safety and operational limitations

**This integration is not yet approved or verified for real patient information.** The meeting service receives participant names and media. TLS does not by itself provide end-to-end encryption or regulatory compliance. The hospital must assess hosting, privacy, consent, recording, retention, audit, access policies, role/relationship restrictions, account security, and applicable laws before clinical use. Server-provided Jitsi scripts must be trusted and maintained.

Exact-email lookup limits casual browsing of the user directory but is not a complete defense against account enumeration; add rate limiting and relationship-based authorization before production. An issued JWT cannot be revoked by this API once delivered; ending a call updates app invitations and connected app clients leave on their next poll, but cannot guarantee immediate removal of a copied token or an external Jitsi client. Configure meeting-service moderation and revocation controls if needed. If a host closes the tab without leaving, invitations may remain active until expiry. Clean up expired records on a schedule according to the hospital's retention policy. Test the deployed system—including token validation and both browsers—before relying on it.
