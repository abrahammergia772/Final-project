import unittest

from fastapi import HTTPException

from routers.data import _belongs_to_user, _enforce_patient_body, _filter_rows


class DataAccessTests(unittest.TestCase):
    patient = {"sub": "U-008", "role": "patient", "name": "Abel Mekonnen"}
    staff = {"sub": "U-003", "role": "doctor", "name": "Dr. Daniel Alemu"}

    def test_patient_rows_are_filtered_to_their_own_name(self):
        result = {"items": [
            {"id": "P-1", "first_name": "Abel", "last_name": "Mekonnen"},
            {"id": "P-2", "first_name": "Hana", "last_name": "Wolde"},
        ], "total": 2, "source": "demo"}
        filtered = _filter_rows("patients", result, self.patient)
        self.assertEqual([row["id"] for row in filtered["items"]], ["P-1"])
        self.assertEqual(filtered["total"], 1)

    def test_staff_can_see_role_scoped_rows(self):
        row = {"patient": "Hana Wolde"}
        self.assertTrue(_belongs_to_user("patients", row, self.staff))

    def test_patient_submission_cannot_impersonate_another_patient(self):
        with self.assertRaises(HTTPException) as raised:
            _enforce_patient_body("appointments", {"patient": "Hana Wolde"}, self.patient)
        self.assertEqual(raised.exception.status_code, 403)

    def test_patient_complaint_is_attributed_to_authenticated_user(self):
        body = _enforce_patient_body("complaints", {"subject": "Wait time"}, self.patient)
        self.assertEqual(body["reporter"], "Abel Mekonnen")
        self.assertEqual(body["reporter_role"], "patient")


if __name__ == "__main__":
    unittest.main()
