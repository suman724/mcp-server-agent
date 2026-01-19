# Server Agent Notes

This app exposes the MCP calculator tools over HTTP/SSE.
See the repo overview in `AGENTS.md`.

## Run

From repo root:
```bash
make server
# or
.venv/bin/python -m mcp_calculator
```

Default endpoint: `http://localhost:8000/mcp/` (from `server/mcp_calculator/app.py`).

## Code-derived details

- Server entry point: `server/mcp_calculator/__main__.py` runs Uvicorn on `0.0.0.0:8000`.
- MCP app config: `server/mcp_calculator/app.py` uses `streamable_http_path="/mcp/"`,
  `stateless_http=True`, and `json_response=True`.
- Tools are registered in `server/mcp_calculator/tools/calculator.py`:
  `add`, `subtract`, `multiply`, `divide` (divide raises on `b == 0`).

## Tests

From repo root:
```bash
make test
```

## Tips

- Keep tool names and MCP path stable unless the change is coordinated with the agent/client.
