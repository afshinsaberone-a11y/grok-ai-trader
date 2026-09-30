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

from tools.dropbox_free_tier_policy_v2 import load_policy, select_files

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


def content_download(endpoint: str, args: dict[str, Any]) -> bytes:
    request = urllib.request.Request(
        CONTENT_URL + "/" + endpoint,
        data=b"",
        method="POST",
        headers={
            "Authorization": "Bearer " + token(),
            "Dropbox-API-Arg": json.dumps(args, ensure_ascii=False, separators=(",", ":")),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            return response.read()
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


def upload_small_bytes(payload: bytes, remote: str) -> dict[str, Any]:
    return content_call(
        "files/upload",
        {
            "path": remote,
            "mode": "add",
            "autorename": False,
            "mute": True,
            "strict_conflict": True,
        },
        payload,
    )


def upload_large(path: Path, remote: str) -> dict[str, Any]:
    size = path.stat().st_size
    with path.open("rb") as handle:
        first = handle.read(CHUNK_SIZE)
        if not first:
            return upload_small_bytes(b"", remote)
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
                    "mode": "add",
                    "autorename": False,
                    "mute": True,
                    "strict_conflict": True,
                },
            },
            final,
        )


def upload(path: Path, remote: str) -> dict[str, Any]:
    if path.stat().st_size <= DIRECT_LIMIT:
        return upload_small_bytes(path.read_bytes(), remote)
    return upload_large(path, remote)


def remote_metadata(remote: str) -> dict[str, Any] | None:
    try:
        return api_json("files/get_metadata", {"path": remote})
    except DropboxSyncError as exc:
        message = str(exc).lower()
        if "not_found" in message or "path/not_found" in message:
            return None
        raise


def remote_sha256(remote: str, expected_size: int) -> tuple[dict[str, Any], str]:
    metadata = remote_metadata(remote)
    if metadata is None:
        raise DropboxSyncError("remote evidence disappeared during integrity check: " + remote)
    remote_size = int(metadata.get("size") or 0)
    if remote_size != expected_size:
        raise DropboxSyncError(
            "IMMUTABLE_CONFLICT: remote size differs for "
            + remote
            + " (remote="
            + str(remote_size)
            + ", local="
            + str(expected_size)
            + ")"
        )
    payload = content_download("files/download", {"path": remote})
    if len(payload) != expected_size:
        raise DropboxSyncError(
            "IMMUTABLE_CONFLICT: remote download size differs for " + remote
        )
    return metadata, hashlib.sha256(payload).hexdigest()


def verify_or_mark_existing(remote: str, payload: bytes, local_sha256: str) -> dict[str, Any] | None:
    metadata = remote_metadata(remote)
    if metadata is None:
        return None
    remote_size = int(metadata.get("size") or 0)
    if remote_size != len(payload):
        raise DropboxSyncError(
            "IMMUTABLE_CONFLICT: remote file exists with a different size: " + remote
        )
    _, remote_hash = remote_sha256(remote, len(payload))
    if remote_hash != local_sha256:
        raise DropboxSyncError(
            "IMMUTABLE_CONFLICT: remote file exists with different SHA-256: " + remote
        )
    return metadata


def upload_immutable_bytes(
    remote: str, payload: bytes, local_sha256: str
) -> tuple[dict[str, Any], str]:
    existing = verify_or_mark_existing(remote, payload, local_sha256)
    if existing is not None:
        return existing, "already_present"

    try:
        metadata = upload_small_bytes(payload, remote)
        return metadata, "uploaded"
    except DropboxSyncError as exc:
        if "conflict" not in str(exc).lower():
            raise
        # A concurrent writer may have won the race. Accept only a byte-for-byte
        # identical object; never overwrite a different object.
        existing = verify_or_mark_existing(remote, payload, local_sha256)
        if existing is not None:
            return existing, "already_present_after_race"
        raise DropboxSyncError(
            "IMMUTABLE_CONFLICT: destination appeared during upload: " + remote
        ) from exc


def get_space_usage() -> tuple[int, int]:
    usage = api_json("users/get_space_usage", {})
    used = usage.get("used")
    allocation = usage.get("allocation") or {}
    allocated = allocation.get("allocated")
    if not isinstance(used, int) or not isinstance(allocated, int):
        raise DropboxSyncError("Dropbox space usage response is missing used/allocated bytes")
    return used, allocated


