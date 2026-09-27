"""Dropbox Basic quota-aware evidence selection policy."""
from __future__ import annotations

import json
from pathlib import Path


class PolicyError(ValueError):
    pass


def load_policy(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PolicyError(f"invalid Dropbox policy: {path}") from exc
    if data.get("schema_version") != "forexai.dropbox_free_tier_policy.v1":
        raise PolicyError("unexpected Dropbox free-tier policy schema")
    return data


def classify(path: Path, policy: dict) -> tuple[bool, str]:
    lower = path.as_posix().lower()
    ext = path.suffix.lower()

    if ext in set(policy.get("denied_extensions", [])):
        return False, "denied_extension"

    for token in policy.get("denied_path_tokens", []):
        if token.lower() in lower:
            return False, "denied_path"

    if ext not in set(policy.get("allowed_extensions", [])):
        return False, "extension_not_allowed"

    filename = path.name.lower()
    for token in policy.get("denied_filename_tokens", []):
        if str(token).lower() in filename:
            return False, "denied_filename"

    allowed_tokens = [str(token).lower() for token in policy.get("allowed_filename_tokens", [])]
    if ext in {".json", ".md", ".txt", ".csv"} and allowed_tokens:
        if not any(token in filename for token in allowed_tokens):
            return False, "filename_not_evidence"

    size = path.stat().st_size
    max_file = int(policy.get("max_file_upload_bytes", 0))
    if size > max_file:
        return False, "file_size_limit"

    if ext == ".csv" and size > int(policy.get("max_csv_upload_bytes", 0)):
        return False, "csv_size_limit"

    if ext in {".mq5", ".ex5"}:
        if not any(
            token.lower() in lower for token in policy.get("binary_allow_tokens", [])
        ):
            return False, "binary_not_release_artifact"

    return True, "allowed"


def select_files(source_dir: Path, policy: dict) -> tuple[list[Path], list[dict]]:
    if not source_dir.is_dir():
        raise PolicyError(f"source directory does not exist: {source_dir}")

    accepted: list[Path] = []
    excluded: list[dict] = []
    for path in sorted(p for p in source_dir.rglob("*") if p.is_file()):
        keep, reason = classify(path, policy)
        if keep:
            accepted.append(path)
        else:
            excluded.append(
                {
                    "path": str(path),
                    "bytes": path.stat().st_size,
                    "reason": reason,
                }
            )

    if not accepted:
        raise PolicyError(
            "no Dropbox Basic-compatible evidence files found; "
            "raw/large/source datasets are intentionally excluded"
        )

    total = sum(p.stat().st_size for p in accepted)
    max_run = int(policy.get("max_run_upload_bytes", 0))
    if total > max_run:
        raise PolicyError(
            f"selected evidence exceeds per-run cap: {total} > {max_run} bytes"
        )

    return accepted, excluded
