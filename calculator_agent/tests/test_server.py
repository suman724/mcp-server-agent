import pytest
from starlette.testclient import TestClient

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH

from calculator_agent import server

@pytest.fixture
def client():
    with TestClient(server.app) as client:
        yield client

def test_get_agent_card(client):
    """Test the agent card endpoint."""
    response = client.get(f"/calculator{AGENT_CARD_WELL_KNOWN_PATH}")
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

def test_run_agent_invalid_params(client):
    """Test agent invocation with invalid params."""
    request = {
        "jsonrpc": "2.0",
        "id": "req-1",
        "method": "message/send",
        "params": {},
    }
    response = client.post(
        "/calculator",
        json=request,
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
