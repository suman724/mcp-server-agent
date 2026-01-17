import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import sys
from pathlib import Path

from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Message,
    Part,
    Role,
    SendMessageSuccessResponse,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
)

# Add parent directory to path to import the invoker module
sys.path.insert(0, str(Path(__file__).parent))

@pytest.mark.asyncio
async def test_get_agent_card_success():
    """Test fetching agent card successfully."""
    # Import here after path is set
    from main import get_agent_card
    
    mock_response = MagicMock()
    card = AgentCard(
        name="Calculator Agent",
        description="Test agent",
        url="http://localhost:8001/calculator",
        version="0.1.0",
        capabilities=AgentCapabilities(streaming=False),
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        skills=[
            AgentSkill(
                id="calculator",
                name="Calculator",
                description="Test skill",
                tags=["math"],
            )
        ],
    )
    mock_response.json.return_value = card.model_dump(
        mode="json", exclude_none=True
    )
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        result = await get_agent_card()
        
        assert result is not None
        assert result.name == "Calculator Agent"
        assert result.capabilities is not None
        mock_client.get.assert_called_once()

@pytest.mark.asyncio
async def test_get_agent_card_http_error():
    """Test fetching agent card with HTTP error."""
    from main import get_agent_card
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
        mock_client_class.return_value = mock_client
        
        result = await get_agent_card()
        
        assert result is None

@pytest.mark.asyncio
async def test_invoke_agent_success():
    """Test invoking agent successfully."""
    from main import invoke_agent
    
    user_message = Message(
        message_id="msg-user",
        role=Role.user,
        parts=[Part(root=TextPart(text="Calculate 6 * 7"))],
    )
    agent_message = Message(
        message_id="msg-agent",
        role=Role.agent,
        parts=[Part(root=TextPart(text="The result is 42"))],
    )
    task = Task(
        id="task-1",
        context_id="ctx-1",
        status=TaskStatus(state=TaskState.completed, message=agent_message),
        history=[user_message, agent_message],
    )
    success = SendMessageSuccessResponse(id="req-1", result=task)

    mock_response = MagicMock()
    mock_response.json.return_value = success.model_dump(
        mode="json", exclude_none=True
    )
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        result = await invoke_agent("Calculate 6 * 7")
        
        assert result == "The result is 42"
        
        # Verify the request was made
        assert mock_client.post.called

@pytest.mark.asyncio
async def test_invoke_agent_http_error():
    """Test invoking agent with HTTP error."""
    from main import invoke_agent
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(side_effect=httpx.HTTPError("Server error"))
        mock_client_class.return_value = mock_client
        
        result = await invoke_agent("Test prompt")
        
        assert "Error invoking agent" in result

@pytest.mark.asyncio
async def test_invoke_agent_no_assistant_message():
    """Test invoking agent when response has no assistant message."""
    from main import invoke_agent
    
    user_message = Message(
        message_id="msg-user",
        role=Role.user,
        parts=[Part(root=TextPart(text="Test"))],
    )
    task = Task(
        id="task-1",
        context_id="ctx-1",
        status=TaskStatus(state=TaskState.completed),
        history=[user_message],
    )
    success = SendMessageSuccessResponse(id="req-1", result=task)

    mock_response = MagicMock()
    mock_response.json.return_value = success.model_dump(
        mode="json", exclude_none=True
    )
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        result = await invoke_agent("Test prompt")
        
        assert result == "No response content found."
