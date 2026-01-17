import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from calculator_agent.server import app

@pytest.fixture
def client():
    return TestClient(app)

def test_get_agent_card(client):
    """Test the agent card endpoint."""
    response = client.get("/calculator/info")
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Calculator Agent"
    assert data["version"] == "0.1.0"
    assert "capabilities" in data
    assert "math_operations" in data["capabilities"]
    assert "input_schema" in data
    assert "output_schema" in data

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
    
    assert response.status_code == 422  # Validation error

def test_run_agent_empty_messages(client):
    """Test agent invocation with empty messages list."""
    response = client.post(
        "/calculator",
        json={"messages": []}
    )
    
    # Should either be 400 or 503 depending on agent_instance state
    assert response.status_code in [400, 503]

def test_agent_card_structure():
    """Test the agent card has the expected structure."""
    from calculator_agent.server import AgentCard
    
    card = AgentCard(
        name="Test Agent",
        description="Test description",
        capabilities=["test"],
        input_schema={"type": "object"},
        output_schema={"type": "object"}
    )
    
    assert card.name == "Test Agent"
    assert card.version == "0.1.0"
    assert len(card.capabilities) == 1
