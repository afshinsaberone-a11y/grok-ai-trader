"""Collect selected GitHub Actions evidence artifacts into the current workspace.

The collector downloads only named, pre-approved artifacts from known ForexAI runs.
It never downloads market data or OOS data and never fabricates evidence.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

SOURCES = (
    (34019276235, "robustness-validation-v29-1-M5", "reports/evidence/v29.1/M5"),
    (34020209424, "robustness-validation-v29-1-M1", "reports/evidence/v29.1/M1"),
    (34022425980, "robustness-validation-v29-1-M15", "reports/evidence/v29.1/M15"),
)


def download(run_id: int, artifact: str, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["GH_TOKEN"] = env.get("GH_TOKEN") or env.get("GITHUB_TOKEN", "")
    if not env["GH_TOKEN"]:
        raise RuntimeError("GH_TOKEN/GITHUB_TOKEN is required to collect Actions artifacts")
    subprocess.run(
        ["gh", "run", "download", str(run_id), "--name", artifact, "--dir", str(destination)],
        check=True,
        env=env,
        text=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    args = parser.parse_args()
    if not args.repo:
        raise SystemExit("GITHUB_REPOSITORY is required")

    manifest = {
        "schema": "forexai.evidence_collection.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": args.repo,
        "sources": [],
        "policy": {
            "real_artifacts_only": True,
            "synthetic_generation": False,
            "oos_2026_downloaded": False,
        },
    }

    for run_id, artifact, rel_dest in SOURCES:
        dest = Path(rel_dest)
        download(run_id, artifact, dest)
        files = sorted(str(p) for p in dest.rglob("*") if p.is_file())
        if not files:
            raise RuntimeError(f"artifact {artifact} from run {run_id} produced no files")
        manifest["sources"].append(
            {"run_id": run_id, "artifact": artifact, "destination": str(dest), "files": files}
        )

    out = Path("reports/evidence/evidence-collection-manifest.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
