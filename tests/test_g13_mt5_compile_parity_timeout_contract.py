from pathlib import Path


WORKFLOW = Path(".github/workflows/forexai-g13-mt5-compile-parity.yml")


def test_mt5_compile_parity_has_a_bounded_job_timeout():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    compile_job = workflow.split("  compile-and-parity:", 1)[1]
    assert "timeout-minutes: 60" in compile_job
    assert "timeout-minutes: 240" not in compile_job


def test_expensive_mt5_compile_and_parity_steps_have_individual_timeouts():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    expectations = {
        "Compile all promoted G13 EAs with MetaEditor": 20,
        "Compile and deploy MQL5 real-data parity script": 10,
        "Run MQL5 real-data parity script": 25,
        "Run fail-closed Python vs MQL5 signal parity": 10,
        "Build immutable Demo package manifest": 5,
    }
    for step_name, minutes in expectations.items():
        marker = f"      - name: {step_name}\n"
        assert workflow.count(marker) == 1, f"workflow step missing or duplicated: {step_name}"
        start = workflow.index(marker) + len(marker)
        next_step = workflow.find("\n      - name:", start)
        block = workflow[start: next_step if next_step >= 0 else len(workflow)]
        assert f"        timeout-minutes: {minutes}\n" in block, (
            f"{step_name} timeout must be {minutes} minutes"
        )
