"""Offline evidence audit for ForexAI when OpenAI API access is unavailable.

This mission never calls an external model. It evaluates only repository-local
evidence through the deterministic stage controller and emits a machine-readable
report. Missing evidence remains HOLD, never inferred PASS.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from research_controller import decide

STAGES = ("discovery", "optimization", "validation", "robustness", "oos")


def main() -> int:
    results = [decide(stage) for stage in STAGES]
    overall = "GO" if all(r.status == "GO" for r in results) else "HOLD"
    report = {
        "schema": "forexai.offline_agent_mission.v1",
        "mission": "MISSION-001-OFFLINE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "api_required": False,
        "real_model_called": False,
        "overall_status": overall,
        "stage_decisions": [json.loads(r.to_json()) for r in results],
        "policy": {
            "fail_closed": True,
            "missing_evidence_is_unknown": True,
            "synthetic_data_allowed": False,
            "oos_2026_must_remain_held_out": True,
        },
        "recommendation": (
            "Proceed only to the next research stage when its deterministic gates are GO."
            if overall == "GO"
            else "HOLD: missing or failed deterministic evidence blocks promotion."
        ),
    }

    out = Path("reports/agents/mission-001-offline.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
