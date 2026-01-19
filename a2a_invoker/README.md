# A2A Invoker

This client application demonstrates how to invoke the Calculator Agent using the A2A (Agent-to-Agent) protocol. It uses `httpx` for HTTP communication and leverages Google's `a2a-sdk` types for Agent Card and JSON-RPC validation.

## Setup

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    For the LangGraph variant:
    ```bash
    pip install -r requirements-langgraph.txt
    ```

## Usage

1.  Ensure the Calculator Agent is running (see root Makefile `run-agent-server`).
2.  Run the invoker:
    ```bash
    python main.py "Calculate 5 * 5"
    ```

## LangGraph Invoker

This variant uses LangGraph and LangChain primitives to discover the Agent Card
and invoke the A2A endpoint.

```bash
pip install -r requirements-langgraph.txt
python langgraph_invoker.py "Calculate 5 * 5"
```

## How It Works

The invoker uses a hybrid approach:
1. **HTTP Communication**: Uses `httpx` for simple, direct HTTP calls to the A2A endpoints
2. **Type Safety**: Leverages `a2a-sdk` types (like `AgentCard`) for proper A2A data structure handling
3. **A2A Protocol**: Follows the standard A2A message format for requests and responses

Workflow:
1. Fetches the Agent Card from `/calculator/.well-known/agent-card.json` to discover agent capabilities
2. Sends a JSON-RPC `message/send` request to `/calculator`
3. Receives and displays the agent's response

This demonstrates a pragmatic approach to A2A: using standard HTTP clients with proper A2A type validation.
