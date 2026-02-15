from __future__ import annotations

import contextvars
import logging
import sys
import uuid

import structlog

correlation_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default=""
)


def set_correlation_id(correlation_id: str | None = None) -> str:
    cid = correlation_id or str(uuid.uuid4())
    correlation_id_ctx.set(cid)
    return cid


def get_correlation_id() -> str:
    return correlation_id_ctx.get()


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "finance-lm"):
    return structlog.get_logger(name)
