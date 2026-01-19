# A2A Invoker Notes

This app calls the Calculator Agent via A2A over HTTP.
See the repo overview in `AGENTS.md`.

## Setup

From this directory:
```bash
pip install -r requirements.txt
```

## Run

Requires the agent server running (`make run-agent-server` at repo root):
```bash
python main.py "Calculate 5 * 5"
```

LangGraph variant:
```bash
python langgraph_invoker.py "Calculate 5 * 5"
```

## Tests

From repo root:
```bash
.venv/bin/pytest a2a_invoker/test_invoker.py -v
```

## Code-derived details

- Defaults in `a2a_invoker/main.py`:
  `AGENT_BASE_URL="http://localhost:8001"`, `AGENT_PATH="/calculator"`.
- Optional overrides: `AGENT_RPC_URL` and `AGENT_CARD_URL`.
- Agent Card URL defaults to `"{rpc_url}/.well-known/agent-card.json"` if not set.
- The invoker selects the preferred RPC URL from the Agent Card when available,
  then posts JSON-RPC `message/send` to the RPC endpoint.
- `langgraph_invoker.py` uses the same env vars and discovery pattern with LangGraph.
