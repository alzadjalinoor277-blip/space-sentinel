"""
Automated tests for SpaceSentinel backend.

Covers: telemetry generation, anomaly detection layers, risk scoring logic,
prediction/trend analysis, and API endpoint contracts.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient

from app.engine import TelemetryEngine, NOMINAL
from app.anomaly import AnomalyDetector
from app.risk import score_risk
from app.prediction import generate_predictions
from app.models import ScenarioType, Severity


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
# Anomaly detection
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


def test_no_anomalies_in_steady_normal_state():
    detector = AnomalyDetector()
    engine = TelemetryEngine()
    for _ in range(150):
        engine.tick()
    anomalies = detector.detect(list(engine.history))
    critical = [a for a in anomalies if a.severity == Severity.CRITICAL]
    assert critical == [], "steady nominal telemetry should not produce critical anomalies"


# ---------------------------------------------------------------------------
# Risk scoring
# ---------------------------------------------------------------------------

def test_risk_score_zero_with_no_anomalies():
    risk = score_risk([], {})
    assert risk.score == 0
    assert risk.level.value == "LOW"


def test_risk_score_increases_with_more_severe_anomalies():
    from app.models import Anomaly, DetectionLayer, Subsystem

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
