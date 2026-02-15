from __future__ import annotations

import time
from collections.abc import Callable

from fastapi import Request, Response
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_COUNTER = Counter(
    "finance_lm_http_requests_total", "Total HTTP requests", ["method", "path", "status"]
)
REQUEST_LATENCY = Histogram("finance_lm_http_request_latency_seconds", "HTTP latency", ["path"])
JOB_COUNTER = Counter(
    "finance_lm_job_runs_total", "Total job runs", ["job", "status"]
)
JOB_DURATION = Histogram("finance_lm_job_duration_seconds", "Job execution duration", ["job"])


def setup_tracing(service_name: str) -> None:
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    trace.set_tracer_provider(provider)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        path = request.url.path
        REQUEST_COUNTER.labels(request.method, path, str(response.status_code)).inc()
        REQUEST_LATENCY.labels(path).observe(elapsed)
        return response


def metrics_response() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
