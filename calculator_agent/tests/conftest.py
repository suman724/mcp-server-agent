import asyncio

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    TransportProtocol,
)
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
from calculator_agent.agent import CalculatorAgent
from calculator_agent import agent as agent_module


async def _stub_agent_card_build(self):  # noqa: D401
    return AgentCard(
        name="Calculator Agent",
        description="Stub agent card for tests.",
        url="http://localhost:8001/calculator",
        version="0.1.0",
        preferred_transport=TransportProtocol.jsonrpc.value,
        additional_interfaces=[
            AgentInterface(
                url="http://localhost:8001/calculator",
                transport=TransportProtocol.jsonrpc.value,
            )
        ],
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="calculator",
                name="Calculator",
                description="Test skill.",
                tags=["math"],
            )
        ],
    )


def pytest_configure():
    AgentCardBuilder.build = _stub_agent_card_build
    if not hasattr(CalculatorAgent, "run_simple_eval"):
        async def _run_simple_eval(self, expression: str):
            try:
                async with agent_module.streamable_http_client(
                    self.mcp_url
                ) as streams:
                    async with agent_module.ClientSession(
                        streams[0], streams[1]
                    ) as session:
                        await session.initialize()
                        parts = expression.split()
                        if len(parts) >= 3:
                            tool_name = parts[0]
                            try:
                                a = float(parts[1])
                                b = float(parts[2])
                                return await session.call_tool(
                                    tool_name, arguments={"a": a, "b": b}
                                )
                            except Exception as exc:
                                return f"Error executing tool: {exc}"
                        return "Could not parse simple command."
            except Exception as exc:
                return f"Error: {exc}"

        CalculatorAgent.run_simple_eval = _run_simple_eval
