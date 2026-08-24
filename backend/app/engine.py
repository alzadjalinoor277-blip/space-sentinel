"""
SpaceSentinel telemetry simulation engine.

Generates realistic, continuously-fluctuating spacecraft telemetry. A
"normal mission" baseline uses small stochastic noise around nominal
setpoints. Scenarios perturb one or more metrics with a directional trend
layered on top of the same noise model, so the transition from nominal to
anomalous behavior looks organic rather than switched on/off.

This is a simulation for demonstration purposes only. It does not model
real spacecraft physics and must never be represented as flight-grade.
"""
from __future__ import annotations

import time
import uuid
from collections import deque
from dataclasses import dataclass, field

import numpy as np

from .models import ScenarioType, TelemetryPoint

HISTORY_MAXLEN = 600  # ~10 minutes at 1Hz tick, plenty for charts + ML baseline

# Nominal operating setpoints and safe thresholds for each metric.
# thresholds are the deterministic "Layer 1" safety limits referenced
# throughout the app (charts, anomaly detection, predictions).
NOMINAL = {
    "temperature_c": {"setpoint": 21.0, "noise": 0.6, "min": -10.0, "max": 85.0},
    "battery_voltage_v": {"setpoint": 28.0, "noise": 0.15, "min": 24.0, "max": 32.0},
    "battery_percent": {"setpoint": 87.0, "noise": 0.8, "min": 20.0, "max": 100.0},
    "power_consumption_w": {"setpoint": 420.0, "noise": 8.0, "min": 150.0, "max": 900.0},
    "radiation_level_msv": {"setpoint": 0.42, "noise": 0.03, "min": 0.0, "max": 2.5},
    "comm_signal_strength_pct": {"setpoint": 92.0, "noise": 1.5, "min": 35.0, "max": 100.0},
    "cpu_load_pct": {"setpoint": 38.0, "noise": 3.0, "min": 0.0, "max": 95.0},
    "memory_usage_pct": {"setpoint": 54.0, "noise": 2.0, "min": 0.0, "max": 92.0},
    "fuel_percent": {"setpoint": 76.0, "noise": 0.05, "min": 5.0, "max": 100.0},
    "altitude_km": {"setpoint": 408.0, "noise": 0.4, "min": 350.0, "max": 450.0},
    "velocity_kms": {"setpoint": 7.66, "noise": 0.01, "min": 7.4, "max": 7.9},
}

METRIC_SUBSYSTEM = {
    "temperature_c": "THERMAL",
    "battery_voltage_v": "POWER",
    "battery_percent": "POWER",
    "power_consumption_w": "POWER",
    "radiation_level_msv": "RADIATION",
    "comm_signal_strength_pct": "COMMUNICATION",
    "cpu_load_pct": "COMPUTE",
    "memory_usage_pct": "COMPUTE",
    "fuel_percent": "PROPULSION",
    "altitude_km": "NAVIGATION",
    "velocity_kms": "NAVIGATION",
}


@dataclass
class ScenarioState:
    scenario: ScenarioType = ScenarioType.NORMAL
    started_at: float = field(default_factory=time.time)
    tick_in_scenario: int = 0


class TelemetryEngine:
    """Holds live telemetry state and produces the next simulated sample."""

    def __init__(self) -> None:
        self.history: deque[TelemetryPoint] = deque(maxlen=HISTORY_MAXLEN)
        self.scenario_state = ScenarioState()
        self.running = False
        self.speed = 1.0
        self.mission_start = time.time()
        self._rng = np.random.default_rng()
        # seed with a short baseline so charts aren't empty on first load
        for _ in range(30):
            self._advance(seed=True)

    # -- public API ---------------------------------------------------

    def start(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False
        self.scenario_state = ScenarioState(scenario=ScenarioType.NORMAL)

    def set_scenario(self, scenario: ScenarioType) -> None:
        self.scenario_state = ScenarioState(scenario=scenario)
        self.running = True

    def tick(self) -> TelemetryPoint:
        return self._advance(seed=False)

    def current(self) -> TelemetryPoint:
        return self.history[-1]

    def recent(self, n: int = 120) -> list[TelemetryPoint]:
        items = list(self.history)
        return items[-n:]

    def mission_elapsed_seconds(self) -> int:
        return int(time.time() - self.mission_start)

    # -- internals ------------------------------------------------------

    def _advance(self, seed: bool) -> TelemetryPoint:
        prev = self.history[-1] if self.history else None
        values: dict[str, float] = {}

        scenario = self.scenario_state.scenario if not seed else ScenarioType.NORMAL
        t = self.scenario_state.tick_in_scenario if not seed else 0

        for metric, cfg in NOMINAL.items():
            base = prev.__dict__[metric] if prev else cfg["setpoint"]
            target = cfg["setpoint"]
            noise = self._rng.normal(0, cfg["noise"])

            drift = self._scenario_drift(scenario, metric, t)

            # gentle mean-reversion toward setpoint + drift target, plus noise
            reverted = base + (target - base) * 0.02 + noise + drift
            clipped = float(np.clip(reverted, cfg["min"] - abs(cfg["min"]) * 0.2 if cfg["min"] != 0 else -5, cfg["max"] * 1.15))
            values[metric] = round(clipped, 3)

        point = TelemetryPoint(timestamp=time.time(), **values)
        self.history.append(point)
        if not seed:
            self.scenario_state.tick_in_scenario += 1
        return point

    def _scenario_drift(self, scenario: ScenarioType, metric: str, t: int) -> float:
        """Directional bias injected per scenario, ramping in over time."""
        ramp = min(t / 40.0, 1.0)  # reach full intensity after ~40 ticks

        if scenario == ScenarioType.NORMAL:
            return 0.0

        if scenario == ScenarioType.THERMAL_EVENT:
            if metric == "temperature_c":
                return ramp * 1.6
            if metric == "power_consumption_w":
                return ramp * 6.0
            if metric == "cpu_load_pct":
                return ramp * 0.4

        if scenario == ScenarioType.POWER_INSTABILITY:
            if metric == "battery_voltage_v":
                return -ramp * 0.18 + self._rng.normal(0, 0.25) * ramp
            if metric == "battery_percent":
                return -ramp * 0.9
            if metric == "power_consumption_w":
                return self._rng.normal(0, 25) * ramp

        if scenario == ScenarioType.COMMUNICATION_DEGRADATION:
            if metric == "comm_signal_strength_pct":
                return -ramp * 1.4

        if scenario == ScenarioType.MULTI_SUBSYSTEM_ANOMALY:
            if metric == "temperature_c":
                return ramp * 1.2
            if metric == "power_consumption_w":
                return ramp * 5.0
            if metric == "radiation_level_msv":
                return ramp * 0.035
            if metric == "comm_signal_strength_pct":
                return -ramp * 1.0
            if metric == "cpu_load_pct":
                return ramp * 0.6

        return 0.0


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10]}"
