import os
import logging
import certifi
import ssl
import jwt
from jwt import PyJWKClient
from starlette.requests import Request
from starlette.responses import JSONResponse

# Configure logging
logger = logging.getLogger(__name__)

# Load OIDC Configuration from Environment
OIDC_ISSUER = os.getenv("OIDC_ISSUER", "https://dev-d2i2ktw25ycepyad.us.auth0.com/")
OIDC_AUDIENCE = os.getenv("OIDC_AUDIENCE", "https://mcp.msgraph.com")
OIDC_JWKS_URL = os.getenv("OIDC_JWKS_URL", "https://dev-d2i2ktw25ycepyad.us.auth0.com/.well-known/jwks.json")

class TokenVerifier:
    def __init__(self):
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        self.jwks_client = PyJWKClient(OIDC_JWKS_URL, ssl_context=ssl_context)

    def verify_token(self, token: str) -> dict:
        try:
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            data = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=OIDC_AUDIENCE,
                issuer=OIDC_ISSUER,
            )
            return data
        except jwt.PyJWTError as e:
            logger.error(f"Token verification failed: {e}")
            raise

    async def verify_request(self, request: Request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise ValueError("Missing or invalid Authorization header")

        token = auth_header.split(" ")[1]
        try:
            self.verify_token(token)
            return token  # Return the token so it can be used
        except Exception as e:
            raise ValueError(f"Invalid token: {str(e)}")
