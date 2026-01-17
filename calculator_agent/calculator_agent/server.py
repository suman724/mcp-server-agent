import asyncio
import logging

import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from a2a.types import AgentCard
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from .agent import build_adk_agent
from .config import A2A_BASE_URL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("calculator_server")

AGENT_PATH = "/calculator"


def _agent_base_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    return base if base.endswith(AGENT_PATH) else f"{base}{AGENT_PATH}"


def _build_agent_card(agent) -> AgentCard:
    agent_url = _agent_base_url(A2A_BASE_URL)
    builder = AgentCardBuilder(
        agent=agent,
        rpc_url=agent_url,
        agent_version="0.1.0",
    )
    card = asyncio.run(builder.build())
    return card.model_copy(
        update={
            "name": "Calculator Agent",
            "description": (
                "An intelligent agent that performs mathematical operations "
                "using an MCP calculator server."
            ),
            "version": "0.1.0",
            "url": agent_url,
        }
    )


root_agent = build_adk_agent()
agent_card = _build_agent_card(root_agent)
a2a_app = to_a2a(root_agent, agent_card=agent_card)


async def _agent_card_alias(_request):
    return JSONResponse(agent_card.model_dump(mode="json", exclude_none=True))


async def _health_check(_request):
    return JSONResponse({"status": "ok"})


app = Starlette(
    routes=[
        Mount(AGENT_PATH, app=a2a_app, name="a2a_agent"),
        Route("/.well-known/agent-card.json", _agent_card_alias),
        Route("/calculator/info", _agent_card_alias),
        Route("/health", _health_check),
    ],
)


def start():
    """Entry point for running the server programmatically."""
    uvicorn.run(
        "calculator_agent.server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )


if __name__ == "__main__":
    start()
