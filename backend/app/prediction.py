"""
Predictive monitoring for SpaceSentinel.

Uses simple linear regression over a recent rolling window to estimate
trend direction and rate. This is intentionally lightweight -- a
transparent statistical projection, not a claim of flight-grade predictive
accuracy. The system is explicit in its UI copy that this is a simulation.
"""
from __future__ import annotations

from typing import Optional

import numpy as np

from .engine import NOMINAL, METRIC_SUBSYSTEM
from .models import Prediction, Subsystem, TelemetryPoint

WINDOW = 60  # samples used for trend fit
TREND_FLAT_EPSILON = 1e-3

# Metrics worth surfacing predictions for, and which bound to watch.
WATCHED_METRICS = {
    "temperature_c": "max",
    "power_consumption_w": "max",
    "battery_percent": "min",
    "battery_voltage_v": "min",
    "radiation_level_msv": "max",
    "comm_signal_strength_pct": "min",
    "fuel_percent": "min",
    "cpu_load_pct": "max",
}


def _fit_trend(values: np.ndarray, timestamps: np.ndarray) -> tuple[float, float]:
    """Returns (slope_per_second, intercept) via least squares."""
    t0 = timestamps - timestamps[0]
    A = np.vstack([t0, np.ones_like(t0)]).T
    slope, intercept = np.linalg.lstsq(A, values, rcond=None)[0]
    return float(slope), float(intercept)


def generate_predictions(history: list[TelemetryPoint]) -> list[Prediction]:
    if len(history) < 10:
        return []

    window = history[-WINDOW:]
    timestamps = np.array([p.timestamp for p in window])
    predictions: list[Prediction] = []

    for metric, bound_type in WATCHED_METRICS.items():
        values = np.array([getattr(p, metric) for p in window])
        slope, intercept = _fit_trend(values, timestamps)
        current_value = float(values[-1])
        slope_per_min = slope * 60.0

        if abs(slope_per_min) < TREND_FLAT_EPSILON:
            trend = "stable"
        elif slope_per_min > 0:
            trend = "increasing"
        else:
            trend = "decreasing"

        threshold = NOMINAL[metric]["max"] if bound_type == "max" else NOMINAL[metric]["min"]
        predicted_10min = current_value + slope_per_min * 10

        time_to_threshold = _time_to_threshold(current_value, slope_per_min, threshold, bound_type)

        # confidence: based on how well the linear fit explains the data (R^2-ish)
        residuals = values - (slope * (timestamps - timestamps[0]) + intercept)
        ss_res = float(np.sum(residuals ** 2))
        ss_tot = float(np.sum((values - values.mean()) ** 2)) + 1e-9
        r2 = max(0.0, 1 - ss_res / ss_tot)
        confidence = float(np.clip(0.4 + r2 * 0.55, 0.35, 0.95))

        insight = _build_insight(metric, trend, current_value, threshold, time_to_threshold, bound_type)

        predictions.append(Prediction(
            metric=metric,
            subsystem=Subsystem(METRIC_SUBSYSTEM[metric]),
            current_value=round(current_value, 3),
            threshold=round(threshold, 3),
            trend=trend,
            trend_rate_per_min=round(slope_per_min, 4),
            predicted_value_10min=round(predicted_10min, 3),
            confidence=round(confidence, 2),
            time_to_threshold_minutes=round(time_to_threshold, 1) if time_to_threshold is not None else None,
            insight=insight,
        ))

    return predictions


def _time_to_threshold(current: float, slope_per_min: float, threshold: float, bound_type: str) -> Optional[float]:
    if abs(slope_per_min) < TREND_FLAT_EPSILON:
        return None
    if bound_type == "max" and slope_per_min > 0 and current < threshold:
        minutes = (threshold - current) / slope_per_min
        return minutes if 0 < minutes < 24 * 60 else None
    if bound_type == "min" and slope_per_min < 0 and current > threshold:
        minutes = (threshold - current) / slope_per_min
        return minutes if 0 < minutes < 24 * 60 else None
    return None


def _build_insight(metric: str, trend: str, current: float, threshold: float, ttt: Optional[float], bound_type: str) -> str:
    label = metric.replace("_", " ").replace(" c", "").title()
    if trend == "stable":
        return f"{label} is stable near current levels with no significant trend toward its configured threshold."
    direction = "toward" if ttt is not None else "away from"
    base = f"Telemetry indicates {label} is {trend} {direction} its configured threshold ({threshold:.1f})."
    if ttt is not None:
        base += f" At the current rate, the threshold could be reached in approximately {ttt:.0f} minutes."
    return base
