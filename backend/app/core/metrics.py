"""Helpers for publishing custom CloudWatch metrics."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Mapping, Sequence

try:  # pragma: no cover - optional for local testing
    import boto3  # type: ignore
except ImportError:  # pragma: no cover - boto3 missing locally
    boto3 = None  # type: ignore

logger = logging.getLogger(__name__)

_METRICS_NAMESPACE = "AleenasCuisine/Application"


@lru_cache(maxsize=1)
def _cloudwatch_client():
    if boto3 is None:
        raise RuntimeError("boto3 is required to publish metrics")
    return boto3.client("cloudwatch")


def emit_metric(
    name: str,
    value: float = 1.0,
    unit: str = "Count",
    *,
    dimensions: Mapping[str, str] | None = None,
) -> None:
    """Publish a single data point to CloudWatch, swallowing runtime errors."""

    try:
        client = _cloudwatch_client()
    except RuntimeError:
        logger.debug(
            "CloudWatch client unavailable; metric dropped", extra={"metric": name}
        )
        return

    metric_dimensions: Sequence[dict[str, str]] = []
    if dimensions:
        metric_dimensions = [
            {"Name": key, "Value": str(value)}
            for key, value in dimensions.items()
            if value is not None
        ]

    try:
        client.put_metric_data(
            Namespace=_METRICS_NAMESPACE,
            MetricData=[
                {
                    "MetricName": name,
                    "Value": value,
                    "Unit": unit,
                    "Dimensions": list(metric_dimensions),
                }
            ],
        )
    except Exception as exc:  # pragma: no cover - network errors
        logger.warning(
            "Failed to publish CloudWatch metric",
            extra={"metric": name, "error": str(exc)},
        )
