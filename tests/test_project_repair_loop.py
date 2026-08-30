from pathlib import Path

from research.project_repair_loop import audit


def test_repair_loop_is_fail_closed_and_returns_structured_report():
    report = audit(Path(__file__).resolve().parents[1])
    assert report["fail_closed"] is True
    assert report["status"] in {"BLOCKED", "READY_FOR_TEST_RUN"}
    assert report["checks"]
    assert all(set(f) >= {"check", "status", "severity", "evidence", "remediation"} for f in report["checks"])
