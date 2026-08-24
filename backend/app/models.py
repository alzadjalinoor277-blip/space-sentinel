"""
SpaceSentinel data models.

These Pydantic models define the core domain objects that flow through the
pipeline: Telemetry -> Anomaly Detection -> Risk Scoring -> Prediction ->
AI Explanation -> Mission Dashboard.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    NORMAL = "NORMAL"
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AnomalyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DetectionLayer(str, Enum):
    THRESHOLD = "THRESHOLD"          # deterministic rule
    STATISTICAL = "STATISTICAL"      # z-score / rolling deviation
    ML_ISOLATION_FOREST = "ML_ISOLATION_FOREST"  # learned model


class ScenarioType(str, Enum):
    NORMAL = "NORMAL"
    THERMAL_EVENT = "THERMAL_EVENT"
    POWER_INSTABILITY = "POWER_INSTABILITY"
    COMMUNICATION_DEGRADATION = "COMMUNICATION_DEGRADATION"
    MULTI_SUBSYSTEM_ANOMALY = "MULTI_SUBSYSTEM_ANOMALY"


class Subsystem(str, Enum):
    THERMAL = "THERMAL"
    POWER = "POWER"
    RADIATION = "RADIATION"
    COMMUNICATION = "COMMUNICATION"
    COMPUTE = "COMPUTE"
    PROPULSION = "PROPULSION"
    NAVIGATION = "NAVIGATION"


# ---------------------------------------------------------------------------
# Core objects
# ---------------------------------------------------------------------------

class Spacecraft(BaseModel):
    id: str
    name: str
    mission: str
    status: str
    orbit: str
    mission_time_seconds: int


class TelemetryPoint(BaseModel):
    timestamp: float
    temperature_c: float
    battery_voltage_v: float
    battery_percent: float
    power_consumption_w: float
    radiation_level_msv: float
    comm_signal_strength_pct: float
    cpu_load_pct: float
    memory_usage_pct: float
    fuel_percent: float
    altitude_km: float
    velocity_kms: float


class Anomaly(BaseModel):
    id: str
    timestamp: float
    subsystem: Subsystem
    metric: str
    observed_value: float
    expected_min: float
    expected_max: float
    severity: Severity
    confidence: float = Field(ge=0, le=1)
    anomaly_score: float
    detection_layer: DetectionLayer
    explanation: str
    recommended_action: str
    status: AnomalyStatus = AnomalyStatus.ACTIVE


class RiskBreakdown(BaseModel):
    thermal: float
    power: float
    radiation: float
    communication: float
    navigation: float
    propulsion: float


class RiskAssessment(BaseModel):
    timestamp: float
    score: float = Field(ge=0, le=100)
    level: RiskLevel
    breakdown: RiskBreakdown
    contributing_anomaly_ids: list[str]
    explanation: str


class Prediction(BaseModel):
    metric: str
    subsystem: Subsystem
    current_value: float
    threshold: float
    trend: str  # "increasing" | "decreasing" | "stable"
    trend_rate_per_min: float
    predicted_value_10min: float
    confidence: float = Field(ge=0, le=1)
    time_to_threshold_minutes: Optional[float] = None
    insight: str


class MissionEvent(BaseModel):
    id: str
    timestamp: float
    category: str  # "SIMULATION" | "ANOMALY" | "SYSTEM" | "RISK"
    severity: Severity
    message: str


class AIInsight(BaseModel):
    id: str
    timestamp: float
    title: str
    confidence: float = Field(ge=0, le=1)
    analysis: str
    recommended_action: str
    related_subsystems: list[Subsystem]
    related_anomaly_ids: list[str]


class SimulationScenarioRequest(BaseModel):
    scenario: ScenarioType


class SimulationStatus(BaseModel):
    running: bool
    scenario: ScenarioType
    elapsed_seconds: float
    speed: float
