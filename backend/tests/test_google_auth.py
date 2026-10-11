"""Google identity checks. No network."""
import google_auth


def test_pasted_client_address_is_cleaned():
    raw = "https://4041090243-ubu08f0g2n73n7tueo4bo9n14qv8v6pq.apps.googleusercontent.com"
    assert google_auth.clean_client_id(raw) == "4041090243-ubu08f0g2n73n7tueo4bo9n14qv8v6pq.apps.googleusercontent.com"


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


def test_access_token_identity_accepts_account_chooser_payload():
    identity = google_auth.parse_access_identity({
        "audience": "client-123",
        "email": "Nurse@Gmail.com",
        "verified_email": True,
        "user_id": "99",
        "name": "Sara Bekele",
    }, "client-123")
    assert identity["email"] == "nurse@gmail.com"
    assert identity["sub"] == "99"
    assert identity["name"] == "Sara Bekele"


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
