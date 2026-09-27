"""Quota-aware evidence selection for Dropbox Basic."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class PolicyError(ValueError):
    """Dropbox Basic policy violation."""


def load_policy(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PolicyError("invalid Dropbox policy: " + str(path)) from exc
    if data.get("schema_version") != "forexai.dropbox_free_tier_policy.v1":
        raise PolicyError("unexpected Dropbox free-tier policy schema")
    return data


def priority(path: Path, policy: dict[str, Any]) -> int:
    filename = path.name.lower()
    critical = [str(x).lower() for x in policy.get("critical_filename_tokens", [])]
    standard = [str(x).lower() for x in policy.get("standard_filename_tokens", [])]
    if any(token in filename for token in critical):
        return 0
    if any(token in filename for token in standard):
        return 1
    return 2


def classify(path: Path, policy: dict[str, Any]) -> tuple[bool, str]:
    filename = path.name.lower()
    lower_path = path.as_posix().lower()
    ext = path.suffix.lower()

    if ext in set(policy.get("denied_extensions", [])):
        return False, "denied_extension"

    for token in policy.get("denied_path_tokens", []):
        if str(token).lower() in lower_path:
            return False, "denied_path"

    for token in policy.get("denied_filename_tokens", []):
        if str(token).lower() in filename:
            return False, "denied_filename"

    if ext not in set(policy.get("allowed_extensions", [])):
        return False, "extension_not_allowed"

    allowed_tokens = [str(x).lower() for x in policy.get("allowed_filename_tokens", [])]
    if ext in {".json", ".md", ".txt", ".csv"} and allowed_tokens:
        if not any(token in filename for token in allowed_tokens):
            return False, "filename_not_evidence"

    size = path.stat().st_size
    if size > int(policy.get("max_file_upload_bytes", 0)):
        return False, "file_size_limit"

    if ext == ".csv" and size > int(policy.get("max_csv_upload_bytes", 0)):
        return False, "csv_size_limit"

    if ext in {".mq5", ".ex5"}:
        binary_tokens = [str(x).lower() for x in policy.get("binary_allow_tokens", [])]
        if not any(token in lower_path for token in binary_tokens):
            return False, "binary_not_release_artifact"

    return True, "allowed"


def select_files(source_dir: Path, policy: dict[str, Any]) -> tuple[list[Path], list[dict[str, Any]]]:
    if not source_dir.is_dir():
        raise PolicyError("source directory does not exist: " + str(source_dir))

    accepted: list[Path] = []
    excluded: list[dict[str, Any]] = []

    for path in sorted(p for p in source_dir.rglob("*") if p.is_file()):
        keep, reason = classify(path, policy)
        if keep:
            accepted.append(path)
        else:
            excluded.append(
                {"path": str(path), "bytes": path.stat().st_size, "reason": reason}
            )

    if not accepted:
        raise PolicyError(
            "no Dropbox Basic-compatible evidence files found; "
            "raw/large/source datasets are intentionally excluded"
        )

    accepted.sort(
        key=lambda path: (
            priority(path, policy),
            -path.stat().st_size,
            path.as_posix(),
        )
    )

    max_run = int(policy.get("max_run_upload_bytes", 0))
    selected: list[Path] = []
    selected_bytes = 0

    for path in accepted:
        size = path.stat().st_size
        if selected_bytes + size <= max_run:
            selected.append(path)
            selected_bytes += size
            continue

        if priority(path, policy) == 0:
            raise PolicyError(
                "critical evidence exceeds per-run cap: "
                + str(selected_bytes + size)
                + " > "
                + str(max_run)
                + " bytes"
            )

        excluded.append(
            {
                "path": str(path),
                "bytes": size,
                "reason": "per_run_cap_priority_dropped",
            }
        )

    if not selected:
        raise PolicyError("no evidence remained after Dropbox Basic quota selection")

    return selected, excluded
