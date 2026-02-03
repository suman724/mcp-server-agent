import asyncio
import logging
from mcp.types import ListToolsResult
from google.adk.tools.mcp_tool.mcp_tool import MCPTool
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

logger = logging.getLogger(__name__)

def apply_patches():
    """Applies monkey patches to fix upstream issues."""
    logger.info("Applying McpToolset monkey patch...")
    McpToolset.get_tools = _get_tools_patched

# ------------------------------------------------------------------------------
# Monkey Patch: McpToolset.get_tools
# ------------------------------------------------------------------------------
# The default implementation of McpToolset.get_tools only invokes the header_provider
# if a readonly_context is provided. However, the AgentCardBuilder calls canonical_tools()
# with a None context, causing the auth headers to be skipped.
# We patch it to always call header_provider if available.

async def _get_tools_patched(
      self,
      readonly_context = None,
  ) -> list:
    
    # PATCH: Always call header_provider if it exists, regardless of context
    headers = (
        self._header_provider(readonly_context)
        if self._header_provider
        else None
    )

    # Get session from session manager
    session = await self._mcp_session_manager.create_session(headers=headers)

    # Fetch available tools from the MCP server
    timeout_in_seconds = (
        self._connection_params.timeout
        if hasattr(self._connection_params, "timeout")
        else None
    )
    try:
      tools_response = await asyncio.wait_for(
          session.list_tools(), timeout=timeout_in_seconds
      )
    except Exception as e:
      raise ConnectionError("Failed to get tools from MCP server.") from e

    # Apply filtering based on context and tool_filter
    tools = []
    for tool in tools_response.tools:
      mcp_tool = MCPTool(
          mcp_tool=tool,
          mcp_session_manager=self._mcp_session_manager,
          auth_scheme=self._auth_scheme,
          auth_credential=self._auth_credential,
          require_confirmation=self._require_confirmation,
          header_provider=self._header_provider,
      )

      if self._is_tool_selected(mcp_tool, readonly_context):
        tools.append(mcp_tool)
    return tools
