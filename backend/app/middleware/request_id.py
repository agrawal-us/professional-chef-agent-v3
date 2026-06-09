import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.start_time = time.monotonic()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
