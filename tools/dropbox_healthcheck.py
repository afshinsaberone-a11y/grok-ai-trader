"""Read-only Dropbox health check for the ForexAI evidence plane."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


API_URL = "https://api.dropboxapi.com/2"

REQUIRED_PATHS = (
    "/ForexAI",
    "/ForexAI/00_CONTROL",
    "/ForexAI/01_RAW_MARKET_DATA",
    "/ForexAI/03_DATA_QUALITY",
    "/ForexAI/04_RESEARCH",
    "/ForexAI/06_BACKTESTS",
    "/ForexAI/07_CANDIDATES",
    "/ForexAI/08_OOS_LOCKED",
    "/ForexAI/09_EVIDENCE_LEDGER",
    "/ForexAI/10_MQL5_RELEASES",
    "/ForexAI/11_GITHUB_ACTIONS",
    "/ForexAI/12_PROJECT_REPORTS",
)


def token() -> str:
    value = os.environ.get("DROPBOX_ACCESS_TOKEN", "").strip()
    if not value:
        raise RuntimeError("DROPBOX_ACCESS_TOKEN is required")
    return value


def call(endpoint: str, payload: dict) -> dict:
    request = urllib.request.Request(
        API_URL + "/" + endpoint,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": "Bearer " + token(),
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            "Dropbox API {} HTTP {}: {}".format(endpoint, exc.code, detail)
        ) from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/ForexAI")
    args = parser.parse_args()

    root = args.root.rstrip("/")
    if root != "/ForexAI":
        raise RuntimeError("health check is pinned to the canonical /ForexAI root")

    failures = []
    account = call("users/get_current_account", {})
    for path in REQUIRED_PATHS:
        try:
            meta = call("files/get_metadata", {"path": path})
            if meta.get(".tag") != "folder" and meta.get("name") != path.rsplit("/", 1)[-1]:
                failures.append({"path": path, "reason": "not_a_folder"})
        except RuntimeError as exc:
            failures.append({"path": path, "reason": str(exc)})

    result = {
        "schema_version": "forexai.dropbox_healthcheck.v1",
        "status": "PASS" if not failures else "HOLD",
        "account_id_present": bool(account.get("account_id")),
        "root": root,
        "required_paths_checked": len(REQUIRED_PATHS),
        "failures": failures,
        "write_capability": "not_tested",
        "policy": {
            "read_only": True,
            "no_files_created": True,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        print("DROPBOX_HEALTHCHECK_FAIL_CLOSED: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
