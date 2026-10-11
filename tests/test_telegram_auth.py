import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from fastapi import HTTPException

from app.services.telegram import validate_webapp_init_data


def _make_init_data(bot_token: str, user_id: int = 42, auth_date: int | None = None) -> str:
    if auth_date is None:
        auth_date = int(time.time())
    user = json.dumps({"id": user_id, "first_name": "Test"}, separators=(",", ":"))
    pairs = {"auth_date": str(auth_date), "user": user}
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    sig = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    pairs["hash"] = sig
    return urlencode(pairs)


def test_validate_init_data_ok():
    token = "123456:ABC-DEF"
    raw = _make_init_data(token)
    user = validate_webapp_init_data(raw, token)
    assert user["id"] == 42


def test_validate_rejects_missing_auth_date():
    token = "123456:ABC-DEF"
    user = json.dumps({"id": 1})
    pairs = {"user": user}
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    pairs["hash"] = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    raw = urlencode(pairs)
    with pytest.raises(HTTPException) as exc:
        validate_webapp_init_data(raw, token)
    assert exc.value.status_code == 401


def test_validate_rejects_future_auth_date():
    token = "123456:ABC-DEF"
    future = int(time.time()) + 3600
    raw = _make_init_data(token, auth_date=future)
    with pytest.raises(HTTPException) as exc:
        validate_webapp_init_data(raw, token)
    assert "future" in exc.value.detail.lower()


def test_validate_rejects_bad_signature():
    token = "123456:ABC-DEF"
    raw = _make_init_data(token) + "tampered"
    with pytest.raises(HTTPException):
        validate_webapp_init_data(raw, token)
