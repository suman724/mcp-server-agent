# Calculator MCP Server

A basic MCP server that provides calculator tools (add, subtract, multiply, divide).

## Setup

1. Create a virtual environment and install dependencies:
    ```bash
    make venv
    ```

## Running the Server

### HTTP/SSE Mode (default)
The server runs on port 8000 by default using uvicorn.
```bash
make server
# or
python -m mcp_calculator
```
This is useful for development and remote connections.

### Stdio Mode
To run in stdio mode (e.g. for connecting to an MCP client like Claude Desktop), you can use the MCP CLI or run the FastMCP app directly if configured.
Currently, the main entry point runs the HTTP server.
