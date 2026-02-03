from contextvars import ContextVar

# ContextVar to store the JWT token for the current request
token_context: ContextVar[str | None] = ContextVar("token_context", default=None)
