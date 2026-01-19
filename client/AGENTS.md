# Client Notes

This app is a minimal MCP client for quick sanity checks.
See the repo overview in `AGENTS.md`.

## Setup

From this directory:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

Requires MCP server running (`make server` at repo root):
```bash
python client.py
```

## Code-derived details

- `client/client.py` instantiates `MCPClient(base_url="http://localhost:8000/mcp/")`.
- `client/mcp_client.py` posts JSON-RPC to `"{base_url}/"` and expects MCP
  streamable HTTP responses with `Accept: application/json, text/event-stream`.
- The client exercises `add`, `subtract`, `multiply`, `divide` and verifies divide-by-zero error handling.
