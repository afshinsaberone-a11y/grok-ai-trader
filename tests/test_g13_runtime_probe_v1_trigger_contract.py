from pathlib import Path


LEGACY_V1 = Path(
    ".github/workflows/forexai-g13-mt5-runtime-safety-probe-m15.yml"
)
CURRENT_V2 = Path(
    ".github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml"
)


def test_legacy_runtime_probe_is_manual_only():
    workflow = LEGACY_V1.read_text(encoding="utf-8")
    triggers = workflow.split("permissions:", 1)[0]
    assert "workflow_dispatch:" in triggers
    assert "\n  push:" not in triggers


def test_legacy_and_v2_runtime_probes_share_non_cancelling_runner_lock():
    for path in (LEGACY_V1, CURRENT_V2):
        workflow = path.read_text(encoding="utf-8")
        assert "group: g13-mt5-runtime-safety-probe-shared" in workflow
        assert "cancel-in-progress: false" in workflow
