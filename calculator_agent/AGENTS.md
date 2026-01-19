# Calculator Agent Notes

This app is a Google ADK-based agent that calls the MCP server.
See the repo overview in `AGENTS.md`.

## Run (CLI)

From repo root:
```bash
make install-agent
make run-agent ARGS="Calculate 5 + 3"
```

## Run (A2A server)

From repo root (MCP server must be running):
```bash
make run-agent-server
```

A2A endpoints (from `calculator_agent/calculator_agent/server.py`):
- Agent Card: `GET http://localhost:8001/calculator/.well-known/agent-card.json`
- Agent Card alias: `GET http://localhost:8001/.well-known/agent-card.json`
- Agent Card alias: `GET http://localhost:8001/calculator/info`
- Invoke: `POST http://localhost:8001/calculator`
- Health: `GET http://localhost:8001/health`
- MCP health: `GET http://localhost:8001/health/mcp`

## Code-derived behavior

- Server binds to `0.0.0.0:8001` with `AGENT_PATH="/calculator"` (`calculator_agent/calculator_agent/server.py`).
- A2A app initialization is lazy and returns `503` if initialization fails on first request.
- CLI supports a hidden "simple_exec" mode: `simple_exec add 5 10`
  (see `calculator_agent/calculator_agent/main.py`).
- LiteLLM is used when `LLM_PROVIDER` is `litellm`, `local`, or `ollama`, or when
  `LLM_API_BASE` is set, or when `LLM_MODEL` contains `/` (`calculator_agent/calculator_agent/agent.py`).

## Environment variables (from code defaults)

- `MCP_SERVER_URL` (default `http://localhost:8000/mcp/`)
- `A2A_BASE_URL` (default `http://localhost:8001`)
- `API_KEY` (Gemini API key; fallback for LiteLLM)
- `LLM_PROVIDER` (`gemini` default; LiteLLM triggers are in `agent.py`)
- `LLM_MODEL` (default `gemini-pro`; for LiteLLM, use `provider/model`)
- `LLM_API_BASE` / `LLM_BASE_URL`
- `LLM_API_KEY` / `OPENAI_API_KEY`

## Tests

From repo root:
```bash
make test-agent
```

## Tips

- Keep MCP endpoint path as `/mcp/` unless server changes are coordinated.
