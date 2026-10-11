"""Google identity checks. No network."""
import google_auth


def test_google_identity_accepts_verified_account():
    identity = google_auth.parse_identity({
        "aud": "client-123",
        "iss": "https://accounts.google.com",
        "email": "Person@Gmail.com",
        "email_verified": True,
        "sub": "abc",
        "name": "Abel Mekonnen",
    }, "client-123")
    assert identity["email"] == "person@gmail.com"
    assert identity["name"] == "Abel Mekonnen"
    assert identity["sub"] == "abc"


def test_google_identity_rejects_other_app_and_unverified_email():
    payload = {
        "aud": "other-app",
        "iss": "https://accounts.google.com",
        "email": "person@gmail.com",
        "email_verified": True,
        "sub": "abc",
    }
    try:
        google_auth.parse_identity(payload, "client-123")
        assert False
    except google_auth.GoogleAuthError as exc:
        assert exc.code == "audience"
    payload["aud"] = "client-123"
    payload["email_verified"] = False
    try:
        google_auth.parse_identity(payload, "client-123")
        assert False
    except google_auth.GoogleAuthError as exc:
        assert exc.code == "unverified"
