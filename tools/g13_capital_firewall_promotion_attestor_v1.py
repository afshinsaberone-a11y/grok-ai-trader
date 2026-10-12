#!/usr/bin/env python3
"""Attest exact G13 Actions evidence only when a signed one-signal Capital Firewall grant exists.

Run on the independently administered attestor host, not on the MT5 runner.
The script reads current GitHub Actions runs/artifacts, verifies their exact SHA,
artifact digests and evidence contracts, checks an externally signed one-signal
grant, then signs a narrowly scoped promotion source attestation. It never
connects to MT5, emits orders, enables Live, or edits the Kill Switch.
"""
from __future__ import annotations

import argparse
import base64
import binascii
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


API_ROOT = "https://api.github.com"
ATTESTATION_SCHEMA = "forexai.control_plane_source_attestation.v1"
PROMOTION_EVIDENCE_SCHEMA = "forexai.g13.promotion_evidence.v1"
GRANT_SCHEMA = "forexai.capital_firewall.one_signal_demo_grant.v1"
ATTESTOR_KEY_ID = "forexai-g13-evidence-attestor-v1"
GRANT_KEY_ID = "forexai-capital-firewall-grant-v1"
MAX_ATTESTATION_AGE_SECONDS = 300
MAX_GRANT_LIFETIME_SECONDS = 900
MAX_CLOCK_SKEW_SECONDS = 2
MAX_ARTIFACT_BYTES = 250 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 512 * 1024 * 1024
MAX_ARTIFACT_FILES = 10000
SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
BASE64_SHA256_KEY = re.compile(r"^[A-Za-z0-9+/]{43}=$")

# Workflow IDs are pinned as well as names and workflow paths. If a workflow is
# intentionally recreated, this allowlist must be reviewed and changed in code.
REQUIRED_RUNS = {
    "validation": {
        "name": "ForexAI G13 Validation M15",
        "path": ".github/workflows/forexai-g13-validation-m15.yml",
        "workflow_id": 355468598,
        "job_name": "g13-validation",
        "artifact_name": "g13-validation-m15",
        "document": "g13-validation-m15.json",
    },
    "robustness": {
        "name": "ForexAI G13 Robustness M15",
        "path": ".github/workflows/forexai-g13-robustness-m15.yml",
        "workflow_id": 355473409,
        "job_name": "g13-robustness",
        "artifact_name": "g13-robustness-m15",
        "document": "g13-robustness-m15.json",
    },
    "oos": {
        "name": "ForexAI G13 OOS M15 Current",
        "path": ".github/workflows/forexai-g13-oos-m15-current.yml",
        "workflow_id": 356162316,
        "job_name": "G13 2026 OOS M15 Current",
        "artifact_name": "g13-oos-m15-2026-current",
        "document": "g13-oos-m15-2026.json",
    },
    "promotion": {
        "name": "ForexAI G13 Final Promotion M15",
        "path": ".github/workflows/forexai-g13-promotion-m15.yml",
        "workflow_id": 356366824,
        "job_name": "promotion",
        "artifact_name": "g13-promotion-manifest-m15",
        "document": "g13-promotion-manifest-m15.json",
    },
    "parity": {
        "name": "ForexAI G13 MT5 Compile + Signal Parity",
        "path": ".github/workflows/forexai-g13-mt5-compile-parity.yml",
        "workflow_id": 356474778,
        "job_name": "compile-and-parity",
        "artifact_name_prefix": "g13-mt5-compile-parity-",
        "document": "g13-mql5-signal-parity.json",
        "package_document": "g13-demo-package-manifest-m15.json",
    },
    "package_preflight": {
        "name": "ForexAI G13 Controlled Demo Package Preflight M15",
        "path": ".github/workflows/forexai-g13-controlled-demo-package-preflight-m15.yml",
        "workflow_id": 368483289,
        "job_name": "preflight",
        "artifact_name": "g13-controlled-demo-package-preflight-m15",
        "document": "g13-demo-package-preflight-m15.json",
    },
    "safety_audit": {
        "name": "ForexAI G13 Execution Safety Audit M15",
        "path": ".github/workflows/forexai-g13-execution-safety-audit-m15.yml",
        "workflow_id": 368434934,
        "job_name": "audit",
        "artifact_name": "g13-execution-safety-audit-m15",
        "document": "g13-execution-safety-audit-m15.json",
    },
    "readiness": {
        "name": "ForexAI G13 Demo Readiness Gate M15",
        "path": ".github/workflows/forexai-g13-demo-readiness-gate-m15.yml",
        "workflow_id": 368449689,
        "job_name": "readiness",
        "artifact_name": "g13-demo-readiness-gate-m15",
        "document": "g13-demo-readiness-gate-m15.json",
    },
}
RUN_ID_FIELDS = set(REQUIRED_RUNS)
GRANT_FIELDS = {
    "schema", "key_id", "grant_id", "repository", "commit_sha", "run_ids",
    "candidate_id", "candidate_config_hash", "signal_id", "trade_id",
    "authorization_id", "reservation_id", "scope", "symbol", "timeframe", "side",
    "issued_at_utc", "valid_until_utc", "demo_trading_allowed",
    "live_trading_allowed", "signature",
}
SIGNATURE_FIELDS = {"algorithm", "key_id", "signature"}


class AttestorError(RuntimeError):
    """Evidence, key provisioning, source grant, or GitHub trust checks failed."""


