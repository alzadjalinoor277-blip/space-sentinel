# SpaceSentinel — Simulation Scenarios

All scenarios are driven by `backend/app/engine.py`. Each scenario applies
a directional "drift" on top of the same Gaussian noise model used for
normal operations, ramping in over roughly the first 40 ticks (~40 seconds)
so the transition looks organic rather than switched on/off.

| Scenario | Endpoint value | Behavior |
|---|---|---|
| Normal Mission | `NORMAL` | All metrics fluctuate around nominal setpoints with small noise. No sustained drift. |
| Thermal Event | `THERMAL_EVENT` | Temperature rises steadily; power consumption and CPU load increase alongside it (representing increased cooling/compute load). |
| Power Instability | `POWER_INSTABILITY` | Battery voltage and battery percentage decline and become noisier; power draw fluctuates unpredictably. |
| Communication Degradation | `COMMUNICATION_DEGRADATION` | Comm signal strength decays steadily. |
| Multi-Subsystem Anomaly | `MULTI_SUBSYSTEM_ANOMALY` | Temperature, power, radiation, and comm signal all drift simultaneously — demonstrates cross-subsystem correlation in the risk score and AI analysis. |

## Triggering a scenario

```
POST /api/simulation/start
POST /api/simulation/scenario   { "scenario": "THERMAL_EVENT" }
POST /api/simulation/stop
```

Or via the **Simulation** page in the UI, which exposes all five scenarios
as buttons plus a live event timeline.

## What to expect during a demo run

1. Telemetry charts on the Telemetry page begin trending immediately.
2. After ~15-30s, Layer 2 (statistical) or Layer 3 (ML) detection typically
   flags the drifting metric first, before it crosses the hard Layer 1
   threshold — this is intentional and demonstrates why a hybrid detector
   catches problems earlier than thresholds alone.
3. Mission risk score climbs from the Overview/Simulation pages as
   anomalies accumulate confidence and persistence.
4. AI Analysis generates a subsystem-specific insight, and — for the
   Multi-Subsystem scenario — an additional "correlated pattern" insight
   once more than one subsystem is affected.
5. Predictions page shows the trending metric with an estimated
   time-to-threshold once enough history has accumulated.
6. Stopping the simulation resets the scenario to Normal and anomalies
   resolve as telemetry returns to nominal ranges.
