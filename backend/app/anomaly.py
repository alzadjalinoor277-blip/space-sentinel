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

Design notes
------------
* The statistical layer computes the mean of the most-recent N samples and
  compares it to an older baseline window.  Using a mean (rather than a
  single point) gives robustness against brief noise spikes — only sustained
  deviations that persist across several samples will cross the threshold.

* The z-score threshold is set at 3.0 (≈ 0.27 % false-positive rate under a
  perfect Gaussian) rather than 2.5, and the noise-floor for the per-metric
  standard deviation is the full nominal noise level rather than half.  Both
  choices reduce false positives for naturally noisy spacecraft metrics
  (e.g. power_consumption_w with nominal noise of 8 W).

* The Isolation Forest baseline is trained once on synthetic nominal data.
  Keeping a fixed baseline means a slow thermal ramp stays anomalous even
  after many hours — the model never adapts to the drift.

* _merge() boosts confidence and score when multiple detection layers agree
  on the same metric (cross-validation). The per-layer boost is 0.08 so that
  3-layer agreement produces a meaningful uplift rather than a cosmetic one.
"""
from __future__ import annotations

import time
from typing import Optional

import numpy as np
from sklearn.ensemble import IsolationForest

from .engine import NOMINAL, METRIC_SUBSYSTEM, new_id
from .models import Anomaly, DetectionLayer, Severity, Subsystem, TelemetryPoint

# Minimum history lengths before each layer activates.
# Layer 1 (threshold) needs only the current point.
# Layer 2 (statistical) needs enough baseline samples to compute a stable mean/std.
# Layer 3 (ML) needs enough samples for the rolling feature vector to be representative.
MIN_HISTORY_FOR_STATS = 20
MIN_HISTORY_FOR_ML = 40

# How many recent samples are averaged to form the "current mean" for z-score.
# A larger window suppresses noise spikes; a window that is too large will
# delay detection of a genuine ramp.  10 samples (10 s at 1 Hz) is a
# reasonable balance for spacecraft telemetry.
RECENT_WINDOW_MIN = 10

# Z-score threshold for the statistical layer.  3.0 corresponds to a ≈ 0.27%
# false-positive rate under an ideal Gaussian distribution, which is
# appropriate for monitoring systems where too many spurious alerts erode
# operator trust.
STAT_Z_THRESHOLD = 3.0

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

# Direction that counts as "bad" for each metric — used only for phrasing in
# the human-readable explanation string; it does not affect detection logic.
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
        """Train the Isolation Forest once on synthetic 'known-good'
        telemetry sampled from the nominal operating envelope.

        Using a fixed baseline (rather than continuously retraining on live,
        possibly-drifting telemetry) means the model keeps recognising a slow
        ramp as abnormal instead of adapting to it as the new normal — which
        is the correct behaviour for a mission anomaly detector.

        400 synthetic samples per metric gives the forest enough coverage of
        the nominal cloud while remaining fast to train.  The normalisation
        (subtract mean, divide by std) puts all metrics on a comparable scale
        so that high-amplitude metrics like power_consumption_w (noise≈8W)
        don't dominate over low-amplitude ones like velocity_kms (noise≈0.01).
        """
        rng = np.random.default_rng(42)
        metrics = list(NOMINAL.keys())
        samples = np.array([
            rng.normal(NOMINAL[m]["setpoint"], NOMINAL[m]["noise"], size=400)
            for m in metrics
        ]).T                            # shape: (400, n_metrics)
        mean = samples.mean(axis=0)
        std = samples.std(axis=0)
        std[std < 1e-6] = 1.0           # guard against degenerate zero-std columns
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
        """Deterministic hard-limit check.

        A breach is flagged with high confidence (0.97) because the limits are
        mission-defined safety margins — there is no statistical uncertainty.
        The score starts at 0.6 (WARNING) and grows with the magnitude of the
        breach relative to the limit value, approaching 1.0 for extreme
        violations.
        """
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
        """Detect sustained trends by comparing a recent window mean against
        an older baseline window mean.

        Using a *mean* over RECENT_WINDOW_MIN (≥ 10) samples instead of a
        single point gives robustness: a brief noise spike that crosses the
        threshold for one tick will not trigger an anomaly because it is
        averaged out.  Only deviations that are sustained across several
        consecutive samples — i.e. genuine ramps or step changes — will shift
        the recent mean far enough to cross the z-score threshold.

        The standard-deviation floor is set to the full nominal noise level
        (cfg["noise"]), not half of it.  This prevents the layer from flagging
        fluctuations that are merely large relative to the *observed* quiet
        period in the baseline window but are still well within the nominal
        operating noise budget.

        The z-score threshold STAT_Z_THRESHOLD = 3.0 keeps false-positive
        rates low for noisy metrics such as power_consumption_w.
        """
        if len(history) < MIN_HISTORY_FOR_STATS:
            return []
        out = []

        # Use up to the last 60 ticks as the working window.
        window = history[-60:]

        # Recent window: at least RECENT_WINDOW_MIN points, up to 1/6 of the
        # working window.  A longer recent window gives a more stable mean but
        # delays detection slightly.
        recent_n = max(RECENT_WINDOW_MIN, len(window) // 6)
        recent_n = min(recent_n, len(window) - RECENT_WINDOW_MIN)  # leave enough for baseline
        if recent_n <= 0:
            return []

        baseline = window[:-recent_n]
        recent = window[-recent_n:]
        if len(baseline) < RECENT_WINDOW_MIN:
            return []

        for metric, cfg in NOMINAL.items():
            baseline_series = np.array([getattr(p, metric) for p in baseline])
            recent_series = np.array([getattr(p, metric) for p in recent])
            mean = float(baseline_series.mean())
            std = float(baseline_series.std())

            # Floor at the full nominal noise level so that fluctuations
            # within the instrument's noise budget never trigger alerts.
            std = max(std, cfg["noise"])

            recent_mean = float(recent_series.mean())
            z = (recent_mean - mean) / std

            if abs(z) >= STAT_Z_THRESHOLD:
                # Score: starts at INFO level (0.35) and climbs with |z|.
                # Each extra sigma above the threshold adds ≈ 0.10 to the score.
                score = float(np.clip(0.35 + (abs(z) - STAT_Z_THRESHOLD) * 0.10, 0, 1))
                low = mean - STAT_Z_THRESHOLD * std
                high = mean + STAT_Z_THRESHOLD * std
                # Confidence grows with the z-score but is capped below the
                # threshold layer because statistical detection has inherent
                # uncertainty (distribution assumptions may not hold perfectly).
                confidence = min(0.90, 0.50 + abs(z) * 0.04)
                out.append(self._build(
                    metric, recent_mean, low, high, score,
                    DetectionLayer.STATISTICAL,
                    confidence=round(confidence, 2),
                    reason=(
                        f"sustained trend: recent {recent_n}-sample mean deviates "
                        f"{abs(z):.1f}\u03c3 from baseline"
                    ),
                ))
        return out

    # -- Layer 3 ---------------------------------------------------------

    def _ml_layer(self, history: list[TelemetryPoint]) -> list[Anomaly]:
        """Multivariate Isolation Forest outlier detection.

        Scores the current telemetry vector against the fixed nominal baseline
        model.  When the model flags an outlier (-1 prediction), we attribute
        the anomaly to the metric with the largest normalised deviation from
        its nominal setpoint — this provides a concrete, human-readable
        explanation even though the underlying detection is multivariate.

        The anomaly score is derived from the model's decision_function output
        (higher = more normal, roughly in [-0.5, 0.5]).  We invert and scale
        it to [0, 1], but floor at 0.30 so that any ML-flagged point is at
        least INFO severity.  Without the floor, a point that barely crosses
        the outlier boundary would produce a score near zero and be invisible
        in the merged result.
        """
        if len(history) < MIN_HISTORY_FOR_ML:
            return []

        metrics = list(NOMINAL.keys())
        current_row = np.array([[getattr(history[-1], m) for m in metrics]])
        norm_current = (current_row - self._ml_mean) / self._ml_std

        raw_score = self._ml_model.decision_function(norm_current)[0]  # higher = more normal
        is_outlier = self._ml_model.predict(norm_current)[0] == -1

        if not is_outlier:
            return []

        # Attribute to the metric with highest normalised deviation.
        deviations = np.abs(norm_current[0])
        worst_idx = int(np.argmax(deviations))
        metric = metrics[worst_idx]
        value = float(current_row[0][worst_idx])
        cfg = NOMINAL[metric]

        # Map decision_function score (higher=normal) to anomaly score (higher=bad).
        # Floor at 0.30 so that even the most marginal ML flags register as INFO.
        raw_anomaly = float(np.clip(0.5 - raw_score, 0, 1))
        score = max(0.30, raw_anomaly)

        # Confidence grows with the magnitude of the largest normalised deviation.
        confidence = min(0.88, 0.50 + float(deviations[worst_idx]) * 0.08)

        return [self._build(
            metric, value,
            cfg["setpoint"] - cfg["noise"] * 3,
            cfg["setpoint"] + cfg["noise"] * 3,
            score,
            DetectionLayer.ML_ISOLATION_FOREST,
            confidence=round(confidence, 2),
            reason="Isolation Forest flagged this multivariate telemetry pattern as an outlier",
        )]

    # -- shared ------------------------------------------------------------

    def _build(self, metric, value, low, high, score, layer, confidence, reason) -> Anomaly:
        label, unit = METRIC_LABELS.get(metric, (metric, ""))
        subsystem = Subsystem(METRIC_SUBSYSTEM.get(metric, "COMPUTE"))
        severity = _severity_from_score(score)
        # Simple directional phrasing: "below" when the value is under the
        # lower bound, "above" otherwise.
        direction = "below" if value < low else "above"
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
        """Merge anomalies for the same metric across detection layers.

        When multiple independent layers all flag the same metric, that
        cross-validation should meaningfully increase our confidence in the
        detection.  Each additional agreeing layer beyond the first adds 0.08
        to both confidence and anomaly_score (capped at 0.99 and 1.0
        respectively).  With three layers agreeing the uplift is 0.16, which
        is enough to push a borderline WARNING (score ≈ 0.60) into confirmed
        WARNING territory and potentially up to CRITICAL if the base score was
        already high.

        The merged anomaly retains the best (highest-score) detection as the
        canonical record with an updated explanation noting all contributing
        layers.
        """
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
            # 0.08 per additional agreeing layer (so 2-layer → +0.08, 3-layer → +0.16)
            boosted_confidence = min(0.99, best.confidence + 0.08 * (agree_count - 1))
            boosted_score = min(1.0, best.anomaly_score + 0.08 * (agree_count - 1))
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
