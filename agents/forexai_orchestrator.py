"""ForexAI multi-agent orchestration scaffold using OpenAI Agents SDK.

The orchestrator is intentionally fail-closed: specialist agents can inspect and
recommend, but promotion to validation/EA is blocked unless the statistical gates
and execution-contract requirements are explicitly satisfied.
"""
from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass

try:
    from agents import Agent, Runner
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Install with: pip install openai-agents") from exc

REPO = "afshinsaberone-a11y/grok-ai-trader"

COMMON = f"""You work on ForexAI v0.1 in GitHub repository {REPO}.
Never invent metrics, trades, datasets, artifacts, or GitHub results.
Never use synthetic market data or synthetic fallback data.
Never relax statistical gates.
2026 is held out as OOS and must not influence discovery or parameter selection.
All trading evaluation must use execution_contract_v1: next-bar-open, 0.7 pip adverse
entry and exit cost per side, 1.4 pip round trip, SL-first, 30-bar expiry, one position.
AI proposes; statistics approves; only statistically validated systems may reach EA/Demo/Live.
"""

ROLES = {
    "data": "Validate real data provenance, schema, cadence, timezone, gaps, duplicates and OHLC invariants.",
    "execution": "Audit execution mechanics and enforce execution_contract_v1.",
    "research": "Design simple deterministic rule-based strategy hypotheses with no look-ahead.",
    "discovery": "Run/inspect pre-OOS candidate discovery and reject leakage or validation contamination.",
    "optimization": "Optimize only inside declared discovery space; never tune on validation or OOS.",
    "validation": "Apply yearly PF, expectancy, trade-count, drawdown, robustness and Monte Carlo gates.",
    "review": "Perform adversarial code review for look-ahead, leakage, stale paths, schema and gate bypasses.",
    "ci": "Inspect GitHub Actions runs, jobs, artifacts and workflow failures; report verified facts only.",
    "champion": "Independently verify Champion eligibility; fail closed on any missing/failed gate.",
}


def make_specialist(key: str) -> Agent:
    return Agent(name=f"ForexAI {key.title()} Agent", instructions=COMMON + "\nYour role: " + ROLES[key])


@dataclass
class TeamResult:
    reports: dict[str, str]


def build_orchestrator() -> Agent:
    specialists = [make_specialist(k) for k in ROLES]
    tools = [
        a.as_tool(
            tool_name=f"{k}_agent",
            tool_description=ROLES[k],
        )
        for k, a in zip(ROLES, specialists)
    ]
    return Agent(
        name="ForexAI Orchestrator",
        instructions=COMMON + """
You are the manager. Delegate to specialists as needed, reconcile their reports,
and produce one evidence-based next action. Prefer parallel independent checks when
possible. Never call a candidate Champion merely because it is the best rejected
candidate. A missing artifact or failed gate means STOP/REJECT, not infer success.
""",
        tools=tools,
    )


async def run(task: str) -> str:
    orchestrator = build_orchestrator()
    result = await Runner.run(orchestrator, task)
    return result.final_output


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required to run the agent team.")
    prompt = os.getenv("FOREXAI_AGENT_TASK", "Inspect the latest ForexAI discovery state and determine the safest next research action.")
    print(asyncio.run(run(prompt)))
