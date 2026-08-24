"""
Hybrid anomaly detection for SpaceSentinel.

Layer 1 - Safety thresholds: deterministic min/max limits per metric.
Layer 2 - Statistical deviation: rolling z-score against recent history.
Layer 3 - Machine learning: IsolationForest trained on the recent normal
          telemetry window, flags multivariate outliers that single-metric
          rules might miss.

Each layer can independently produce an Anomaly. When multiple layers agree
on the same metric, confidence is boosted. This keeps detection logic
transparent and explainable rather than a black box.
"""
from __future__ import annotations

import time
from typing import Optional

import numpy as np
from sklearn.ensemble import IsolationForest

from .engine import NOMINAL, METRIC_SUBSYSTEM, new_id
from .models import Anomaly, DetectionLayer, Severity, Subsystem, TelemetryPoint

MIN_HISTORY_FOR_STATS = 20
MIN_HISTORY_FOR_ML = 40

METRIC_LABELS = {
    "temperature_c": ("Temperature", "\u00b0C"),
    "battery_voltage_v": ("Battery Voltage", "V"),
    "battery_percent": ("Battery Level", "%"),
    "power_consumption_w": ("Power Consumption", "W"),
    "radiation_level_msv": ("Radiation Level", "mSv"),
    "comm_signal_strength_pct": ("Comm Signal Strength", "%"),
    "cpu_load_pct": ("CPU Load", "%"),
    "memory_usage_pct": ("Memory Usage", "%"),
    "fuel_percent": ("Fuel Level", "%"),
    "altitude_km": ("Altitude", "km"),
    "velocity_kms": ("Velocity", "km/s"),
}

# Direction that counts as "bad" for each metric, used for phrasing and
# for deciding whether a statistical deviation is actually concerning.
LOWER_IS_BAD = {"battery_voltage_v", "battery_percent", "comm_signal_strength_pct", "fuel_percent"}


def _severity_from_score(score: float) -> Severity:
    if score >= 0.85:
        return Severity.CRITICAL
    if score >= 0.6:
        return Severity.WARNING
    if score >= 0.35:
        return Severity.INFO
    return Severity.NORMAL