def canonical_json(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            dict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AttestorError("G13_ATTESTOR_CANONICAL_JSON_INVALID") from exc


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise AttestorError("G13_ATTESTOR_DUPLICATE_JSON_KEY")
        out[key] = value
    return out


def parse_json_bytes(raw: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_unique_object)
    except AttestorError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AttestorError("G13_ATTESTOR_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise AttestorError("G13_ATTESTOR_JSON_ROOT_INVALID")
    return value


def _exact(value: Any, fields: set[str], code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise AttestorError(code)
    return value


def _safe_id(value: Any, code: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise AttestorError(code)
    return value


def _utc(value: Any, code: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise AttestorError(code)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AttestorError(code) from exc
    if parsed.tzinfo is None:
        raise AttestorError(code)
    return parsed.astimezone(timezone.utc)


def _load_raw_ed25519_public(encoded: str, code: str) -> Ed25519PublicKey:
    if not isinstance(encoded, str) or not encoded or not BASE64_SHA256_KEY.fullmatch(encoded):
        raise AttestorError(code)
    try:
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) != 32:
            raise ValueError("invalid raw key size")
        return Ed25519PublicKey.from_public_bytes(raw)
    except (binascii.Error, ValueError) as exc:
        raise AttestorError(code) from exc


def load_attestor_private_key(path: str | Path, passphrase: str | None = None) -> Ed25519PrivateKey:
    try:
        key = serialization.load_pem_private_key(
            Path(path).read_bytes(), password=passphrase.encode("utf-8") if passphrase else None,
        )
    except (OSError, ValueError, TypeError) as exc:
        raise AttestorError("G13_ATTESTOR_PRIVATE_KEY_UNAVAILABLE_OR_INVALID") from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise AttestorError("G13_ATTESTOR_PRIVATE_KEY_MUST_BE_ED25519")
    return key


def verify_attestor_key(private_key: Ed25519PrivateKey, expected_public_key: str) -> None:
    if not expected_public_key:
        raise AttestorError("G13_ATTESTOR_TRUST_ANCHOR_NOT_CONFIGURED")
    expected = _load_raw_ed25519_public(
        expected_public_key, "G13_ATTESTOR_TRUST_ANCHOR_INVALID",
    ).public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    actual = private_key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw,
    )
    if not hmac.compare_digest(expected, actual):
        raise AttestorError("G13_ATTESTOR_PRIVATE_KEY_TRUST_ANCHOR_MISMATCH")


def _api_request(path: str, token: str, *, no_redirect: bool = False) -> bytes:
    if not token:
        raise AttestorError("G13_ATTESTOR_GITHUB_READ_TOKEN_NOT_CONFIGURED")
    url = path if path.startswith("https://") else f"{API_ROOT}{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ForexAI-G13-Evidence-Attestor/1.0",
        },
    )
    if no_redirect:
        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
                return None
        opener = urllib.request.build_opener(_NoRedirect)
        try:
            with opener.open(req, timeout=30) as response:
                raw = response.read(MAX_ARTIFACT_BYTES + 1)
        except urllib.error.HTTPError as exc:
            if exc.code in (301, 302, 303, 307, 308):
                location = exc.headers.get("Location")
                if not location:
                    raise AttestorError("G13_ATTESTOR_ARTIFACT_REDIRECT_MISSING") from exc
                # Deliberately make the signed-URL request without GitHub credentials.
                try:
                    with urllib.request.urlopen(
                        urllib.request.Request(location, headers={"User-Agent": "ForexAI-G13-Evidence-Attestor/1.0"}),
                        timeout=60,
                    ) as response:
                        raw = response.read(MAX_ARTIFACT_BYTES + 1)
                except Exception as inner:
                    raise AttestorError("G13_ATTESTOR_ARTIFACT_DOWNLOAD_FAILED") from inner
            else:
                raise AttestorError(f"G13_ATTESTOR_GITHUB_HTTP_{exc.code}") from exc
        except urllib.error.URLError as exc:
            raise AttestorError("G13_ATTESTOR_GITHUB_UNREACHABLE") from exc
    else:
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read(MAX_ARTIFACT_BYTES + 1)
        except urllib.error.HTTPError as exc:
            raise AttestorError(f"G13_ATTESTOR_GITHUB_HTTP_{exc.code}") from exc
        except urllib.error.URLError as exc:
            raise AttestorError("G13_ATTESTOR_GITHUB_UNREACHABLE") from exc
    if len(raw) > MAX_ARTIFACT_BYTES:
        raise AttestorError("G13_ATTESTOR_ARTIFACT_TOO_LARGE")
    return raw


def _api_json(repo: str, path: str, token: str) -> dict[str, Any]:
    raw = _api_request(f"/repos/{repo}/{path.lstrip('/')}", token)
    return parse_json_bytes(raw)


def _artifact_documents(raw_zip: bytes, wanted: set[str]) -> dict[str, dict[str, Any]]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw_zip))
        infos = archive.infolist()
    except (zipfile.BadZipFile, OSError) as exc:
        raise AttestorError("G13_ATTESTOR_ARTIFACT_ZIP_INVALID") from exc
    if len(infos) > MAX_ARTIFACT_FILES:
        raise AttestorError("G13_ATTESTOR_ARTIFACT_FILE_COUNT_EXCEEDED")
    total = sum(info.file_size for info in infos)
    if total > MAX_UNCOMPRESSED_BYTES:
        raise AttestorError("G13_ATTESTOR_ARTIFACT_EXPANSION_LIMIT")
    for info in infos:
        path = PurePosixPath(info.filename)
        if path.is_absolute() or ".." in path.parts or "\\" in info.filename:
            raise AttestorError("G13_ATTESTOR_ARTIFACT_PATH_INVALID")
    matches: dict[str, list[zipfile.ZipInfo]] = {name: [] for name in wanted}
    for info in infos:
        if not info.is_dir() and PurePosixPath(info.filename).name in matches:
            matches[PurePosixPath(info.filename).name].append(info)
    docs: dict[str, dict[str, Any]] = {}
    for name in wanted:
        candidates = matches[name]
        if len(candidates) != 1:
            raise AttestorError(f"G13_ATTESTOR_ARTIFACT_DOCUMENT_CARDINALITY:{name}")
        try:
            docs[name] = parse_json_bytes(archive.read(candidates[0]))
        except (KeyError, RuntimeError, zipfile.BadZipFile) as exc:
            raise AttestorError(f"G13_ATTESTOR_ARTIFACT_DOCUMENT_INVALID:{name}") from exc
    return docs


def _download_verified_artifact(repo: str, run_id: int, artifact: Mapping[str, Any], token: str) -> tuple[bytes, str]:
    digest = artifact.get("digest")
    if not isinstance(digest, str) or not digest.startswith("sha256:") or not SHA256.fullmatch(digest[7:]):
        raise AttestorError("G13_ATTESTOR_GITHUB_ARTIFACT_DIGEST_MISSING")
    artifact_id = artifact.get("id")
    if isinstance(artifact_id, bool) or not isinstance(artifact_id, int) or artifact_id <= 0:
        raise AttestorError("G13_ATTESTOR_GITHUB_ARTIFACT_ID_INVALID")
    raw = _api_request(
        f"/repos/{repo}/actions/artifacts/{artifact_id}/zip", token, no_redirect=True,
    )
    actual = hashlib.sha256(raw).hexdigest()
    if not hmac.compare_digest(actual, digest[7:]):
        raise AttestorError("G13_ATTESTOR_GITHUB_ARTIFACT_DIGEST_MISMATCH")
    return raw, digest


