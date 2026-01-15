import os

# MCP Server Configuration
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000/mcp/")

# LLM Configuration
API_KEY = os.environ.get("API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", "gemini-pro")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL")
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "gemini")
LLM_API_BASE = os.environ.get("LLM_API_BASE") or LLM_BASE_URL
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
LLM_API_KEY = os.environ.get("LLM_API_KEY") or OPENAI_API_KEY
