.PHONY: venv server test install-agent install-invoker run-agent test-agent


venv:
	uv venv .venv
	uv pip install -e "server/[dev]"

server:
	.venv/bin/python -m mcp_calculator

test:
	.venv/bin/pytest server/tests

install-agent:
	uv pip install -e "calculator_agent[dev]"


#make run-agent ARGS="what is the sum of 5 and 10"

run-agent:
	@MCP_SERVER_URL=$${MCP_SERVER_URL:-http://localhost:8000/mcp/} \
	API_KEY=$${API_KEY:-MISSING} \
	LLM_PROVIDER=$${LLM_PROVIDER:-litellm} \
	LLM_MODEL=$${LLM_MODEL:-openai/qwen3-4b-instruct} \
	LLM_API_BASE=$${LLM_API_BASE:-http://saispark:30090/v1} \
	LLM_API_KEY=$${LLM_API_KEY:-MISSING} \
	PYTHONPATH=. .venv/bin/python -m calculator_agent.main $(ARGS)

test-agent:
	.venv/bin/pytest calculator_agent/tests

run-agent-server:
	@MCP_SERVER_URL=$${MCP_SERVER_URL:-http://localhost:8000/mcp/} \
	API_KEY=$${API_KEY:-MISSING} \
	LLM_PROVIDER=$${LLM_PROVIDER:-litellm} \
	LLM_MODEL=$${LLM_MODEL:-openai/qwen3-4b-instruct} \
	LLM_API_BASE=$${LLM_API_BASE:-http://saispark:30090/v1} \
	LLM_API_KEY=$${LLM_API_KEY:-MISSING} \
	PYTHONPATH=. .venv/bin/python -m calculator_agent.server

run-invoker:
	@cd a2a_invoker && ../.venv/bin/python main.py $(ARGS)

install-invoker:
	@cd a2a_invoker && ../.venv/bin/python -m pip install -r requirements.txt

install-invoker-langgraph:
	@cd a2a_invoker && ../.venv/bin/python -m pip install -r requirements-langgraph.txt
