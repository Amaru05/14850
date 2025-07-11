# logging_middleware.py
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from logger_util import Log

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        try:
            response = await call_next(request)
        except Exception as e:
            Log("backend", "error", "handler", f"unexpected error: {str(e)}")
            raise
        duration = round(time.time() - start, 4)
        Log("backend", "info", "middleware", f"{request.method} {request.url} took {duration}s")
        return response
