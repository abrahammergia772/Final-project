"""JaaS token and invitation behavior, tested offline with a temporary RSA key."""
import base64
import json
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from test_calls import setup, auth  # shared test database fixture


def decode(segment):
    return json.loads(base64.urlsafe_b64decode(segment + '=' * (-len(segment) % 4)))


def enable_jaas(monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                            serialization.NoEncryption()).decode()
    app_id = 'vpaas-magic-cookie-test123'
    monkeypatch.setenv('CALL_PROVIDER', 'jaas')
    monkeypatch.setenv('JAAS_APP_ID', app_id)
    monkeypatch.setenv('JAAS_KEY_ID', app_id + '/key123')
    # Test Render-compatible literal newline representation too.
    monkeypatch.setenv('JAAS_PRIVATE_KEY', pem.replace('\n', '\\n'))
    return key, app_id


def test_jaas_uses_rsa_room_scope_and_correct_moderator(setup, monkeypatch):
    client, db = setup
    key, app_id = enable_jaas(monkeypatch)
    doctor, nurse = auth('doc', 'doctor'), auth('nurse', 'nurse')
    created = client.post('/calls', headers=doctor, json={'recipients': ['nurse'], 'mode': 'video'})
    assert created.status_code == 200
    call_id = created.json()['call_id']
    host = client.post('/calls/' + call_id + '/join', headers=doctor).json()
    guest = client.post('/calls/' + call_id + '/join', headers=nurse).json()
    for response, is_host in [(host, True), (guest, False)]:
        assert response['domain'] == '8x8.vc' and response['provider'] == 'jaas'
        assert response['app_id'] == app_id and response['room'].startswith(app_id + '/wsh-')
        head, body, sig = response['token'].split('.')
        header, payload = decode(head), decode(body)
        key.public_key().verify(base64.urlsafe_b64decode(sig + '=' * (-len(sig) % 4)),
                                (head + '.' + body).encode(), padding.PKCS1v15(), hashes.SHA256())
        assert header == {'alg': 'RS256', 'kid': app_id + '/key123', 'typ': 'JWT'}
        assert payload['iss'] == 'chat' and payload['sub'] == app_id and payload['aud'] == 'jitsi'
        assert payload['room'] == response['room'].split('/')[1] != '*'
        assert payload['context']['user']['moderator'] is is_host
        assert payload['context']['features']['recording'] is False


def test_jaas_fails_closed_if_configuration_invalid(setup, monkeypatch):
    client, db = setup; enable_jaas(monkeypatch)
    doctor = auth('doc', 'doctor')
    monkeypatch.setenv('JAAS_KEY_ID', 'another-app/key')
    assert client.post('/calls', headers=doctor, json={'recipients':['nurse'], 'mode':'video'}).status_code == 503
    assert not db.store['call_invites']
    monkeypatch.setenv('JAAS_KEY_ID', 'vpaas-magic-cookie-test123/key123')
    monkeypatch.setenv('JAAS_PRIVATE_KEY', 'not a private key')
    assert client.post('/calls', headers=doctor, json={'recipients':['nurse'], 'mode':'video'}).status_code == 503


def test_public_jitsi_rejected_in_private_mode(setup, monkeypatch):
    client, db = setup
    monkeypatch.setenv('JITSI_DOMAIN', 'meet.jit.si')
    result = client.post('/calls', headers=auth('doc','doctor'), json={'recipients':['nurse'], 'mode':'audio'})
    assert result.status_code == 503 and 'JaaS' in result.json()['detail']
