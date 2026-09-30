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
    if data.get("schema_version") != "forexai.dropbox_free_tier_policy.v2":
        raise PolicyError("unexpected Dropbox free-tier policy schema")

    quota = int(data.get("quota_bytes", 0))
    reserve = int(data.get("reserve_bytes", 0))
    run_cap = int(data.get("max_run_upload_bytes", 0))
    file_cap = int(data.get("max_file_upload_bytes", 0))
    csv_cap = int(data.get("max_csv_upload_bytes", 0))
    manifest_cap = int(data.get("max_manifest_bytes", 0))
    manifest_reserve = int(data.get("manifest_reserve_bytes", 0))

    if quota <= 0:
        raise PolicyError("quota_bytes must be positive")
    if reserve < 0 or reserve >= quota:
        raise PolicyError("reserve_bytes must be >= 0 and smaller than quota_bytes")
    if run_cap <= 0 or run_cap > quota - reserve:
        raise PolicyError("max_run_upload_bytes exceeds safe quota budget")
    if file_cap <= 0 or file_cap > run_cap:
        raise PolicyError("max_file_upload_bytes exceeds max_run_upload_bytes")
    if csv_cap <= 0 or csv_cap > file_cap:
        raise PolicyError("max_csv_upload_bytes exceeds max_file_upload_bytes")
    if manifest_cap <= 0 or manifest_cap > file_cap:
        raise PolicyError("max_manifest_bytes exceeds max_file_upload_bytes")
    if manifest_reserve < 0 or manifest_reserve > quota - reserve:
        raise PolicyError("manifest_reserve_bytes exceeds safe quota budget")
    if not isinstance(data.get("allowed_extensions"), list):
        raise PolicyError("allowed_extensions must be a list")
    if not isinstance(data.get("denied_extensions"), list):
        raise PolicyError("denied_extensions must be a list")
    if set(str(x).lower() for x in data["allowed_extensions"]) & set(
        str(x).lower() for x in data["denied_extensions"]
    ):
        raise PolicyError("allowed_extensions and denied_extensions overlap")

    return data


def workflow_key(workflow_name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "-", workflow_name.strip().lower()).strip("-") or "workflow"


def workflow_profile(workflow_name: str, policy: dict[str, Any]) -> dict[str, Any]:
    profiles = policy.get("workflow_profiles") or {}
    if not profiles:
        return {}
    key = workflow_key(workflow_name)
    profile = profiles.get(key)
    if not isinstance(profile, dict):
        if policy.get("require_known_workflow_profile", False):
            raise PolicyError("unknown Dropbox workflow profile: " + key)
        return {}
    prefixes = profile.get("allowed_artifact_prefixes")
    if not isinstance(prefixes, list) or not prefixes:
        raise PolicyError("workflow profile has no allowed_artifact_prefixes: " + key)
    return profile


def artifact_root(path: Path, source_dir: Path) -> str:
    relative = path.relative_to(source_dir)
    parts = relative.parts
    return parts[0].lower() if parts else ""


def classify_workflow_artifact(
    path: Path,
    source_dir: Path,
    workflow_name: str,
    policy: dict[str, Any],
) -> tuple[bool, str]:
    profile = workflow_profile(workflow_name, policy)
    if not profile:
        return True, "profile_not_configured"

    root = artifact_root(path, source_dir)
    prefixes = [str(x).lower() for x in profile["allowed_artifact_prefixes"]]
    if not any(root.startswith(prefix) for prefix in prefixes):
        return False, "artifact_family_not_allowed"
    return True, "artifact_family_allowed"


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


def select_files(
    source_dir: Path,
    policy: dict[str, Any],
    workflow_name: str | None = None,
) -> tuple[list[Path], list[dict[str, Any]]]:
    if not source_dir.is_dir():
        raise PolicyError("source directory does not exist: " + str(source_dir))

    accepted: list[Path] = []
    excluded: list[dict[str, Any]] = []

    paths = sorted(p for p in source_dir.rglob("*") if p.is_file())
    if paths and policy.get("require_known_workflow_profile", False) and not workflow_name:
        raise PolicyError("workflow_name is required for workflow-scoped Dropbox selection")

    for path in paths:
        keep, reason = classify(path, policy)
        if keep and workflow_name:
            keep, reason = classify_workflow_artifact(
                path, source_dir, workflow_name, policy
            )
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
