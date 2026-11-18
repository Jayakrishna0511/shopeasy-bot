"""Sliding-window in-memory rate limiter for ShopEasy Support Bot.

Enforces:
- Maximum requests per minute per authenticated customer or client IP.
- Protects API keys, database connection pool, and prevents denial of service.
"""

from collections import defaultdict
import time
from typing import Dict, List
from fastapi import HTTPException, Request, status

from app.models.user import User

# Configuration
DEFAULT_MAX_REQUESTS = 15  # requests per minute
WINDOW_SECONDS = 60        # 1 minute sliding window

# In-memory storage: key (user_id or client_ip) -> list of timestamp floats
_request_history: Dict[str, List[float]] = defaultdict(list)


def check_rate_limit(
    request: Request,
    current_user: User = None,
    max_requests: int = DEFAULT_MAX_REQUESTS,
    window_seconds: int = WINDOW_SECONDS,
) -> None:
    """Sliding-window rate limiter dependency.

    Identifies the client by:
    1. Authenticated user ID (e.g. 'ravi', 'priya')
    2. Client IP address (fallback)

    Raises:
        HTTPException 429 if the request limit is exceeded within the window.
    """
    now = time.time()
    cutoff = now - window_seconds

    # Determine rate limit key
    if current_user and getattr(current_user, "id", None):
        client_key = f"user:{current_user.id}"
    else:
        client_ip = request.client.host if request.client else "unknown"
        client_key = f"ip:{client_ip}"

    # Filter out timestamps outside the active sliding window
    timestamps = [t for t in _request_history[client_key] if t > cutoff]

    if len(timestamps) >= max_requests:
        oldest_in_window = timestamps[0]
        retry_after = int(window_seconds - (now - oldest_in_window)) + 1
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded ({max_requests} requests/min). Please wait {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )

    # Record this request
    timestamps.append(now)
    _request_history[client_key] = timestamps
