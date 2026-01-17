# Calculator Agent

This is an intelligent agent built using Google ADK (Agent Development Kit) concepts and the Model Context Protocol (MCP).

It connects to a remote MCP server (in this case, the `mcp-calculator` server) to perform mathematical operations.

The agent can run in two modes:
1. **CLI Mode**: Run the agent from the command line with a prompt.
2. **A2A Server Mode**: Expose the agent as an HTTP service for agent-to-agent communication.

## Setup

1.  **Install Dependencies**:
    ```bash
    make install-agent
    ```

2.  **Start MCP Server**:
    Ensure the MCP server is running in a separate terminal:
    ```bash
    make server
    ```

## Usage

Run the agent using the `make` command. You can pass environment variables directly.

```bash
make run-agent ARGS="Calculate 5 + 3" API_KEY=your_api_key
```

To use a local model via LiteLLM (for example, Ollama):

```bash
make run-agent ARGS="Calculate 5 + 3" \
  LLM_PROVIDER=litellm \
  LLM_MODEL=ollama/llama3 \
  LLM_API_BASE=http://localhost:11434
```

### Environment Variables

-   `MCP_SERVER_URL`: URL of the MCP server (default: `http://0.0.0.0:8000/mcp/`)
-   `A2A_BASE_URL`: Base URL used in the Agent Card (default: `http://localhost:8001`).
-   `API_KEY`: Google API Key for Gemini (or set `GEMINI_API_KEY`/`GOOGLE_API_KEY`).
-   `LLM_PROVIDER`: `gemini` (default) or `litellm` for local/third-party models.
-   `LLM_MODEL`: Model name to use. For LiteLLM, use `provider/model` (example: `ollama/llama3`).
-   `LLM_API_BASE`: Base URL for LiteLLM providers (example: `http://localhost:11434`).
-   `LLM_API_KEY`: Optional key for LiteLLM providers that require it.
-   `LLM_BASE_URL`: Alias for `LLM_API_BASE` (kept for compatibility).

### Simple Execution Mode (No LLM)

For testing connection without an API Key:

```bash
make run-agent ARGS="simple_exec add 10 20"
```

## A2A Server Mode

You can expose the agent as an HTTP service:

```bash
make run-agent-server
```

This starts a FastAPI server on port 8001 with the following endpoints:

-   **Agent Card**: `GET http://localhost:8001/.well-known/agent-card.json` - Returns the A2A Agent Card.
-   **Invoke Agent**: `POST http://localhost:8001/calculator` - JSON-RPC `message/send` endpoint.

Example JSON-RPC request:
```bash
curl -s http://localhost:8001/calculator \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": "req-1",
    "method": "message/send",
    "params": {
      "message": {
        "message_id": "msg-1",
        "role": "user",
        "parts": [{"kind": "text", "text": "Calculate 5 + 3"}]
      }
    }
  }'
```

See the `a2a_invoker` app for an example client.
