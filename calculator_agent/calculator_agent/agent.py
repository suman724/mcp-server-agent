import logging
import os
from google.adk import Agent
from google.adk.models import Gemini
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StreamableHTTPConnectionParams,
)
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

from . import config
from .patches import apply_patches
from .context import token_context

# Apply monkey patches at import time
apply_patches()

logger = logging.getLogger(__name__)


class AgentError(Exception):
    """Base exception for agent errors."""
    pass


def _use_litellm(llm_provider: str | None, llm_api_base: str | None, model_name: str | None) -> bool:
    if llm_provider:
        provider = llm_provider.strip().lower()
        if provider in {"litellm", "local", "ollama"}:
            return True
        if provider in {"gemini", "google"}:
            return False
    if llm_api_base:
        return True
    if model_name and "/" in model_name:
        return True
    return False


def _build_model():
    """Builds the AI model based on configuration."""
    api_key = config.API_KEY
    model_name = config.LLM_MODEL
    llm_provider = config.LLM_PROVIDER
    llm_api_base = config.LLM_API_BASE
    llm_api_key = config.LLM_API_KEY

    if _use_litellm(llm_provider, llm_api_base, model_name):
        try:
            from google.adk.models.lite_llm import LiteLlm
        except Exception as e:
            raise AgentError(
                "LiteLlm import failed. Details: {e}"
            ) from e
        
        kwargs = {}
        if llm_api_base:
            kwargs["api_base"] = llm_api_base
        
        # Fallback to main API_KEY if LLM_API_KEY is missing
        final_api_key = llm_api_key
        if not final_api_key and api_key:
            logger.warning("LLM_API_KEY not set; falling back to API_KEY for LiteLLM.")
            final_api_key = api_key
            
        if final_api_key:
            kwargs["api_key"] = final_api_key
            os.environ.setdefault("OPENAI_API_KEY", final_api_key)
            logger.info("Using custom LLM API key for LiteLLM.")
            
        return LiteLlm(model=model_name, **kwargs)

    # Default to Gemini
    if api_key:
        os.environ.setdefault("GEMINI_API_KEY", api_key)
        os.environ.setdefault("GOOGLE_API_KEY", api_key)
    elif not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
        logger.warning("API_KEY not set for Gemini.")
        
    return Gemini(model=model_name)


def _get_auth_headers():
    """Retrieves auth token from context and formats header."""
    token = token_context.get()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def build_adk_agent() -> Agent:
    """Builds the ADK Agent with MCP tools and configured model."""
    model = _build_model()
    
    connection_params = StreamableHTTPConnectionParams(
        url=config.MCP_SERVER_URL,
        terminate_on_close=False,
    )
    
    toolset = McpToolset(
        connection_params=connection_params,
        header_provider=lambda _: _get_auth_headers(),
    )
    
    return Agent(
        name="calculator_agent",
        description="Calculator agent backed by MCP tools.",
        model=model,
        tools=[toolset],
    )
