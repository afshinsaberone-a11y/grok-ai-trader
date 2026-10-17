from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.optimization.g13_demo_readiness_gate_m15 import (
    validate_preflight_binding,
    validate_promotion_binding,
    validate_runtime_probe_identity,
)


def _write(tmp_path: Path, name: str, payload: dict) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _case(tmp_path: Path):
    provenance = {
        "schema_version": "forexai.g13.promotion_evidence_provenance.m15.v1",
        "sources": {
            "validation": {"run_id": 34559825574},
            "robustness": {"run_id": 34679210600},
            "oos": {"run_id": 34679937623},
        },
    }
    promotion = {
        "schema_version": "forexai.g13.promotion_manifest.m15.v1",
        "status": "PROMOTION_READY",
        "evidence_provenance_sha256": __import__(
            "research.optimization.g13_demo_readiness_gate_m15",
            fromlist=["canonical_hash"],
        ).canonical_hash(provenance),
    }
    p = _write(tmp_path, "promotion.json", promotion)
    prov = _write(tmp_path, "source-provenance.json", provenance)
    attestation = {
        "schema_version": "forexai.g13.promotion_run_attestation.m15.v1",
        "workflow_run_id": 999,
        "head_sha": "abc123",
        "manifest_sha256": __import__(
            "research.optimization.g13_demo_readiness_gate_m15",
            fromlist=["file_sha256"],
        ).file_sha256(p),
        "provenance_sha256": __import__(
            "research.optimization.g13_demo_readiness_gate_m15",
            fromlist=["file_sha256"],
        ).file_sha256(prov),
    }
    a = _write(tmp_path, "attestation.json", attestation)
    return p, prov, a


def test_exact_promotion_binding_passes(tmp_path: Path):
    p, prov, att = _case(tmp_path)
    validate_promotion_binding(
        json.loads(p.read_text()),
        json.loads(prov.read_text()),
        json.loads(att.read_text()),
        promotion_run_id=999,
        main_head_sha="abc123",
        promotion_path=p,
        provenance_path=prov,
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("workflow_run_id", 1000),
        ("head_sha", "wrong"),
        ("manifest_sha256", "bad"),
        ("provenance_sha256", "bad"),
    ],
)
def test_tampered_promotion_attestation_fails(tmp_path: Path, field: str, value):
    p, prov, att = _case(tmp_path)
    payload = json.loads(att.read_text())
    payload[field] = value
    with pytest.raises(AssertionError):
        validate_promotion_binding(
            json.loads(p.read_text()),
            json.loads(prov.read_text()),
            payload,
            promotion_run_id=999,
            main_head_sha="abc123",
            promotion_path=p,
            provenance_path=prov,
        )


def test_provenance_hash_mismatch_fails(tmp_path: Path):
    p, prov, att = _case(tmp_path)
    payload = json.loads(p.read_text())
    payload["evidence_provenance_sha256"] = "0" * 64
    with pytest.raises(AssertionError):
        validate_promotion_binding(
            payload,
            json.loads(prov.read_text()),
            json.loads(att.read_text()),
            promotion_run_id=999,
            main_head_sha="abc123",
            promotion_path=p,
            provenance_path=prov,
        )


def _preflight():
    hashes = {
        str(cid): f"hash-{cid}"
        for cid in [2, 6, 10, 12, 14, 22, 26, 28, 30, 32, 34, 38, 42, 46, 48]
    }
    return {
        "schema_version": "forexai.g13.controlled_demo_package_preflight.m15.v1",
        "status": "PASS",
        "candidate_count": 15,
        "candidate_ids": [2, 6, 10, 12, 14, 22, 26, 28, 30, 32, 34, 38, 42, 46, 48],
        "binary_hashes_verified": 15,
        "source_hashes_verified": 15,
        "source_safety_contracts_verified": 15,
        "real_data_only": True,
        "synthetic_data": False,
        "demo_trading_allowed_by_source": False,
        "live_trading_allowed": False,
        "compile_parity_run_id": 55,
        "compile_parity_head_sha": "main-sha",
        "compile_parity_artifact_id": 66,
        "compile_parity_artifact_digest": "sha256:" + "a" * 64,
        "downloaded_zip_sha256": "a" * 64,
        "promotion_manifest_sha256": "p" * 64,
        "candidate_config_hashes": hashes,
    }


def _promotion():
    return {
        "status": "PROMOTION_READY",
        "candidates": [
            {"candidate_id": int(cid), "config_hash": value}
            for cid, value in _preflight()["candidate_config_hashes"].items()
        ],
    }


def test_exact_preflight_binding_passes():
    validate_preflight_binding(
        _promotion(),
        _preflight(),
        promotion_manifest_sha256=_preflight()["promotion_manifest_sha256"],
        parity_run_id=55,
        parity_head_sha="main-sha",
        main_head_sha="main-sha",
        promoted_ids=tuple(_preflight()["candidate_ids"]),
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("compile_parity_run_id", 56),
        ("compile_parity_head_sha", "wrong"),
        ("promotion_manifest_sha256", "q" * 64),
        ("downloaded_zip_sha256", "b" * 64),
    ],
)
def test_preflight_binding_rejects_tampering(field, value):
    payload = _preflight()
    payload[field] = value
    with pytest.raises(AssertionError):
        validate_preflight_binding(
            _promotion(),
            payload,
            promotion_manifest_sha256="p" * 64,
            parity_run_id=55,
            parity_head_sha="main-sha",
            main_head_sha="main-sha",
            promoted_ids=tuple(_preflight()["candidate_ids"]),
        )


