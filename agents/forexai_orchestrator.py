"""ForexAI evidence-first multi-agent orchestration using OpenAI Agents SDK.

Specialists are given read-only tools over the checked-out repository. The team
must base every claim on observable repository evidence and remains fail-closed:
missing evidence is reported as missing, never inferred as success.
"""
from __future__ import annotations

import asyncio
import os

from agents import Agent, Runner

from forexai_tools import evidence_tools

REPO = "afshinsaberone-a11y/grok-ai-trader"

COMMON = f"""You work on ForexAI v0.1 in GitHub repository {REPO}.
Evidence policy is strict: never invent metrics, trades, datasets, artifacts, CI results,
or candidate status. Use repository evidence tools before making factual claims.
A missing artifact, missing log, or unavailable external CI evidence is UNKNOWN, not PASS.
Never use synthetic market data or synthetic fallback data.
Never relax statistical gates.
2026 is held out as OOS and must not influence discovery, parameter selection, ranking, or optimization.
All trading evaluation must use execution_contract_v1: next-bar-open, 0.7 pip adverse
entry and exit cost per side, 1.4 pip round trip, SL-first, 30-bar expiry, one position.
AI proposes; statistics approves; only statistically validated systems may reach EA/Demo/Live.
Separate every report into VERIFIED FACTS, GAPS/UNKNOWN, and RECOMMENDATION.
"""

ROLES = {
    "data": "Validate real data provenance, schema, cadence, timezone, gaps, duplicates and OHLC invariants.",
    "execution": "Audit execution mechanics and enforce execution_contract_v1.",
    "research": "Design simple deterministic rule-based strategy hypotheses with no look-ahead.",
    "discovery": "Inspect or run pre-OOS candidate discovery and reject leakage or validation contamination.",
    "optimization": "Verify optimization remains inside declared discovery space; never tune on validation or OOS.",
    "validation": "Audit yearly PF, expectancy, trade-count, drawdown, robustness and Monte Carlo gates.",
    "review": "Perform adversarial code review for look-ahead, leakage, stale paths, schema and gate bypasses.",
    "ci": "Inspect repository evidence of GitHub Actions runs, jobs, artifacts and workflow failures; never infer an unobserved run.",
    "champion": "Independently verify Champion eligibility and block promotion on any missing or failed gate.",
}


def make_specialist(key: str) -> Agent:
    return Agent(
        name=f"ForexAI {key.title()} Agent",
        instructions=COMMON + "\nYour role: " + ROLES[key],
        tools=evidence_tools(),
    )


def build_orchestrator() -> Agent:
    specialists = {key: make_specialist(key) for key in ROLES}
    tools = [
        agent.as_tool(
            tool_name=f"{key}_agent",
            tool_description=ROLES[key],
        )
        for key, agent in specialists.items()
    ]
    # The manager also has direct read-only evidence access so it can verify a specialist claim.
    return Agent(
        name="ForexAI Orchestrator",
        instructions=COMMON + """
You are the manager. Delegate independent checks to the most relevant specialists,
then cross-check important claims with repository evidence yourself.
For a discovery/validation decision, prefer Data + Execution + Discovery/Optimization + Validation + CI,
then Champion only after the prior gates are evidenced.
Do not ask the Champion agent to rescue missing evidence.
Produce exactly one next action with explicit GO / HOLD / REJECT status.
EA generation is never authorized by this orchestrator unless a frozen candidate has
passed validation, frozen robustness, and strictly held-out 2026 OOS with recorded evidence.
""", tools=tools + evidence_tools(),
    )


async def run(task: str) -> str:
    orchestrator = build_orchestrator()
    result = await Runner.run(orchestrator, task)
    return result.final_output


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is required to run the agent team.")
    prompt = os.getenv(
        "FOREXAI_AGENT_TASK",
        "Inspect the latest committed ForexAI research evidence and determine the safest next action.",
    )
    print(asyncio.run(run(prompt)))
