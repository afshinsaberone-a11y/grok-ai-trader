"""Regression tests for the source-signer eligibility report wiring."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "provider-source-wheel-candidate.yml"
BOOTSTRAP = ROOT / "tools" / "bootstrap_provider_host_v1.ps1"
DOC = ROOT / "docs" / "PROVIDER_SOURCE_SIGNER_ALLOWLIST_GATE_V1.md"


def test_source_build_workflow_runs_source_signer_manifest_checker():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "tools/verify_provider_source_signer_manifest_v1.py" in text
    assert "FOREXAI_TRUST_REGISTRY_BUNDLE_BASE64: ${{ vars.FOREXAI_TRUST_REGISTRY_BUNDLE_BASE64 }}" in text
    assert "FOREXAI_TRUST_REGISTRY_ROOT_PUBLIC_KEY: ${{ vars.FOREXAI_TRUST_REGISTRY_ROOT_PUBLIC_KEY }}" in text
    assert "FOREXAI_TRUST_REGISTRY_ROOT_FINGERPRINT: ${{ vars.FOREXAI_TRUST_REGISTRY_ROOT_FINGERPRINT }}" in text
    assert "FOREXAI_TRUST_REGISTRY_EXPECTED_BUNDLE_SHA256: ${{ vars.FOREXAI_TRUST_REGISTRY_EXPECTED_BUNDLE_SHA256 }}" in text
    assert "FOREXAI_PROVIDER_SOURCE_BUILD_MANIFEST_PATH" in text
    assert "SOURCE_SIGNER_ALLOWLIST_MATCH=BLOCKED" in text
    assert "SOURCE_SIGNER_PRODUCTION_APPROVED=false" in text
    assert "SOURCE_SIGNER_BOOTSTRAP_APPROVED=false" in text
    assert "SOURCE_SIGNER_TRADING_AUTHORIZATION_CREATED=false" in text


def test_source_signer_report_is_uploaded_and_is_not_an_approval():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "artifacts/provider-source-build/source-signer-eligibility-report.json" in text
    assert "SOURCE_SIGNER_ALLOWLIST_MATCH_ONLY_NO_PRODUCTION_APPROVAL=true" in text
    assert "SOURCE_SIGNER_PRODUCTION_ELIGIBILITY=BLOCKED" in text
    assert "TRUST_REGISTRY_BUNDLE_NOT_CONFIGURED" in text
    assert '"production_approved": False' in text
    assert '"bootstrap_approved": False' in text
    assert '"trading_authorization_created": False' in text


def test_source_built_candidate_remains_separate_from_production_bootstrap():
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    assert "requirements-provider.lock.txt" in bootstrap
    assert "requirements-provider-test.lock.txt" in bootstrap
    assert "provider-source-build" not in bootstrap


def test_documentation_states_blocked_default_and_production_limits():
    text = DOC.read_text(encoding="utf-8")
    assert "BLOCKED" in text
    assert "production_approved=false" in text
    assert "bootstrap_approved=false" in text
    assert "does not deploy it" in text