def collect_and_upload(
    source_dir: Path,
    remote_root: str,
    policy: dict[str, Any],
    *,
    manifest_count: int = 1,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not source_dir.is_dir():
        raise DropboxSyncError("source directory does not exist: " + str(source_dir))
    try:
        files, excluded = select_files(source_dir, policy)
    except ValueError as exc:
        raise DropboxSyncError(str(exc)) from exc

    prepared: list[dict[str, Any]] = []
    projected_new_bytes = 0
    for local in files:
        payload = local.read_bytes()
        sha256 = hashlib.sha256(payload).hexdigest()
        relative = local.relative_to(source_dir).as_posix()
        remote = remote_root.rstrip("/") + "/" + relative
        existing = verify_or_mark_existing(remote, payload, sha256)
        prepared.append(
            {
                "local": local,
                "payload": payload,
                "sha256": sha256,
                "remote": remote,
                "existing": existing,
            }
        )
        if existing is None:
            projected_new_bytes += len(payload)

    used_bytes, allocated_bytes = get_space_usage()
    reserve_bytes = int(policy.get("reserve_bytes", 0))
    manifest_reserve = int(policy.get("manifest_reserve_bytes", 0))
    available_bytes = allocated_bytes - used_bytes
    projected_required = (
        projected_new_bytes + reserve_bytes + manifest_reserve * max(1, manifest_count)
    )
    if available_bytes < projected_required:
        raise DropboxSyncError(
            "Dropbox quota guard: required="
            + str(projected_required)
            + " available="
            + str(available_bytes)
            + " (new="
            + str(projected_new_bytes)
            + ", reserve="
            + str(reserve_bytes)
            + ", manifest_reserve="
            + str(manifest_reserve)
            + ")"
        )

    ensure_folder(remote_root)
    records: list[dict[str, Any]] = []
    for item in prepared:
        local = item["local"]
        payload = item["payload"]
        sha256 = item["sha256"]
        remote = item["remote"]
        ensure_folder(str(Path(remote).parent).replace("\\", "/"))
        meta = item["existing"]
        status = "already_present"
        if meta is None:
            meta, status = upload_immutable_bytes(remote, payload, sha256)
        records.append(
            {
                "local_path": str(local),
                "remote_path": remote,
                "bytes": len(payload),
                "sha256": sha256,
                "dropbox_id": meta.get("id"),
                "dropbox_rev": meta.get("rev"),
                "dropbox_size": meta.get("size"),
                "sync_status": status,
                "immutable": True,
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
    parser.add_argument("--run-attempt", required=True)
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
    manifest_count = 2 if args.ledger_out and args.ledger_remote_root else 1
    records, excluded = collect_and_upload(
        source, args.dropbox_root, policy, manifest_count=manifest_count
    )

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
            "run_attempt": int(args.run_attempt),
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
            "remote_paths_write_once": True,
            "idempotent_replay": True,
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

    manifest_payload = manifest_path.read_bytes()
    manifest_sha256 = hashlib.sha256(manifest_payload).hexdigest()
    remote_manifest = args.dropbox_root.rstrip("/") + "/_SYNC_MANIFEST.json"
    manifest_meta, manifest_status = upload_immutable_bytes(
        remote_manifest, manifest_payload, manifest_sha256
    )

    if args.ledger_out and args.ledger_remote_root:
        ledger_path = Path(args.ledger_out)
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        ledger_payload = ledger_path.read_bytes()
        ledger_sha256 = hashlib.sha256(ledger_payload).hexdigest()
        ledger_remote = (
            args.ledger_remote_root.rstrip("/")
            + "/run-manifest__"
            + str(int(args.run_id))
            + "__attempt-"
            + str(int(args.run_attempt))
            + "__v2.json"
        )
        ledger_meta, ledger_status = upload_immutable_bytes(
            ledger_remote, ledger_payload, ledger_sha256
        )

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
                "manifest_sync_status": manifest_status,
                "manifest_sha256": manifest_sha256,
                "manifest_dropbox_rev": manifest_meta.get("rev"),
                "ledger_sync_status": ledger_status if args.ledger_out and args.ledger_remote_root else None,
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
