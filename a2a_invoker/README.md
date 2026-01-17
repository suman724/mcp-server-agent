# A2A Invoker

This is a simple client application that demonstrates how to invoke the Calculator Agent using the A2A (Agent-to-Agent) protocol over HTTP.

## Setup

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Ensure the Calculator Agent is running (see root Makefile `run-agent-server`).
2.  Run the invoker:
    ```bash
    python main.py "Calculate 5 * 5"
    ```
