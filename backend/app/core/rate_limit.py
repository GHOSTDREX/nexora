"""
AgriNova Backend — minimal in-memory rate limiter.

Single-process, in-memory sliding window — sufficient for this app's
current single-instance deployment (would need a shared store like Redis if
ever run behind multiple worker processes/instances). Guards
/api/auth/login and /api/auth/register against unlimited attempts.
"""

import time
from collections import defaultdict

from fastapi import HTTPException, Request, status

_attempts: dict[str, list[float]] = defaultdict(list)


def rate_limit(request: Request, *, key_prefix: str, max_attempts: int, window_seconds: float) -> None:
    client_ip = request.client.host if request.client else "unknown"
    key = f"{key_prefix}:{client_ip}"
    now = time.monotonic()
    window_start = now - window_seconds

    attempts = _attempts[key]
    attempts[:] = [t for t in attempts if t > window_start]

    if len(attempts) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please wait a few minutes and try again.",
        )

    attempts.append(now)
