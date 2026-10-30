from __future__ import annotations

from typing import Final
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Info, generate_latest

FORECAST_ABS_LOG_ERROR: Final[Gauge] = Gauge(
    "forecast_abs_log_error",
    "Absolute log forecast error for champion model",
    ["series", "commodity", "market"],
)

DRIFT_Z_SCORE: Final[Gauge] = Gauge(
    "drift_z",
    "Robust z-score of forecast error relative to 24-month baseline",
    ["series", "commodity", "market"],
)

ALERTS_TOTAL: Final[Counter] = Counter(
    "alerts_total",
    "Total count of drift alerts triggered",
    ["tier"],
)

MONTHS_WITHOUT_FORECAST: Final[Counter] = Counter(
    "months_without_forecast",
    "Count of valid months with missing lag prices preventing forecast",
    ["year"],
)

MODEL_CUTOFF_INFO: Final[Info] = Info(
    "model_cutoff",
    "Information regarding current model training cutoff",
)


def get_latest_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
