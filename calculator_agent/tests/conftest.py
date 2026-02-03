import pytest
from unittest.mock import AsyncMock, patch

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
    TransportProtocol,
)
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder

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

@pytest.fixture(autouse=True)
def mock_auth():
    """Mock TokenVerifier to bypass auth in tests."""
    with patch("calculator_agent.server.TokenVerifier") as mock_verifier_cls:
        mock_instance = AsyncMock()
        mock_instance.verify_request.return_value = "mock_token"
        mock_verifier_cls.return_value = mock_instance
        yield mock_verifier_cls

@pytest.fixture(autouse=True)
def mock_agent_card_builder():
    """Stub AgentCardBuilder to avoid real MCP calls."""
    with patch.object(AgentCardBuilder, "build", side_effect=_stub_agent_card_build) as mock_build:
        yield mock_build
