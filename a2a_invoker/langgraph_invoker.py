import asyncio
import os
import uuid
from typing import TypedDict

import httpx
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
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, StateGraph

DEFAULT_AGENT_BASE_URL = "http://localhost:8001"
DEFAULT_AGENT_PATH = "/calculator"


class A2AState(TypedDict, total=False):
    prompt: str
    rpc_url: str
    result: str
    error: str


def _normalize_path(path: str) -> str:
    cleaned = path.strip()
    if not cleaned.startswith("/"):
        cleaned = f"/{cleaned}"
    return cleaned.rstrip("/")


def _ensure_trailing_slash(url: str) -> str:
    return url if url.endswith("/") else f"{url}/"


def _resolve_urls() -> tuple[str, str]:
    base = os.getenv("AGENT_BASE_URL", DEFAULT_AGENT_BASE_URL).rstrip("/")
    path = _normalize_path(os.getenv("AGENT_PATH", DEFAULT_AGENT_PATH))
    rpc_url = os.getenv("AGENT_RPC_URL")
    if rpc_url:
        rpc_url = _ensure_trailing_slash(rpc_url.strip())
    else:
        rpc_url = _ensure_trailing_slash(f"{base}{path}")
    card_url = os.getenv("AGENT_CARD_URL")
    if card_url:
        card_url = card_url.rstrip("/")
    else:
        card_url = f"{rpc_url}.well-known/agent-card.json"
    return rpc_url, card_url


def _resolve_rpc_url_from_card(card: AgentCard, fallback_url: str) -> str:
    preferred = (card.preferred_transport or "JSONRPC").upper()
    if card.additional_interfaces:
        for iface in card.additional_interfaces:
            if iface.transport and iface.transport.upper() == preferred:
                return _ensure_trailing_slash(iface.url.rstrip("/"))
        for iface in card.additional_interfaces:
            if iface.transport and iface.transport.upper() == "JSONRPC":
                return _ensure_trailing_slash(iface.url.rstrip("/"))
    if card.url:
        return _ensure_trailing_slash(card.url.rstrip("/"))
    return _ensure_trailing_slash(fallback_url.rstrip("/"))


def _extract_text_from_parts(parts: list[Part]) -> str:
    texts = []
    for part in parts:
        payload = getattr(part, "root", part)
        text = getattr(payload, "text", None)
        if text:
            texts.append(text)
    return " ".join(texts).strip()


async def _discover_agent(state: A2AState) -> A2AState:
    rpc_url, card_url = _resolve_urls()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(card_url)
            response.raise_for_status()
            card = AgentCard.model_validate(response.json())
        rpc_url = _resolve_rpc_url_from_card(card, rpc_url)
        return {**state, "rpc_url": rpc_url}
    except httpx.HTTPError as exc:
        return {**state, "rpc_url": rpc_url, "error": f"Agent card error: {exc}"}


async def _invoke_agent(state: A2AState) -> A2AState:
    rpc_url = _ensure_trailing_slash(state.get("rpc_url") or _resolve_urls()[0])
    message = Message(
        message_id=str(uuid.uuid4()),
        role=Role.user,
        parts=[Part(root=TextPart(text=state["prompt"]))],
    )
    request = SendMessageRequest(
        id=str(uuid.uuid4()),
        params=MessageSendParams(message=message),
    )
    payload = request.model_dump(mode="json", exclude_none=True)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(rpc_url, json=payload)
            response.raise_for_status()
            parsed = SendMessageResponse.model_validate(response.json()).root
    except httpx.HTTPError as exc:
        return {**state, "error": f"Error invoking agent: {exc}"}

    if isinstance(parsed, JSONRPCErrorResponse):
        return {**state, "error": f"Error invoking agent: {parsed.error.message}"}

    result = parsed.result
    if isinstance(result, Message):
        text = get_message_text(result).strip()
        return {**state, "result": text or "No response content found."}

    if isinstance(result, Task):
        if result.status and result.status.message:
            text = get_message_text(result.status.message).strip()
            if text:
                return {**state, "result": text}
        if result.history:
            for msg in reversed(result.history):
                if msg.role == Role.agent:
                    text = get_message_text(msg).strip()
                    if text:
                        return {**state, "result": text}
        if result.artifacts:
            for artifact in reversed(result.artifacts):
                text = _extract_text_from_parts(artifact.parts)
                if text:
                    return {**state, "result": text}
        return {**state, "result": "No response content found."}

    return {**state, "result": "No response content found."}


def _build_graph():
    graph = StateGraph(A2AState)
    graph.add_node("discover", RunnableLambda(_discover_agent))
    graph.add_node("invoke", RunnableLambda(_invoke_agent))
    graph.set_entry_point("discover")
    graph.add_edge("discover", "invoke")
    graph.add_edge("invoke", END)
    return graph.compile()


async def main():
    prompt = "Calculate 10 + 20"
    if len(os.sys.argv) > 1:
        prompt = " ".join(os.sys.argv[1:])

    graph = _build_graph()
    result = await graph.ainvoke({"prompt": prompt})
    if result.get("error"):
        print(result["error"])
        return
    print(result.get("result", "No response content found."))


if __name__ == "__main__":
    asyncio.run(main())