def _positive_run_id(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise AttestorError("G13_ATTESTOR_GRANT_RUN_IDS_INVALID")
    return value


def _verify_grant(
    grant: Mapping[str, Any],
    *,
    repo: str,
    target_sha: str,
    now: datetime,
    public_key_encoded: str,
) -> dict[str, Any]:
    _exact(grant, GRANT_FIELDS, "G13_ATTESTOR_GRANT_FIELDS_INVALID")
    if grant["schema"] != GRANT_SCHEMA or grant["key_id"] != GRANT_KEY_ID:
        raise AttestorError("G13_ATTESTOR_GRANT_SCHEMA_OR_KEY_ID_INVALID")
    if grant["repository"] != repo or grant["commit_sha"] != target_sha:
        raise AttestorError("G13_ATTESTOR_GRANT_REPOSITORY_OR_SHA_MISMATCH")
    if not COMMIT_SHA.fullmatch(str(grant["commit_sha"])):
        raise AttestorError("G13_ATTESTOR_GRANT_SHA_INVALID")
    if grant["scope"] != "ONE_SIGNAL_DEMO_ONLY":
        raise AttestorError("G13_ATTESTOR_GRANT_SCOPE_INVALID")
    if grant["demo_trading_allowed"] is not True:
        raise AttestorError("G13_ATTESTOR_GRANT_DEMO_NOT_GRANTED")
    if grant["live_trading_allowed"] is not False:
        raise AttestorError("G13_ATTESTOR_GRANT_LIVE_MUST_REMAIN_DISABLED")
    if grant["symbol"] != "EURUSD" or grant["timeframe"] != "M15" or grant["side"] != "SELL":
        raise AttestorError("G13_ATTESTOR_GRANT_TRADE_IDENTITY_UNSUPPORTED")
    _safe_id(grant["grant_id"], "G13_ATTESTOR_GRANT_ID_INVALID")
    _safe_id(grant["signal_id"], "G13_ATTESTOR_GRANT_SIGNAL_ID_INVALID")
    _safe_id(grant["authorization_id"], "G13_ATTESTOR_GRANT_AUTHORIZATION_ID_INVALID")
    _safe_id(grant["reservation_id"], "G13_ATTESTOR_GRANT_RESERVATION_ID_INVALID")
    trade_id = _safe_id(grant["trade_id"], "G13_ATTESTOR_GRANT_TRADE_ID_INVALID")
    if not trade_id.endswith("-S"):
        raise AttestorError("G13_ATTESTOR_GRANT_TRADE_ID_MUST_END_WITH_-S")
    candidate_id = grant["candidate_id"]
    if isinstance(candidate_id, bool) or not isinstance(candidate_id, int) or candidate_id <= 0:
        raise AttestorError("G13_ATTESTOR_GRANT_CANDIDATE_ID_INVALID")
    if not isinstance(grant["candidate_config_hash"], str) or not SHA256.fullmatch(grant["candidate_config_hash"]):
        raise AttestorError("G13_ATTESTOR_GRANT_CONFIG_HASH_INVALID")
    run_ids = _exact(grant["run_ids"], RUN_ID_FIELDS, "G13_ATTESTOR_GRANT_RUN_IDS_INVALID")
    normalized_ids = {key: _positive_run_id(value) for key, value in run_ids.items()}
    if len(set(normalized_ids.values())) != len(normalized_ids):
        raise AttestorError("G13_ATTESTOR_GRANT_RUN_IDS_NOT_UNIQUE")
    issued = _utc(grant["issued_at_utc"], "G13_ATTESTOR_GRANT_ISSUED_AT_INVALID")
    until = _utc(grant["valid_until_utc"], "G13_ATTESTOR_GRANT_EXPIRY_INVALID")
    if issued > now + timedelta(seconds=MAX_CLOCK_SKEW_SECONDS):
        raise AttestorError("G13_ATTESTOR_GRANT_FROM_FUTURE")
    if now - issued > timedelta(seconds=MAX_GRANT_LIFETIME_SECONDS):
        raise AttestorError("G13_ATTESTOR_GRANT_STALE")
    if until <= now or until <= issued:
        raise AttestorError("G13_ATTESTOR_GRANT_EXPIRED")
    if until - issued > timedelta(seconds=MAX_GRANT_LIFETIME_SECONDS):
        raise AttestorError("G13_ATTESTOR_GRANT_VALIDITY_TOO_LONG")
    signature = _exact(grant["signature"], SIGNATURE_FIELDS, "G13_ATTESTOR_GRANT_SIGNATURE_FIELDS_INVALID")
    if signature["algorithm"] != "Ed25519" or signature["key_id"] != GRANT_KEY_ID:
        raise AttestorError("G13_ATTESTOR_GRANT_SIGNATURE_METADATA_INVALID")
    encoded = signature["signature"]
    if not isinstance(encoded, str):
        raise AttestorError("G13_ATTESTOR_GRANT_SIGNATURE_INVALID")
    try:
        raw_signature = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise AttestorError("G13_ATTESTOR_GRANT_SIGNATURE_INVALID") from exc
    if len(raw_signature) != 64:
        raise AttestorError("G13_ATTESTOR_GRANT_SIGNATURE_INVALID")
    public_key = _load_raw_ed25519_public(
        public_key_encoded, "G13_ATTESTOR_CAPITAL_FIREWALL_PUBLIC_KEY_INVALID",
    )
    unsigned = {key: value for key, value in grant.items() if key != "signature"}
    try:
        public_key.verify(raw_signature, canonical_json(unsigned))
    except InvalidSignature as exc:
        raise AttestorError("G13_ATTESTOR_GRANT_SIGNATURE_VERIFICATION_FAILED") from exc
    return {**dict(grant), "run_ids": normalized_ids, "_issued": issued, "_until": until}


def _expected_artifact_name(role: str, run_id: int) -> str:
    spec = REQUIRED_RUNS[role]
    if role == "parity":
        return f"{spec['artifact_name_prefix']}{run_id}"
    return str(spec["artifact_name"])


def _fetch_run_and_artifact(
    repo: str, role: str, run_id: int, target_sha: str, token: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, dict[str, Any]], str]:
    spec = REQUIRED_RUNS[role]
    run = _api_json(repo, f"actions/runs/{run_id}", token)
    if (
        run.get("id") != run_id
        or run.get("name") != spec["name"]
        or run.get("path") != spec["path"]
        or run.get("workflow_id") != spec["workflow_id"]
        or run.get("head_branch") != "main"
        or run.get("head_sha") != target_sha
        or run.get("status") != "completed"
        or run.get("conclusion") != "success"
        or run.get("repository", {}).get("full_name") != repo
    ):
        raise AttestorError(f"G13_ATTESTOR_EXACT_SHA_RUN_NOT_SUCCESS:{role}")
    job_list = _api_json(repo, f"actions/runs/{run_id}/jobs?per_page=100", token)
    expected_job_name = str(spec["job_name"])
    successful_jobs = [
        job for job in job_list.get("jobs", [])
        if job.get("name") == expected_job_name
        and job.get("status") == "completed"
        and job.get("conclusion") == "success"
    ]
    if len(successful_jobs) != 1:
        raise AttestorError(f"G13_ATTESTOR_EXACT_SHA_JOB_NOT_SUCCESS:{role}")
    job_id = successful_jobs[0].get("id")
    if isinstance(job_id, bool) or not isinstance(job_id, int) or job_id <= 0:
        raise AttestorError(f"G13_ATTESTOR_SUCCESS_JOB_ID_INVALID:{role}")
    run = dict(run)
    run["_attestor_success_job_id"] = job_id

    artifact_list = _api_json(repo, f"actions/runs/{run_id}/artifacts?per_page=100", token)
    expected_name = _expected_artifact_name(role, run_id)
    found = [item for item in artifact_list.get("artifacts", []) if item.get("name") == expected_name]
    if len(found) != 1 or found[0].get("expired") is not False:
        raise AttestorError(f"G13_ATTESTOR_EXPECTED_ARTIFACT_UNAVAILABLE:{role}")
    artifact = found[0]
    expected_docs = {spec["document"]}
    if role == "parity":
        expected_docs.add(str(spec["package_document"]))
    raw_zip, digest = _download_verified_artifact(repo, run_id, artifact, token)
    docs = _artifact_documents(raw_zip, expected_docs)
    return run, artifact, docs, digest


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise AttestorError(reason)


