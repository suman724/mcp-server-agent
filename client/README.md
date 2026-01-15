# MCP Client App

A simple Python client to interact with the Calculator MCP Server.

## Setup

1. Create a virtual environment (optional, but recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Ensure you have `mcp[cli]` or `mcp` installed if using the SDK helper.* 
   Actually, `requirements.txt` should include `mcp`.

## Usage

1. Ensure the MCP Server is running (see root README).
   ```bash
   # From root
   make server
   ```

2. Run the client:
   ```bash
   python client.py
   ```
