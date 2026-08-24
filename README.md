# SpaceSentinel

**AI-Powered Predictive Spacecraft Health and Anomaly Monitoring**

A simulated spacecraft mission-control platform: real-time telemetry
monitoring, hybrid anomaly detection, transparent mission risk scoring,
predictive trend analysis, and explainable AI-assisted recommendations for
mission operators.

> **This is a simulation and proof-of-concept prototype.** It does not
> control any real spacecraft. All telemetry is synthetically generated.

Built for the **AI Builders Challenge with IBM Bob — August 2026**.

## Challenge Theme

**Advance Space Exploration with AI**

## Problem Statement

Modern spacecraft generate continuous streams of telemetry across many
subsystems simultaneously — thermal, power, radiation, communications,
compute, propulsion, and navigation. A single-metric threshold alarm
catches obvious failures, but it misses slow-developing trends and, more
importantly, misses **correlated** anomalies across subsystems that share
a root cause. Mission operators need a system that can detect abnormal
behavior early, explain *why* it's abnormal in plain language, quantify
overall mission risk transparently, and estimate how much time remains
before a trend becomes a hard safety violation.

## Solution

SpaceSentinel implements the full pipeline from raw telemetry to
operator-ready recommendations:

```
Telemetry → Validation → Anomaly Detection → Correlation → Risk Scoring
→ Trend Analysis → Prediction → Explanation → Recommended Action → Dashboard
```

- A **hybrid 3-layer anomaly detector** (hard thresholds, statistical
  trend deviation, and an Isolation Forest ML model) catches both sudden
  breaches and slow-developing ramps.
- A **transparent, documented risk score** (0-100) weighs severity,
  confidence, persistence, and how many subsystems are affected — no
  hidden or random numbers.
- **Predictive monitoring** projects current trends forward and estimates
  time-to-threshold using simple, explainable linear regression.
- **Rule-based explainable AI analysis** composes human-readable
  diagnosis and recommended actions directly from the evidence — this is
  deterministic natural-language generation, **not** a call to a large
  language model, and is labeled as such throughout.
- A **5-scenario simulation engine** (Normal, Thermal Event, Power
  Instability, Communication Degradation, Multi-Subsystem Anomaly) drives
  a live, compelling demonstration.

## Key Features

- Real-time mission dashboard with live spacecraft status, risk, and
  orbital visualization
- Full telemetry charts (temperature, battery, power, radiation, comms,
  CPU, memory, fuel) with threshold overlays
- SOC/SIEM-style Anomaly Center with detail drill-down (observed value,
  expected range, detection layer, explanation, recommended action)
- AI Analysis page with confidence-scored, evidence-cited insights
- Predictions page with trend direction, projected values, and
  time-to-threshold
- Interactive Simulation page: start/stop, scenario selector, live event
  timeline
- Mission Logs with category filtering
- Dark, glassmorphic "mission control" UI — no generic admin-dashboard
  template

## Architecture

See [`docs/architecture.md`](docs/architecture.md) for the full diagram
and module breakdown. Summary:

- **Backend:** Python, FastAPI, Pydantic, NumPy, Pandas, scikit-learn,
  SQLite
- **Frontend:** React, Vite, TypeScript, Tailwind CSS, Recharts, Lucide
  icons
- REST polling (1.5-3s intervals) between frontend and backend; see
  `docs/architecture.md` for why polling was chosen over WebSockets for
  this MVP

## AI / ML Approach

See [`docs/ai-approach.md`](docs/ai-approach.md) for full detail,
including exact formulas and an honest breakdown of what is/isn't machine
learning. In short:

- **Anomaly detection:** deterministic thresholds + statistical z-score +
  scikit-learn `IsolationForest` (trained once on a fixed nominal
  baseline, not continuously retrained — see the doc for why that matters)
- **Risk scoring:** a documented deterministic formula, not a model
- **Prediction:** ordinary least-squares linear regression over recent
  telemetry
- **"AI Analysis":** rule-based template + evidence composition — clearly
  not an LLM call

## IBM Bob Usage

*To be completed once the IBM Bob development phase runs. This project
maintains an honest, evidence-based record of tool usage in*
[`docs/development-workflow.md`](docs/development-workflow.md) *— that
file will be updated with the specific task given to Bob and what Bob
actually produced, and this section will then summarize it. No Bob
contribution is claimed here or anywhere in this submission until it has
genuinely happened.*

## Claude Code Usage

Claude Code was used for the full initial build documented in this
repository: project scaffolding, backend (data models, simulation engine,
hybrid anomaly detection, risk scoring, prediction, rule-based AI
analysis, SQLite persistence, REST API), backend automated tests (16
passing) plus live manual end-to-end verification (including diagnosing
and fixing a real anomaly-detection bug found during that verification —
see `docs/testing.md`), the full frontend (design system, all 9 pages,
routing, charts, live polling), a security review pass, and this
documentation set. Full detail in
[`docs/development-workflow.md`](docs/development-workflow.md).

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React, Vite, TypeScript, Tailwind CSS v4, Recharts, Lucide React, React Router |
| Backend | Python 3.12, FastAPI, Pydantic, Uvicorn |
| Data / ML | NumPy, Pandas, scikit-learn (Isolation Forest) |
| Database | SQLite |
| Testing | pytest, FastAPI TestClient |

## Running Locally

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+
- Git

### Backend

```bash
cd backend
pip install -r requirements.txt --break-system-packages
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verify: `curl http://127.0.0.1:8000/api/health` should return
`{"status":"ok",...}`.

### Frontend

```bash
cd frontend
cp .env.example .env   # points the frontend at the local backend
npm install
npm run dev
```

Open the printed local URL (default `http://localhost:5173`). The
dashboard will show "CONNECTING" briefly, then live spacecraft data.

### Starting a demo scenario

From the **Simulation** page in the UI, click **Start Simulation**, then
select any scenario (e.g. **Thermal Event**). Or via API:

```bash
curl -X POST http://127.0.0.1:8000/api/simulation/start
curl -X POST http://127.0.0.1:8000/api/simulation/scenario \
  -H "Content-Type: application/json" \
  -d '{"scenario":"THERMAL_EVENT"}'
```

## Simulation Scenarios

See [`docs/simulation.md`](docs/simulation.md) for full detail on all 5
scenarios and what to expect during a demo run.

## Testing

```bash
cd backend
python3 -m pytest tests/ -v
```

16 automated tests covering telemetry generation, all three anomaly
detection layers, risk scoring, prediction/trend logic, and API contracts.
See [`docs/testing.md`](docs/testing.md) for full coverage notes and a
record of manual end-to-end verification (including a real bug found and
fixed during testing).

## Screenshots

*Placeholder — screenshots to be added before final submission.*

## Demo

*Placeholder — public demo video link (max 3 minutes) to be added before
final submission. See the suggested demo flow in*
[`docs/competition-submission.md`](docs/competition-submission.md)*.*

## Competition

Submitted to the **AI Builders Challenge with IBM Bob**, August 2026,
theme *Advance Space Exploration with AI*. See
[`docs/competition-submission.md`](docs/competition-submission.md) for the
full submission checklist.

## License

See [`LICENSE`](LICENSE).
