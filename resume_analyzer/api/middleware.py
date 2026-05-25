from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response


async def request_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    started_at = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - started_at) * 1000

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.2f}"
    return response