class AnomalyDetector:
    def __init__(self) -> None:
        self._ml_model: Optional[IsolationForest] = None
        self._ml_mean: Optional[np.ndarray] = None
        self._ml_std: Optional[np.ndarray] = None
        self._train_baseline_model()

    def _train_baseline_model(self) -> None:
        """Trains the Isolation Forest once on synthetic 'known-good'
        telemetry sampled from the nominal operating envelope. Using a
        fixed baseline (rather than continuously retraining on live,
        possibly-drifting telemetry) means the model keeps recognizing a
        slow ramp as abnormal instead of adapting to it as the new normal
        -- which is what a real anomaly-detection baseline should do."""
        rng = np.random.default_rng(42)
        metrics = list(NOMINAL.keys())
        samples = np.array([
            rng.normal(NOMINAL[m]["setpoint"], NOMINAL[m]["noise"], size=400)
            for m in metrics
        ]).T
        mean = samples.mean(axis=0)
        std = samples.std(axis=0)
        std[std < 1e-6] = 1.0
        norm_samples = (samples - mean) / std
        model = IsolationForest(n_estimators=150, contamination=0.03, random_state=42)
        model.fit(norm_samples)
        self._ml_model = model
        self._ml_mean = mean
        self._ml_std = std

    def detect(self, history: list[TelemetryPoint]) -> list[Anomaly]:
        if not history:
            return []
        current = history[-1]
        anomalies: list[Anomaly] = []

        anomalies.extend(self._threshold_layer(current))
        anomalies.extend(self._statistical_layer(history))
        anomalies.extend(self._ml_layer(history))

        return self._merge(anomalies)

    # -- Layer 1 ---------------------------------------------------------

    def _threshold_layer(self, current: TelemetryPoint) -> list[Anomaly]:
        out = []
        for metric, cfg in NOMINAL.items():
            value = getattr(current, metric)
            low, high = cfg["min"], cfg["max"]
            if value < low or value > high:
                breach_ratio = max(
                    (low - value) / (abs(low) + 1e-6) if value < low else 0,
                    (value - high) / (abs(high) + 1e-6) if value > high else 0,
                )
                score = float(np.clip(0.6 + breach_ratio, 0, 1))
                out.append(self._build(
                    metric, value, low, high, score,
                    DetectionLayer.THRESHOLD,
                    confidence=0.97,
                    reason="value breached the configured hard safety threshold",
                ))
        return out

    # -- Layer 2 ---------------------------------------------------------

    def _statistical_layer(self, history: list[TelemetryPoint]) -> list[Anomaly]:
        """Compares the mean of the most recent samples against an older
        baseline window (rather than a single point against the whole
        window). This makes the layer sensitive to sustained trends/ramps,
        not just sudden spikes, which is what a gradually-developing event
        (e.g. a thermal ramp) looks like."""
        if len(history) < MIN_HISTORY_FOR_STATS:
            return []
        out = []
        window = history[-60:]
        recent_n = min(5, len(window) // 4 or 1)
        baseline = window[:-recent_n]
        recent = window[-recent_n:]
        if len(baseline) < 10:
            return []

        for metric, cfg in NOMINAL.items():
            baseline_series = np.array([getattr(p, metric) for p in baseline])
            recent_series = np.array([getattr(p, metric) for p in recent])
            mean, std = float(baseline_series.mean()), float(baseline_series.std())
            std = max(std, cfg["noise"] * 0.5)  # floor so near-constant metrics remain sensitive
            recent_mean = float(recent_series.mean())
            z = (recent_mean - mean) / std
            if abs(z) >= 2.5:
                score = float(np.clip(0.35 + (abs(z) - 2.5) * 0.12, 0, 1))
                low = mean - 2.5 * std
                high = mean + 2.5 * std
                out.append(self._build(
                    metric, recent_mean, low, high, score,
                    DetectionLayer.STATISTICAL,
                    confidence=min(0.9, 0.55 + abs(z) * 0.05),
                    reason=f"recent trend deviates {abs(z):.1f} standard deviations from baseline behavior",
                ))
        return out

    # -- Layer 3 ---------------------------------------------------------

    def _ml_layer(self, history: list[TelemetryPoint]) -> list[Anomaly]:
        if len(history) < MIN_HISTORY_FOR_ML:
            return []

        metrics = list(NOMINAL.keys())
        current_row = np.array([[getattr(history[-1], m) for m in metrics]])

        norm_current = (current_row - self._ml_mean) / self._ml_std
        raw_score = self._ml_model.decision_function(norm_current)[0]  # higher = more normal
        is_outlier = self._ml_model.predict(norm_current)[0] == -1

        if not is_outlier:
            return []

        # find which metric deviates most in normalized space to attribute the anomaly
        deviations = np.abs(norm_current[0])
        worst_idx = int(np.argmax(deviations))
        metric = metrics[worst_idx]
        value = float(current_row[0][worst_idx])
        cfg = NOMINAL[metric]

        score = float(np.clip(0.5 - raw_score, 0, 1))
        return [self._build(
            metric, value, cfg["setpoint"] - cfg["noise"] * 3, cfg["setpoint"] + cfg["noise"] * 3, score,
            DetectionLayer.ML_ISOLATION_FOREST,
            confidence=min(0.88, 0.5 + deviations[worst_idx] * 0.08),
            reason="Isolation Forest flagged this multivariate telemetry pattern as an outlier",
        )]

    # -- shared ------------------------------------------------------------

    def _build(self, metric, value, low, high, score, layer, confidence, reason) -> Anomaly:
        label, unit = METRIC_LABELS.get(metric, (metric, ""))
        subsystem = Subsystem(METRIC_SUBSYSTEM.get(metric, "COMPUTE"))
        severity = _severity_from_score(score)
        direction = "below" if (metric in LOWER_IS_BAD and value < low) or (metric not in LOWER_IS_BAD and value < low) else "above"
        explanation = (
            f"{label} reading of {value:.2f}{unit} is {direction} the expected operating "
            f"range ({low:.2f}\u2013{high:.2f}{unit}); {reason}."
        )
        action = _recommend_action(subsystem, metric, direction)
        return Anomaly(
            id=new_id("anom"),
            timestamp=time.time(),
            subsystem=subsystem,
            metric=metric,
            observed_value=value,
            expected_min=low,
            expected_max=high,
            severity=severity,
            confidence=round(confidence, 2),
            anomaly_score=round(score, 3),
            detection_layer=layer,
            explanation=explanation,
            recommended_action=action,
        )

    def _merge(self, anomalies: list[Anomaly]) -> list[Anomaly]:
        """Merge anomalies on the same metric across layers, boosting confidence
        when multiple detection layers agree (cross-validated anomaly)."""
        by_metric: dict[str, list[Anomaly]] = {}
        for a in anomalies:
            by_metric.setdefault(a.metric, []).append(a)

        merged: list[Anomaly] = []
        for metric, group in by_metric.items():
            if len(group) == 1:
                merged.append(group[0])
                continue
            best = max(group, key=lambda a: a.anomaly_score)
            agree_count = len(group)
            boosted_confidence = min(0.99, best.confidence + 0.05 * (agree_count - 1))
            boosted_score = min(1.0, best.anomaly_score + 0.05 * (agree_count - 1))
            layers = ", ".join(sorted({a.detection_layer.value for a in group}))
            best = best.model_copy(update={
                "confidence": round(boosted_confidence, 2),
                "anomaly_score": round(boosted_score, 3),
                "severity": _severity_from_score(boosted_score),
                "explanation": best.explanation + f" Confirmed by {agree_count} detection layers ({layers}).",
            })
            merged.append(best)
        return sorted(merged, key=lambda a: a.anomaly_score, reverse=True)


def _recommend_action(subsystem: Subsystem, metric: str, direction: str) -> str:
    table = {
        Subsystem.THERMAL: "Reduce non-critical workload and initiate thermal diagnostics.",
        Subsystem.POWER: "Switch to backup power regulation and inspect battery telemetry.",
        Subsystem.RADIATION: "Activate radiation shielding protocol and monitor crew/electronics exposure.",
        Subsystem.COMMUNICATION: "Reacquire signal via backup antenna and verify ground station link.",
        Subsystem.COMPUTE: "Throttle background processes and check for runaway tasks.",
        Subsystem.PROPULSION: "Verify propellant line integrity and recompute burn margins.",
        Subsystem.NAVIGATION: "Cross-check orbital elements against ground tracking data.",
    }
    return table.get(subsystem, "Escalate to mission operators for manual review.")
