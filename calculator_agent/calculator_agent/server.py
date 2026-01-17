import asyncio
import logging

import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from a2a.types import AgentCard
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from .agent import build_adk_agent
from .config import A2A_BASE_URL, MCP_SERVER_URL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("calculator_server")

AGENT_PATH = "/calculator"
AGENT_NAME = "Calculator Agent"
AGENT_VERSION = "0.1.0"
AGENT_DESCRIPTION = (
    "An intelligent agent that performs mathematical operations "
    "using an MCP calculator server."
)


def _agent_base_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    return base if base.endswith(AGENT_PATH) else f"{base}{AGENT_PATH}"


async def _build_agent_card(agent, agent_url: str) -> AgentCard:
    builder = AgentCardBuilder(
        agent=agent,
        rpc_url=agent_url,
        agent_version=AGENT_VERSION,
    )
    card = await builder.build()
    return card.model_copy(
        update={
            "name": AGENT_NAME,
            "description": AGENT_DESCRIPTION,
            "version": AGENT_VERSION,
            "url": agent_url,
        },
    )


class LazyA2AApp:
    def __init__(self, agent, agent_url: str):
        self._agent = agent
        self._agent_url = agent_url
        self._app = None
        self._agent_card = None
        self._lock = asyncio.Lock()

    async def _ensure_app(self):
        if self._app is not None:
            return self._app
        async with self._lock:
            if self._app is not None:
                return self._app
            self._agent_card = await _build_agent_card(
                self._agent,
                self._agent_url,
            )
            app = to_a2a(self._agent, agent_card=self._agent_card)
            await app.router.startup()
            self._app = app
            return app

    async def get_agent_card(self) -> AgentCard:
        await self._ensure_app()
        return self._agent_card

    async def __call__(self, scope, receive, send):
        try:
            app = await self._ensure_app()
        except Exception as exc:
            logger.exception("Failed to initialize A2A app", exc_info=exc)
            response = JSONResponse(
                {"error": "A2A app initialization failed", "detail": str(exc)},
                status_code=503,
            )
            await response(scope, receive, send)
            return
        await app(scope, receive, send)


def _agent_card_alias(lazy_app: LazyA2AApp):
    async def handler(_request):
        card = await lazy_app.get_agent_card()
        return JSONResponse(card.model_dump(mode="json", exclude_none=True))

    return handler


async def _health_check(_request):
    return JSONResponse({"status": "ok"})


async def _mcp_health_check(_request):
    try:
        async with streamable_http_client(
            MCP_SERVER_URL, terminate_on_close=False
        ) as (read, write, _get_session_id):
            async with ClientSession(read, write) as session:
                await asyncio.wait_for(session.initialize(), timeout=3.0)
        return JSONResponse({"status": "ok", "mcp_url": MCP_SERVER_URL})
    except Exception as exc:
        logger.exception("MCP health check failed", exc_info=exc)
        return JSONResponse(
            {"status": "error", "mcp_url": MCP_SERVER_URL, "detail": str(exc)},
            status_code=503,
        )


def create_app() -> Starlette:
    agent_url = _agent_base_url(A2A_BASE_URL)
    lazy_app = LazyA2AApp(build_adk_agent(), agent_url)
    return Starlette(
        routes=[
            Mount(AGENT_PATH, app=lazy_app, name="a2a_agent"),
            Route("/.well-known/agent-card.json", _agent_card_alias(lazy_app)),
            Route("/calculator/info", _agent_card_alias(lazy_app)),
            Route("/health", _health_check),
            Route("/health/mcp", _mcp_health_check),
        ],
    )


app = create_app()


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
