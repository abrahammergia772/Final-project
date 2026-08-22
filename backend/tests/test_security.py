import hashlib
import unittest

from fastapi import HTTPException

from routers.auth import DEMO_PASSWORDS, LoginRequest, login
from security import decode_token, hash_password, issue_token, verify_password


class SecurityTests(unittest.TestCase):
    def test_password_hash_is_salted_and_verifies(self):
        first = hash_password("correct horse battery staple")
        second = hash_password("correct horse battery staple")
        self.assertNotEqual(first, second)
        self.assertTrue(verify_password("correct horse battery staple", first))
        self.assertFalse(verify_password("wrong password", first))
        self.assertTrue(verify_password("admin123", hashlib.sha256(b"admin123").hexdigest()))

    def test_signed_token_round_trip_and_tamper_detection(self):
        token = issue_token("U-001", "admin", name="Solomon Tadesse")
        claims = decode_token(token)
        self.assertEqual(claims["sub"], "U-001")
        self.assertEqual(claims["role"], "admin")
        self.assertEqual(claims["name"], "Solomon Tadesse")
        with self.assertRaises(HTTPException):
            decode_token(token[:-1] + ("0" if token[-1] != "0" else "1"))

    def test_demo_login_is_available_without_database(self):
        response = login(LoginRequest(email="admin@mediq.pro", password=DEMO_PASSWORDS["admin@mediq.pro"]))
        self.assertEqual(response["role"], "admin")
        self.assertNotIn("password", response)

    def test_malformed_token_is_a_401_not_a_server_error(self):
        with self.assertRaises(HTTPException) as raised:
            decode_token("not.a.valid.token")
        self.assertEqual(raised.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
