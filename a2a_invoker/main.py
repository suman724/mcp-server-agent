
import asyncio
import httpx
import sys
import os
import uuid

from a2a.types import (
    AgentCard,
    JSONRPCErrorResponse,
    Message,
    MessageSendParams,
    Part,
    Role,
    SendMessageRequest,
    SendMessageResponse,
    Task,
    TextPart,
)
from a2a.utils import get_message_text

# Configuration
AGENT_BASE_URL = os.getenv("AGENT_BASE_URL", "http://localhost:8001").rstrip("/")
AGENT_PATH = os.getenv("AGENT_PATH", "/calculator")

def _agent_base_url() -> str:
    if AGENT_BASE_URL.endswith(AGENT_PATH):
        return AGENT_BASE_URL
    return f"{AGENT_BASE_URL}{AGENT_PATH}"

AGENT_RPC_URL = os.getenv("AGENT_RPC_URL", _agent_base_url())
AGENT_CARD_URL = os.getenv(
    "AGENT_CARD_URL", f"{AGENT_RPC_URL}/.well-known/agent-card.json"
)

async def get_agent_card() -> AgentCard | None:
    """Fetch and parse the Agent Card using A2A types."""
    url = AGENT_CARD_URL
    print(f"Fetching Agent Card from {url}...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            card_data = response.json()
            
            # Display the raw card data
            print("--- Agent Card ---")
            print(f"Name: {card_data.get('name')}")
            print(f"Description: {card_data.get('description')}")
            print(f"Version: {card_data.get('version')}")
            print(f"Capabilities: {card_data.get('capabilities')}")
            print("------------------\n")
            
            return AgentCard.model_validate(card_data)
        except httpx.HTTPError as e:
            print(f"Error fetching agent card: {e}")
            return None

async def invoke_agent(prompt: str):
    """Invoke the agent via A2A protocol."""
    url = AGENT_RPC_URL
    print(f"Invoking Agent at {url} with prompt: '{prompt}'")
    
    message = Message(
        message_id=str(uuid.uuid4()),
        role=Role.user,
        parts=[Part(root=TextPart(text=prompt))],
    )
    request = SendMessageRequest(
        id=str(uuid.uuid4()),
        params=MessageSendParams(message=message),
    )
    payload = request.model_dump(mode="json", exclude_none=True)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            print(f"Response: {data}")
            
            parsed = SendMessageResponse.model_validate(data).root
            if isinstance(parsed, JSONRPCErrorResponse):
                return f"Error invoking agent: {parsed.error.message}"

            result = parsed.result
            if isinstance(result, Message):
                text = get_message_text(result).strip()
                return text or "No response content found."

            if isinstance(result, Task):
                if result.status and result.status.message:
                    text = get_message_text(result.status.message).strip()
                    if text:
                        return text
                if result.history:
                    for msg in reversed(result.history):
                        if msg.role == Role.agent:
                            text = get_message_text(msg).strip()
                            if text:
                                return text
            
            return "No response content found."
            
        except httpx.HTTPError as e:
            return f"Error invoking agent: {e}"

async def main():
    if len(sys.argv) < 2:
        prompt = "Calculate 10 + 20"
    else:
        prompt = " ".join(sys.argv[1:])

    # 1. Get Agent Card (demonstrates A2A discovery)
    card = await get_agent_card()
    
    # 2. Invoke Agent
    result = await invoke_agent(prompt)
    print(f"\nResult from Agent:\n{result}")

if __name__ == "__main__":
    asyncio.run(main())
