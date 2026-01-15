import pytest
from unittest.mock import AsyncMock, patch
from calculator_agent.agent import CalculatorAgent

@pytest.mark.asyncio
async def test_agent_run_simple_exec():
    # Mock streamable_http_client and ClientSession to avoid real network calls
    with patch("calculator_agent.agent.streamable_http_client") as mock_transport:
        mock_streams = (AsyncMock(), AsyncMock())
        mock_transport.return_value.__aenter__.return_value = mock_streams
        
        with patch("calculator_agent.agent.ClientSession") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session_cls.return_value.__aenter__.return_value = mock_session
            
            # Setup mock return for call_tool
            mock_session.call_tool.return_value = 8.0
            
            agent = CalculatorAgent()
            result = await agent.run_simple_eval("add 5 3")
            
            assert result == 8.0
            mock_session.call_tool.assert_called_with("add", arguments={"a": 5.0, "b": 3.0})

@pytest.mark.asyncio
async def test_agent_run_invalid_command():
    with patch("calculator_agent.agent.streamable_http_client") as mock_transport, \
         patch("calculator_agent.agent.ClientSession") as mock_session_cls:
             
        agent = CalculatorAgent()
        result = await agent.run_simple_eval("invalid")
        assert result == "Could not parse simple command."
