"""
AgriNova Backend — response security headers and request body-size cap.

Two small ASGI middlewares:
- SecurityHeadersMiddleware: adds Strict-Transport-Security to every
  response. It's a no-op protection over plain HTTP (browsers only honor
  HSTS on responses actually served over TLS) but costs nothing to send now
  and takes effect the moment this API sits behind HTTPS in deployment.
- BodySizeLimitMiddleware: rejects any request whose declared Content-Length
  exceeds MAX_BODY_BYTES before it reaches route handlers, as a cheap
  defense against oversized-payload abuse (chat messages, manual sensor
  readings, etc. have no other size ceiling).
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

MAX_BODY_BYTES = 2 * 1024 * 1024  # 2 MB — generous for this app's JSON-only endpoints


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                if int(content_length) > MAX_BODY_BYTES:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Request body too large."},
                    )
            except ValueError:
                pass
        return await call_next(request)
