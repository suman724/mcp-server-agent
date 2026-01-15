import uvicorn
from mcp_calculator.app import app

def main():
    """Entry point for the application script."""
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
