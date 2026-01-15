import asyncio
import sys
import logging
from mcp_client import MCPClient, MCPClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    client = MCPClient(base_url="http://localhost:8000/mcp/")
    
    logger.info("Connecting to MCP Calculator Server at http://localhost:8000...")
    
    try:
        # Test Add
        logger.info("--- Testing Add (5 + 3) ---")
        result = await client.call_tool("add", {"a": 5, "b": 3})
        logger.info(f"Result: {result['content'][0]['text']}")

        # Test Subtract
        logger.info("--- Testing Subtract (10 - 4) ---")
        result = await client.call_tool("subtract", {"a": 10, "b": 4})
        logger.info(f"Result: {result['content'][0]['text']}")

        # Test Multiply
        logger.info("--- Testing Multiply (6 * 7) ---")
        result = await client.call_tool("multiply", {"a": 6, "b": 7})
        logger.info(f"Result: {result['content'][0]['text']}")

        # Test Divide
        logger.info("--- Testing Divide (20 / 5) ---")
        result = await client.call_tool("divide", {"a": 20, "b": 5})
        logger.info(f"Result: {result['content'][0]['text']}")

        # Test Divide by Zero (Error Case)
        logger.info("--- Testing Divide by Zero (5 / 0) ---")
        try:
            await client.call_tool("divide", {"a": 5, "b": 0})
        except MCPClientError as e:
            logger.info(f"Caught expected error: {e}")

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
