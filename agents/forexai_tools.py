"""Evidence-first local tools for the ForexAI agent team.

The tools are deliberately read-only with respect to the repository. Agents may
inspect committed files, git metadata, local test results, and discovery handoffs,
but they cannot silently mutate the research state.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from agents import function_tool

REPO_ROOT = Path(__file__).resolve().parents[1]
MAX_READ = 20_000
ALLOWED_PREFIXES = (
    "agents/", ".github/workflows/", "src/", "tests/", "scripts/", "configs/",
    "docs/", "artifacts/", "reports/",
)


def _safe_path(relative_path: str) -> Path:
    p = Path(relative_path)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError("path must be repository-relative and cannot contain '..'")
    normalized = p.as_posix()
    if not normalized.startswith(ALLOWED_PREFIXES):
        raise ValueError("path is outside the agent evidence allowlist")
    target = (REPO_ROOT / p).resolve()
    if REPO_ROOT not in target.parents and target != REPO_ROOT:
        raise ValueError("path escapes repository root")
    return target


@function_tool
def list_evidence_files(subdir: str = "") -> str:
    """List evidence-bearing files under an allowlisted repository directory."""
    base = _safe_path(subdir) if subdir else REPO_ROOT
    files = []
    for p in sorted(base.rglob("*")):
        if p.is_file() and any(p.relative_to(REPO_ROOT).as_posix().startswith(x) for x in ALLOWED_PREFIXES):
            files.append(p.relative_to(REPO_ROOT).as_posix())
        if len(files) >= 500:
            break
    return json.dumps({"root": str(base.relative_to(REPO_ROOT)), "files": files}, ensure_ascii=False)


@function_tool
def read_evidence_file(path: str) -> str:
    """Read a bounded text evidence file."""
    target = _safe_path(path)
    if not target.exists() or not target.is_file():
        return json.dumps({"path": path, "exists": False})
    raw = target.read_text(encoding="utf-8", errors="replace")
    return json.dumps({"path": path, "exists": True, "truncated": len(raw) > MAX_READ, "content": raw[:MAX_READ]}, ensure_ascii=False)


@function_tool
def search_evidence(term: str, subdir: str = "") -> str:
    """Search allowlisted evidence files for a case-insensitive term."""
    if not term.strip():
        raise ValueError("term must not be empty")
    base = _safe_path(subdir) if subdir else REPO_ROOT
    hits = []
    needle = term.lower()
    for p in sorted(base.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(REPO_ROOT).as_posix()
        if not any(rel.startswith(prefix) for prefix in ALLOWED_PREFIXES):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for idx, line in enumerate(text.splitlines(), start=1):
            if needle in line.lower():
                hits.append({"path": rel, "line": idx, "text": line[:500]})
                if len(hits) >= 200:
                    return json.dumps({"term": term, "hits": hits}, ensure_ascii=False)
    return json.dumps({"term": term, "hits": hits}, ensure_ascii=False)


def _run_git(*args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=REPO_ROOT, text=True, capture_output=True, timeout=30, check=False)
    return json.dumps({"returncode": proc.returncode, "stdout": proc.stdout[:MAX_READ], "stderr": proc.stderr[:MAX_READ]}, ensure_ascii=False)


@function_tool
def repository_state() -> str:
    """Return read-only git state."""
    return json.dumps({"status": json.loads(_run_git("status", "--short", "--branch")), "log": json.loads(_run_git("log", "-12", "--oneline", "--decorate"))}, ensure_ascii=False)


@function_tool
def run_pytest(target: str = "tests") -> str:
    """Run pytest only against an allowlisted test path."""
    p = _safe_path(target)
    if not p.exists():
        return json.dumps({"target": target, "exists": False})
    proc = subprocess.run(["python", "-m", "pytest", "-q", str(p)], cwd=REPO_ROOT, text=True, capture_output=True, timeout=180, check=False)
    return json.dumps({"target": target, "returncode": proc.returncode, "stdout": proc.stdout[-MAX_READ:], "stderr": proc.stderr[-MAX_READ:]}, ensure_ascii=False)


@function_tool
def inspect_discovery_artifact(path: str, max_candidates: int = 20) -> str:
    """Run the deterministic evidence-only discovery handoff inspection."""
    from research_mission import inspect_discovery
    decision = inspect_discovery(_safe_path(path), max_candidates=max_candidates)
    return decision.to_json()


def evidence_tools() -> list:
    return [list_evidence_files, read_evidence_file, search_evidence, repository_state, run_pytest, inspect_discovery_artifact]
