
import asyncio
import httpx
import sys
import json
import os
from a2a.types import AgentCard

# Configuration
AGENT_BASE_URL = os.getenv("AGENT_BASE_URL", "http://localhost:8001")
AGENT_PATH = os.getenv("AGENT_PATH", "/calculator")

async def get_agent_card() -> AgentCard:
    """Fetch and parse the Agent Card using A2A types."""
    url = f"{AGENT_BASE_URL}{AGENT_PATH}/info"
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
            
            return card_data
        except httpx.HTTPError as e:
            print(f"Error fetching agent card: {e}")
            return None

async def invoke_agent(prompt: str):
    """Invoke the agent via A2A protocol."""
    url = f"{AGENT_BASE_URL}{AGENT_PATH}"
    print(f"Invoking Agent at {url} with prompt: '{prompt}'")
    
    # A2A standard message format
    payload = {
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extract assistant response from A2A format
            messages = data.get("messages", [])
            for msg in messages:
                if msg.get("role") == "assistant":
                    return msg.get("content")
            
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
