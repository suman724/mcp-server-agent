# Calculator Agent

This is an intelligent agent built using Google ADK (Agent Development Kit) concepts and the Model Context Protocol (MCP).

It connects to a remote MCP server (in this case, the `mcp-calculator` server) to perform mathematical operations.

The agent can run in two modes:
1. **CLI Mode**: Run the agent from the command line with a prompt.
2. **A2A Server Mode**: Expose the agent as an HTTP service for agent-to-agent communication.
- **FastAPI / Starlette Support**: Easily mountable agent server.
- **MCP Tool Integration**: Connects to any MCP server to provide tools to the agent.
- **JWT Authentication**: Secure interaction using OIDC-compliant JWT tokens.
- **Authenticated Tool Discovery**: Supports tool lists via authenticated headers.

Python 3.12+ is required.

## Authentication Architecture

This agent uses a **Caller Token Discovery** pattern to ensure secure and dynamic access to tools.

1.  **Client-Side (Invoker/Client)**:
    - The client obtains an OIDC JWT (e.g., from `MCP_TOKEN` env var).
    - It includes this token in the `Authorization: Bearer <token>` header when making requests to the Agent (both for `agent-card` and invocations).

2.  **Agent Server (`AuthMiddleware`)**:
    - Intercepts every request to `/calculator`.
    - Validates the token against the configured OIDC provider (Issuer/Audience).
    - If valid, stores the token in a `ContextVar` (`token_context`).
    - If invalid/missing, returns `401 Unauthorized`.

3.  **Agent Logic (`McpToolset`)**:
    - When the Agent needs to list tools (for the Agent Card) or call tools (during execution), it needs to authenticate with the backend MCP Server.
    - We use `token_context.get()` to retrieve the caller's token.
    - This token is injected into the MCP Session headers via `McpToolset(header_provider=...)`.

This ensures that the **end-user's identity** is propagated all the way to the backend MCP tools.

## Dynamic Initialization

The agent uses a `DynamicA2AHandler` to manage the lifecycle of the agent application.

**Why?**
1.  **Authentication Context**: The agent needs the caller's JWT (from the request) to list and use tools from the MCP server.
2.  **Startup Reliability**: The Agent Server can start successfully even if the MCP Server is temporarily unavailable, as the connection is established only when a request is received.

**How it works:**
- `DynamicA2AHandler` rebuilds the Agent and Agent Card for **every** request.
- This ensures that the `McpToolset` is initialized with the correct `token_context` for the current user.
- While this adds a small overhead per request (tool listing), it ensures robust security and multi-user support.

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
-   `OIDC_ISSUER`: The OIDC issuer URL for token validation (default: Auth0 dev).
-   `OIDC_AUDIENCE`: The expected audience in the JWT (default: `https://mcp.msgraph.com`).
-   `OIDC_JWKS_URL`: URL to fetch the JSON Web Key Set for signature verification.

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

This starts a Starlette ASGI server on port 8001 with the following endpoints:

-   **Agent Card**: `GET http://localhost:8001/calculator/.well-known/agent-card.json` - Returns the A2A Agent Card.
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