def test_preflight_candidate_hash_mismatch_fails():
    payload = _preflight()
    payload["candidate_config_hashes"]["2"] = "wrong"
    with pytest.raises(AssertionError):
        validate_preflight_binding(
            _promotion(),
            payload,
            promotion_manifest_sha256="p" * 64,
            parity_run_id=55,
            parity_head_sha="main-sha",
            main_head_sha="main-sha",
            promoted_ids=tuple(_preflight()["candidate_ids"]),
        )


def test_static_lint_freshness_reuses_only_unchanged_ancestor():
    workflow = Path(
        ".github/workflows/forexai-g13-demo-readiness-gate-m15.yml"
    ).read_text(encoding="utf-8")

    assert 'latest_success "forexai-g13-workflow-lint.yml"' in workflow
    assert 'latest_success_exact "forexai-g13-workflow-lint.yml" "$MAIN_SHA"' not in workflow
    assert 'git merge-base --is-ancestor "$LINT_HEAD_SHA" "$MAIN_HEAD_SHA"' in workflow
    start = workflow.index("      - name: Verify static validation freshness")
    end = workflow.index("      - name: Run readiness gate", start)
    freshness = workflow[start:end]
    for audited_path in (
        ".github/workflows",
        ".github/actionlint.yaml",
        "research/optimization",
        "research/real_data",
        "tests",
        "tools",
    ):
        assert audited_path in freshness


def test_readiness_requires_runtime_probe_from_exact_current_main_sha():
    workflow = Path(
        ".github/workflows/forexai-g13-demo-readiness-gate-m15.yml"
    ).read_text(encoding="utf-8")

    assert 'runtime_id="$(latest_success_exact "forexai-g13-mt5-runtime-safety-probe-m15-v2.yml" "$MAIN_SHA")"' in workflow
    assert 'if [ "$key" = "RUNTIME" ] || [ "$key" = "SAFETY" ]' in workflow

def test_runtime_safety_probe_startup_attaches_script_to_explicit_chart():
    workflow = Path(
        ".github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml"
    ).read_text(encoding="utf-8")

    # MT5 does not start a startup Script when the current profile has no
    # chart. Force an explicit, deterministic chart for both no-order probes.
    assert workflow.count("          Script=$scriptRel\n") == 2
    assert workflow.count("          Symbol=EURUSD\n") == 2
    assert workflow.count("          Period=M15\n") == 2
    assert workflow.count("          ShutdownTerminal=1\n") == 2


def test_mt5_runner_waits_for_exact_candidate_parity_before_diagnostic_compile():
    parity_workflow = Path(
        ".github/workflows/forexai-control-plane-pr-parity.yml"
    ).read_text(encoding="utf-8")
    compile_workflow = Path(
        ".github/workflows/forexai-control-plane-mt5-compile-guard.yml"
    ).read_text(encoding="utf-8")

    assert "group: forexai-control-plane-pr-real-data-parity-pull_request-" in parity_workflow
    assert "forexai-g13-oos-watchdog-m15.yml/runs?branch=main&per_page=100" in parity_workflow
    assert 'get("workflow_id")==377528976' in parity_workflow
    assert "CONTROL_PLANE_MAIN_G13_WATCHDOG_COMPLETED" in parity_workflow
    assert "CANDIDATE_SHA: ${{ github.event_name == 'pull_request'" in compile_workflow
    assert 'get("workflow_id")==385709004' in compile_workflow
    assert '"SUCCESS|"+str(latest["id"])' in compile_workflow
    assert '"FAILED|"+str(latest["id"])' in compile_workflow
    assert "MT5_COMPILE_GUARD_CANDIDATE_PARITY_FAILED" in compile_workflow
    assert "MT5_COMPILE_GUARD_WAITING_FOR_CANDIDATE_PARITY" in compile_workflow
    assert "MT5_COMPILE_GUARD_RUNNER_SLOT_ORDER=MAIN_PARITY_THEN_CANDIDATE_PARITY_THEN_DIAGNOSTIC_COMPILE" in compile_workflow
    assert "timeout-minutes: 85" in compile_workflow

