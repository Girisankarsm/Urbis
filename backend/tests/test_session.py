from app.services.session import create_session_token, decode_session_token


def test_session_roundtrip():
    token = create_session_token(user_id="user-123", email="citizen@example.com", name="Citizen")
    payload = decode_session_token(token)
    assert payload is not None
    assert payload["sub"] == "user-123"
    assert payload["email"] == "citizen@example.com"


def test_session_rejects_tampered_token():
    token = create_session_token(user_id="user-123", email="citizen@example.com", name="Citizen")
    assert decode_session_token(token + "x") is None
