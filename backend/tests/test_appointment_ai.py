"""Appointment assistant uses saved rows, not a trained model."""
from datetime import date

from routers.appointment import choose_gap, open_slots, risk_from_history


def test_open_slots_skip_a_booked_time():
    rows = [{"doctor": "Dr. Daniel Alemu", "date": "2026-10-19", "time": "09:00", "status": "confirmed"}]
    slots = open_slots(rows, "Dr. Daniel Alemu", "Cardiology", date(2026, 10, 19), 1)
    assert slots
    assert all(not (item["date"] == "2026-10-19" and item["time"] == "09:00") for item in slots)


def test_no_history_is_not_scored():
    risk = risk_from_history([], "Abel Mekonnen", date(2026, 10, 16))
    assert risk["no_show_percent"] is None
    assert risk["risk_level"] == "Unknown"


def test_missed_visits_set_the_risk():
    rows = [
        {"patient": "Abel Mekonnen", "date": "2026-10-01", "status": "cancelled"},
        {"patient": "Abel Mekonnen", "date": "2026-10-02", "status": "completed"},
    ]
    risk = risk_from_history(rows, "Abel Mekonnen", date(2026, 10, 16))
    assert risk["no_show_percent"] == 50.0
    assert risk["missed_visits"] == 1


def test_cancelled_slot_moves_a_later_visit_with_the_same_doctor():
    freed = {"id": "1", "doctor": "Dr. Daniel Alemu", "date": "2026-10-20", "time": "09:00"}
    rows = [
        freed,
        {"id": "2", "patient": "Abel", "doctor": "Dr. Daniel Alemu", "date": "2026-10-22", "time": "11:00", "status": "confirmed"},
        {"id": "3", "patient": "Hana", "doctor": "Dr. Meron Assefa", "date": "2026-10-21", "time": "09:00", "status": "confirmed"},
    ]
    chosen = choose_gap(rows, freed)
    assert chosen["id"] == "2"
