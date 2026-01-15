import asyncio
import sys
import logging
from .agent import CalculatorAgent, AgentError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m calculator_agent <task>")
        sys.exit(1)
        
    task = " ".join(sys.argv[1:])
    agent = CalculatorAgent()
    
    try:
        # Run the async agent
        if "simple_exec" in task: 
            # Hidden mode for direct testing: "simple_exec add 5 10"
            expr = task.replace("simple_exec ", "")
            logger.info(f"Running simple execution mode: {expr}")
            result = asyncio.run(agent.run_simple_eval(expr))
            logger.info(f"Result: {result}")
        else:
            logger.info(f"Running task: {task}")
            asyncio.run(agent.run(task))
    except KeyboardInterrupt:
        logger.warning("\nOperation cancelled by user.")
    except AgentError as e:
        logger.exception(f"Agent error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
