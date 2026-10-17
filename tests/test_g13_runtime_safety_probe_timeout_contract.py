from pathlib import Path


WORKFLOW = Path(
    ".github/workflows/forexai-g13-mt5-runtime-safety-probe-m15-v2.yml"
)


def _step(workflow: str, name: str, next_name: str) -> str:
    start = workflow.index(f"      - name: {name}\n")
    end = workflow.index(f"      - name: {next_name}\n", start + 1)
    return workflow[start:end]


def test_auth_off_and_auth_on_probes_have_hard_timeouts_and_bounded_scheduler_calls():
    workflow = WORKFLOW.read_text(encoding="utf-8")

    pairs = (
        ("Run Auth OFF probe", "Run Auth ON probe", "AUTH_OFF"),
        ("Run Auth ON probe", "Evaluate runtime evidence", "AUTH_ON"),
    )
    for name, next_name, label in pairs:
        step = _step(workflow, name, next_name)
        assert "timeout-minutes: 5" in step
        assert "Start-Process -FilePath $schtasks" in step
        assert "WaitForExit(15000)" in step
        assert f"G13_RUNTIME_{label}_TASK_START_TIMEOUT" in step
        assert "$deadline = $taskStartedAt.AddSeconds(180)" in step
        assert f"G13_RUNTIME_{label}_WAITING_FOR_MARKER" in step
        assert "WaitForExit(10000)" in step
        assert "Start-ScheduledTask -TaskName $taskName" not in step
        assert "Get-ScheduledTask -TaskName $taskName" not in step
        assert "Get-ScheduledTaskInfo -TaskName $taskName" not in step

    # Keep the safety boundary explicit while making the runner wait bounded.
    assert "AllowLiveTrading=0" in workflow
    assert "G13_RUNTIME_AUTH_OFF_MUST_BLOCK" in workflow
    assert "G13_RUNTIME_AUTH_OFF_ORDER_INVARIANT_FAILED" in workflow
    assert "G13_RUNTIME_AUTH_ON_ORDER_INVARIANT_FAILED" in workflow
    assert "KILL_SWITCH_UNCHANGED=true" in workflow
