
import asyncio
import httpx
import sys
import json
import os

# Configuration
AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8001/calculator")
AGENT_INFO_URL = os.getenv("AGENT_INFO_URL", "http://localhost:8001/calculator/info")

async def get_agent_card():
    print(f"Fetching Agent Card from {AGENT_INFO_URL}...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(AGENT_INFO_URL)
            response.raise_for_status()
            card = response.json()
            print("--- Agent Card ---")
            print(json.dumps(card, indent=2))
            print("------------------")
            return card
        except httpx.HTTPError as e:
            print(f"Error fetching agent card: {e}")
            return None

async def invoke_agent(prompt: str):
    print(f"Invoking Agent at {AGENT_URL} with prompt: '{prompt}'")
    
    payload = {
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(AGENT_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Extract assistant response
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

    # 1. Get Info
    await get_agent_card()
    
    # 2. Invoke
    result = await invoke_agent(prompt)
    print(f"\nResult from Agent:\n{result}")

if __name__ == "__main__":
    asyncio.run(main())
