import unittest

from fastapi.testclient import TestClient

from main import app


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = TestClient(app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.context.__exit__(None, None, None)

    def test_health_is_public_and_does_not_expose_secrets(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertNotIn("SECRET_KEY", response.text)
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")

    def test_data_routes_require_authentication(self):
        response = self.client.get("/patients")
        self.assertEqual(response.status_code, 401)

    def test_malformed_json_is_rejected_by_validation(self):
        response = self.client.post("/auth/login", json={"email": "not-an-email", "password": "x"})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
