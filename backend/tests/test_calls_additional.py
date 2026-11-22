"""Additional individual-call and expiration tests using the fake database."""
from datetime import datetime, timedelta, timezone

from test_calls import setup, auth  # pytest fixture and shared in-memory service


def test_individual_video_call_and_leaving(setup):
    client, db = setup
    doctor, patient = auth('doc', 'doctor'), auth('patient', 'patient')
    call = client.post('/calls', headers=doctor, json={'recipients': ['patient'], 'mode': 'video'}).json()['call_id']
    assert client.post(f'/calls/{call}/join', headers=patient).json()['mode'] == 'video'
    assert client.post(f'/calls/{call}/leave', headers=patient).status_code == 200
    assert client.post(f'/calls/{call}/join', headers=patient).status_code == 410
    assert client.get('/calls', headers=doctor).json()['items'][0]['status'] == 'accepted'


def test_expired_call_and_inactive_account_cannot_join(setup):
    client, db = setup
    doctor, patient = auth('doc', 'doctor'), auth('patient', 'patient')
    call = client.post('/calls', headers=doctor, json={'recipients': ['patient'], 'mode': 'audio'}).json()['call_id']
    expiry = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    for row in db.store['call_invites']: row['expires_at'] = expiry
    assert client.get('/calls', headers=patient).json()['items'] == []
    assert client.post(f'/calls/{call}/join', headers=patient).status_code == 410
    db.store['users'][2]['status'] = 'inactive'
    assert client.get('/calls', headers=patient).status_code == 403
