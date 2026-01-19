# Agents Guide

This repository contains multiple Python apps that work together to demonstrate an MCP calculator server, an agent that calls it, and client/invoker tools.
Each app also has its own `AGENTS.md` with code-derived, app-specific details:
`server/AGENTS.md`, `calculator_agent/AGENTS.md`, `client/AGENTS.md`, `a2a_invoker/AGENTS.md`.

## Repo layout

- `server/`: FastMCP calculator server (tools: add, subtract, multiply, divide).
- `calculator_agent/`: Google ADK-based agent that calls the MCP server; can run CLI or A2A HTTP server.
- `client/`: Minimal MCP client for quick sanity checks.
- `a2a_invoker/`: A2A client that calls the agent over HTTP; includes LangGraph variant.

## Common setup

- Python 3.12+ required.
- Virtualenv and server deps are managed with `uv` via the Makefile.

```bash
make venv
```

## Running apps

Server (port 8000, MCP endpoint `/mcp/`):
```bash
make server
# or
.venv/bin/python -m mcp_calculator
```

Agent CLI (requires MCP server running):
```bash
make install-agent
make run-agent ARGS="Calculate 5 + 3"
```

Agent A2A server (port 8001, requires MCP server running):
```bash
make run-agent-server
```

A2A invoker (requires agent server running):
```bash
make install-invoker
make run-invoker ARGS="Calculate 10 * 5"
# or
.venv/bin/python a2a_invoker/langgraph_invoker.py "Calculate 10 * 5"
```

Client (requires MCP server running):
```bash
cd client
python client.py
```

## Runtime defaults (from code)

- MCP server: `server/mcp_calculator/__main__.py` runs on `0.0.0.0:8000`.
- MCP endpoint: `server/mcp_calculator/app.py` sets `streamable_http_path="/mcp/"`.
- Agent server: `calculator_agent/calculator_agent/server.py` runs on `0.0.0.0:8001` with
  `AGENT_PATH="/calculator"` and adds `/health` and `/health/mcp`.
- Agent config defaults in `calculator_agent/calculator_agent/config.py`:
  - `MCP_SERVER_URL="http://localhost:8000/mcp/"`
  - `A2A_BASE_URL="http://localhost:8001"`
  - `LLM_MODEL="gemini-pro"`
  - `LLM_PROVIDER="gemini"`
  - `LLM_API_BASE` from `LLM_API_BASE` or `LLM_BASE_URL`
  - `LLM_API_KEY` from `LLM_API_KEY` or `OPENAI_API_KEY`
  - `API_KEY` has no default (must be set for Gemini unless `GEMINI_API_KEY`/`GOOGLE_API_KEY` is set)

## Environment variables (agent)

The agent reads these env vars at runtime (see `calculator_agent/calculator_agent/config.py`):

- `MCP_SERVER_URL` (default `http://localhost:8000/mcp/`)
- `A2A_BASE_URL` (default `http://localhost:8001`)
- `API_KEY` (Gemini API key; also used as fallback for LiteLLM if `LLM_API_KEY` is unset)
- `LLM_PROVIDER` (`gemini` or `litellm`)
- `LLM_MODEL` (default `gemini-pro`; for LiteLLM, use `provider/model`)
- `LLM_API_BASE` / `LLM_BASE_URL`
- `LLM_API_KEY` / `OPENAI_API_KEY`

Note: `make run-agent` and `make run-agent-server` set their own defaults in `Makefile`
(LiteLLM provider, model, and API base). Override as needed.

## Tests

```bash
make test        # server tests
make test-agent  # agent tests
```

Invoker tests live in `a2a_invoker/test_invoker.py` and can be run with:
```bash
.venv/bin/pytest a2a_invoker/test_invoker.py -v
```

## Notes for contributors/agents

- Keep changes scoped to the app you are modifying (`server/`, `calculator_agent/`, `client/`, `a2a_invoker/`).
- When touching agent behavior, ensure the MCP server endpoint remains `/mcp/` and ports stay 8000/8001 unless explicitly changed.
- The Makefile is the canonical entry point for common workflows.
