from __future__ import annotations

from agents import Agent, Runner, function_tool


def test_openai_agents_sdk_runtime_imports() -> None:
    assert Agent is not None
    assert Runner is not None
    assert function_tool is not None


def test_agent_can_be_constructed_without_network_call() -> None:
    @function_tool
    def ping() -> str:
        return "pong"

    agent = Agent(
        name="runtime-smoke",
        instructions="Return exactly pong when asked.",
        tools=[ping],
    )
    assert agent.name == "runtime-smoke"
    assert len(agent.tools) == 1
