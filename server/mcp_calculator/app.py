from mcp.server.fastmcp import FastMCP
from mcp_calculator.tools.calculator import register_calculator_tools

# Initialize FastMCP server
server = FastMCP(
    name="mcp-calculator",
    streamable_http_path="/mcp/",
    stateless_http=True,
    json_response=True,
)

# Register tools
register_calculator_tools(server)

# Expose the FastAPI app
app = server.streamable_http_app()
