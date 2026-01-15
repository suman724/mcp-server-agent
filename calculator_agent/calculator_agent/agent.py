import logging
import os
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from google.adk import Agent
from google.adk.apps.app import App
from google.adk.models import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.utils.context_utils import Aclosing
from google.genai import types

from . import config

logger = logging.getLogger(__name__)

class AgentError(Exception):
    """Base exception for agent errors."""
    pass

def _format_exception_group(exc: BaseExceptionGroup) -> str:
    lines = []

    def walk(group: BaseExceptionGroup, prefix: str) -> None:
        for index, sub in enumerate(group.exceptions, 1):
            if isinstance(sub, BaseExceptionGroup):
                lines.append(f"{prefix}Group {index}: {sub.__class__.__name__}: {sub}")
                walk(sub, prefix + "  ")
            else:
                lines.append(f"{prefix}Exception {index}: {sub.__class__.__name__}: {sub}")

    walk(exc, "")
    return "\n".join(lines)

class CalculatorAgent:
    def __init__(self):
        self.api_key = config.API_KEY
        self.model_name = config.LLM_MODEL
        self.mcp_url = config.MCP_SERVER_URL
        self.llm_provider = config.LLM_PROVIDER
        self.llm_api_base = config.LLM_API_BASE
        self.llm_api_key = config.LLM_API_KEY

    def _use_litellm(self) -> bool:
        if self.llm_provider:
            provider = self.llm_provider.strip().lower()
            if provider in {"litellm", "local", "ollama"}:
                return True
            if provider in {"gemini", "google"}:
                return False
        if self.llm_api_base:
            return True
        if self.model_name and "/" in self.model_name:
            return True
        return False

    def _build_model(self):
        if self._use_litellm():
            # if not self.model_name or "/" not in self.model_name:
            #     raise AgentError(
            #         "LLM_MODEL must be in provider/model format for LiteLLM "
            #         "(example: 'ollama/llama3')."
            #     )
            try:
                from google.adk.models.lite_llm import LiteLlm
            except Exception as e:
                raise AgentError(
                    "LiteLlm import failed. This usually means a native "
                    "dependency (like `tokenizers` or `tiktoken`) is missing "
                    f"or the wrong architecture is installed. Details: {e}"
                ) from e
            kwargs = {}
            if self.llm_api_base:
                kwargs["api_base"] = self.llm_api_base
            api_key = self.llm_api_key
            if not api_key and self.api_key:
                logger.warning(
                    "LLM_API_KEY not set; falling back to API_KEY for LiteLLM."
                )
                api_key = self.api_key
            if api_key:
                kwargs["api_key"] = api_key
                os.environ.setdefault("OPENAI_API_KEY", api_key)
                logger.info("Using custom LLM API key for LiteLLM.")
            return LiteLlm(model=self.model_name, **kwargs)

        if self.api_key:
            os.environ.setdefault("GEMINI_API_KEY", self.api_key)
            os.environ.setdefault("GOOGLE_API_KEY", self.api_key)
        elif not (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")):
            logger.warning(
                "API_KEY not set; set API_KEY or GEMINI_API_KEY/GOOGLE_API_KEY "
                "to use Gemini."
            )
        return Gemini(model=self.model_name)
        
    async def run(self, user_prompt: str):
        logger.info(f"Agent received task: {user_prompt}")
        
        try:
            logger.info(f"Connecting to MCP Server at {self.mcp_url} (Streamable HTTP)")
            
            async with streamable_http_client(self.mcp_url) as streams:
                async with ClientSession(streams[0], streams[1]) as mcp_session:
                    await mcp_session.initialize()
                    
                    tools = await mcp_session.list_tools()
                    logger.info(f"Connected. Available tools: {[t.name for t in tools.tools]}")
                    
                    # Create ADK-compatible tools
                    adk_tools = []
                    for t in tools.tools:
                        # Define a closure for the tool
                        # Note: We assume calculator tools take 'a' and 'b'.
                        # For a generic agent, we would need dynamic signature generation.
                        async def dynamic_tool(a: float, b: float, _name=t.name) -> float:
                            logger.info(f"Calling MCP tool {_name} with a={a}, b={b}")
                            result = await mcp_session.call_tool(_name, arguments={"a": a, "b": b})
                            # Extract text content
                            if result.content and hasattr(result.content[0], "text"):
                                return float(result.content[0].text)
                            return str(result)
                        
                        dynamic_tool.__name__ = t.name
                        dynamic_tool.__doc__ = t.description
                        adk_tools.append(dynamic_tool)

                    # Initialize ADK components
                    model = self._build_model()
                    agent = Agent(
                        name="calculator_agent",
                        description="Calculator agent backed by MCP tools.",
                        model=model,
                        tools=adk_tools,
                    )

                    logger.info("Running ADK Agent loop...")
                    app = App(name="calculator_agent_app", root_agent=agent)
                    async with InMemoryRunner(app=app) as runner:
                        adk_session = await runner.session_service.create_session(
                            app_name=runner.app_name,
                            user_id="local-user",
                        )
                        content = types.Content(
                            role="user",
                            parts=[types.Part(text=user_prompt)],
                        )

                        result_text = None
                        async with Aclosing(
                            runner.run_async(
                                user_id=adk_session.user_id,
                                session_id=adk_session.id,
                                new_message=content,
                            )
                        ) as agen:
                            async for event in agen:
                                if event.author != agent.name:
                                    continue
                                if not event.content or not event.content.parts:
                                    continue
                                text = "".join(
                                    part.text or "" for part in event.content.parts
                                )
                                if not text:
                                    continue
                                if event.is_final_response():
                                    result_text = text
                                elif result_text is None:
                                    result_text = text

                    if result_text is None:
                        return "No response from agent."
                    logger.info(f"ADK Agent finished. Result: {result_text}")
                    return result_text

        except Exception as e:
            if "Connection refused" in str(e):
                 raise AgentError(f"Connection refused to {self.mcp_url}. Is the server running?") from e
            if isinstance(e, BaseExceptionGroup):
                details = _format_exception_group(e)
                raise AgentError(
                    "Error during agent execution (exception group):\n"
                    f"{details}"
                ) from e
            raise AgentError(f"Error during agent execution: {e}") from e

    async def run_simple_eval(self, expression: str):
        """
        A direct tool usage example without LLM.
        """
        try:
            async with streamable_http_client(self.mcp_url) as streams:
                 async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    parts = expression.split()
                    if len(parts) >= 3:
                         tool_name = parts[0]
                         try:
                             a = float(parts[1])
                             b = float(parts[2])
                             result = await session.call_tool(tool_name, arguments={"a": a, "b": b})
                             return result
                         except Exception as e:
                             return f"Error executing tool: {e}"
                    return "Could not parse simple command."
        except Exception as e:
             return f"Error: {e}"
