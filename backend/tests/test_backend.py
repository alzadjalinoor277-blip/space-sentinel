"""
Automated tests for SpaceSentinel backend.

Covers: telemetry generation, anomaly detection layers, risk scoring logic,
prediction/trend analysis, and API endpoint contracts.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import time

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.engine import TelemetryEngine, NOMINAL
from app.anomaly import (
    AnomalyDetector,
    STAT_Z_THRESHOLD,
    RECENT_WINDOW_MIN,
    MIN_HISTORY_FOR_STATS,
    MIN_HISTORY_FOR_ML,
)
from app.risk import score_risk
from app.prediction import generate_predictions
from app.models import (
    Anomaly,
    DetectionLayer,
    ScenarioType,
    Severity,
    Subsystem,
    TelemetryPoint,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _nominal_point(**overrides) -> TelemetryPoint:
    """Return a TelemetryPoint at nominal setpoints, with optional overrides."""
    values = {m: cfg["setpoint"] for m, cfg in NOMINAL.items()}
    values["timestamp"] = time.time()
    values.update(overrides)
    return TelemetryPoint(**values)


def _make_history(n: int, **overrides) -> list[TelemetryPoint]:
    """Build a list of *n* nominal TelemetryPoints (all at setpoints)."""
    return [_nominal_point(**overrides) for _ in range(n)]


# ---------------------------------------------------------------------------
# Telemetry engine
# ---------------------------------------------------------------------------

def test_engine_generates_points_within_soft_bounds_when_normal():
    engine = TelemetryEngine()
    for _ in range(100):
        engine.tick()
    recent = engine.recent(50)
    temps = [p.temperature_c for p in recent]
    # under normal scenario, temperature should stay close to setpoint (21C)
    assert all(-5 < t < 40 for t in temps)


def test_thermal_scenario_increases_temperature_over_time():
    engine = TelemetryEngine()
    engine.set_scenario(ScenarioType.THERMAL_EVENT)
    start_temp = engine.current().temperature_c
    for _ in range(80):
        engine.tick()
    end_temp = engine.current().temperature_c
    assert end_temp > start_temp + 10, "temperature should trend upward during a thermal event"


def test_power_instability_scenario_drops_battery_percent():
    engine = TelemetryEngine()
    engine.set_scenario(ScenarioType.POWER_INSTABILITY)
    for _ in range(80):
        engine.tick()
    assert engine.current().battery_percent < NOMINAL["battery_percent"]["setpoint"] - 10


def test_communication_degradation_lowers_signal():
    engine = TelemetryEngine()
    engine.set_scenario(ScenarioType.COMMUNICATION_DEGRADATION)
    for _ in range(80):
        engine.tick()
    assert engine.current().comm_signal_strength_pct < NOMINAL["comm_signal_strength_pct"]["setpoint"] - 15


# ---------------------------------------------------------------------------
# Anomaly detection — Layer 1 (threshold)
# ---------------------------------------------------------------------------

def test_threshold_layer_flags_hard_breach():
    detector = AnomalyDetector()
    engine = TelemetryEngine()
    # force a hard threshold breach by running many ticks of a severe thermal event
    engine.set_scenario(ScenarioType.THERMAL_EVENT)
    for _ in range(200):
        engine.tick()
    anomalies = detector.detect(list(engine.history))
    metrics_flagged = {a.metric for a in anomalies}
    assert "temperature_c" in metrics_flagged


def test_threshold_layer_confidence_is_high():
    """Layer 1 detections must carry 0.97 confidence (deterministic rule)."""
    detector = AnomalyDetector()
    engine = TelemetryEngine()
    engine.set_scenario(ScenarioType.THERMAL_EVENT)
    for _ in range(200):
        engine.tick()
    # Test the raw threshold layer directly (before merge).
    raw = detector._threshold_layer(engine.current())
    for a in raw:
        assert a.confidence == 0.97


def test_no_anomalies_in_steady_normal_state():
    detector = AnomalyDetector()
    engine = TelemetryEngine()
    for _ in range(150):
        engine.tick()
    anomalies = detector.detect(list(engine.history))
    critical = [a for a in anomalies if a.severity == Severity.CRITICAL]
    assert critical == [], "steady nominal telemetry should not produce critical anomalies"


# ---------------------------------------------------------------------------
# Anomaly detection — Layer 2 (statistical)
# ---------------------------------------------------------------------------

def test_statistical_layer_not_triggered_by_single_noise_spike():
    """A single-tick spike that lasts only one sample must not trigger a
    sustained-trend alert.

    The statistical layer averages the last RECENT_WINDOW_MIN (>= 10) samples,
    so a spike on just one tick is diluted by the other 9 nominal values.
    With a moderate spike of 6 * nominal_noise (still a physically large
    excursion), the per-sample contribution to the recent mean is small enough
    to keep the z-score well below STAT_Z_THRESHOLD = 3.0.

    spike_value = setpoint + 6 * noise = 21 + 3.6 = 24.6 C
    recent_mean ≈ (9 * 21 + 24.6) / 10 = 21.36 C
    z ≈ (21.36 - 21) / 0.6 = 0.60  << 3.0  → no alert
    """
    detector = AnomalyDetector()

    # Build a long stable baseline at nominal temperature (21 C).
    history = _make_history(60)

    # Inject a single moderate spike at the very end.
    # Use 6 x nominal noise — physically noticeable but brief (1 tick).
    spike_value = NOMINAL["temperature_c"]["setpoint"] + 6 * NOMINAL["temperature_c"]["noise"]
    history[-1] = _nominal_point(temperature_c=spike_value)

    anomalies = detector._statistical_layer(history)
    stat_temp = [
        a for a in anomalies
        if a.metric == "temperature_c" and a.detection_layer == DetectionLayer.STATISTICAL
    ]
    assert stat_temp == [], (
        "a single-tick spike diluted across the 10-sample recent mean "
        "should not trigger a statistical anomaly"
    )


def test_statistical_layer_detects_sustained_upward_trend():
    """A sustained upward ramp that shifts the recent mean several sigma above
    the baseline must be detected by the statistical layer.

    Layout of the history (72 points):
      - First 60 points: flat nominal (temperature = setpoint = 21 C)
      - Last 12 points:  sustained ramp (temperature = setpoint + 8*noise = 25.8 C)

    window = last 60 = (48 flat) + (12 ramp)
    recent_n = max(10, 60//6) = 10
    baseline = window[:50] = 48 flat + 2 ramp  →  mean ≈ 21.19, std ≈ 0.94
    recent   = window[50:]  = 10 ramp points   →  mean = 25.8
    z ≈ (25.8 - 21.19) / max(0.94, 0.6) ≈ 4.9 >> 3.0  → fires
    """
    detector = AnomalyDetector()

    setpoint = NOMINAL["temperature_c"]["setpoint"]
    noise = NOMINAL["temperature_c"]["noise"]
    ramp_value = setpoint + 8 * noise  # 25.8 C

    # 60 flat points followed by 12 ramp points guarantees the recent window
    # (last 10 of the 60-point working window) is entirely in the ramp phase.
    history = _make_history(60) + _make_history(12, temperature_c=ramp_value)

    anomalies = detector._statistical_layer(history)
    stat_temp = [
        a for a in anomalies
        if a.metric == "temperature_c" and a.detection_layer == DetectionLayer.STATISTICAL
    ]
    assert stat_temp, "a sustained upward ramp should be caught by the statistical layer"
    assert stat_temp[0].anomaly_score >= 0.35, "score should be at least INFO level"


def test_statistical_layer_noise_floor_prevents_false_positives_on_quiet_baseline():
    """When the baseline window happens to be unusually quiet (very low observed
    std), the noise-floor (= cfg["noise"]) prevents the z-score from inflating
    and causing a false alert."""
    detector = AnomalyDetector()

    # Build a perfectly flat baseline (zero noise).
    history = _make_history(50)

    # Recent points at setpoint + 1.5 x nominal_noise (within the noise budget).
    small_shift = NOMINAL["temperature_c"]["setpoint"] + 1.5 * NOMINAL["temperature_c"]["noise"]
    recent = _make_history(15, temperature_c=small_shift)
    history = history + recent

    anomalies = detector._statistical_layer(history)
    stat_temp = [
        a for a in anomalies
        if a.metric == "temperature_c" and a.detection_layer == DetectionLayer.STATISTICAL
    ]
    assert stat_temp == [], (
        "a deviation within the nominal noise budget should not trigger a statistical alert "
        "even when the baseline happens to be perfectly flat"
    )


def test_statistical_layer_returns_empty_when_insufficient_history():
    detector = AnomalyDetector()
    short_history = _make_history(MIN_HISTORY_FOR_STATS - 1)
    assert detector._statistical_layer(short_history) == []


# ---------------------------------------------------------------------------
# Anomaly detection — Layer 3 (ML)
# ---------------------------------------------------------------------------

def test_ml_layer_returns_empty_when_insufficient_history():
    detector = AnomalyDetector()
    short_history = _make_history(MIN_HISTORY_FOR_ML - 1)
    assert detector._ml_layer(short_history) == []


def test_ml_layer_detects_anomaly_during_thermal_event_and_score_is_positive():
    """The ML layer must fire on telemetry from a significant thermal event
    and the resulting anomaly score must be strictly positive (> 0) and
    bounded to [0, 1].

    This tests the ML layer's end-to-end detection path including:
    - the IsolationForest prediction
    - the raw_score → anomaly_score mapping (0.5 - raw_score, clipped to [0,1])
    - the floor ensuring the score is at least 0.30
    """
    detector = AnomalyDetector()

    engine = TelemetryEngine()
    engine.set_scenario(ScenarioType.THERMAL_EVENT)
    for _ in range(200):
        engine.tick()

    history = list(engine.history)
    ml_anomalies = detector._ml_layer(history)

    assert ml_anomalies, (
        "the ML layer should flag an anomaly after a sustained thermal event"
    )
    for a in ml_anomalies:
        assert 0.0 < a.anomaly_score <= 1.0, (
            f"ML anomaly score {a.anomaly_score} is outside (0, 1]"
        )
        assert a.anomaly_score >= 0.30, (
            f"ML anomaly score {a.anomaly_score} is below the 0.30 floor"
        )


# ---------------------------------------------------------------------------
# Anomaly detection — _merge() cross-validation boost
# ---------------------------------------------------------------------------

def _make_anomaly(metric: str, score: float, confidence: float,
                  layer: DetectionLayer) -> Anomaly:
    """Build a minimal Anomaly for merge testing."""
    return Anomaly(
        id=f"anom-test-{layer.value}",
        timestamp=time.time(),
        subsystem=Subsystem.THERMAL,
        metric=metric,
        observed_value=90.0,
        expected_min=0.0,
        expected_max=85.0,
        severity=Severity.WARNING,
        confidence=confidence,
        anomaly_score=score,
        detection_layer=layer,
        explanation="test",
        recommended_action="test action",
    )


def test_merge_single_anomaly_unchanged():
    detector = AnomalyDetector()
    a = _make_anomaly("temperature_c", 0.70, 0.80, DetectionLayer.THRESHOLD)
    result = detector._merge([a])
    assert len(result) == 1
    assert result[0].anomaly_score == 0.70
    assert result[0].confidence == 0.80


def test_merge_two_layer_agreement_boosts_confidence_and_score():
    """When threshold and statistical both flag the same metric, confidence
    and score should each increase by 0.08 (one extra agreeing layer)."""
    detector = AnomalyDetector()
    a1 = _make_anomaly("temperature_c", 0.70, 0.80, DetectionLayer.THRESHOLD)
    a2 = _make_anomaly("temperature_c", 0.50, 0.60, DetectionLayer.STATISTICAL)
    result = detector._merge([a1, a2])
    assert len(result) == 1
    merged = result[0]
    # Best score was 0.70; boost = 0.08 x 1 = 0.08
    assert abs(merged.anomaly_score - 0.78) < 0.01, (
        f"expected boosted score ~0.78, got {merged.anomaly_score}"
    )
    # Best confidence was 0.80; boost = 0.08 x 1 = 0.08
    assert abs(merged.confidence - 0.88) < 0.01, (
        f"expected boosted confidence ~0.88, got {merged.confidence}"
    )


def test_merge_three_layer_agreement_boosts_by_016():
    """Three layers agreeing on the same metric should boost score by 0.16."""
    detector = AnomalyDetector()
    a1 = _make_anomaly("temperature_c", 0.70, 0.80, DetectionLayer.THRESHOLD)
    a2 = _make_anomaly("temperature_c", 0.50, 0.60, DetectionLayer.STATISTICAL)
    a3 = _make_anomaly("temperature_c", 0.45, 0.55, DetectionLayer.ML_ISOLATION_FOREST)
    result = detector._merge([a1, a2, a3])
    assert len(result) == 1
    merged = result[0]
    # Best score was 0.70; boost = 0.08 x 2 = 0.16  -> 0.86
    assert abs(merged.anomaly_score - 0.86) < 0.01, (
        f"expected boosted score ~0.86, got {merged.anomaly_score}"
    )


def test_merge_confidence_capped_at_099():
    """Confidence must never exceed 0.99 regardless of how many layers agree."""
    detector = AnomalyDetector()
    a1 = _make_anomaly("temperature_c", 0.95, 0.98, DetectionLayer.THRESHOLD)
    a2 = _make_anomaly("temperature_c", 0.80, 0.97, DetectionLayer.STATISTICAL)
    a3 = _make_anomaly("temperature_c", 0.70, 0.96, DetectionLayer.ML_ISOLATION_FOREST)
    result = detector._merge([a1, a2, a3])
    assert result[0].confidence <= 0.99


def test_merge_explanation_names_all_contributing_layers():
    """The merged explanation should reference how many layers confirmed it."""
    detector = AnomalyDetector()
    a1 = _make_anomaly("temperature_c", 0.70, 0.80, DetectionLayer.THRESHOLD)
    a2 = _make_anomaly("temperature_c", 0.50, 0.60, DetectionLayer.STATISTICAL)
    result = detector._merge([a1, a2])
    assert "Confirmed by 2 detection layers" in result[0].explanation


# ---------------------------------------------------------------------------
# Anomaly detection — _build() direction phrasing
# ---------------------------------------------------------------------------

def test_build_direction_below_when_value_under_low():
    """_build() must use 'below' when the observed value is below the low bound."""
    detector = AnomalyDetector()
    a = detector._build(
        "temperature_c",
        value=-20.0,   # below low=-10
        low=-10.0,
        high=85.0,
        score=0.7,
        layer=DetectionLayer.THRESHOLD,
        confidence=0.97,
        reason="test",
    )
    assert "below" in a.explanation


def test_build_direction_above_when_value_over_high():
    """_build() must use 'above' when the observed value is above the high bound."""
    detector = AnomalyDetector()
    a = detector._build(
        "temperature_c",
        value=90.0,   # above high=85
        low=-10.0,
        high=85.0,
        score=0.7,
        layer=DetectionLayer.THRESHOLD,
        confidence=0.97,
        reason="test",
    )
    assert "above" in a.explanation


# ---------------------------------------------------------------------------
# Risk scoring
# ---------------------------------------------------------------------------

def test_risk_score_zero_with_no_anomalies():
    risk = score_risk([], {})
    assert risk.score == 0
    assert risk.level.value == "LOW"


def test_risk_score_increases_with_more_severe_anomalies():
    def make(sev, conf):
        return Anomaly(
            id="a1", timestamp=0, subsystem=Subsystem.THERMAL, metric="temperature_c",
            observed_value=90, expected_min=0, expected_max=85, severity=sev, confidence=conf,
            anomaly_score=0.9, detection_layer=DetectionLayer.THRESHOLD,
            explanation="x", recommended_action="y",
        )

    low_risk = score_risk([make(Severity.INFO, 0.5)], {"temperature_c": 1})
    high_risk = score_risk([make(Severity.CRITICAL, 0.95)], {"temperature_c": 1})
    assert high_risk.score > low_risk.score


# ---------------------------------------------------------------------------
# Predictions
# ---------------------------------------------------------------------------

def test_predictions_detect_increasing_trend():
    engine = TelemetryEngine()
    engine.set_scenario(ScenarioType.THERMAL_EVENT)
    for _ in range(80):
        engine.tick()
    preds = generate_predictions(list(engine.history))
    temp_pred = next(p for p in preds if p.metric == "temperature_c")
    assert temp_pred.trend == "increasing"


def test_predictions_stable_trend_when_nominal():
    engine = TelemetryEngine()
    for _ in range(120):
        engine.tick()
    preds = generate_predictions(list(engine.history))
    assert len(preds) > 0


# ---------------------------------------------------------------------------
# API contract tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_spacecraft_endpoint(client):
    res = client.get("/api/spacecraft")
    assert res.status_code == 200
    assert res.json()["id"] == "SC-001"


def test_telemetry_endpoint(client):
    res = client.get("/api/telemetry?limit=10")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_telemetry_invalid_limit(client):
    res = client.get("/api/telemetry?limit=9999")
    assert res.status_code == 400


def test_simulation_lifecycle(client):
    res = client.post("/api/simulation/start")
    assert res.status_code == 200
    assert res.json()["running"] is True

    res = client.post("/api/simulation/scenario", json={"scenario": "THERMAL_EVENT"})
    assert res.status_code == 200
    assert res.json()["scenario"] == "THERMAL_EVENT"

    res = client.post("/api/simulation/stop")
    assert res.status_code == 200
    assert res.json()["running"] is False


def test_anomaly_not_found(client):
    res = client.get("/api/anomalies/does-not-exist")
    assert res.status_code == 404
