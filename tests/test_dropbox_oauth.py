import json

from tools import dropbox_oauth


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_static_access_token_mode(monkeypatch):
    monkeypatch.setenv("DROPBOX_ACCESS_TOKEN", "opaque-token")
    monkeypatch.delenv("DROPBOX_REFRESH_TOKEN", raising=False)
    monkeypatch.delenv("DROPBOX_APP_KEY", raising=False)
    monkeypatch.delenv("DROPBOX_APP_SECRET", raising=False)

    assert dropbox_oauth.auth_mode() == "access_token"
    assert dropbox_oauth.get_access_token() == "opaque-token"


def test_refresh_token_mode_exchanges_for_access_token(monkeypatch):
    monkeypatch.delenv("DROPBOX_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("DROPBOX_REFRESH_TOKEN", "refresh-token")
    monkeypatch.setenv("DROPBOX_APP_KEY", "app-key")
    monkeypatch.setenv("DROPBOX_APP_SECRET", "app-secret")

    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["authorization"] = request.get_header("Authorization")
        captured["body"] = request.data.decode("ascii")
        captured["timeout"] = timeout
        return _Response({"access_token": "sl.test-access-token", "expires_in": 14400})

    monkeypatch.setattr(dropbox_oauth.urllib.request, "urlopen", fake_urlopen)

    assert dropbox_oauth.auth_mode() == "refresh_token"
    assert dropbox_oauth.get_access_token() == "sl.test-access-token"
    assert captured["url"] == dropbox_oauth.TOKEN_URL
    assert captured["authorization"].startswith("Basic ")
    assert "grant_type=refresh_token" in captured["body"]
    assert "refresh_token=refresh-token" in captured["body"]
    assert captured["timeout"] == 60


def test_refresh_token_mode_requires_app_credentials(monkeypatch):
    monkeypatch.delenv("DROPBOX_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("DROPBOX_REFRESH_TOKEN", "refresh-token")
    monkeypatch.delenv("DROPBOX_APP_KEY", raising=False)
    monkeypatch.delenv("DROPBOX_APP_SECRET", raising=False)

    try:
        dropbox_oauth.get_access_token()
    except dropbox_oauth.DropboxOAuthError as exc:
        assert "DROPBOX_APP_KEY" in str(exc)
    else:
        raise AssertionError("missing OAuth app credentials must fail closed")


def test_missing_credentials_fail_closed(monkeypatch):
    for name in (
        "DROPBOX_ACCESS_TOKEN",
        "DROPBOX_REFRESH_TOKEN",
        "DROPBOX_APP_KEY",
        "DROPBOX_APP_SECRET",
    ):
        monkeypatch.delenv(name, raising=False)

    assert dropbox_oauth.auth_mode() == "missing"
    try:
        dropbox_oauth.get_access_token()
    except dropbox_oauth.DropboxOAuthError as exc:
        assert "configure" in str(exc)
    else:
        raise AssertionError("missing Dropbox credentials must fail closed")
