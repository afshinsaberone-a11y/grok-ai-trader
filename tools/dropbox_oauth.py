"""Dropbox OAuth 2 token resolution for CI/CD and evidence sync.

The preferred automation path is an offline OAuth refresh token. A static
DROPBOX_ACCESS_TOKEN remains supported for compatibility and diagnostics.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"


class DropboxOAuthError(RuntimeError):
    """Dropbox OAuth configuration or token exchange failed."""


def auth_mode() -> str:
    refresh = os.environ.get("DROPBOX_REFRESH_TOKEN", "").strip()
    access = os.environ.get("DROPBOX_ACCESS_TOKEN", "").strip()
    app_key = os.environ.get("DROPBOX_APP_KEY", "").strip()
    app_secret = os.environ.get("DROPBOX_APP_SECRET", "").strip()

    if refresh:
        if not app_key or not app_secret:
            raise DropboxOAuthError(
                "DROPBOX_REFRESH_TOKEN requires DROPBOX_APP_KEY and DROPBOX_APP_SECRET"
            )
        return "refresh_token"
    if access:
        return "access_token"
    return "missing"


def _refresh_access_token() -> str:
    refresh = os.environ.get("DROPBOX_REFRESH_TOKEN", "").strip()
    app_key = os.environ.get("DROPBOX_APP_KEY", "").strip()
    app_secret = os.environ.get("DROPBOX_APP_SECRET", "").strip()

    if not refresh:
        raise DropboxOAuthError("DROPBOX_REFRESH_TOKEN is required for refresh-token mode")
    if not app_key or not app_secret:
        raise DropboxOAuthError(
            "DROPBOX_REFRESH_TOKEN requires DROPBOX_APP_KEY and DROPBOX_APP_SECRET"
        )

    body = (
        "grant_type=refresh_token&refresh_token="
        + urllib.parse.quote_plus(refresh)
    ).encode("ascii")
    basic = base64.b64encode(
        (app_key + ":" + app_secret).encode("utf-8")
    ).decode("ascii")

    request = urllib.request.Request(
        TOKEN_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": "Basic " + basic,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload: Any = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise DropboxOAuthError(
            "Dropbox OAuth refresh HTTP {0}: {1}".format(exc.code, detail)
        ) from exc
    except urllib.error.URLError as exc:
        raise DropboxOAuthError(
            "Dropbox OAuth refresh transport error: {0}".format(exc)
        ) from exc

    access = payload.get("access_token") if isinstance(payload, dict) else None
    if not isinstance(access, str) or not access.strip():
        raise DropboxOAuthError("Dropbox OAuth refresh response has no access_token")
    return access.strip()


def get_access_token() -> str:
    mode = auth_mode()
    if mode == "refresh_token":
        return _refresh_access_token()
    if mode == "access_token":
        return os.environ["DROPBOX_ACCESS_TOKEN"].strip()
    raise DropboxOAuthError(
        "configure DROPBOX_REFRESH_TOKEN + DROPBOX_APP_KEY + DROPBOX_APP_SECRET "
        "or DROPBOX_ACCESS_TOKEN"
    )


__all__ = ["DropboxOAuthError", "auth_mode", "get_access_token"]
