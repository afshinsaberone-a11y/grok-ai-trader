"""Read-only Dropbox health check for the ForexAI evidence plane."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_URL = "https://api.dropboxapi.com/2"
ROOT = "/ForexAI"


def token() -> str:
    value = os.environ.get("DROPBOX_ACCESS_TOKEN", "").strip()
    if not value:
        raise RuntimeError("DROPBOX_ACCESS_TOKEN is required")
    return value


def call(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        API_URL + "/" + endpoint,
        data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
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


def configured_paths(mapping: dict[str, Any]) -> set[str]:
    paths: set[str] = set()

    def walk(value: Any) -> None:
        if isinstance(value, str) and value.startswith(ROOT + "/"):
            paths.add(value)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(mapping)
    return paths


def list_all_folders(start: str) -> set[str]:
    result = call(
        "files/list_folder",
        {"path": start, "recursive": True, "include_deleted": False},
    )
    folders: set[str] = {start}
    for entry in result.get("entries", []):
        if entry.get(".tag") == "folder":
            path = entry.get("path_display")
            if isinstance(path, str):
                folders.add(path)

    while result.get("has_more"):
        cursor = result.get("cursor")
        if not cursor:
            raise RuntimeError("Dropbox returned has_more=true without cursor")
        result = call("files/list_folder/continue", {"cursor": cursor})
        for entry in result.get("entries", []):
            if entry.get(".tag") == "folder":
                path = entry.get("path_display")
                if isinstance(path, str):
                    folders.add(path)
    return folders


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=ROOT)
    parser.add_argument(
        "--map",
        default="config/dropbox_repository_map.json",
        help="Machine-readable Dropbox repository map",
    )
    args = parser.parse_args()

    if args.root != ROOT:
        raise RuntimeError("health check is pinned to the canonical /ForexAI root")

    map_path = Path(args.map)
    if not map_path.is_file():
        raise RuntimeError("repository map does not exist: " + str(map_path))
    mapping = json.loads(map_path.read_text(encoding="utf-8"))
    if not isinstance(mapping, dict):
        raise RuntimeError("repository map must be a JSON object")
    if mapping.get("dropbox_root") != ROOT:
        raise RuntimeError("repository map root must be /ForexAI")

    account = call("users/get_current_account", {})
    actual = list_all_folders(ROOT)
    expected = configured_paths(mapping)
    missing = sorted(expected - actual)

    result = {
        "schema_version": "forexai.dropbox_healthcheck.v2",
        "status": "PASS" if not missing else "HOLD",
        "account_id_present": bool(account.get("account_id")),
        "root": ROOT,
        "configured_paths_checked": len(expected),
        "missing_paths": missing,
        "actual_folder_count": len(actual),
        "write_capability": "not_tested",
        "policy": {
            "read_only": True,
            "no_files_created": True,
            "source_of_truth": "config/dropbox_repository_map.json",
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not missing else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, ValueError, TypeError, KeyError) as exc:
        print("DROPBOX_HEALTHCHECK_FAIL_CLOSED: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
