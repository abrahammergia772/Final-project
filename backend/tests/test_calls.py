"""Offline API tests for call invitations; a real Jitsi server is not required."""
import base64
import hashlib
import hmac
import json
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import calls
from security import issue_token


class FakeQuery:
    def __init__(self, store, table):
        self.store, self.table_name = store, table
        self.filters = []
        self.operation, self.values = 'select', None
    def select(self, *args): return self
    def eq(self, key, value): self.filters.append(lambda r: r.get(key) == value); return self
    def in_(self, key, values): self.filters.append(lambda r: r.get(key) in values); return self
    def gt(self, key, value): self.filters.append(lambda r: r.get(key, '') > value); return self
    def limit(self, value): return self
    def order(self, *args, **kwargs): return self
    def insert(self, rows): self.operation, self.values = 'insert', rows; return self
    def update(self, values): self.operation, self.values = 'update', values; return self
    def execute(self):
        rows = self.store[self.table_name]
        if self.operation == 'insert':
            from datetime import datetime, timezone
            for row in self.values:
                row = dict(row); row.setdefault('created_at', datetime.now(timezone.utc).isoformat()); rows.append(row)
            return SimpleNamespace(data=self.values)
        found = [r for r in rows if all(fn(r) for fn in self.filters)]
        if self.operation == 'update':
            for row in found: row.update(self.values)
        return SimpleNamespace(data=[dict(r) for r in found])


class FakeDatabase:
    def __init__(self):
        self.store = {'users': [
            {'id': 'doc', 'email': 'doc@example.org', 'name': 'Doctor', 'role': 'doctor', 'status': 'active'},
            {'id': 'nurse', 'email': 'nurse@example.org', 'name': 'Nurse', 'role': 'nurse', 'status': 'active'},
            {'id': 'patient', 'email': 'patient@example.org', 'name': 'Patient', 'role': 'patient', 'status': 'active'},
            {'id': 'outsider', 'email': 'outsider@example.org', 'name': 'Other', 'role': 'manager', 'status': 'active'},
            {'id': 'inactive', 'email': 'inactive@example.org', 'name': 'Inactive', 'role': 'doctor', 'status': 'inactive'},
        ], 'call_invites': []}
    def table(self, name): return FakeQuery(self.store, name)


@pytest.fixture
def setup(monkeypatch):
    db = FakeDatabase()
    monkeypatch.setattr(calls, 'get_client', lambda: db)
    monkeypatch.setattr(calls, 'SUPABASE_SERVICE_KEY', 'server-only-key')
    monkeypatch.setenv('JITSI_DOMAIN', 'meet.hospital.example')
    monkeypatch.setenv('JITSI_APP_ID', 'hospital')
    monkeypatch.setenv('JITSI_APP_SECRET', 'jitsi-test-secret')
    app = FastAPI(); app.include_router(calls.router)
    return TestClient(app), db


def auth(user, role):
    return {'Authorization': 'Bearer ' + issue_token(user, role)}


def test_group_call_requires_invitation_and_ends_for_all(setup):
    client, db = setup
    doctor, nurse, patient, outsider = [auth(*x) for x in [('doc', 'doctor'), ('nurse', 'nurse'), ('patient', 'patient'), ('outsider', 'manager')]]
    assert client.get('/calls').status_code == 401
    directory = client.post('/calls/directory', headers=doctor, json={'email': 'nurse@example.org'}).json()['items']
    assert {x['id'] for x in directory} == {'nurse'}
    response = client.post('/calls', headers=doctor, json={'recipients': ['nurse', 'patient'], 'mode': 'audio'})
    assert response.status_code == 200
    call_id = response.json()['call_id']
    assert client.get('/calls', headers=nurse).json()['items'][0]['status'] == 'pending'
    assert client.post(f'/calls/{call_id}/join', headers=outsider).status_code == 404
    joined = client.post(f'/calls/{call_id}/join', headers=nurse)
    assert joined.status_code == 200 and joined.json()['mode'] == 'audio'
    token = joined.json()['token']; head, body, signature = token.split('.')
    expected = base64.urlsafe_b64encode(hmac.new(b'jitsi-test-secret', (head + '.' + body).encode(), hashlib.sha256).digest()).rstrip(b'=').decode()
    assert signature == expected
    claims = json.loads(base64.urlsafe_b64decode(body + '=' * (-len(body) % 4)))
    assert claims['room'] == joined.json()['room'] and claims['context']['user']['id'] == 'nurse'
    assert client.post(f'/calls/{call_id}/decline', headers=patient).status_code == 200
    assert client.post(f'/calls/{call_id}/join', headers=patient).status_code == 410
    assert client.post(f'/calls/{call_id}/leave', headers=doctor).status_code == 200
    assert client.get('/calls', headers=nurse).json()['items'] == []
    assert client.post(f'/calls/{call_id}/join', headers=nurse).status_code == 410


def test_invalid_recipients_and_configuration_fail_closed(setup, monkeypatch):
    client, db = setup; doctor = auth('doc', 'doctor')
    assert client.post('/calls', headers=doctor, json={'recipients': ['inactive'], 'mode': 'video'}).status_code == 422
    assert client.post('/calls', headers=doctor, json={'recipients': ['doc'], 'mode': 'audio'}).status_code == 422
    monkeypatch.delenv('JITSI_APP_SECRET')
    assert client.post('/calls', headers=doctor, json={'recipients': ['nurse'], 'mode': 'video'}).status_code == 503
    assert not db.store['call_invites']
    monkeypatch.setenv('JITSI_APP_SECRET', 'secret')
    monkeypatch.setenv('JITSI_DOMAIN', 'https://public.example/path')
    assert client.post('/calls', headers=doctor, json={'recipients': ['nurse'], 'mode': 'video'}).status_code == 503
