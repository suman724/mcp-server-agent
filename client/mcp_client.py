import httpx
import uuid
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class MCPClientError(Exception):
    """Base exception for MCP Client errors."""
    pass

class MCPClient:
    def __init__(self, base_url: str = "http://localhost:8000", token: str = None):
        self.base_url = base_url.rstrip("/")
        self.token = token

    async def call_tool(self, tool_name: str, arguments: dict = None) -> Any:
        """
        Calls a tool on the MCP server via HTTP POST (JSON-RPC).
        """
        if arguments is None:
            arguments = {}

        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        async with httpx.AsyncClient() as client:
            headers = {"Accept": "application/json, text/event-stream"}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            logger.debug(f"Sending request to {self.base_url}/: {payload}")
            try:
                response = await client.post(
                    f"{self.base_url}/", # Server is mounted at /
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP Error: {e}")
                logger.error(f"Response content: {e.response.text}")
                raise MCPClientError(f"HTTP Error: {e.response.text}") from e
            except httpx.HTTPError as e:
                logger.error(f"HTTP Connection Error: {e}")
                raise MCPClientError(f"HTTP Connection Error: {e}")

            data = response.json()
            
            if "error" in data:
                error_msg = data['error']
                logger.error(f"RPC Error from server: {error_msg}")
                raise MCPClientError(f"RPC Error: {error_msg}")
            
            logger.debug(f"Received result: {data['result']}")
            
            return data["result"]