def _id_set(rows: Any, id_field: str, pass_field: str | None = None) -> list[int]:
    if not isinstance(rows, list):
        raise AttestorError("G13_ATTESTOR_CANDIDATE_ROWS_INVALID")
    selected = []
    for row in rows:
        if not isinstance(row, Mapping):
            raise AttestorError("G13_ATTESTOR_CANDIDATE_ROW_INVALID")
        value = row.get(id_field)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise AttestorError("G13_ATTESTOR_CANDIDATE_ID_INVALID")
        if pass_field is None or row.get(pass_field) is True:
            selected.append(value)
    return selected


def _validate_evidence(
    *, repo: str, target_sha: str, grant: Mapping[str, Any],
    runs: Mapping[str, Mapping[str, Any]], artifacts: Mapping[str, Mapping[str, Any]],
    docs: Mapping[str, Mapping[str, Any]], digests: Mapping[str, str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    validation = docs["validation"]
    _require(validation.get("schema") == "forexai.g13.validation_m15.v1", "G13_ATTESTOR_VALIDATION_SCHEMA_INVALID")
    _require(validation.get("real_data_only") is True, "G13_ATTESTOR_VALIDATION_REAL_DATA_POLICY_FAILED")
    _require(validation.get("selection_used_2025") is False, "G13_ATTESTOR_VALIDATION_2025_SELECTION_DETECTED")
    _require(validation.get("oos_evaluated") is False, "G13_ATTESTOR_VALIDATION_OOS_WAS_EVALUATED")
    validation_count = validation.get("validation_qualified_count")
    _require(isinstance(validation_count, int) and not isinstance(validation_count, bool) and validation_count > 0,
             "G13_ATTESTOR_VALIDATION_QUALIFIED_COUNT_INVALID")
    validation_ids = _id_set(validation.get("candidates"), "candidate_id", "validation_pass")
    _require(len(validation_ids) == len(set(validation_ids)),
             "G13_ATTESTOR_VALIDATION_CANDIDATE_IDS_DUPLICATE")
    _require(len(validation_ids) == validation_count,
             "G13_ATTESTOR_VALIDATION_CANDIDATE_COVERAGE_INVALID")

    robustness = docs["robustness"]
    _require(robustness.get("schema") == "forexai.g13.robustness_m15.v1", "G13_ATTESTOR_ROBUSTNESS_SCHEMA_INVALID")
    _require(robustness.get("status") == "PASS", "G13_ATTESTOR_ROBUSTNESS_NOT_PASS")
    _require(robustness.get("real_data_only") is True, "G13_ATTESTOR_ROBUSTNESS_REAL_DATA_POLICY_FAILED")
    _require(robustness.get("selection_performed") is False and robustness.get("optimization_enabled") is False,
             "G13_ATTESTOR_ROBUSTNESS_SELECTION_OR_OPTIMIZATION_DETECTED")
    _require(robustness.get("oos") == {"status": "HELD_OUT", "evaluated": False, "optimization_allowed": False},
             "G13_ATTESTOR_ROBUSTNESS_OOS_POLICY_FAILED")
    robustness_ids = _id_set(robustness.get("candidates"), "candidate_id")
    robustness_pass_ids = _id_set(robustness.get("candidates"), "candidate_id", "robustness_pass")
    _require(len(robustness_ids) == len(set(robustness_ids))
             and sorted(robustness_ids) == sorted(validation_ids),
             "G13_ATTESTOR_ROBUSTNESS_CANDIDATE_IDENTITY_MISMATCH")
    _require(len(robustness_pass_ids) == len(robustness_ids)
             and all(row.get("robustness_pass") is True for row in robustness["candidates"]),
             "G13_ATTESTOR_ROBUSTNESS_CANDIDATE_PASS_FLAGS_INVALID")
    _require(robustness.get("candidate_count") == validation_count, "G13_ATTESTOR_ROBUSTNESS_CANDIDATE_COUNT_MISMATCH")
    _require(robustness.get("robustness_pass_count") == validation_count, "G13_ATTESTOR_ROBUSTNESS_NOT_ALL_CANDIDATES_PASS")

    oos = docs["oos"]
    _require(oos.get("schema_version") == "forexai.g13.oos_m15.2026.v1", "G13_ATTESTOR_OOS_SCHEMA_INVALID")
    _require(oos.get("real_data_only") is True, "G13_ATTESTOR_OOS_REAL_DATA_POLICY_FAILED")
    _require(oos.get("selection_performed") is False and oos.get("optimization_enabled") is False,
             "G13_ATTESTOR_OOS_SELECTION_OR_OPTIMIZATION_DETECTED")
    _require(oos.get("parameters_frozen") is True, "G13_ATTESTOR_OOS_PARAMETERS_NOT_FROZEN")
    _require(oos.get("oos", {}).get("status") == "EVALUATED"
             and oos.get("oos", {}).get("evaluated") is True
             and oos.get("oos", {}).get("optimization_allowed") is False
             and oos.get("oos", {}).get("selection_allowed") is False,
             "G13_ATTESTOR_OOS_POLICY_FAILED")
    oos_all_ids = _id_set(oos.get("candidates"), "candidate_id")
    oos_ids = _id_set(oos.get("candidates"), "candidate_id", "oos_pass")
    _require(len(oos_all_ids) == len(set(oos_all_ids))
             and sorted(oos_all_ids) == sorted(validation_ids),
             "G13_ATTESTOR_OOS_CANDIDATE_COVERAGE_MISMATCH")
    _require(len(oos_ids) == len(set(oos_ids)),
             "G13_ATTESTOR_OOS_CANDIDATE_IDS_DUPLICATE")
    _require(oos.get("candidate_count") == len(oos_all_ids),
             "G13_ATTESTOR_OOS_CANDIDATE_COUNT_INVALID")
    _require(oos.get("oos_pass_count") == len(oos_ids) and len(oos_ids) > 0,
             "G13_ATTESTOR_OOS_PASS_COUNT_INVALID")

    promotion_manifest = docs["promotion"]
    _require(promotion_manifest.get("schema_version") == "forexai.g13.promotion_manifest.m15.v1",
             "G13_ATTESTOR_PROMOTION_SCHEMA_INVALID")
    _require(promotion_manifest.get("status") == "PROMOTION_READY", "G13_ATTESTOR_PROMOTION_NOT_READY")
    decision = promotion_manifest.get("decision_policy")
    _require(isinstance(decision, Mapping)
             and decision.get("selection_performed") is False
             and decision.get("optimization_performed") is False
             and decision.get("demo_trading_allowed") is False
             and decision.get("live_trading_allowed") is False,
             "G13_ATTESTOR_PROMOTION_POLICY_INVALID")
    promoted_ids = promotion_manifest.get("promoted_candidate_ids")
    _require(isinstance(promoted_ids, list) and promoted_ids and all(
        isinstance(x, int) and not isinstance(x, bool) and x > 0 for x in promoted_ids
    ) and len(promoted_ids) == len(set(promoted_ids)), "G13_ATTESTOR_PROMOTED_CANDIDATES_INVALID")
    _require(sorted(promoted_ids) == oos_ids, "G13_ATTESTOR_PROMOTION_OOS_CANDIDATE_MISMATCH")
    candidates = promotion_manifest.get("candidates")
    if not isinstance(candidates, list):
        raise AttestorError("G13_ATTESTOR_PROMOTION_CANDIDATES_INVALID")
    config_hashes: dict[str, str] = {}
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise AttestorError("G13_ATTESTOR_PROMOTION_CANDIDATE_INVALID")
        cid = candidate.get("candidate_id")
        config_hash = candidate.get("config_hash")
        if isinstance(cid, bool) or not isinstance(cid, int) or cid not in promoted_ids:
            raise AttestorError("G13_ATTESTOR_PROMOTION_CANDIDATE_ID_INVALID")
        if not isinstance(config_hash, str) or not SHA256.fullmatch(config_hash):
            raise AttestorError("G13_ATTESTOR_PROMOTION_CONFIG_HASH_INVALID")
        if str(cid) in config_hashes:
            raise AttestorError("G13_ATTESTOR_PROMOTION_DUPLICATE_CANDIDATE")
        config_hashes[str(cid)] = config_hash
    _require(set(config_hashes) == {str(x) for x in promoted_ids}, "G13_ATTESTOR_PROMOTION_CONFIG_HASH_COVERAGE_INVALID")

    # Promotion itself records Demo=False. Only the separately signed, scoped
    # Capital Firewall grant may authorize the one candidate/signal below.
    grant_candidate_id = grant["candidate_id"]
    _require(grant_candidate_id in promoted_ids, "G13_ATTESTOR_GRANT_CANDIDATE_NOT_PROMOTED")
    _require(
        hmac.compare_digest(str(grant["candidate_config_hash"]), config_hashes[str(grant_candidate_id)]),
        "G13_ATTESTOR_GRANT_CONFIG_HASH_MISMATCH",
    )

    sources = promotion_manifest.get("source_artifacts")
    _require(isinstance(sources, Mapping), "G13_ATTESTOR_PROMOTION_SOURCE_ARTIFACTS_INVALID")
    for role in ("validation", "robustness", "oos"):
        source = sources.get(role)
        if not isinstance(source, Mapping):
            raise AttestorError(f"G13_ATTESTOR_PROMOTION_SOURCE_MISSING:{role}")
        _require(source.get("run_id") == runs[role]["id"], f"G13_ATTESTOR_PROMOTION_SOURCE_RUN_MISMATCH:{role}")
        _require(source.get("artifact_id") == artifacts[role]["id"], f"G13_ATTESTOR_PROMOTION_SOURCE_ARTIFACT_MISMATCH:{role}")
        _require(source.get("artifact_name") == artifacts[role]["name"], f"G13_ATTESTOR_PROMOTION_SOURCE_NAME_MISMATCH:{role}")
        _require(source.get("artifact_digest") == digests[role], f"G13_ATTESTOR_PROMOTION_SOURCE_DIGEST_MISMATCH:{role}")
        _require(source.get("run_head_sha") == target_sha and source.get("head_branch") == "main",
                 f"G13_ATTESTOR_PROMOTION_SOURCE_SHA_MISMATCH:{role}")
        _require(source.get("workflow_id") == runs[role]["workflow_id"]
                 and source.get("workflow_name") == runs[role]["name"],
                 f"G13_ATTESTOR_PROMOTION_SOURCE_WORKFLOW_MISMATCH:{role}")
        _require(source.get("job_name") == REQUIRED_RUNS[role]["job_name"]
                 and source.get("job_id") == runs[role]["_attestor_success_job_id"],
                 f"G13_ATTESTOR_PROMOTION_SOURCE_JOB_MISMATCH:{role}")

    parity = docs["parity"]
    _require(parity.get("schema_version") == "forexai.g13.mql5_signal_parity.v2", "G13_ATTESTOR_PARITY_SCHEMA_INVALID")
    _require(parity.get("status") == "PASS" and parity.get("real_data_only") is True and parity.get("synthetic_data") is False,
             "G13_ATTESTOR_PARITY_REAL_DATA_OR_STATUS_INVALID")
    _require(parity.get("selection_performed") is False and parity.get("optimization_enabled") is False,
             "G13_ATTESTOR_PARITY_SELECTION_OR_OPTIMIZATION_DETECTED")
    parity_ids = sorted(_id_set(parity.get("results"), "candidate_id"))
    _require(parity.get("candidate_count") == len(promoted_ids)
             and parity.get("passed_count") == len(promoted_ids)
             and parity_ids == sorted(promoted_ids),
             "G13_ATTESTOR_PARITY_CANDIDATE_COVERAGE_INVALID")
    _require(all(row.get("status") == "PASS" and row.get("actual_signals") == row.get("expected_signals")
                 for row in parity["results"]),
             "G13_ATTESTOR_PARITY_SIGNAL_MISMATCH")

    package = docs["parity_package"]
    _require(package.get("schema_version") == "forexai.g13.demo_package_manifest.m15.v2",
             "G13_ATTESTOR_PACKAGE_MANIFEST_SCHEMA_INVALID")
    _require(package.get("ea_source_commit") == target_sha, "G13_ATTESTOR_PACKAGE_SOURCE_SHA_MISMATCH")
    _require(package.get("compile_parity_run_id") == runs["parity"]["id"], "G13_ATTESTOR_PACKAGE_PARITY_RUN_MISMATCH")
    _require(package.get("promoted_candidate_ids") == promoted_ids, "G13_ATTESTOR_PACKAGE_CANDIDATE_SET_MISMATCH")
    _require(package.get("demo_trading_allowed_by_source") is False
             and package.get("live_trading_allowed") is False
             and package.get("real_data_only") is True
             and package.get("synthetic_data") is False,
             "G13_ATTESTOR_PACKAGE_POLICY_INVALID")

    preflight = docs["package_preflight"]
    _require(preflight.get("schema_version") == "forexai.g13.controlled_demo_package_preflight.m15.v1"
             and preflight.get("status") == "PASS", "G13_ATTESTOR_PREFLIGHT_NOT_PASS")
    _require(preflight.get("ea_source_commit") == target_sha and preflight.get("compile_parity_head_sha") == target_sha,
             "G13_ATTESTOR_PREFLIGHT_SOURCE_SHA_MISMATCH")
    _require(preflight.get("compile_parity_run_id") == runs["parity"]["id"], "G13_ATTESTOR_PREFLIGHT_PARITY_RUN_MISMATCH")
    _require(preflight.get("compile_parity_artifact_id") == artifacts["parity"]["id"]
             and preflight.get("compile_parity_artifact_digest") == digests["parity"]
             and preflight.get("downloaded_zip_sha256") == digests["parity"][7:],
             "G13_ATTESTOR_PREFLIGHT_PARITY_ARTIFACT_MISMATCH")
    preflight_ids = preflight.get("candidate_ids")
    _require(isinstance(preflight_ids, list)
             and len(preflight_ids) == len(set(preflight_ids))
             and sorted(preflight_ids) == sorted(promoted_ids)
             and preflight.get("candidate_count") == len(promoted_ids),
             "G13_ATTESTOR_PREFLIGHT_CANDIDATES_MISMATCH")
    _require(preflight.get("source_hashes_verified") == len(promoted_ids)
             and preflight.get("binary_hashes_verified") == len(promoted_ids)
             and preflight.get("source_safety_contracts_verified") == len(promoted_ids),
             "G13_ATTESTOR_PREFLIGHT_HASH_OR_SAFETY_COVERAGE_INVALID")
    _require(preflight.get("demo_trading_allowed_by_source") is False and preflight.get("live_trading_allowed") is False,
             "G13_ATTESTOR_PREFLIGHT_PERMISSION_MUST_BE_SOURCE_DENIED")
    _require(preflight.get("real_data_only") is True and preflight.get("synthetic_data") is False,
             "G13_ATTESTOR_PREFLIGHT_DATA_POLICY_INVALID")

    safety = docs["safety_audit"]
    _require(safety.get("schema") == "forexai.g13.execution_safety_audit_m15.v1"
             and safety.get("status") == "PASS", "G13_ATTESTOR_SAFETY_AUDIT_NOT_PASS")
    safety_policy = safety.get("policy")
    _require(isinstance(safety_policy, Mapping)
             and safety_policy.get("live_trading_allowed") is False
             and safety_policy.get("demo_trading_default_authorized") is False,
             "G13_ATTESTOR_SAFETY_PERMISSION_POLICY_INVALID")
    source_results = safety.get("sources")
    safety_source_ids = _id_set(source_results, "candidate_id")
    _require(isinstance(source_results, list) and len(safety_source_ids) == len(set(safety_source_ids))
             and sorted(safety_source_ids) == sorted(promoted_ids)
             and all(row.get("pass") is True for row in source_results),
             "G13_ATTESTOR_SAFETY_SOURCE_COVERAGE_INVALID")
    matrix = safety.get("matrix")
    _require(isinstance(matrix, list) and len(matrix) == 1536 and all(row.get("pass") is True for row in matrix),
             "G13_ATTESTOR_SAFETY_MATRIX_INVALID")

    readiness = docs["readiness"]
    _require(readiness.get("schema") == "forexai.g13.demo_readiness_gate_m15.v1"
             and readiness.get("status") == "READY_FOR_CONTROLLED_DEMO_AUDIT"
             and readiness.get("next_gate") == "CONTROLLED_DEMO_EXECUTION_AUDIT",
             "G13_ATTESTOR_READINESS_STATUS_INVALID")
    readiness_promotion = readiness.get("promotion")
    _require(isinstance(readiness_promotion, Mapping)
             and readiness_promotion.get("head_sha") == target_sha
             and readiness_promotion.get("run_id") == runs["promotion"]["id"]
             and readiness_promotion.get("status") == "PROMOTION_READY"
             and readiness_promotion.get("demo_trading_allowed") is False
             and readiness_promotion.get("live_trading_allowed") is False,
             "G13_ATTESTOR_READINESS_PROMOTION_POLICY_INVALID")
    _require(readiness.get("live_remains_disabled") is True, "G13_ATTESTOR_READINESS_LIVE_NOT_LOCKED")
    evidence = readiness.get("evidence")
    _require(isinstance(evidence, Mapping)
             and evidence.get("parity_head_sha") == target_sha
             and evidence.get("parity_status") == "PASS"
             and evidence.get("parity_passed_count") == len(promoted_ids)
             and evidence.get("safety_head_sha") == target_sha,
             "G13_ATTESTOR_READINESS_EVIDENCE_MISMATCH")
    readiness_preflight = readiness.get("preflight")
    _require(isinstance(readiness_preflight, Mapping)
             and readiness_preflight.get("status") == "PASS"
             and readiness_preflight.get("run_id") == runs["package_preflight"]["id"]
             and readiness_preflight.get("compile_parity_run_id") == runs["parity"]["id"],
             "G13_ATTESTOR_READINESS_PREFLIGHT_MISMATCH")
    runtime = readiness.get("runtime")
    _require(isinstance(runtime, Mapping)
             and runtime.get("orders_submitted") is False
             and runtime.get("real_account_detected") is False,
             "G13_ATTESTOR_RUNTIME_ORDER_OR_REAL_ACCOUNT_FLAGGED")

    data_sha = parity.get("data_sha256")
    manifest_sha = parity.get("data_manifest_sha256")
    _require(isinstance(data_sha, str) and SHA256.fullmatch(data_sha), "G13_ATTESTOR_DATA_SHA_INVALID")
    _require(isinstance(manifest_sha, str) and SHA256.fullmatch(manifest_sha), "G13_ATTESTOR_DATA_MANIFEST_SHA_INVALID")
    for source, data_field, manifest_field in (
        (package, "data_sha256", "data_manifest_sha256"),
        (preflight, "data_sha256", "data_manifest_sha256"),
        (readiness.get("evidence", {}), "data_sha256", "data_manifest_sha256"),
    ):
        _require(source.get(data_field) == data_sha and source.get(manifest_field) == manifest_sha,
                 "G13_ATTESTOR_REAL_DATA_HASH_CHAIN_MISMATCH")

    # Build the complete and independently verifiable artifact digest statement.
    digest_payload = {
        "repository": repo,
        "commit_sha": target_sha,
        "run_ids": {role: runs[role]["id"] for role in REQUIRED_RUNS},
        "artifacts": {
            role: {"id": artifacts[role]["id"], "name": artifacts[role]["name"], "digest": digests[role]}
            for role in REQUIRED_RUNS
        },
        "capital_firewall_grant_sha256": hashlib.sha256(canonical_json({
            key: value for key, value in grant.items() if not key.startswith("_")
        })).hexdigest(),
    }
    evidence_bundle_sha256 = hashlib.sha256(canonical_json(digest_payload)).hexdigest()
    grant_sha256 = digest_payload["capital_firewall_grant_sha256"]

    payload = {
        "schema": PROMOTION_EVIDENCE_SCHEMA,
        "commit_sha": target_sha,
        "gates": {
            "validation": "PASS", "robustness": "PASS", "oos": "PASS",
            "parity": "PASS", "package_preflight": "PASS", "safety_audit": "PASS",
        },
        "readiness_status": "READY_FOR_CONTROLLED_DEMO_AUDIT",
        "demo_trading_allowed": True,
        "live_trading_allowed": False,
        "real_data_only": True,
        "synthetic_data": False,
        "run_ids": {role: runs[role]["id"] for role in REQUIRED_RUNS},
        "promoted_candidate_ids": promoted_ids,
        "candidate_config_hashes": config_hashes,
        "source_grant_id": grant["grant_id"],
        "source_grant_candidate_id": grant_candidate_id,
        "source_grant_signal_id": grant["signal_id"],
        "source_grant_trade_id": grant["trade_id"],
        "source_grant_authorization_id": grant["authorization_id"],
        "source_grant_reservation_id": grant["reservation_id"],
        "source_grant_sha256": grant_sha256,
        "evidence_bundle_sha256": evidence_bundle_sha256,
    }
    audit = {
        "schema": "forexai.g13.capital_firewall_promotion_attestation_receipt.v1",
        "status": "PASS",
        "repository": repo,
        "commit_sha": target_sha,
        "run_ids": payload["run_ids"],
        "grant_id": grant["grant_id"],
        "grant_scope": grant["scope"],
        "candidate_id": grant_candidate_id,
        "signal_id": grant["signal_id"],
        "trade_id": grant["trade_id"],
        "authorization_id": grant["authorization_id"],
        "reservation_id": grant["reservation_id"],
        "source_grant_sha256": grant_sha256,
        "evidence_bundle_sha256": evidence_bundle_sha256,
        "artifact_receipts": digest_payload["artifacts"],
        "evidence_bundle": digest_payload,
        "demo_trading_allowed": True,
        "live_trading_allowed": False,
        "orders_submitted": False,
    }
    return payload, audit


def build_signed_attestation(
    payload: Mapping[str, Any],
    *,
    private_key: Ed25519PrivateKey,
    now: datetime,
    grant_expiry: datetime,
) -> dict[str, Any]:
    issued = now.astimezone(timezone.utc)
    expiry = min(grant_expiry.astimezone(timezone.utc), issued + timedelta(seconds=MAX_ATTESTATION_AGE_SECONDS))
    if expiry <= issued:
        raise AttestorError("G13_ATTESTOR_GRANT_TOO_CLOSE_TO_EXPIRY")
    attestation = {
        "schema": ATTESTATION_SCHEMA,
        "source_type": "promotion",
        "key_id": ATTESTOR_KEY_ID,
        "issued_at_utc": issued.isoformat(),
        "valid_until_utc": expiry.isoformat(),
        "payload": dict(payload),
    }
    attestation["signature"] = {
        "algorithm": "Ed25519",
        "key_id": ATTESTOR_KEY_ID,
        "signature": base64.b64encode(private_key.sign(canonical_json(attestation))).decode("ascii"),
    }
    return attestation


def _write_pair_new(
    first_path: Path, first_value: Mapping[str, Any],
    second_path: Path, second_value: Mapping[str, Any],
) -> None:
    """Atomically publish a new attestation and matching audit receipt as a pair."""
    pairs = [
        (first_path.expanduser().resolve(strict=False), first_value),
        (second_path.expanduser().resolve(strict=False), second_value),
    ]
    if pairs[0][0] == pairs[1][0]:
        raise AttestorError("G13_ATTESTOR_OUTPUT_RECEIPT_PATH_COLLISION")
    staged: list[tuple[Path, Path]] = []
    published: list[Path] = []
    try:
        for target, value in pairs:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                raise AttestorError("G13_ATTESTOR_OUTPUT_ALREADY_EXISTS")
            raw = json.dumps(
                dict(value), ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False
            ).encode("utf-8") + b"\n"
            temp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
            fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            staged.append((temp, target))
        for temp, target in staged:
            try:
                os.link(temp, target)
            except FileExistsError as exc:
                raise AttestorError("G13_ATTESTOR_OUTPUT_ALREADY_EXISTS") from exc
            except OSError as exc:
                if target.exists():
                    raise AttestorError("G13_ATTESTOR_OUTPUT_ALREADY_EXISTS") from exc
                raise AttestorError("G13_ATTESTOR_OUTPUT_ATOMIC_PUBLISH_FAILED") from exc
            published.append(target)
    except AttestorError:
        for target in published:
            try:
                target.unlink()
            except OSError:
                pass
        raise
    except OSError as exc:
        for target in published:
            try:
                target.unlink()
            except OSError:
                pass
        raise AttestorError("G13_ATTESTOR_OUTPUT_WRITE_FAILED") from exc
    finally:
        for temp, _target in staged:
            try:
                temp.unlink()
            except OSError:
                pass


def _validate_paths(
    grant_path: str, key_path: str, output_path: str, receipt_path: str, repo: str,
) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise AttestorError("G13_ATTESTOR_REPOSITORY_NAME_INVALID")
    paths = {
        "grant": Path(grant_path).expanduser().resolve(strict=False),
        "key": Path(key_path).expanduser().resolve(strict=False),
        "output": Path(output_path).expanduser().resolve(strict=False),
        "receipt": Path(receipt_path).expanduser().resolve(strict=False),
    }
    vals = list(paths.items())
    for i, (name_a, path_a) in enumerate(vals):
        for name_b, path_b in vals[i + 1:]:
            if path_a == path_b:
                raise AttestorError(f"G13_ATTESTOR_PATH_COLLISION:{name_a.upper()}:{name_b.upper()}")
    if paths["output"].exists():
        raise AttestorError("G13_ATTESTOR_OUTPUT_ALREADY_EXISTS")


def run_attestor(
    *,
    repo: str,
    grant_path: str,
    private_key_path: str,
    output_path: str,
    receipt_path: str,
    token: str,
    grant_public_key: str,
    expected_attestor_public_key: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    _validate_paths(grant_path, private_key_path, output_path, receipt_path, repo)
    now_utc = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    grant_raw = Path(grant_path).read_bytes()
    grant_doc = parse_json_bytes(grant_raw)
    main_info = _api_json(repo, "commits/main", token)
    target_sha = main_info.get("sha")
    if not isinstance(target_sha, str) or not COMMIT_SHA.fullmatch(target_sha):
        raise AttestorError("G13_ATTESTOR_CURRENT_MAIN_SHA_INVALID")
    grant = _verify_grant(
        grant_doc, repo=repo, target_sha=target_sha, now=now_utc,
        public_key_encoded=grant_public_key,
    )
    key = load_attestor_private_key(
        private_key_path, os.environ.get("FOREXAI_G13_ATTESTOR_KEY_PASSPHRASE"),
    )
    verify_attestor_key(key, expected_attestor_public_key)
    grant_public = _load_raw_ed25519_public(
        grant_public_key, "G13_ATTESTOR_CAPITAL_FIREWALL_PUBLIC_KEY_INVALID",
    ).public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    attestor_public = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw,
    )
    if hmac.compare_digest(grant_public, attestor_public):
        raise AttestorError("G13_ATTESTOR_GRANT_AND_ATTESTOR_KEYS_MUST_BE_DISTINCT")

    ids = grant["run_ids"]
    runs: dict[str, Mapping[str, Any]] = {}
    artifacts: dict[str, Mapping[str, Any]] = {}
    docs: dict[str, Mapping[str, Any]] = {}
    digests: dict[str, str] = {}
    for role in REQUIRED_RUNS:
        run, artifact, documents, digest = _fetch_run_and_artifact(
            repo, role, ids[role], target_sha, token,
        )
        runs[role] = run
        artifacts[role] = artifact
        digests[role] = digest
        if role == "parity":
            docs["parity"] = documents[str(REQUIRED_RUNS[role]["document"])]
            docs["parity_package"] = documents[str(REQUIRED_RUNS[role]["package_document"])]
        else:
            docs[role] = documents[str(REQUIRED_RUNS[role]["document"])]
    payload, audit = _validate_evidence(
        repo=repo, target_sha=target_sha, grant=grant, runs=runs,
        artifacts=artifacts, docs=docs, digests=digests,
    )
    attestation = build_signed_attestation(
        payload, private_key=key, now=now_utc, grant_expiry=grant["_until"],
    )
    output = Path(output_path).expanduser().resolve(strict=False)
    receipt = Path(receipt_path).expanduser().resolve(strict=False)
    audit["attestation_sha256"] = hashlib.sha256(canonical_json(attestation)).hexdigest()
    audit["attestation_path"] = str(output)
    audit["receipt_path"] = str(receipt)
    _write_pair_new(output, attestation, receipt, audit)
    return audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="owner/repository")
    parser.add_argument("--grant", required=True, help="Signed one-signal Capital Firewall grant JSON")
    parser.add_argument("--attestor-private-key", required=True, help="External Ed25519 PKCS#8 PEM path")
    parser.add_argument("--output", required=True, help="New signed promotion source attestation path")
    parser.add_argument("--receipt-output", required=True, help="New artifact-digest and grant audit receipt path")
    args = parser.parse_args(argv)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    grant_public_key = os.environ.get("FOREXAI_CAPITAL_FIREWALL_GRANT_PUBLIC_KEY", "")
    attestor_public_key = os.environ.get("FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY", "")
    try:
        audit = run_attestor(
            repo=args.repo, grant_path=args.grant,
            private_key_path=args.attestor_private_key, output_path=args.output,
            receipt_path=args.receipt_output, token=token, grant_public_key=grant_public_key,
            expected_attestor_public_key=attestor_public_key,
        )
    except AttestorError as exc:
        print(json.dumps({
            "status": "BLOCKED", "reason": str(exc),
            "signed_attestation_created": False, "orders_submitted": False,
            "live_trading_allowed": False,
        }, sort_keys=True))
        return 2
    except Exception:
        # Never write exception text that might contain remote response data,
        # authorization headers, key paths, or source grant values into logs.
        print(json.dumps({
            "status": "BLOCKED", "reason": "G13_ATTESTOR_UNEXPECTED_FAILURE",
            "signed_attestation_created": False, "orders_submitted": False,
            "live_trading_allowed": False,
        }, sort_keys=True))
        return 2
    print(json.dumps({
        "status": "PASS", "attestor_key_id": ATTESTOR_KEY_ID,
        "grant_id": audit["grant_id"], "candidate_id": audit["candidate_id"],
        "signal_id": audit["signal_id"], "trade_id": audit["trade_id"],
        "evidence_bundle_sha256": audit["evidence_bundle_sha256"],
        "attestation_sha256": audit["attestation_sha256"],
        "receipt_path": audit["receipt_path"],
        "signed_attestation_created": True, "orders_submitted": False,
        "live_trading_allowed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
