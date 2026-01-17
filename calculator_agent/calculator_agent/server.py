
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from .agent import CalculatorAgent, AgentError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("calculator_server")

app = FastAPI(title="Calculator Agent A2A", description="Exposes the Calculator Agent via A2A protocol.")

class AgentMessage(BaseModel):
    role: str
    content: str

class AgentInput(BaseModel):
    messages: List[AgentMessage]
    context: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    messages: List[AgentMessage]

# Agent Card Model (can be refined based on A2A specs)
class AgentCard(BaseModel):
    name: str
    description: str
    capabilities: List[str]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    version: str = "0.1.0"

agent_instance = None

@app.on_event("startup")
async def startup_event():
    global agent_instance
    try:
        agent_instance = CalculatorAgent()
        logger.info("CalculatorAgent initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize CalculatorAgent: {e}")
        # We might want to let it fail or handle it gracefully? 
        # For now, we log it. logic will fail if agent is None.

@app.get("/calculator/info", response_model=AgentCard)
async def get_agent_card():
    return AgentCard(
        name="Calculator Agent",
        description="An intelligent agent that performs mathematical operations using an MCP calculator server.",
        capabilities=["math_operations", "basic_calculation"],
        input_schema={"type": "object", "properties": {"messages": {"type": "array"}}},
        output_schema={"type": "object", "properties": {"messages": {"type": "array"}}}
    )

@app.post("/calculator", response_model=AgentResponse)
async def run_agent(input_data: AgentInput):
    if agent_instance is None:
        raise HTTPException(status_code=503, detail="Agent not initialized.")
    
    # Extract the last user message as the prompt
    # In a real A2A Scenario, we might process the whole history.
    # The current CalculatorAgent.run() takes a single string prompt.
    
    last_user_msg = next((m for m in reversed(input_data.messages) if m.role == "user"), None)
    
    if not last_user_msg:
        raise HTTPException(status_code=400, detail="No user message found in input.")

    try:
        response_text = await agent_instance.run(last_user_msg.content)
        return AgentResponse(
            messages=[AgentMessage(role="assistant", content=response_text)]
        )
    except AgentError as e:
        logger.error(f"Agent execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

def start():
    """Entry point for running the server programmatically."""
    uvicorn.run("calculator_agent.server:app", host="0.0.0.0", port=8001, reload=True)

if __name__ == "__main__":
    start()
