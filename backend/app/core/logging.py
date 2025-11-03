"""Logging helpers providing JSON structured output and request context."""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

_REQUEST_CONTEXT: ContextVar[dict[str, Any]] = ContextVar("request_context", default={})

_LOG_RECORD_RESERVED_ATTRS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
}

_SENSITIVE_KEY_FRAGMENTS: tuple[str, ...] = (
    "password",
    "secret",
    "token",
    "key",
    "authorization",
    "cookie",
    "credential",
)

_REDACTED = "***redacted***"


def _sanitize_value(value: Any) -> Any:
    """Recursively sanitize sensitive structures."""

    if isinstance(value, Mapping):
        return {k: _sanitize_item(k, v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        sanitized: Iterable[Any] = (_sanitize_value(item) for item in value)
        return type(value)(sanitized)  # type: ignore[call-arg]
    return value


def _sanitize_item(key: str, value: Any) -> Any:
    """Redact values whose keys indicate sensitive data."""

    lowered = key.lower()
    if any(fragment in lowered for fragment in _SENSITIVE_KEY_FRAGMENTS):
        return _REDACTED
    return _sanitize_value(value)


class RequestContextFilter(logging.Filter):
    """Attach request context values from ContextVar to log records."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401 - meaningful name
        context = get_request_context()
        for key, value in context.items():
            setattr(record, key, _sanitize_item(key, value))
        return True


class JsonLogFormatter(logging.Formatter):
    """Render log records as JSON for ingestion by CloudWatch."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc)
        payload: dict[str, Any] = {
            "timestamp": timestamp.isoformat(timespec="milliseconds"),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }

        for attribute in (
            "request_id",
            "path",
            "method",
            "customer_id",
            "order_id",
            "status_code",
            "duration_ms",
        ):
            value = getattr(record, attribute, None)
            if value is not None:
                payload[attribute] = _sanitize_item(attribute, value)

        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _LOG_RECORD_RESERVED_ATTRS
            and not key.startswith("_")
            and key not in payload
        }
        if extras:
            payload.update(
                {key: _sanitize_item(key, value) for key, value in extras.items()}
            )

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = record.stack_info

        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger with JSON formatting and context filter."""

    root = logging.getLogger()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    handler.addFilter(RequestContextFilter())
    root.handlers = [handler]
    root.setLevel(level.upper())
    logging.captureWarnings(True)


def set_request_context(context: Mapping[str, Any]) -> Token:
    """Bind request context values for downstream log records."""

    return _REQUEST_CONTEXT.set(dict(context))


def update_request_context(**values: Any) -> None:
    """Merge additional values into the current request context."""

    context = get_request_context().copy()
    context.update({k: v for k, v in values.items() if v is not None})
    _REQUEST_CONTEXT.set(context)


def get_request_context() -> dict[str, Any]:
    """Return the current request context dictionary."""

    return _REQUEST_CONTEXT.get({}).copy()


def reset_request_context(token: Token) -> None:
    """Restore the request context to a previous state."""

    _REQUEST_CONTEXT.reset(token)
