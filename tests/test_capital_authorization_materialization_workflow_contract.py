from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "forexai-control-plane-materialize-authorization-v1.yml"


def test_materialization_workflow_is_manual_and_explicitly_confirmed() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "MATERIALIZE_ONE_SIGNAL_DEMO_AUTHORIZATION" in text
    assert "\n  push:" not in text
    assert "\n  pull_request:" not in text
    assert "runs-on: [self-hosted, windows, mt5]" in text


def test_materialization_requires_real_upstream_outputs_and_current_identity_binding() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    for token in (
        "FOREXAI_CONTROL_PLANE_ADMISSION_REQUEST_PATH",
        "FOREXAI_TRADE_LEDGER_PATH",
        "FOREXAI_AUTHENTICATED_ENVELOPE_PATH",
        "forexai.control_plane_admission_request.v1",
        "promotion_evidence.demo_trading_allowed",
        "promotion_evidence.live_trading_allowed",
        "promotion_evidence.real_data_only",
        "promotion_evidence.synthetic_data",
        "MQL5_AUTH_ENVELOPE_TRADE_ID_MISMATCH",
        "MQL5_AUTH_AUTHORIZATION_ID_MISMATCH",
        "MQL5_AUTH_RESERVATION_ID_MISMATCH",
    ):
        assert token in text, f"materialization guard missing: {token}"


def test_materialization_uses_official_verifier_and_redacted_secret_scope() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "tools.materialize_mql5_authorization_v1" in text
    assert "tools.diagnose_capital_authorization_prerequisites_v1" in text
    assert "FOREXAI_CONTROL_PLANE_HMAC_SECRET: ${{ secrets.FOREXAI_CONTROL_PLANE_HMAC_SECRET }}" in text
    assert "MQL5_AUTH_CONTROL_PLANE_SECRET_NOT_CONFIGURED" in text
    assert "MQL5_AUTH_RECORD_ALREADY_EXISTS_MANUAL_REVIEW_REQUIRED" in text
    assert "if: success()" in text
    assert "if: always()" in text  # report upload only
    assert "actions/upload-artifact@v4" in text
    assert "artifacts/g13-control-plane-materialization/report.json" in text


def test_materialization_never_enables_switch_live_or_order_submission() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "-SetDenyKillSwitch" in text
    assert "ORDER_SUBMISSION_PERFORMED=false" in text
    assert "LIVE_TRADING_ALLOWED=false" in text
    assert "ORDER_SEND(" not in text.upper()
    assert "OrderSend(" not in text

def test_failed_post_materialization_audit_cleans_only_the_unchanged_run_owned_record() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "MATERIALIZE_AUTH_CREATED_BY_RUN=true" in text
    assert "MATERIALIZE_AUTH_SHA256=$authHash" in text
    assert "MATERIALIZE_AUDIT_PASS=true" in text
    assert "if: failure()" in text
    assert "MQL5_AUTH_FAILURE_CLEANUP_OWNERSHIP_PROOF_MISSING" in text
    assert "MQL5_AUTH_FAILURE_CLEANUP_HASH_MISMATCH_MANUAL_REVIEW_REQUIRED" in text
    assert "Remove-Item -LiteralPath $env:MATERIALIZE_AUTH_PATH -Force" in text
    assert text.index("CAPITAL_AUTH_PREFLIGHT=PASS_PREREQUISITES_PRESENT_NO_EXECUTION") < text.index(
        "MATERIALIZE_AUDIT_PASS=true"
    )
