"""Validate the machine-readable Dropbox repository contract.

This check is offline and has no Dropbox side effects. It validates the contract
before a workflow attempts any remote write.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = "/ForexAI"
REQUIRED_TOP_LEVEL = {
    "00_CONTROL",
    "01_RAW_MARKET_DATA",
    "02_NORMALIZED_DATA",
    "03_DATA_QUALITY",
    "04_RESEARCH",
    "05_STRATEGIES",
    "06_BACKTESTS",
    "07_CANDIDATES",
    "08_OOS_LOCKED",
    "09_EVIDENCE_LEDGER",
    "10_MQL5_RELEASES",
    "11_GITHUB_ACTIONS",
    "12_PROJECT_REPORTS",
    "99_ARCHIVE",
}
PATH_RE = re.compile(r"^/ForexAI(?:/[^/]+)+$")


class ContractError(ValueError):
    pass


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.startswith(ROOT + "/") else []
    if isinstance(value, dict):
        result: list[str] = []
        for item in value.values():
            result.extend(_strings(item))
        return result
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_strings(item))
        return result
    return []


def validate(mapping: dict[str, Any]) -> dict[str, Any]:
    if mapping.get("schema_version") != "forexai.dropbox_repository_map.v1":
        raise ContractError("unexpected repository map schema_version")
    if mapping.get("dropbox_root") != ROOT:
        raise ContractError("dropbox_root must be /ForexAI")

    planes = mapping.get("planes")
    if not isinstance(planes, dict):
        raise ContractError("planes must be an object")

    missing_planes = REQUIRED_TOP_LEVEL - {
        str(name) for name in planes.keys() if isinstance(name, str)
    }
    # Plane keys use semantic names while their root paths use numbered names.
    roots = set()
    for plane in planes.values():
        if isinstance(plane, str):
            roots.add(plane)
        elif isinstance(plane, dict) and isinstance(plane.get("root"), str):
            roots.add(plane["root"])

    missing_roots = sorted(
        ROOT + "/" + name for name in REQUIRED_TOP_LEVEL
        if ROOT + "/" + name not in roots
    )
    if missing_roots:
        raise ContractError("missing top-level roots: " + ", ".join(missing_roots))

    all_paths = _strings(mapping)
    malformed = sorted(path for path in all_paths if not PATH_RE.fullmatch(path))
    if malformed:
        raise ContractError("malformed Dropbox paths: " + ", ".join(malformed))

    duplicates = sorted({p for p in all_paths if all_paths.count(p) > 1})
    if duplicates:
        raise ContractError("duplicate configured paths: " + ", ".join(duplicates))

    naming = mapping.get("naming") or {}
    if naming.get("hash_algorithm") != "SHA-256":
        raise ContractError("hash_algorithm must be SHA-256")
    if naming.get("utc_required") is not True:
        raise ContractError("utc_required must be true")

    return {
        "status": "PASS",
        "schema_version": mapping["schema_version"],
        "root": ROOT,
        "configured_path_count": len(all_paths),
        "top_level_root_count": len(roots),
        "hash_algorithm": naming["hash_algorithm"],
        "utc_required": naming["utc_required"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--map",
        dest="mapping_path",
        default="config/dropbox_repository_map.json",
    )
    args = parser.parse_args()
    path = Path(args.mapping_path)
    if not path.is_file():
        raise ContractError("repository map does not exist: " + str(path))
    try:
        mapping = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractError("invalid repository map JSON: " + str(path)) from exc
    if not isinstance(mapping, dict):
        raise ContractError("repository map must be a JSON object")
    print(json.dumps(validate(mapping), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ContractError, OSError, TypeError) as exc:
        print("DROPBOX_CONTRACT_FAIL_CLOSED: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
