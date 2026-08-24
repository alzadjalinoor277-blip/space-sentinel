"""
SpaceSentinel backend — FastAPI application.

This is a simulation and proof-of-concept mission-control platform. It does
not control real spacecraft. All telemetry is synthetically generated.
"""
from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import database as db
from .ai_analysis import generate_insights
from .anomaly import AnomalyDetector
from .engine import TelemetryEngine, new_id
from .models import (
    AIInsight,
    Anomaly,
    AnomalyStatus,
    MissionEvent,
    Prediction,
    RiskAssessment,
    ScenarioType,
    Severity,
    SimulationScenarioRequest,
    SimulationStatus,
    Spacecraft,
    TelemetryPoint,
)
from .prediction import generate_predictions
from .risk import score_risk

@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    state.log_event("SYSTEM", Severity.INFO, "SpaceSentinel backend initialized.")
    state.tick_task = asyncio.create_task(_simulation_loop())
    yield
    if state.tick_task:
        state.tick_task.cancel()


app = FastAPI(
    title="SpaceSentinel API",
    description="AI-powered predictive spacecraft health and anomaly monitoring (simulation).",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://alzadjalinoor277-blip.github.io",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# In-memory application state
# ---------------------------------------------------------------------------

class AppState:
    def __init__(self) -> None:
        self.engine = TelemetryEngine()
        self.detector = AnomalyDetector()
        self.active_anomalies: dict[str, Anomaly] = {}   # keyed by metric
        self.persistence: dict[str, int] = {}             # metric -> consecutive tick count
        self.risk: RiskAssessment = score_risk([], {})
        self.predictions: list[Prediction] = []
        self.insights: list[AIInsight] = []
        self.spacecraft = Spacecraft(
            id="SC-001",
            name="ORBIT-07",
            mission="SpaceSentinel Demonstration Mission",
            status="NOMINAL",
            orbit="LEO 408km",
            mission_time_seconds=0,
        )
        self.tick_task: Optional[asyncio.Task] = None

    def log_event(self, category: str, severity: Severity, message: str) -> None:
        event = MissionEvent(id=new_id("evt"), timestamp=time.time(), category=category, severity=severity, message=message)
        db.insert_event(event.model_dump(mode="json"))

    def reconcile_anomalies(self, candidates: list[Anomaly]) -> None:
        candidate_by_metric = {a.metric: a for a in candidates}

        # updated / new
        for metric, candidate in candidate_by_metric.items():
            if metric in self.active_anomalies:
                existing = self.active_anomalies[metric]
                self.persistence[metric] = self.persistence.get(metric, 1) + 1
                updated = candidate.model_copy(update={
                    "id": existing.id,
                    "status": AnomalyStatus.ACTIVE,
                })
                self.active_anomalies[metric] = updated
            else:
                self.persistence[metric] = 1
                self.active_anomalies[metric] = candidate
                self.log_event(
                    "ANOMALY", candidate.severity,
                    f"New anomaly detected: {candidate.metric.replace('_', ' ')} "
                    f"({candidate.severity.value}) on {candidate.subsystem.value} subsystem.",
                )

        # resolved
        resolved_metrics = [m for m in self.active_anomalies if m not in candidate_by_metric]
        for metric in resolved_metrics:
            resolved = self.active_anomalies.pop(metric)
            self.persistence.pop(metric, None)
            resolved = resolved.model_copy(update={"status": AnomalyStatus.RESOLVED})
            db.insert_anomaly_record(resolved.id, resolved.timestamp, resolved.model_dump(mode="json"))
            self.log_event(
                "ANOMALY", Severity.INFO,
                f"Anomaly resolved: {resolved.metric.replace('_', ' ')} returned to normal range.",
            )

    def step(self) -> None:
        self.engine.tick()
        history = self.engine.history
        candidates = self.detector.detect(list(history))
        self.reconcile_anomalies(candidates)

        active_list = list(self.active_anomalies.values())
        self.risk = score_risk(active_list, self.persistence)
        self.predictions = generate_predictions(list(history))
        self.insights = generate_insights(active_list, self.risk, self.predictions)

        self.spacecraft.status = self.risk.level.value if active_list else "NOMINAL"
        self.spacecraft.mission_time_seconds = self.engine.mission_elapsed_seconds()


state = AppState()


# ---------------------------------------------------------------------------
# Background simulation loop
# ---------------------------------------------------------------------------

async def _simulation_loop() -> None:
    while True:
        try:
            if state.engine.running:
                state.step()
        except Exception as exc:  # keep the loop alive; log and continue
            state.log_event("SYSTEM", Severity.WARNING, f"Simulation loop error handled: {exc}")
        await asyncio.sleep(1.0)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "simulation_running": state.engine.running, "time": time.time()}