def test_compile_guard_embedded_candidate_parity_resolver_executes_fail_closed_states():
    import json
    import subprocess
    import sys

    workflow = Path(
        ".github/workflows/forexai-control-plane-mt5-compile-guard.yml"
    ).read_text(encoding="utf-8")
    marker = 'pr_state="$(printf \'%s\' "$pr_payload" | python -c \''
    start = workflow.index(marker) + len(marker)
    terminator = "' \"$candidate_sha\")\""
    end = workflow.index(terminator, start)
    resolver_code = workflow[start:end]

    # Parsing alone catches shell-embedded Python syntax errors before a scarce
    # Windows runner is ever requested.
    compile(resolver_code, "<candidate-parity-resolver>", "exec")

    target = "a" * 40
    cases = [
        (
            "success",
            [{
                "id": 123,
                "name": "ForexAI Control Plane PR Real-Data Parity",
                "workflow_id": 385709004,
                "event": "pull_request",
                "head_sha": target,
                "status": "completed",
                "conclusion": "success",
            }],
            "SUCCESS|123",
        ),
        (
            "failure",
            [{
                "id": 124,
                "name": "ForexAI Control Plane PR Real-Data Parity",
                "workflow_id": 385709004,
                "event": "pull_request",
                "head_sha": target,
                "status": "completed",
                "conclusion": "failure",
            }],
            "FAILED|124|failure",
        ),
        (
            "pending",
            [{
                "id": 125,
                "name": "ForexAI Control Plane PR Real-Data Parity",
                "workflow_id": 385709004,
                "event": "pull_request",
                "head_sha": target,
                "status": "in_progress",
                "conclusion": None,
            }],
            "PENDING",
        ),
        ("not-started", [], "NOT_STARTED"),
    ]
    for _, workflow_runs, expected in cases:
        result = subprocess.run(
            [sys.executable, "-c", resolver_code, target],
            input=json.dumps({"workflow_runs": workflow_runs}),
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == expected

def test_runtime_probe_is_dispatch_only_to_preserve_main_mt5_ordering():
    workflow = Path(
        ".github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml"
    ).read_text(encoding="utf-8")
    trigger_block = workflow.split("\npermissions:", 1)[0]

    # Only the official main watchdog may queue this single-runner probe, and
    # it dispatches after current-main Compile + Signal Parity succeeds.
    assert "  workflow_dispatch:\n" in trigger_block
    assert "\n  push:" not in trigger_block
    assert "workflow_run:" not in trigger_block


def _runtime_probe(*, connected: bool, identity: bool, authorization: bool) -> dict[str, str]:
    demo = connected and identity
    return {
        "status": "PASS",
        "account_identity_verified": "true" if identity else "false",
        "terminal_connected": "true" if connected else "false",
        "account_mode": "0",
        "demo_account": "true" if demo else "false",
        "real_account_detected": "false",
        "authorization": "true" if authorization else "false",
        "execution_allowed": "false",
        "orders_submitted": "false",
    }


def test_runtime_identity_accepts_connected_verified_demo_only():
    validate_runtime_probe_identity(
        _runtime_probe(connected=True, identity=True, authorization=False),
        _runtime_probe(connected=True, identity=True, authorization=True),
    )


@pytest.mark.parametrize(
    ("connected", "identity"),
    [
        (False, False),
        (False, True),
        (True, False),
    ],
)
def test_runtime_identity_rejects_offline_or_unverified_demo_defaults(connected: bool, identity: bool):
    off = _runtime_probe(connected=connected, identity=identity, authorization=False)
    on = _runtime_probe(connected=connected, identity=identity, authorization=True)
    # Old offline MT5 instances returned account_mode=0 (the DEMO enum) even
    # with no broker connection. That must never count as Demo account evidence.
    with pytest.raises(AssertionError):
        validate_runtime_probe_identity(off, on)


def test_runtime_probe_mql5_sources_bind_demo_status_to_connected_account_identity():
    for path in (
        "research/optimization/G13_Safety_Probe_AuthOff.mq5",
        "research/optimization/G13_Safety_Probe_AuthOn.mq5",
    ):
        source = Path(path).read_text(encoding="utf-8")
        assert "AccountInfoInteger(ACCOUNT_LOGIN)" in source
        assert "AccountInfoString(ACCOUNT_SERVER)" in source
        assert "terminal_connected && account_login>0 && StringLen(account_server)>0" in source
        assert 'FileWrite(h,"account_identity_verified,' in source
        assert 'mode==ACCOUNT_TRADE_MODE_DEMO && account_identity_verified' in source


def test_runtime_probe_workflow_is_denied_first_and_uses_isolated_portable_mt5():
    workflow = Path(
        ".github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml"
    ).read_text(encoding="utf-8")

    assert "Enforce shared Kill Switch DENY" in workflow
    assert "-SetDenyKillSwitch" in workflow
    assert "Prepare run-unique isolated portable MT5 instance" in workflow
    assert "G13_ISOLATED_TERMINAL_PATH" in workflow
    assert workflow.count("/portable /config:") == 2
    assert "Cleanup isolated portable MT5 runtime" in workflow
    assert '"G13_ISOLATED_MT5_ROOT=$portableRoot" | Out-File $env:GITHUB_ENV' in workflow
    assert "G13_RUNTIME_AUTH_OFF_ACCOUNT_IDENTITY_UNVERIFIED" in workflow
    assert "G13_RUNTIME_AUTH_ON_ACCOUNT_IDENTITY_UNVERIFIED" in workflow
