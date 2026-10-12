"""Independent G13 evidence attestor for a separately signed one-signal Demo grant.

This service runs outside the MT5 execution host. It verifies the official
GitHub Actions readiness and exact upstream artifacts, verifies a short-lived
grant signed by a separate governance key, and emits the promotion-source
attestation consumed by the G13 Control Plane admission issuer. It never
changes the repository's default Demo/Live policy or submits broker orders.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import hmac
import io
import json
import math
import os
import re
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


ATTESTATION_SCHEMA = "forexai.control_plane_source_attestation.v1"
ATTESTOR_SOURCE_TYPE = "promotion"
ATTESTOR_KEY_ID = "forexai-g13-evidence-attestor-v1"
GRANT_SCHEMA = "forexai.g13.one_signal_demo_grant.v1"
GRANT_KEY_ID = "forexai-g13-demo-grant-authority-v1"
PROMOTION_MANIFEST_SCHEMA = "forexai.g13.promotion_manifest.m15.v1"
PROMOTION_PROVENANCE_SCHEMA = "forexai.g13.promotion_evidence_provenance.m15.v1"
PROMOTION_RUN_ATTESTATION_SCHEMA = "forexai.g13.promotion_run_attestation.m15.v1"
PREFLIGHT_SCHEMA = "forexai.g13.controlled_demo_package_preflight.m15.v1"
PARITY_SCHEMA = "forexai.g13.mql5_signal_parity.v2"
READINESS_SCHEMA = "forexai.g13.demo_readiness_gate_m15.v1"

MAX_GRANT_AGE_SECONDS = 300
MAX_GRANT_VALIDITY_SECONDS = 900
MAX_ATTESTATION_VALIDITY_SECONDS = 300
MAX_RISK_FRACTION = 0.006

ATTESTOR_PRIVATE_KEY_ENV = "FOREXAI_G13_PROMOTION_ATTESTOR_PRIVATE_KEY_PATH"
ATTESTOR_PUBLIC_KEY_ENV = "FOREXAI_PROVIDER_PROMOTION_PUBLIC_KEY"
GRANT_PUBLIC_KEY_ENV = "FOREXAI_G13_DEMO_GRANT_PUBLIC_KEY"
REPOSITORY_ENV = "FOREXAI_GITHUB_REPOSITORY"
TOKEN_ENV_NAMES = ("GH_TOKEN", "GITHUB_TOKEN", "FOREXAI_GITHUB_TOKEN")

WORKFLOWS = {
    "readiness": (
        "ForexAI G13 Demo Readiness Gate M15",
        ".github/workflows/forexai-g13-demo-readiness-gate-m15.yml",
    ),
    "promotion": (
        "ForexAI G13 Final Promotion M15",
        ".github/workflows/forexai-g13-promotion-m15.yml",
    ),
    "validation": (
        "ForexAI G13 Validation M15",
        ".github/workflows/forexai-g13-validation-m15.yml",
    ),
    "robustness": (
        "ForexAI G13 Robustness M15",
        ".github/workflows/forexai-g13-robustness-m15.yml",
    ),
    "oos": (
        "ForexAI G13 OOS M15 Current",
        ".github/workflows/forexai-g13-oos-m15-current.yml",
    ),
    "parity": (
        "ForexAI G13 MT5 Compile + Signal Parity",
        ".github/workflows/forexai-g13-mt5-compile-parity.yml",
    ),
    "preflight": (
        "ForexAI G13 Controlled Demo Package Preflight M15",
        ".github/workflows/forexai-g13-controlled-demo-package-preflight-m15.yml",
    ),
    "safety": (
        "ForexAI G13 Execution Safety Audit M15",
        ".github/workflows/forexai-g13-execution-safety-audit-m15.yml",
    ),
    "runtime": (
        "ForexAI G13 MT5 Runtime Safety Probe M15 v2",
        ".github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml",
    ),
    "static_validation": (
        "ForexAI G13 Workflow Static Validation",
        ".github/workflows/forexai-g13-workflow-lint.yml",
    ),
}
WORKFLOW_IDS = {
    "validation": 355468598,
    "robustness": 355473409,
    "oos": 356162316,
}
SOURCE_ARTIFACT_NAMES = {
    "validation": "g13-validation-m15",
    "robustness": "g13-robustness-m15",
    "oos": "g13-oos-m15-2026-current",
}
SOURCE_JOB_NAMES = {
    "validation": "g13-validation",
    "robustness": "g13-robustness",
    "oos": "G13 2026 OOS M15 Current",
}
PROMOTION_ARTIFACT = "g13-promotion-manifest-m15"
PREFLIGHT_ARTIFACT = "g13-controlled-demo-package-preflight-m15"
SAFETY_ARTIFACT = "g13-execution-safety-audit-m15"
RUNTIME_ARTIFACT = "g13-mt5-runtime-safety-probe-m15-v2"
READINESS_ARTIFACT = "g13-demo-readiness-gate-m15"

SAFE_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

GRANT_FIELDS = {
    "schema", "key_id", "grant_id", "repository", "commit_sha",
    "readiness_run_id", "promotion_run_id", "preflight_run_id", "parity_run_id",
    "candidate_id", "scope", "issued_at_utc", "valid_until_utc",
    "demo_trading_allowed", "live_trading_allowed", "max_authorized_risk_fraction",
    "signature",
}
GRANT_SIGNATURE_FIELDS = {"algorithm", "key_id", "signature"}


class PromotionAttestorError(RuntimeError):
    """Current G13 evidence or the independent one-signal grant did not validate."""


def canonical_json(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            dict(value), ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_CANONICAL_JSON_INVALID") from exc


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PromotionAttestorError("PROMOTION_ATTESTOR_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def load_json_bytes(raw: bytes, code: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    except PromotionAttestorError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PromotionAttestorError(code) from exc
    if not isinstance(value, dict):
        raise PromotionAttestorError(code)
    return value


def load_json_file(path: str | Path) -> dict[str, Any]:
    try:
        return load_json_bytes(Path(path).read_bytes(), "PROMOTION_ATTESTOR_JSON_FILE_INVALID")
    except PromotionAttestorError:
        raise
    except OSError as exc:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_JSON_FILE_UNAVAILABLE") from exc


def _parse_utc(value: Any, code: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise PromotionAttestorError(code)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PromotionAttestorError(code) from exc
    if parsed.tzinfo is None:
        raise PromotionAttestorError(code)
    return parsed.astimezone(timezone.utc)


def _safe_id(value: Any, code: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise PromotionAttestorError(code)
    return value


def _run_id(value: Any, code: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise PromotionAttestorError(code)
    return value


def _positive_fraction(value: Any, code: str, maximum: float) -> float:
    if isinstance(value, bool):
        raise PromotionAttestorError(code)
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise PromotionAttestorError(code) from exc
    if not math.isfinite(result) or result <= 0 or result > maximum:
        raise PromotionAttestorError(code)
    return result


def _decode_public_key(encoded: str, code: str) -> Ed25519PublicKey:
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError, TypeError) as exc:
        raise PromotionAttestorError(code) from exc
    if len(raw) != 32:
        raise PromotionAttestorError(code)
    try:
        return Ed25519PublicKey.from_public_bytes(raw)
    except ValueError as exc:
        raise PromotionAttestorError(code) from exc


def _verify_grant(
    grant: Mapping[str, Any],
    *,
    public_key: str,
    repository: str,
    main_sha: str,
    readiness_run_id: int,
    promotion_run_id: int,
    preflight_run_id: int,
    parity_run_id: int,
    promoted_candidate_ids: list[int],
    now: datetime,
) -> dict[str, Any]:
    if not isinstance(grant, Mapping) or set(grant) != GRANT_FIELDS:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_FIELDS_INVALID")
    if grant["schema"] != GRANT_SCHEMA or grant["key_id"] != GRANT_KEY_ID:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_SCHEMA_OR_KEY_ID_INVALID")
    signature = grant["signature"]
    if not isinstance(signature, Mapping) or set(signature) != GRANT_SIGNATURE_FIELDS:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_SIGNATURE_FIELDS_INVALID")
    if signature["algorithm"] != "Ed25519" or signature["key_id"] != GRANT_KEY_ID:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_SIGNATURE_METADATA_INVALID")
    encoded_signature = signature["signature"]
    if not isinstance(encoded_signature, str):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_SIGNATURE_INVALID")
    try:
        raw_signature = base64.b64decode(encoded_signature, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_SIGNATURE_INVALID") from exc
    if len(raw_signature) != 64:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_SIGNATURE_INVALID")
    unsigned = {key: value for key, value in grant.items() if key != "signature"}
    try:
        _decode_public_key(public_key, "PROMOTION_ATTESTOR_GRANT_PUBLIC_KEY_INVALID").verify(
            raw_signature, canonical_json(unsigned)
        )
    except InvalidSignature as exc:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_SIGNATURE_INVALID") from exc

    _safe_id(grant["grant_id"], "PROMOTION_ATTESTOR_GRANT_ID_INVALID")
    if grant["repository"] != repository:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_REPOSITORY_MISMATCH")
    if grant["commit_sha"] != main_sha or not COMMIT_SHA.fullmatch(str(grant["commit_sha"])):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_COMMIT_MISMATCH")
    expected_runs = {
        "readiness_run_id": readiness_run_id,
        "promotion_run_id": promotion_run_id,
        "preflight_run_id": preflight_run_id,
        "parity_run_id": parity_run_id,
    }
    for key, expected in expected_runs.items():
        if _run_id(grant[key], f"PROMOTION_ATTESTOR_GRANT_{key.upper()}_INVALID") != expected:
            raise PromotionAttestorError(f"PROMOTION_ATTESTOR_GRANT_{key.upper()}_MISMATCH")
    candidate_id = _run_id(grant["candidate_id"], "PROMOTION_ATTESTOR_GRANT_CANDIDATE_ID_INVALID")
    if candidate_id not in promoted_candidate_ids:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_CANDIDATE_NOT_PROMOTED")
    if grant["scope"] != "ONE_SIGNAL_DEMO_ONLY":
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_SCOPE_INVALID")
    if grant["demo_trading_allowed"] is not True:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_DOES_NOT_ALLOW_DEMO")
    if grant["live_trading_allowed"] is not False:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_MUST_KEEP_LIVE_DISABLED")
    max_risk = _positive_fraction(
        grant["max_authorized_risk_fraction"],
        "PROMOTION_ATTESTOR_GRANT_RISK_CAP_INVALID",
        MAX_RISK_FRACTION,
    )
    issued = _parse_utc(grant["issued_at_utc"], "PROMOTION_ATTESTOR_GRANT_ISSUED_AT_INVALID")
    expires = _parse_utc(grant["valid_until_utc"], "PROMOTION_ATTESTOR_GRANT_EXPIRY_INVALID")
    if issued > now + timedelta(seconds=2):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_ISSUED_IN_FUTURE")
    if now - issued > timedelta(seconds=MAX_GRANT_AGE_SECONDS):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_STALE")
    if expires <= now or expires <= issued:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_EXPIRED")
    if expires - issued > timedelta(seconds=MAX_GRANT_VALIDITY_SECONDS):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_VALIDITY_TOO_LONG")
    return {**dict(grant), "_parsed": {"expires": expires, "max_risk": max_risk}}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Do not forward a GitHub API bearer token to a signed artifact host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: N802
        return None


class GitHubEvidenceClient:
    """Minimal read-only GitHub Actions API client with byte-verified artifacts."""

    def __init__(self, repository: str, token: str, *, timeout_seconds: int = 30):
        if not isinstance(repository, str) or not REPOSITORY.fullmatch(repository):
            raise PromotionAttestorError("PROMOTION_ATTESTOR_REPOSITORY_INVALID")
        if not isinstance(token, str) or not token.strip():
            raise PromotionAttestorError("PROMOTION_ATTESTOR_GITHUB_TOKEN_NOT_CONFIGURED")
        self.repository = repository
        self.token = token.strip()
        self.timeout_seconds = timeout_seconds
        self._api_opener = urllib.request.build_opener(_NoRedirect())

    def _api_url(self, path: str) -> str:
        # All call sites use fixed GitHub REST path templates and numeric run/artifact IDs.
        return f"https://api.github.com/repos/{self.repository}/{path.lstrip('/')}"

    def get_json(self, path: str) -> dict[str, Any]:
        request = urllib.request.Request(
            self._api_url(path),
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "ForexAI-G13-Promotion-Attestor/1",
            },
        )
        try:
            with self._api_opener.open(request, timeout=self.timeout_seconds) as response:
                raw = response.read(20 * 1024 * 1024 + 1)
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            raise PromotionAttestorError("PROMOTION_ATTESTOR_GITHUB_API_REQUEST_FAILED") from exc
        if len(raw) > 20 * 1024 * 1024:
            raise PromotionAttestorError("PROMOTION_ATTESTOR_GITHUB_API_RESPONSE_TOO_LARGE")
        return load_json_bytes(raw, "PROMOTION_ATTESTOR_GITHUB_API_JSON_INVALID")

    def current_main_sha(self) -> str:
        payload = self.get_json("git/ref/heads/main")
        sha = payload.get("object", {}).get("sha")
        if not isinstance(sha, str) or not COMMIT_SHA.fullmatch(sha):
            raise PromotionAttestorError("PROMOTION_ATTESTOR_MAIN_SHA_INVALID")
        return sha

    def get_run(self, run_id: int) -> dict[str, Any]:
        return self.get_json(f"actions/runs/{_run_id(run_id, 'PROMOTION_ATTESTOR_RUN_ID_INVALID')}")

    @staticmethod
    def validate_run(
        run: Mapping[str, Any],
        *,
        run_id: int,
        name: str,
        path: str,
        expected_sha: str | None,
    ) -> None:
        if run.get("id") != run_id:
            raise PromotionAttestorError("PROMOTION_ATTESTOR_RUN_ID_MISMATCH")
        if run.get("name") != name or run.get("path") != path:
            raise PromotionAttestorError("PROMOTION_ATTESTOR_WORKFLOW_IDENTITY_MISMATCH")
        if run.get("head_branch") != "main":
            raise PromotionAttestorError("PROMOTION_ATTESTOR_RUN_NOT_ON_MAIN")
        if run.get("status") != "completed" or run.get("conclusion") != "success":
            raise PromotionAttestorError("PROMOTION_ATTESTOR_RUN_NOT_SUCCESSFUL")
        if expected_sha is not None and run.get("head_sha") != expected_sha:
            raise PromotionAttestorError("PROMOTION_ATTESTOR_RUN_HEAD_SHA_MISMATCH")

    def latest_success_exact_sha(self, kind: str, expected_sha: str) -> dict[str, Any]:
        if kind not in WORKFLOWS:
            raise PromotionAttestorError("PROMOTION_ATTESTOR_UNKNOWN_WORKFLOW")
        name, path = WORKFLOWS[kind]
        payload = self.get_json(
            f"actions/workflows/{Path(path).name}/runs?branch=main&status=completed&per_page=100"
        )
        runs = payload.get("workflow_runs")
        if not isinstance(runs, list):
            raise PromotionAttestorError("PROMOTION_ATTESTOR_WORKFLOW_RUN_LIST_INVALID")
        matches = [
            item for item in runs
            if isinstance(item, Mapping)
            and item.get("name") == name
            and item.get("path") == path
            and item.get("head_branch") == "main"
            and item.get("head_sha") == expected_sha
            and item.get("status") == "completed"
            and item.get("conclusion") == "success"
        ]
        if not matches:
            raise PromotionAttestorError(f"PROMOTION_ATTESTOR_NO_SUCCESSFUL_EXACT_SHA_RUN:{kind.upper()}")
        selected = max(matches, key=lambda row: int(row.get("id", 0)))
        return dict(selected)

    def _artifact_metadata(
        self,
        run_id: int,
        name: str,
        *,
        expected_id: int | None = None,
        expected_digest: str | None = None,
    ) -> dict[str, Any]:
        payload = self.get_json(f"actions/runs/{run_id}/artifacts?per_page=100")
        artifacts = payload.get("artifacts")
        if not isinstance(artifacts, list):
            raise PromotionAttestorError("PROMOTION_ATTESTOR_ARTIFACT_LIST_INVALID")
        matches = [
            item for item in artifacts
            if isinstance(item, Mapping) and item.get("name") == name and item.get("expired") is False
        ]
        if len(matches) != 1:
            raise PromotionAttestorError("PROMOTION_ATTESTOR_ARTIFACT_NOT_UNIQUE")
        item = dict(matches[0])
        digest = item.get("digest")
        if not isinstance(digest, str) or not digest.startswith("sha256:") or not SHA256.fullmatch(digest[7:]):
            raise PromotionAttestorError("PROMOTION_ATTESTOR_ARTIFACT_DIGEST_INVALID")
        if expected_id is not None and item.get("id") != expected_id:
            raise PromotionAttestorError("PROMOTION_ATTESTOR_ARTIFACT_ID_MISMATCH")
        if expected_digest is not None and digest != expected_digest:
            raise PromotionAttestorError("PROMOTION_ATTESTOR_ARTIFACT_DIGEST_MISMATCH")
        return item

    def _download_zip_to_temp(self, artifact_id: int) -> tuple[str, str]:
        api_request = urllib.request.Request(
            self._api_url(f"actions/artifacts/{artifact_id}/zip"),
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "ForexAI-G13-Promotion-Attestor/1",
            },
        )
        try:
            try:
                response = self._api_opener.open(api_request, timeout=self.timeout_seconds)
                response.close()
                raise PromotionAttestorError("PROMOTION_ATTESTOR_ARTIFACT_ENDPOINT_DID_NOT_REDIRECT")
            except urllib.error.HTTPError as redirect:
                if redirect.code not in (301, 302, 303, 307, 308):
                    redirect.close()
                    raise PromotionAttestorError("PROMOTION_ATTESTOR_ARTIFACT_DOWNLOAD_FAILED")
                location = redirect.headers.get("Location")
                redirect.close()
            if not isinstance(location, str) or not location:
                raise PromotionAttestorError("PROMOTION_ATTESTOR_ARTIFACT_REDIRECT_MISSING")
            parsed = urllib.parse.urlparse(location)
            if parsed.scheme != "https" or not parsed.netloc:
                raise PromotionAttestorError("PROMOTION_ATTESTOR_ARTIFACT_REDIRECT_INVALID")
            # Intentionally no GitHub Authorization header on the signed artifact-host request.
            final_request = urllib.request.Request(location, headers={"User-Agent": "ForexAI-G13-Promotion-Attestor/1"})
            digest = hashlib.sha256()
            with urllib.request.urlopen(final_request, timeout=self.timeout_seconds) as response:
                with tempfile.NamedTemporaryFile(prefix="forexai-g13-artifact-", suffix=".zip", delete=False) as handle:
                    temp_path = handle.name
                    for chunk in iter(lambda: response.read(1024 * 1024), b""):
                        digest.update(chunk)
                        handle.write(chunk)
                    handle.flush()
                    os.fsync(handle.fileno())
            return temp_path, "sha256:" + digest.hexdigest()
        except PromotionAttestorError:
            raise
        except (OSError, urllib.error.URLError, urllib.error.HTTPError) as exc:
            raise PromotionAttestorError("PROMOTION_ATTESTOR_ARTIFACT_DOWNLOAD_FAILED") from exc

    def read_artifact_files(
        self,
        run_id: int,
        artifact_name: str,
        basenames: set[str],
        *,
        expected_id: int | None = None,
        expected_digest: str | None = None,
    ) -> tuple[dict[str, bytes], dict[str, Any]]:
        metadata = self._artifact_metadata(
            run_id, artifact_name, expected_id=expected_id, expected_digest=expected_digest
        )
        temp_path = None
        try:
            temp_path, actual_digest = self._download_zip_to_temp(int(metadata["id"]))
            if actual_digest != metadata["digest"]:
                raise PromotionAttestorError("PROMOTION_ATTESTOR_ARTIFACT_BYTES_DIGEST_MISMATCH")
            found: dict[str, bytes] = {}
            with zipfile.ZipFile(temp_path, "r") as archive:
                for member in archive.namelist():
                    basename = Path(member).name
                    if basename not in basenames:
                        continue
                    if basename in found:
                        raise PromotionAttestorError("PROMOTION_ATTESTOR_DUPLICATE_ARTIFACT_MEMBER")
                    found[basename] = archive.read(member)
            missing = basenames - set(found)
            if missing:
                raise PromotionAttestorError("PROMOTION_ATTESTOR_ARTIFACT_REQUIRED_FILE_MISSING")
            return found, metadata
        except PromotionAttestorError:
            raise
        except (OSError, ValueError, zipfile.BadZipFile, KeyError) as exc:
            raise PromotionAttestorError("PROMOTION_ATTESTOR_ARTIFACT_ZIP_INVALID") from exc
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass

    def verify_artifact_zip(
        self,
        run_id: int,
        artifact_name: str,
        *,
        expected_id: int,
        expected_digest: str,
    ) -> dict[str, Any]:
        metadata = self._artifact_metadata(
            run_id, artifact_name, expected_id=expected_id, expected_digest=expected_digest
        )
        temp_path = None
        try:
            temp_path, actual_digest = self._download_zip_to_temp(expected_id)
            if actual_digest != metadata["digest"]:
                raise PromotionAttestorError("PROMOTION_ATTESTOR_SOURCE_ARTIFACT_BYTES_DIGEST_MISMATCH")
            return metadata
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass


def _decode_run_artifact_json(files: Mapping[str, bytes], name: str) -> dict[str, Any]:
    if name not in files:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_REQUIRED_JSON_NOT_FOUND")
    return load_json_bytes(files[name], "PROMOTION_ATTESTOR_REQUIRED_JSON_INVALID")


def _kv_bytes(raw: bytes) -> dict[str, str]:
    try:
        content = raw.decode("utf-8")
    except UnicodeError as exc:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_RUNTIME_EVIDENCE_INVALID") from exc
    rows: dict[str, str] = {}
    for line in content.splitlines():
        if not line.strip() or "," not in line:
            continue
        key, value = line.strip().split(",", 1)
        rows[key] = value
    return rows


def _validate_source_provenance(
    client: GitHubEvidenceClient,
    provenance: Mapping[str, Any],
    *,
    repository: str,
    main_sha: str,
) -> dict[str, int]:
    if provenance.get("schema_version") != PROMOTION_PROVENANCE_SCHEMA:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PROVENANCE_SCHEMA_INVALID")
    if provenance.get("target_sha") != main_sha:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PROVENANCE_COMMIT_MISMATCH")
    sources = provenance.get("sources")
    if not isinstance(sources, Mapping) or set(sources) != {"validation", "robustness", "oos"}:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PROVENANCE_SOURCES_INVALID")
    source_run_ids: dict[str, int] = {}
    for kind in ("validation", "robustness", "oos"):
        row = sources[kind]
        if not isinstance(row, Mapping):
            raise PromotionAttestorError("PROMOTION_ATTESTOR_PROVENANCE_ROW_INVALID")
        run_id = _run_id(row.get("run_id"), f"PROMOTION_ATTESTOR_{kind.upper()}_RUN_ID_INVALID")
        source_run_ids[kind] = run_id
        expected_name, expected_path = WORKFLOWS[kind]
        run = client.get_run(run_id)
        client.validate_run(run, run_id=run_id, name=expected_name, path=expected_path, expected_sha=main_sha)
        if row.get("workflow_name") != expected_name or row.get("workflow_id") != WORKFLOW_IDS[kind]:
            raise PromotionAttestorError(f"PROMOTION_ATTESTOR_{kind.upper()}_WORKFLOW_BINDING_INVALID")
        if row.get("head_branch") != "main" or row.get("head_sha") != main_sha:
            raise PromotionAttestorError(f"PROMOTION_ATTESTOR_{kind.upper()}_SHA_BINDING_INVALID")
        if row.get("conclusion") != "success" or row.get("job_name") != SOURCE_JOB_NAMES[kind]:
            raise PromotionAttestorError(f"PROMOTION_ATTESTOR_{kind.upper()}_JOB_BINDING_INVALID")
        if isinstance(row.get("job_id"), bool) or not isinstance(row.get("job_id"), int) or row["job_id"] <= 0:
            raise PromotionAttestorError(f"PROMOTION_ATTESTOR_{kind.upper()}_JOB_ID_INVALID")
        artifact = row.get("artifact")
        if not isinstance(artifact, Mapping):
            raise PromotionAttestorError(f"PROMOTION_ATTESTOR_{kind.upper()}_ARTIFACT_BINDING_INVALID")
        expected_digest = artifact.get("digest")
        if artifact.get("name") != SOURCE_ARTIFACT_NAMES[kind] or artifact.get("expired") is not False:
            raise PromotionAttestorError(f"PROMOTION_ATTESTOR_{kind.upper()}_ARTIFACT_BINDING_INVALID")
        local_zip_sha = row.get("local_zip_sha256")
        if not isinstance(expected_digest, str) or not expected_digest.startswith("sha256:"):
            raise PromotionAttestorError(f"PROMOTION_ATTESTOR_{kind.upper()}_ARTIFACT_DIGEST_INVALID")
        if local_zip_sha != expected_digest.split(":", 1)[1]:
            raise PromotionAttestorError(f"PROMOTION_ATTESTOR_{kind.upper()}_LOCAL_ARTIFACT_DIGEST_MISMATCH")
        client.verify_artifact_zip(
            run_id,
            SOURCE_ARTIFACT_NAMES[kind],
            expected_id=_run_id(artifact.get("artifact_id"), f"PROMOTION_ATTESTOR_{kind.upper()}_ARTIFACT_ID_INVALID"),
            expected_digest=expected_digest,
        )
    return source_run_ids


def collect_verified_evidence(
    client: GitHubEvidenceClient,
    *,
    readiness_run_id: int,
) -> dict[str, Any]:
    """Fetch and byte-verify the current authoritative G13 Actions evidence chain."""
    main_sha = client.current_main_sha()
    readiness_run_id = _run_id(readiness_run_id, "PROMOTION_ATTESTOR_READINESS_RUN_ID_INVALID")
    readiness_name, readiness_path = WORKFLOWS["readiness"]
    readiness_run = client.get_run(readiness_run_id)
    client.validate_run(
        readiness_run,
        run_id=readiness_run_id,
        name=readiness_name,
        path=readiness_path,
        expected_sha=main_sha,
    )
    readiness_files, _ = client.read_artifact_files(
        readiness_run_id,
        READINESS_ARTIFACT,
        {"g13-demo-readiness-gate-m15.json"},
    )
    readiness = _decode_run_artifact_json(readiness_files, "g13-demo-readiness-gate-m15.json")
    if readiness.get("schema") != READINESS_SCHEMA or readiness.get("status") != "READY_FOR_CONTROLLED_DEMO_AUDIT":
        raise PromotionAttestorError("PROMOTION_ATTESTOR_READINESS_NOT_READY")
    if readiness.get("live_remains_disabled") is not True:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_READINESS_LIVE_POLICY_INVALID")
    current_code = readiness.get("current_code")
    if not isinstance(current_code, Mapping) or any(current_code.get(key) is not True for key in (
        "runtime_contract_files_unchanged_since_runtime",
        "safety_contract_files_unchanged_since_safety",
        "parity_contract_files_unchanged_since_parity",
    )):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_READINESS_CURRENT_CODE_INVALID")
    promotion_summary = readiness.get("promotion")
    preflight_summary = readiness.get("preflight")
    safety_summary = readiness.get("safety")
    runtime_summary = readiness.get("runtime")
    evidence_summary = readiness.get("evidence")
    if not all(isinstance(obj, Mapping) for obj in (
        promotion_summary, preflight_summary, safety_summary, runtime_summary, evidence_summary
    )):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_READINESS_SUMMARY_INVALID")
    # The standard G13 source policy remains false. Only the separately signed grant below can
    # introduce a narrowly scoped one-signal Demo authority; the manifest is never rewritten.
    if promotion_summary.get("status") != "PROMOTION_READY":
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PROMOTION_STATUS_INVALID")
    if promotion_summary.get("demo_trading_allowed") is not False or promotion_summary.get("live_trading_allowed") is not False:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_SOURCE_DEFAULT_PERMISSION_INVALID")
    if preflight_summary.get("status") != "PASS" or preflight_summary.get("head_sha") != main_sha:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PREFLIGHT_STATUS_OR_SHA_INVALID")
    if safety_summary.get("status") != "PASS" or safety_summary.get("matrix_cases") != 1536:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_SAFETY_STATUS_INVALID")
    if safety_summary.get("matrix_allowed_states") != 769 or safety_summary.get("non_tester_allowed_states") != 1:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_SAFETY_MATRIX_INVALID")
    if safety_summary.get("live_trading_allowed") is not False:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_SAFETY_LIVE_POLICY_INVALID")
    if runtime_summary.get("demo_account") is not True or runtime_summary.get("real_account_detected") is not False:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_RUNTIME_ACCOUNT_INVALID")
    if runtime_summary.get("authorization_off_blocks") is not True or runtime_summary.get("orders_submitted") is not False:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_RUNTIME_AUTHORIZATION_INVALID")
    if evidence_summary.get("parity_status") != "PASS":
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PARITY_NOT_PASS")
    parity_run_id = _run_id(preflight_summary.get("parity_run_id"), "PROMOTION_ATTESTOR_PARITY_RUN_ID_INVALID")
    promotion_run_id = _run_id(promotion_summary.get("run_id"), "PROMOTION_ATTESTOR_PROMOTION_RUN_ID_INVALID")
    preflight_run_id = _run_id(preflight_summary.get("run_id"), "PROMOTION_ATTESTOR_PREFLIGHT_RUN_ID_INVALID")
    for summary, key in ((promotion_summary, "head_sha"), (preflight_summary, "head_sha")):
        if summary.get(key) != main_sha:
            raise PromotionAttestorError("PROMOTION_ATTESTOR_CURRENT_SHA_MISMATCH")

    # Require current successful runs for all other G13 sub-gates on this exact SHA.
    safety_run = client.latest_success_exact_sha("safety", main_sha)
    static_run = client.latest_success_exact_sha("static_validation", main_sha)
    runtime_sha = runtime_summary.get("runtime_head_sha")
    if not isinstance(runtime_sha, str) or not COMMIT_SHA.fullmatch(runtime_sha):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_RUNTIME_SHA_INVALID")
    runtime_run = client.latest_success_exact_sha("runtime", runtime_sha)
    safety_run_id = _run_id(safety_run.get("id"), "PROMOTION_ATTESTOR_SAFETY_RUN_ID_INVALID")
    if static_run.get("head_sha") != main_sha:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_STATIC_VALIDATION_SHA_MISMATCH")

    promotion_name, promotion_path = WORKFLOWS["promotion"]
    promotion_run = client.get_run(promotion_run_id)
    client.validate_run(promotion_run, run_id=promotion_run_id, name=promotion_name, path=promotion_path, expected_sha=main_sha)
    preflight_name, preflight_path = WORKFLOWS["preflight"]
    preflight_run = client.get_run(preflight_run_id)
    client.validate_run(preflight_run, run_id=preflight_run_id, name=preflight_name, path=preflight_path, expected_sha=main_sha)
    parity_name, parity_path = WORKFLOWS["parity"]
    parity_run = client.get_run(parity_run_id)
    client.validate_run(parity_run, run_id=parity_run_id, name=parity_name, path=parity_path, expected_sha=main_sha)
    if runtime_run.get("head_sha") != runtime_sha:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_RUNTIME_RUN_SHA_MISMATCH")

    promotion_files, _promotion_artifact = client.read_artifact_files(
        promotion_run_id,
        PROMOTION_ARTIFACT,
        {"g13-promotion-manifest-m15.json", "source-provenance.json", "promotion-run-attestation.json"},
    )
    promotion_raw = promotion_files["g13-promotion-manifest-m15.json"]
    provenance_raw = promotion_files["source-provenance.json"]
    promotion_attestation_raw = promotion_files["promotion-run-attestation.json"]
    promotion = _decode_run_artifact_json(promotion_files, "g13-promotion-manifest-m15.json")
    provenance = _decode_run_artifact_json(promotion_files, "source-provenance.json")
    promotion_attestation = _decode_run_artifact_json(promotion_files, "promotion-run-attestation.json")
    if promotion.get("schema_version") != PROMOTION_MANIFEST_SCHEMA or promotion.get("status") != "PROMOTION_READY":
        raise PromotionAttestorError("PROMOTION_ATTESTOR_MANIFEST_STATUS_INVALID")
    policy = promotion.get("decision_policy")
    if not isinstance(policy, Mapping) or policy.get("demo_trading_allowed") is not False or policy.get("live_trading_allowed") is not False:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_MANIFEST_DEFAULT_PERMISSION_INVALID")
    if promotion.get("symbol") != "EURUSD" or promotion.get("timeframe") != "M15":
        raise PromotionAttestorError("PROMOTION_ATTESTOR_MANIFEST_MARKET_SCOPE_INVALID")
    if promotion.get("evidence_provenance_sha256") != hashlib.sha256(canonical_json(provenance)).hexdigest():
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PROVENANCE_HASH_MISMATCH")
    if promotion_attestation.get("schema_version") != PROMOTION_RUN_ATTESTATION_SCHEMA:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PROMOTION_RUN_ATTESTATION_INVALID")
    if promotion_attestation.get("workflow_run_id") != promotion_run_id:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PROMOTION_RUN_ATTESTATION_ID_MISMATCH")
    if promotion_attestation.get("head_sha") != main_sha:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PROMOTION_RUN_ATTESTATION_SHA_MISMATCH")
    if promotion_attestation.get("manifest_sha256") != sha256_bytes(promotion_raw):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PROMOTION_MANIFEST_HASH_MISMATCH")
    if promotion_attestation.get("provenance_sha256") != sha256_bytes(provenance_raw):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PROMOTION_PROVENANCE_HASH_MISMATCH")
    source_run_ids = _validate_source_provenance(
        client, provenance, repository=client.repository, main_sha=main_sha
    )

    preflight_files, _preflight_artifact = client.read_artifact_files(
        preflight_run_id,
        PREFLIGHT_ARTIFACT,
        {"g13-demo-package-preflight-m15.json"},
    )
    preflight_raw = preflight_files["g13-demo-package-preflight-m15.json"]
    preflight = _decode_run_artifact_json(preflight_files, "g13-demo-package-preflight-m15.json")
    if preflight.get("schema_version") != PREFLIGHT_SCHEMA or preflight.get("status") != "PASS":
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PACKAGE_PREFLIGHT_NOT_PASS")
    if preflight.get("demo_trading_allowed_by_source") is not False or preflight.get("live_trading_allowed") is not False:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PREFLIGHT_DEFAULT_PERMISSION_INVALID")
    if preflight.get("real_data_only") is not True or preflight.get("synthetic_data") is not False:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PREFLIGHT_DATA_POLICY_INVALID")
    if preflight.get("promotion_manifest_sha256") != sha256_bytes(promotion_raw):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PREFLIGHT_MANIFEST_HASH_MISMATCH")
    if preflight.get("compile_parity_run_id") != parity_run_id or preflight.get("compile_parity_head_sha") != main_sha:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PREFLIGHT_PARITY_BINDING_INVALID")

    parity_artifact_name = f"g13-mt5-compile-parity-{parity_run_id}"
    parity_files, _parity_artifact = client.read_artifact_files(
        parity_run_id, parity_artifact_name, {"g13-mql5-signal-parity.json"}
    )
    parity = _decode_run_artifact_json(parity_files, "g13-mql5-signal-parity.json")
    if parity.get("schema_version") != PARITY_SCHEMA or parity.get("status") != "PASS":
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PARITY_ARTIFACT_NOT_PASS")
    if parity.get("real_data_only") is not True or parity.get("synthetic_data") is not False:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PARITY_DATA_POLICY_INVALID")
    if parity.get("data_provenance", {}).get("quality_status") != "PASS":
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PARITY_DATA_QUALITY_INVALID")
    if not any(source in str(parity.get("data_provenance", {}).get("source", "")) for source in ("HistData.com", "Dukascopy")):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PARITY_DATA_SOURCE_INVALID")
    promoted_ids = promotion.get("promoted_candidate_ids")
    candidates = promotion.get("candidates")
    if not isinstance(promoted_ids, list) or not promoted_ids or not isinstance(candidates, list):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PROMOTED_CANDIDATES_INVALID")
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in promoted_ids):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PROMOTED_CANDIDATE_IDS_INVALID")
    if len(promoted_ids) != len(set(promoted_ids)):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PROMOTED_CANDIDATE_IDS_DUPLICATE")
    if len(candidates) != len(promoted_ids) or promotion.get("counts", {}).get("promoted") != len(promoted_ids):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PROMOTED_CANDIDATE_COUNT_INVALID")
    candidate_config_hashes: dict[str, str] = {}
    for row in candidates:
        if not isinstance(row, Mapping):
            raise PromotionAttestorError("PROMOTION_ATTESTOR_CANDIDATE_ROW_INVALID")
        candidate_id = _run_id(row.get("candidate_id"), "PROMOTION_ATTESTOR_CANDIDATE_ID_INVALID")
        config_hash = row.get("config_hash")
        if not isinstance(config_hash, str) or not SHA256.fullmatch(config_hash):
            raise PromotionAttestorError("PROMOTION_ATTESTOR_CANDIDATE_CONFIG_HASH_INVALID")
        if str(candidate_id) in candidate_config_hashes:
            raise PromotionAttestorError("PROMOTION_ATTESTOR_CANDIDATE_ID_DUPLICATE")
        candidate_config_hashes[str(candidate_id)] = config_hash
    if set(candidate_config_hashes) != {str(value) for value in promoted_ids}:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_CANDIDATE_HASH_MAP_INCOMPLETE")
    if parity.get("candidate_count") != len(promoted_ids) or parity.get("passed_count") != len(promoted_ids):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PARITY_CANDIDATE_COUNT_INVALID")
    if not all(row.get("status") == "PASS" for row in parity.get("results", [])):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PARITY_CANDIDATE_FAILED")
    if preflight.get("candidate_ids") != promoted_ids:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PREFLIGHT_CANDIDATE_SET_MISMATCH")
    if preflight.get("candidate_config_hashes") != candidate_config_hashes:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PREFLIGHT_CONFIG_HASH_MAP_MISMATCH")
    if preflight.get("candidate_count") != len(promoted_ids):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PREFLIGHT_CANDIDATE_COUNT_MISMATCH")
    if preflight.get("data_sha256") != parity.get("data_sha256") or preflight.get("data_manifest_sha256") != parity.get("data_manifest_sha256"):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PREFLIGHT_DATA_HASH_MISMATCH")
    if preflight.get("data_provenance") != parity.get("data_provenance"):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PREFLIGHT_DATA_PROVENANCE_MISMATCH")

    safety_files, _safety_artifact = client.read_artifact_files(
        safety_run_id,
        SAFETY_ARTIFACT,
        {"g13-execution-safety-audit-m15.json"},
    )
    safety = _decode_run_artifact_json(safety_files, "g13-execution-safety-audit-m15.json")
    matrix = safety.get("matrix")
    if safety.get("status") != "PASS" or not isinstance(matrix, list) or len(matrix) != 1536:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_SAFETY_ARTIFACT_INVALID")
    if sum(1 for row in matrix if isinstance(row, Mapping) and row.get("actual_allowed") is True) != 769:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_SAFETY_ALLOWED_STATES_INVALID")
    if sum(1 for row in matrix if isinstance(row, Mapping) and row.get("is_tester") is False and row.get("actual_allowed") is True) != 1:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_SAFETY_NONTESTER_ALLOW_COUNT_INVALID")
    if safety.get("policy", {}).get("live_trading_allowed") is not False:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_SAFETY_LIVE_POLICY_INVALID")

    runtime_files, _runtime_artifact = client.read_artifact_files(
        int(runtime_run["id"]),
        RUNTIME_ARTIFACT,
        {"g13_safety_probe_auth_off.done.txt", "g13_safety_probe_auth_on.done.txt"},
    )
    runtime_off = _kv_bytes(runtime_files["g13_safety_probe_auth_off.done.txt"])
    runtime_on = _kv_bytes(runtime_files["g13_safety_probe_auth_on.done.txt"])
    if runtime_off.get("status") != "PASS" or runtime_on.get("status") != "PASS":
        raise PromotionAttestorError("PROMOTION_ATTESTOR_RUNTIME_PROBE_NOT_PASS")
    if runtime_off.get("authorization") != "false" or runtime_off.get("execution_allowed") != "false":
        raise PromotionAttestorError("PROMOTION_ATTESTOR_RUNTIME_AUTH_OFF_POLICY_INVALID")
    if runtime_off.get("orders_submitted") != "false" or runtime_on.get("orders_submitted") != "false":
        raise PromotionAttestorError("PROMOTION_ATTESTOR_RUNTIME_PROBE_ORDER_ASSERTION_FAILED")
    if runtime_on.get("authorization") != "true" or runtime_on.get("demo_account") != "true" or runtime_on.get("account_mode") != "0":
        raise PromotionAttestorError("PROMOTION_ATTESTOR_RUNTIME_AUTH_ON_POLICY_INVALID")
    if runtime_on.get("real_account_detected") != "false":
        raise PromotionAttestorError("PROMOTION_ATTESTOR_RUNTIME_REAL_ACCOUNT_DETECTED")

    # Check the explicit run ID/head bindings represented in the official readiness report.
    if preflight.get("compile_parity_run_id") != parity_run_id:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_PARITY_RUN_ID_MISMATCH")
    if readiness.get("evidence", {}).get("parity_head_sha") != main_sha:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_READINESS_PARITY_SHA_MISMATCH")
    if readiness.get("safety_head_sha") != main_sha:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_READINESS_SAFETY_SHA_MISMATCH")

    run_ids = {
        "promotion": promotion_run_id,
        "validation": source_run_ids["validation"],
        "robustness": source_run_ids["robustness"],
        "oos": source_run_ids["oos"],
        "parity": parity_run_id,
        "package_preflight": preflight_run_id,
        "safety_audit": safety_run_id,
        "readiness": readiness_run_id,
    }
    return {
        "repository": client.repository,
        "main_sha": main_sha,
        "readiness_run_id": readiness_run_id,
        "promotion_run_id": promotion_run_id,
        "preflight_run_id": preflight_run_id,
        "parity_run_id": parity_run_id,
        "run_ids": run_ids,
        "promoted_candidate_ids": promoted_ids,
        "candidate_config_hashes": candidate_config_hashes,
        "gates": {
            "validation": "PASS",
            "robustness": "PASS",
            "oos": "PASS",
            "parity": "PASS",
            "package_preflight": "PASS",
            "safety_audit": "PASS",
        },
        "readiness_status": readiness["status"],
        "real_data_only": True,
        "synthetic_data": False,
        "source_default_demo_trading_allowed": False,
    }


def build_promotion_attestation(
    evidence: Mapping[str, Any],
    grant: Mapping[str, Any],
    *,
    grant_public_key: str,
    attestor_private_key: Ed25519PrivateKey,
    attestor_expected_public_key: str,
    now_utc: str | datetime | None = None,
) -> dict[str, Any]:
    if not isinstance(attestor_private_key, Ed25519PrivateKey):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_SIGNING_KEY_INVALID")
    actual_public = attestor_private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    expected_public_obj = _decode_public_key(
        attestor_expected_public_key, "PROMOTION_ATTESTOR_EXPECTED_PUBLIC_KEY_INVALID"
    )
    expected_public = expected_public_obj.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    if not hmac.compare_digest(actual_public, expected_public):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_SIGNING_KEYPAIR_MISMATCH")
    grant_public_obj = _decode_public_key(grant_public_key, "PROMOTION_ATTESTOR_GRANT_PUBLIC_KEY_INVALID")
    grant_public_raw = grant_public_obj.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    if hmac.compare_digest(actual_public, grant_public_raw):
        raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_KEY_MUST_BE_DISTINCT")
    now = (
        now_utc.astimezone(timezone.utc) if isinstance(now_utc, datetime)
        else _parse_utc(now_utc, "PROMOTION_ATTESTOR_NOW_INVALID") if now_utc is not None
        else datetime.now(timezone.utc)
    )
    verified_grant = _verify_grant(
        grant,
        public_key=grant_public_key,
        repository=str(evidence["repository"]),
        main_sha=str(evidence["main_sha"]),
        readiness_run_id=int(evidence["readiness_run_id"]),
        promotion_run_id=int(evidence["promotion_run_id"]),
        preflight_run_id=int(evidence["preflight_run_id"]),
        parity_run_id=int(evidence["parity_run_id"]),
        promoted_candidate_ids=list(evidence["promoted_candidate_ids"]),
        now=now,
    )
    expires = min(
        now + timedelta(seconds=MAX_ATTESTATION_VALIDITY_SECONDS),
        verified_grant["_parsed"]["expires"],
    )
    if expires <= now:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_OUTPUT_ATTESTATION_EXPIRED")
    payload = {
        "schema": "forexai.g13.promotion_evidence.v1",
        "commit_sha": evidence["main_sha"],
        "gates": dict(evidence["gates"]),
        "readiness_status": evidence["readiness_status"],
        "demo_trading_allowed": True,
        "source_default_demo_trading_allowed": False,
        "demo_grant_id": verified_grant["grant_id"],
        "authorized_demo_candidate_id": verified_grant["candidate_id"],
        "demo_grant_max_risk_fraction": verified_grant["_parsed"]["max_risk"],
        "live_trading_allowed": False,
        "real_data_only": evidence["real_data_only"],
        "synthetic_data": evidence["synthetic_data"],
        "run_ids": dict(evidence["run_ids"]),
        "promoted_candidate_ids": list(evidence["promoted_candidate_ids"]),
        "candidate_config_hashes": dict(evidence["candidate_config_hashes"]),
    }
    attestation = {
        "schema": ATTESTATION_SCHEMA,
        "source_type": ATTESTOR_SOURCE_TYPE,
        "key_id": ATTESTOR_KEY_ID,
        "issued_at_utc": now.isoformat(),
        "valid_until_utc": expires.isoformat(),
        "payload": payload,
    }
    attestation["signature"] = {
        "algorithm": "Ed25519",
        "key_id": ATTESTOR_KEY_ID,
        "signature": base64.b64encode(attestor_private_key.sign(canonical_json(attestation))).decode("ascii"),
    }
    return attestation


def write_new_json(path: str | Path, value: Mapping[str, Any]) -> None:
    target = Path(path).expanduser().resolve(strict=False)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise PromotionAttestorError("PROMOTION_ATTESTOR_OUTPUT_ALREADY_EXISTS")
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=target.parent, prefix=f".{target.name}.", suffix=".tmp", delete=False
        ) as handle:
            temp_path = handle.name
            handle.write((json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.chmod(temp_path, 0o600)
        except OSError:
            pass
        try:
            os.link(temp_path, target)
        except FileExistsError as exc:
            raise PromotionAttestorError("PROMOTION_ATTESTOR_OUTPUT_ALREADY_EXISTS") from exc
        os.unlink(temp_path)
        temp_path = None
    except PromotionAttestorError:
        raise
    except OSError as exc:
        raise PromotionAttestorError("PROMOTION_ATTESTOR_OUTPUT_WRITE_FAILED") from exc
    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except OSError:
                pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness-run-id", type=int, required=True)
    parser.add_argument("--grant", required=True, help="Path to an externally signed one-signal Demo grant JSON")
    parser.add_argument("--output", required=True, help="New output path for the promotion source attestation")
    args = parser.parse_args(argv)
    try:
        repository = os.environ.get(REPOSITORY_ENV, "afshinsaberone-a11y/grok-ai-trader")
        token = next((os.environ.get(name, "") for name in TOKEN_ENV_NAMES if os.environ.get(name, "").strip()), "")
        client = GitHubEvidenceClient(repository, token)
        private_path = os.environ.get(ATTESTOR_PRIVATE_KEY_ENV, "")
        if not private_path.strip():
            raise PromotionAttestorError("PROMOTION_ATTESTOR_PRIVATE_KEY_PATH_NOT_CONFIGURED")
        attestor_public_key = os.environ.get(ATTESTOR_PUBLIC_KEY_ENV, "")
        if not attestor_public_key:
            raise PromotionAttestorError("PROMOTION_ATTESTOR_PUBLIC_KEY_NOT_CONFIGURED")
        grant_public_key = os.environ.get(GRANT_PUBLIC_KEY_ENV, "")
        if not grant_public_key:
            raise PromotionAttestorError("PROMOTION_ATTESTOR_GRANT_PUBLIC_KEY_NOT_CONFIGURED")
        grant = load_json_file(args.grant)
        # Avoid path collisions with the governance grant, signer key, and output.
        paths = [
            Path(args.grant).expanduser().resolve(strict=False),
            Path(private_path).expanduser().resolve(strict=False),
            Path(args.output).expanduser().resolve(strict=False),
        ]
        if len(paths) != len(set(paths)):
            raise PromotionAttestorError("PROMOTION_ATTESTOR_PATH_COLLISION")
        evidence = collect_verified_evidence(client, readiness_run_id=args.readiness_run_id)
        private_key_obj = serialization.load_pem_private_key(
            Path(private_path).read_bytes(),
            password=os.environ.get("FOREXAI_G13_PROMOTION_ATTESTOR_KEY_PASSPHRASE", "").encode("utf-8") or None,
        )
        if not isinstance(private_key_obj, Ed25519PrivateKey):
            raise PromotionAttestorError("PROMOTION_ATTESTOR_SIGNING_KEY_MUST_BE_ED25519")
        attestation = build_promotion_attestation(
            evidence,
            grant,
            grant_public_key=grant_public_key,
            attestor_private_key=private_key_obj,
            attestor_expected_public_key=attestor_public_key,
        )
        write_new_json(args.output, attestation)
    except PromotionAttestorError as exc:
        print(json.dumps({
            "status": "BLOCKED",
            "reason": str(exc),
            "attestation_created": False,
            "demo_trading_allowed": False,
            "live_trading_allowed": False,
            "orders_submitted": False,
        }, sort_keys=True))
        return 2
    except Exception:
        # Do not expose URLs, local paths, tokens, artifact contents, or key data in service logs.
        print(json.dumps({
            "status": "BLOCKED",
            "reason": "PROMOTION_ATTESTOR_UNEXPECTED_FAILURE",
            "attestation_created": False,
            "demo_trading_allowed": False,
            "live_trading_allowed": False,
            "orders_submitted": False,
        }, sort_keys=True))
        return 2
    print(json.dumps({
        "status": "PASS",
        "attestation_created": True,
        "source_type": ATTESTOR_SOURCE_TYPE,
        "key_id": ATTESTOR_KEY_ID,
        "commit_sha": attestation["payload"]["commit_sha"],
        "readiness_run_id": attestation["payload"]["run_ids"]["readiness"],
        "demo_grant_id": attestation["payload"]["demo_grant_id"],
        "authorized_demo_candidate_id": attestation["payload"]["authorized_demo_candidate_id"],
        "expires_at_utc": attestation["valid_until_utc"],
        "demo_trading_allowed": True,
        "live_trading_allowed": False,
        "orders_submitted": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
