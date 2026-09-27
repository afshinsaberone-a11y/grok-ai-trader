"""Fail-closed GitHub Actions -> Dropbox evidence synchronizer (v2)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from tools.dropbox_free_tier_policy import load_policy, select_files

API_URL = "https://api.dropboxapi.com/2"
CONTENT_URL = "https://content.dropboxapi.com/2"
CHUNK_SIZE = 64 * 1024 * 1024
DIRECT_LIMIT = 120 * 1024 * 1024


class DropboxSyncError(RuntimeError):
    """A synchronization invariant failed."""


def token() -> str:
    value = os.environ.get("DROPBOX_ACCESS_TOKEN", "").strip()
    if not value:
        raise DropboxSyncError("DROPBOX_ACCESS_TOKEN is required")
    return value


def api_json(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        API_URL + "/" + endpoint,
        data=body,
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
        raise DropboxSyncError(
            "Dropbox API {0} HTTP {1}: {2}".format(endpoint, exc.code, detail)
        ) from exc
    except urllib.error.URLError as exc:
        raise DropboxSyncError("Dropbox API transport error: {0}".format(exc)) from exc


def content_call(endpoint: str, args: dict[str, Any], data: bytes) -> dict[str, Any]:
    request = urllib.request.Request(
        CONTENT_URL + "/" + endpoint,
        data=data,
        method="POST",
        headers={
            "Authorization": "Bearer " + token(),
            "Dropbox-API-Arg": json.dumps(args, ensure_ascii=False, separators=(",", ":")),
            "Content-Type": "application/octet-stream",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise DropboxSyncError(
            "Dropbox content API {0} HTTP {1}: {2}".format(endpoint, exc.code, detail)
        ) from exc
    except urllib.error.URLError as exc:
        raise DropboxSyncError("Dropbox content transport error: {0}".format(exc)) from exc


def ensure_folder(path: str) -> None:
    if not path or path == "/":
        return
    current = ""
    for part in [x for x in path.strip("/").split("/") if x]:
        current += "/" + part
        try:
            api_json("files/create_folder_v2", {"path": current, "autorename": False})
        except DropboxSyncError as exc:
            message = str(exc).lower()
            if "conflict" not in message and "already" not in message:
                raise


def safe_slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return result or "workflow"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def upload_small(path: Path, remote: str) -> dict[str, Any]:
    return content_call(
        "files/upload",
        {
            "path": remote,
            "mode": "overwrite",
            "autorename": False,
            "mute": True,
            "strict_conflict": False,
        },
        path.read_bytes(),
    )


def upload_large(path: Path, remote: str) -> dict[str, Any]:
    size = path.stat().st_size
    with path.open("rb") as handle:
        first = handle.read(CHUNK_SIZE)
        if not first:
            return upload_small(path, remote)
        started = content_call("files/upload_session/start", {"close": False}, first)
        session_id = started["session_id"]
        offset = len(first)
        while offset + CHUNK_SIZE < size:
            chunk = handle.read(CHUNK_SIZE)
            if not chunk:
                raise DropboxSyncError("unexpected EOF during upload: " + str(path))
            content_call(
                "files/upload_session/append_v2",
                {"cursor": {"session_id": session_id, "offset": offset}, "close": False},
                chunk,
            )
            offset += len(chunk)
        final = handle.read()
        if offset + len(final) != size:
            raise DropboxSyncError("file changed while uploading: " + str(path))
        return content_call(
            "files/upload_session/finish",
            {
                "cursor": {"session_id": session_id, "offset": offset},
                "commit": {
                    "path": remote,
                    "mode": "overwrite",
                    "autorename": False,
                    "mute": True,
                    "strict_conflict": False,
                },
            },
            final,
        )


def upload(path: Path, remote: str) -> dict[str, Any]:
    if path.stat().st_size <= DIRECT_LIMIT:
        return upload_small(path, remote)
    return upload_large(path, remote)


def get_space_usage() -> tuple[int, int]:
    usage = api_json("users/get_space_usage", {})
    used = usage.get("used")
    allocation = usage.get("allocation") or {}
    allocated = allocation.get("allocated")
    if not isinstance(used, int) or not isinstance(allocated, int):
        raise DropboxSyncError("Dropbox space usage response is missing used/allocated bytes")
    return used, allocated


def collect_and_upload(
    source_dir: Path, remote_root: str, policy: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not source_dir.is_dir():
        raise DropboxSyncError("source directory does not exist: " + str(source_dir))
    try:
        files, excluded = select_files(source_dir, policy)
    except ValueError as exc:
        raise DropboxSyncError(str(exc)) from exc

    selected_bytes = sum(path.stat().st_size for path in files)
    used_bytes, allocated_bytes = get_space_usage()
    reserve_bytes = int(policy.get("reserve_bytes", 0))
    available_bytes = allocated_bytes - used_bytes
    if available_bytes - selected_bytes < reserve_bytes:
        raise DropboxSyncError(
            "Dropbox quota guard: required="
            + str(selected_bytes + reserve_bytes)
            + " available="
            + str(available_bytes)
        )

    ensure_folder(remote_root)
    records: list[dict[str, Any]] = []
    for local in files:
        relative = local.relative_to(source_dir).as_posix()
        remote = remote_root.rstrip("/") + "/" + relative
        ensure_folder(str(Path(remote).parent).replace("\\", "/"))
        size_before = local.stat().st_size
        sha256 = sha256_file(local)
        meta = upload(local, remote)
        size_after = local.stat().st_size
        if size_before != size_after:
            raise DropboxSyncError("local file changed during sync: " + str(local))
        records.append(
            {
                "local_path": str(local),
                "remote_path": remote,
                "bytes": size_before,
                "sha256": sha256,
                "dropbox_id": meta.get("id"),
                "dropbox_rev": meta.get("rev"),
                "dropbox_size": meta.get("size"),
            }
        )
    return records, excluded


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DropboxSyncError("invalid JSON metadata: {0}".format(path)) from exc
    if not isinstance(value, dict):
        raise DropboxSyncError("metadata must be a JSON object: " + str(path))
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--dropbox-root", required=True)
    parser.add_argument("--workflow-name", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--conclusion", required=True)
    parser.add_argument("--manifest-out", required=True)
    parser.add_argument("--run-metadata", required=False)
    parser.add_argument("--ledger-out", required=False)
    parser.add_argument("--ledger-remote-root", required=False)
    parser.add_argument(
        "--policy",
        default="config/dropbox_free_tier_policy.json",
    )
    args = parser.parse_args()

    policy = load_policy(Path(args.policy))
    source = Path(args.source_dir)
    records, excluded = collect_and_upload(source, args.dropbox_root, policy)

    run_metadata: dict[str, Any] = {}
    if args.run_metadata:
        run_metadata = load_json(Path(args.run_metadata))

    manifest = {
        "schema_version": "forexai.dropbox_evidence_sync.v2",
        "generated_at_utc": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc
        ).isoformat(),
        "workflow": {
            "name": args.workflow_name,
            "run_id": int(args.run_id),
            "head_sha": args.head_sha,
            "conclusion": args.conclusion,
        },
        "dropbox_root": args.dropbox_root,
        "source_run": run_metadata,
        "file_count": len(records),
        "files": records,
        "excluded_file_count": len(excluded),
        "excluded_files": excluded,
        "policy": {
            "real_data_only": True,
            "synthetic_generation": False,
            "hash_algorithm": "SHA-256",
            "source_artifacts_immutable": True,
            "manifest_written_last": True,
            "dropbox_plan": policy.get("plan"),
            "quota_bytes": int(policy.get("quota_bytes", 0)),
            "reserve_bytes": int(policy.get("reserve_bytes", 0)),
            "max_run_upload_bytes": int(policy.get("max_run_upload_bytes", 0)),
        },
    }

    manifest_path = Path(args.manifest_out)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    remote_manifest = args.dropbox_root.rstrip("/") + "/_SYNC_MANIFEST.json"
    upload(manifest_path, remote_manifest)

    if args.ledger_out and args.ledger_remote_root:
        ledger_path = Path(args.ledger_out)
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        ledger_remote = (
            args.ledger_remote_root.rstrip("/")
            + "/run-manifest__"
            + str(int(args.run_id))
            + "__v2.json"
        )
        upload(ledger_path, ledger_remote)

    print(
        json.dumps(
            {
                "status": "PASS",
                "schema_version": "forexai.dropbox_evidence_sync.v2",
                "run_id": int(args.run_id),
                "workflow": args.workflow_name,
                "file_count": len(records),
                "dropbox_root": args.dropbox_root,
                "remote_manifest": remote_manifest,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (DropboxSyncError, OSError, ValueError, KeyError) as exc:
        print("DROPBOX_SYNC_FAIL_CLOSED: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
