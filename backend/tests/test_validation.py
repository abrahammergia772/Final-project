import unittest

from pydantic import ValidationError

from routers.appointment import AppointmentRequest
from routers.vitals import VitalsRequest


class ValidationTests(unittest.TestCase):
    def test_appointment_rejects_bad_date(self):
        with self.assertRaises(ValidationError):
            AppointmentRequest(appointment_date="08/22/2026")

    def test_vitals_require_a_complete_blood_pressure_pair(self):
        with self.assertRaises(ValidationError):
            VitalsRequest(sys=120)
        with self.assertRaises(ValidationError):
            VitalsRequest(sys=80, dia=90)

    def test_vitals_accept_normal_values(self):
        values = VitalsRequest(hr=72, sys=118, dia=76, temp=36.8, spo2=98, rr=16, age=34)
        self.assertEqual(values.hr, 72)


if __name__ == "__main__":
    unittest.main()
