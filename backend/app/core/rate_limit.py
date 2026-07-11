import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


_requests: dict[str, deque[float]] = defaultdict(deque)


def rate_limit(limit: int = 20, window_seconds: int = 60):
    def dependency(request: Request):
        client_host = request.client.host if request.client else "unknown"
        key = f"{client_host}:{request.url.path}"
        now = time.monotonic()
        bucket = _requests[key]

        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()

        if len(bucket) >= limit:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
            )

        bucket.append(now)

    return dependency
