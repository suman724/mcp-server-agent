import asyncio
import logging

import uvicorn
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from contextvars import ContextVar
from .auth import TokenVerifier
from .context import token_context

class AuthMiddleware:
    def __init__(self, app):
        self.app = app
        self.verifier = TokenVerifier()

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Create a lightweight Request wrapper to access headers easily
        request = Request(scope)

        # Protect all calculator endpoints including agent card
        if request.url.path.startswith("/calculator"):
            try:
                # verify_request returns the token string if successful
                token = await self.verifier.verify_request(request)
                token_context.set(token)
            except ValueError as e:
                logger.error(f"Auth failed: {e}")
                response = JSONResponse({"error": str(e)}, status_code=401)
                await response(scope, receive, send)
                return
        
        await self.app(scope, receive, send)

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



# ------------------------------------------------------------------------------
# Dynamic Application Handler
# ------------------------------------------------------------------------------
class DynamicA2AHandler:
    """
    Dynamically builds and routes the A2A application for each request.
    
    This approach ensures that the Agent (and its underlying McpToolset)
    is initialized within the context of the current request, allowing it
    to access the request-scoped 'token_context' for authentication.
    """
    def __init__(self, agent_url: str):
        self._agent_url = agent_url

    async def _build_app_and_card(self):
        # Build the agent (Model + Tools)
        # The McpToolset inside will look at the current token_context
        # when it streams tools in the next steps.
        agent = build_adk_agent()
        
        # Build the Agent Card
        # This triggers a 'list_tools' call to the MCP server, which requires
        # the token from token_context.
        agent_card = await _build_agent_card(agent, self._agent_url)
        
        # Create the A2A app wrapper
        app = to_a2a(agent, agent_card=agent_card)
        
        # Ensure the router is started (if needed, though to_a2a usually handles this)
        if hasattr(app.router, "startup"):
             await app.router.startup()
             
        return app, agent_card

    async def __call__(self, scope, receive, send):
        try:
            app, _ = await self._build_app_and_card()
            await app(scope, receive, send)
        except Exception as exc:
            logger.exception("Failed to initialize dynamic A2A app", exc_info=exc)
            response = JSONResponse(
                {"error": "Dynamic app initialization failed", "detail": str(exc)},
                status_code=503,
            )
            await response(scope, receive, send)

    async def get_agent_card(self) -> AgentCard:
        _, card = await self._build_app_and_card()
        return card


def _agent_card_handler(dynamic_handler: DynamicA2AHandler):
    async def handler(_request):
        try:
            card = await dynamic_handler.get_agent_card()
            return JSONResponse(card.model_dump(mode="json", exclude_none=True))
        except Exception as exc:
            logger.error(f"Failed to fetch agent card: {exc}")
            return JSONResponse(
                 {"error": "Failed to fetch agent card", "detail": str(exc)},
                 status_code=503
            )
    return handler


async def _mcp_health_check(_request):
    try:
        # Note: This health check currently bypasses auth (no token context).
        # Typically health checks should use a dedicated service token or 
        # allow unauthenticated ping. For now, it might fail 401.
        async with streamable_http_client(
            MCP_SERVER_URL, terminate_on_close=False
        ) as (read, write, _get_session_id):
            async with ClientSession(read, write) as session:
                try:
                    await asyncio.wait_for(session.initialize(), timeout=3.0)
                except Exception:
                     # Ignore init errors (like 401) for health check connectivity
                     pass
        return JSONResponse({"status": "ok", "mcp_url": MCP_SERVER_URL})
    except Exception as exc:
        logger.exception("MCP connectivity check failed", exc_info=exc)
        return JSONResponse(
            {"status": "error", "mcp_url": MCP_SERVER_URL, "detail": str(exc)},
            status_code=503,
        )


def create_app() -> Starlette:
    agent_url = _agent_base_url(A2A_BASE_URL)
    dynamic_handler = DynamicA2AHandler(agent_url)
    
    app = Starlette(
        routes=[
            Mount(AGENT_PATH, app=dynamic_handler, name="a2a_agent"),
            Route("/.well-known/agent-card.json", _agent_card_handler(dynamic_handler)),
            # Route("/calculator/info", _agent_card_handler(dynamic_handler)), # Optional alias
            Route("/health", lambda _: JSONResponse({"status": "ok"})),
            Route("/health/mcp", _mcp_health_check),
        ],
    )
    app.add_middleware(AuthMiddleware)
    return app


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
