
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

DEFAULT_AGENT_BASE_URL = "http://localhost:8001"
DEFAULT_AGENT_PATH = "/calculator"


def _normalize_path(path: str) -> str:
    cleaned = path.strip()
    if not cleaned.startswith("/"):
        cleaned = f"/{cleaned}"
    return cleaned.rstrip("/")


def _agent_base_url(base_url: str, agent_path: str) -> str:
    base = base_url.rstrip("/")
    path = _normalize_path(agent_path)
    return base if base.endswith(path) else f"{base}{path}"


def _resolve_agent_urls() -> tuple[str, str, str, str]:
    base = os.getenv("AGENT_BASE_URL", DEFAULT_AGENT_BASE_URL)
    path = os.getenv("AGENT_PATH", DEFAULT_AGENT_PATH)
    rpc_url = os.getenv("AGENT_RPC_URL")
    if rpc_url:
        rpc_url = rpc_url.rstrip("/")
    else:
        rpc_url = _agent_base_url(base, path)
    card_url = os.getenv("AGENT_CARD_URL")
    if card_url:
        card_url = card_url.rstrip("/")
    else:
        card_url = f"{rpc_url}/.well-known/agent-card.json"
    return base.rstrip("/"), _normalize_path(path), rpc_url, card_url


def _resolve_rpc_url_from_card(card: AgentCard, fallback_url: str) -> str:
    preferred = (card.preferred_transport or "JSONRPC").upper()
    if card.additional_interfaces:
        for iface in card.additional_interfaces:
            if iface.transport and iface.transport.upper() == preferred:
                return iface.url.rstrip("/")
        for iface in card.additional_interfaces:
            if iface.transport and iface.transport.upper() == "JSONRPC":
                return iface.url.rstrip("/")
    if card.url:
        return card.url.rstrip("/")
    return fallback_url.rstrip("/")


def _extract_text_from_parts(parts: list[Part]) -> str:
    texts = []
    for part in parts:
        payload = getattr(part, "root", part)
        text = getattr(payload, "text", None)
        if text:
            texts.append(text)
    return " ".join(texts).strip()


def _ensure_trailing_slash(url: str) -> str:
    return url if url.endswith("/") else f"{url}/"

async def get_agent_card() -> AgentCard | None:
    """Fetch and parse the Agent Card using A2A types."""
    _base, _path, _rpc_url, card_url = _resolve_agent_urls()
    url = card_url
    print(f"Fetching Agent Card from {card_url}...")
    headers = {}
    token = os.getenv("MCP_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(card_url, headers=headers)
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

async def invoke_agent(prompt: str, rpc_url: str | None = None):
    """Invoke the agent via A2A protocol."""
    _base, _path, fallback_url, _card_url = _resolve_agent_urls()
    url = _ensure_trailing_slash(rpc_url or fallback_url)
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
    
    headers = {}
    token = os.getenv("MCP_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    else:
        print("Warning: MCP_TOKEN not set. Invocation may fail.")

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
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
                if result.artifacts:
                    for artifact in reversed(result.artifacts):
                        text = _extract_text_from_parts(artifact.parts)
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
    _base, _path, fallback_url, _card_url = _resolve_agent_urls()
    rpc_url = fallback_url
    if card:
        rpc_url = _resolve_rpc_url_from_card(card, fallback_url)
    
    # 2. Invoke Agent
    result = await invoke_agent(prompt, rpc_url=rpc_url)
    print(f"\nResult from Agent:\n{result}")

if __name__ == "__main__":
    asyncio.run(main())
