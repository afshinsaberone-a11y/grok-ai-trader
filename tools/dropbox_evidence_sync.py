"""Sync GitHub Actions evidence into the ForexAI Dropbox evidence plane.

Dependency-free and fail-closed. Requires DROPBOX_ACCESS_TOKEN at runtime.
"""
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

API_URL = "https://api.dropboxapi.com/2"
CONTENT_URL = "https://content.dropboxapi.com/2"
CHUNK_SIZE = 64 * 1024 * 1024
DIRECT_LIMIT = 120 * 1024 * 1024


class DropboxSyncError(RuntimeError):
    pass


def _token() -> str:
    value = os.environ.get("DROPBOX_ACCESS_TOKEN", "").strip()
    if not value:
        raise DropboxSyncError("DROPBOX_ACCESS_TOKEN is required")
    return value


def _api_json(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    req = urllib.request.Request(
        f"{API_URL}/{endpoint}",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {_token()}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise DropboxSyncError(f"Dropbox API {endpoint} HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise DropboxSyncError(f"Dropbox API {endpoint} transport error: {exc}") from exc
    return json.loads(raw.decode("utf-8"))


def _content(endpoint: str, args: dict[str, Any], data: bytes) -> dict[str, Any]:
    req = urllib.request.Request(
        f"{CONTENT_URL}/{endpoint}",
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {_token()}",
            "Dropbox-API-Arg": json.dumps(args, ensure_ascii=False, separators=(",", ":")),
            "Content-Type": "application/octet-stream",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise DropboxSyncError(f"Dropbox content API {endpoint} HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise DropboxSyncError(f"Dropbox content API {endpoint} transport error: {exc}") from exc
    return json.loads(raw.decode("utf-8"))


def _ensure_folder(path: str) -> None:
    if not path or path == "/":
        return
    current = ""
    for part in (x for x in path.strip("/").split("/") if x):
        current += "/" + part
        try:
            _api_json("files/create_folder_v2", {"path": current, "autorename": False})
        except DropboxSyncError as exc:
            message = str(exc).lower()
            if "conflict" not in message and "already" not in message:
                raise


def _safe_slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "workflow"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _upload_direct(path: Path, remote: str) -> dict[str, Any]:
    return _content(
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


def _upload_session(path: Path, remote: str) -> dict[str, Any]:
    size = path.stat().st_size
    with path.open("rb") as handle:
        first = handle.read(CHUNK_SIZE)
        if not first:
            return _upload_direct(path, remote)

        start = _content("files/upload_session/start", {"close": False}, first)
        session_id = start["session_id"]
        offset = len(first)

        while offset + CHUNK_SIZE < size:
            chunk = handle.read(CHUNK_SIZE)
            _content(
                "files/upload_session/append_v2",
                {
                    "cursor": {"session_id": session_id, "offset": offset},
                    "close": False,
                },
                chunk,
            )
            offset += len(chunk)

        final = handle.read()
        if offset + len(final) != size:
            raise DropboxSyncError(
                f"local file changed while uploading: {path} expected={size} "
                f"offset={offset} final={len(final)}"
            )

        return _content(
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
        return _upload_direct(path, remote)
    return _upload_session(path, remote)


def sync_tree(source_dir: Path, remote_root: str) -> list[dict[str, Any]]:
    if not source_dir.is_dir():
        raise DropboxSyncError(f"source directory does not exist: {source_dir}")

    files = sorted(p for p in source_dir.rglob("*") if p.is_file())
    if not files:
        raise DropboxSyncError(f"no evidence files found under {source_dir}")

    _ensure_folder(remote_root)
    records: list[dict[str, Any]] = []

    for path in files:
        relative = path.relative_to(source_dir).as_posix()
        remote = f"{remote_root.rstrip('/')}/{relative}"
        _ensure_folder(str(Path(remote).parent).replace("\\", "/"))
        before = path.stat().st_size
        sha = _sha256(path)
        meta = upload(path, remote)
        after = path.stat().st_size
        if before != after:
            raise DropboxSyncError(f"file changed during sync: {path}")
        records.append(
            {
                "local_path": str(path),
                "remote_path": remote,
                "bytes": before,
                "sha256": sha,
                "dropbox_id": meta.get("id"),
                "dropbox_rev": meta.get("rev"),
                "dropbox_size": meta.get("size"),
            }
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--dropbox-root", required=True)
    parser.add_argument("--workflow-name", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--conclusion", required=True)
    parser.add_argument("--manifest-out", required=True)
    args = parser.parse_args()

    account = _api_json("users/get_current_account", {})
    source = Path(args.source_dir)
    records = sync_tree(source, args.dropbox_root)

    manifest = {
        "schema_version": "forexai.dropbox_evidence_sync.v1",
        "workflow": {
            "name": args.workflow_name,
            "run_id": int(args.run_id),
            "head_sha": args.head_sha,
            "conclusion": args.conclusion,
        },
        "dropbox_root": args.dropbox_root,
        "account_id": account.get("account_id"),
        "file_count": len(records),
        "files": records,
        "policy": {
            "real_data_only": True,
            "synthetic_generation": False,
            "hash_algorithm": "SHA-256",
            "source_artifacts_immutable": True,
        },
    }

    out = Path(args.manifest_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    manifest_remote = f"{args.dropbox_root.rstrip('/')}/_SYNC_MANIFEST.json"
    manifest_meta = upload(out, manifest_remote)
    manifest["manifest_remote_path"] = manifest_remote
    manifest["manifest_dropbox_id"] = manifest_meta.get("id")
    out.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(
        {
            "status": "PASS",
            "workflow": args.workflow_name,
            "run_id": int(args.run_id),
            "files": len(records),
            "dropbox_root": args.dropbox_root,
            "manifest_remote_path": manifest_remote,
        },
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (DropboxSyncError, OSError, ValueError, KeyError) as exc:
        print(f"DROPBOX_SYNC_FAIL_CLOSED: {exc}", file=sys.stderr)
        raise SystemExit(2)