@app.get("/api/spacecraft", response_model=Spacecraft)
def get_spacecraft() -> Spacecraft:
    return state.spacecraft


@app.get("/api/telemetry", response_model=list[TelemetryPoint])
def get_telemetry(limit: int = 120) -> list[TelemetryPoint]:
    if limit < 1 or limit > 600:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 600")
    return state.engine.recent(limit)


@app.get("/api/telemetry/current", response_model=TelemetryPoint)
def get_current_telemetry() -> TelemetryPoint:
    if not state.engine.history:
        raise HTTPException(status_code=404, detail="No telemetry available yet")
    return state.engine.current()


@app.get("/api/anomalies", response_model=list[Anomaly])
def get_anomalies(include_resolved: bool = True, limit: int = 100) -> list[Anomaly]:
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 500")
    active = list(state.active_anomalies.values())
    if not include_resolved:
        return sorted(active, key=lambda a: a.timestamp, reverse=True)
    resolved = [Anomaly(**r) for r in db.list_anomaly_history(limit)]
    combined = active + resolved
    combined.sort(key=lambda a: a.timestamp, reverse=True)
    return combined[:limit]


@app.get("/api/anomalies/{anomaly_id}", response_model=Anomaly)
def get_anomaly(anomaly_id: str) -> Anomaly:
    for a in state.active_anomalies.values():
        if a.id == anomaly_id:
            return a
    for r in db.list_anomaly_history(500):
        if r["id"] == anomaly_id:
            return Anomaly(**r)
    raise HTTPException(status_code=404, detail="Anomaly not found")


@app.get("/api/risk", response_model=RiskAssessment)
def get_risk() -> RiskAssessment:
    return state.risk


@app.get("/api/predictions", response_model=list[Prediction])
def get_predictions() -> list[Prediction]:
    return state.predictions


@app.get("/api/ai-insights", response_model=list[AIInsight])
def get_ai_insights() -> list[AIInsight]:
    return state.insights


@app.get("/api/mission-logs", response_model=list[MissionEvent])
def get_mission_logs(limit: int = 200) -> list[MissionEvent]:
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")
    rows = db.list_events(limit)
    return [MissionEvent(**r) for r in rows]


@app.post("/api/simulation/start", response_model=SimulationStatus)
def start_simulation() -> SimulationStatus:
    state.engine.start()
    state.log_event("SIMULATION", Severity.INFO, "Simulation started.")
    return _sim_status()


@app.post("/api/simulation/stop", response_model=SimulationStatus)
def stop_simulation() -> SimulationStatus:
    state.engine.stop()
    state.log_event("SIMULATION", Severity.INFO, "Simulation stopped and reset to normal mission baseline.")
    return _sim_status()


@app.post("/api/simulation/scenario", response_model=SimulationStatus)
def set_scenario(req: SimulationScenarioRequest) -> SimulationStatus:
    try:
        scenario = req.scenario
    except ValueError:
        raise HTTPException(status_code=400, detail="Unknown scenario")
    state.engine.set_scenario(scenario)
    state.log_event("SIMULATION", Severity.WARNING if scenario != ScenarioType.NORMAL else Severity.INFO,
                     f"Simulation scenario activated: {scenario.value.replace('_', ' ').title()}.")
    return _sim_status()


@app.get("/api/simulation/status", response_model=SimulationStatus)
def get_simulation_status() -> SimulationStatus:
    return _sim_status()


def _sim_status() -> SimulationStatus:
    return SimulationStatus(
        running=state.engine.running,
        scenario=state.engine.scenario_state.scenario,
        elapsed_seconds=time.time() - state.engine.scenario_state.started_at,
        speed=state.engine.speed,
    )
