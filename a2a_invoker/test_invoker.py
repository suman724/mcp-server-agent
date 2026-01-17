import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import sys
from pathlib import Path

# Add parent directory to path to import the invoker module
sys.path.insert(0, str(Path(__file__).parent))

@pytest.mark.asyncio
async def test_get_agent_card_success():
    """Test fetching agent card successfully."""
    # Import here after path is set
    from main import get_agent_card
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "name": "Calculator Agent",
        "description": "Test agent",
        "capabilities": ["math"],
        "version": "0.1.0"
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        result = await get_agent_card()
        
        assert result is not None
        assert result["name"] == "Calculator Agent"
        assert "capabilities" in result
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
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "messages": [
            {"role": "assistant", "content": "The result is 42"}
        ]
    }
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
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "messages": [
            {"role": "user", "content": "Test"}
        ]
    }
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client
        
        result = await invoke_agent("Test prompt")
        
        assert result == "No response content found."
