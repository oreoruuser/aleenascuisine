"""X-Ray tracing utilities with graceful degradation when SDK unavailable."""

from __future__ import annotations

from contextlib import contextmanager
import traceback
from typing import Any, Iterator

try:  # pragma: no cover - optional dependency for local dev
    from aws_xray_sdk.core import patch_all, xray_recorder  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - fallback when aws-xray-sdk missing
    patch_all = None  # type: ignore[assignment]
    xray_recorder = None  # type: ignore[assignment]

_TRACING_INITIALIZED = False


def init_tracing(service_name: str) -> None:
    """Configure AWS X-Ray tracing if the SDK is installed."""

    global _TRACING_INITIALIZED
    if _TRACING_INITIALIZED or xray_recorder is None:
        return
    patch_all()  # type: ignore[misc]
    xray_recorder.configure(service=service_name)
    _TRACING_INITIALIZED = True


@contextmanager
def xray_subsegment(name: str, **metadata: Any) -> Iterator[None]:
    """Create an X-Ray subsegment when tracing is available."""

    if xray_recorder is None:
        yield None
        return

    parent = xray_recorder.current_subsegment() or xray_recorder.current_segment()
    if parent is None:
        yield None
        return

    subsegment: Any = xray_recorder.begin_subsegment(name)
    if subsegment is None:  # pragma: no cover - defensive guard
        yield None
        return
    try:
        for key, value in metadata.items():
            try:
                subsegment.put_annotation(key, value)
            except Exception:  # pragma: no cover - defensive
                subsegment.put_metadata(key, value)
        yield None
    except Exception as exc:
        if hasattr(subsegment, "add_exception"):
            stack = traceback.extract_tb(exc.__traceback__) if exc.__traceback__ else []
            try:
                subsegment.add_exception(exc, stack)
            except TypeError:
                subsegment.add_exception(exc)
            except Exception:
                pass
        raise
    finally:
        xray_recorder.end_subsegment()


def add_tracing_metadata(**metadata: Any) -> None:
    """Attach metadata to the current subsegment if tracing is enabled."""

    if xray_recorder is None:
        return
    subsegment = xray_recorder.current_subsegment()
    if subsegment is None:
        return
    for key, value in metadata.items():
        try:
            subsegment.put_annotation(key, value)
        except Exception:  # pragma: no cover - fallback when unsupported type
            subsegment.put_metadata(key, value)
