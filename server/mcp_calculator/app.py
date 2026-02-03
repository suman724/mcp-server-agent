from mcp.server.fastmcp import FastMCP
from mcp_calculator.tools.calculator import register_calculator_tools
from mcp_calculator.auth import TokenVerifier
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.verifier = TokenVerifier()

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/mcp/"):
            try:
                await self.verifier.verify_request(request)
            except ValueError as e:
                return JSONResponse({"error": str(e)}, status_code=401)
        return await call_next(request)

# Initialize FastMCP server
server = FastMCP(
    name="mcp-calculator",
    streamable_http_path="/mcp/",
    stateless_http=True,
    json_response=True,
)

# Register tools
register_calculator_tools(server)

# Get the internal app and wrap it with auth middleware
http_app = server.streamable_http_app()
http_app.add_middleware(AuthMiddleware)

# Expose the wrapped app
app = http_app
