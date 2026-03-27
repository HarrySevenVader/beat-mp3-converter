from __future__ import annotations

import logging
import time
from uuid import uuid4

from fastapi import Request, Response

from app.core.metrics import metrics_service


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


async def request_logging_middleware(request: Request, call_next) -> Response:
    request_id = request.headers.get("x-request-id") or uuid4().hex
    started = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        metrics_service.record_http_status(500)
        elapsed_ms = (time.perf_counter() - started) * 1000
        logging.exception(
            "request_failed request_id=%s method=%s path=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            elapsed_ms,
        )
        raise

    response.headers["X-Request-Id"] = request_id
    elapsed_ms = (time.perf_counter() - started) * 1000
    metrics_service.record_http_status(response.status_code)
    logging.info(
        "request_completed request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response
