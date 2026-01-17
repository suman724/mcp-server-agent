import pytest
from fastapi.testclient import TestClient

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Message,
    MessageSendParams,
    Role,
    SendMessageRequest,
)
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH

from calculator_agent.server import app

@pytest.fixture
def client():
    return TestClient(app)

def test_get_agent_card(client):
    """Test the agent card endpoint."""
    response = client.get(AGENT_CARD_WELL_KNOWN_PATH)
    assert response.status_code == 200
    
    card = AgentCard.model_validate(response.json())
    assert card.name == "Calculator Agent"
    assert card.version == "0.1.0"
    assert card.url.endswith("/calculator")
    assert card.preferred_transport == "JSONRPC"
    assert card.capabilities is not None

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_run_agent_invalid_payload(client):
    """Test agent invocation with invalid payload."""
    response = client.post(
        "/calculator",
        json={"invalid": "payload"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == -32600  # InvalidRequestError

def test_run_agent_empty_messages(client):
    """Test agent invocation with empty message parts."""
    message = Message(message_id="msg-1", role=Role.user, parts=[])
    request = SendMessageRequest(
        id="req-1",
        params=MessageSendParams(message=message),
    )
    response = client.post(
        "/calculator",
        json=request.model_dump(mode="json", exclude_none=True),
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["error"]["code"] == -32602  # InvalidParamsError

def test_agent_card_structure():
    """Test the agent card has the expected structure."""
    card = AgentCard(
        name="Test Agent",
        description="Test description",
        url="http://localhost:8001/calculator",
        version="0.1.0",
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="test",
                name="Test",
                description="Test skill",
                tags=["test"],
            )
        ],
    )
    
    assert card.name == "Test Agent"
    assert card.version == "0.1.0"
    assert card.skills[0].id == "test"
