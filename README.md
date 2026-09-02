# 🚀 SpaceSentinel

**AI-powered predictive spacecraft health and anomaly monitoring platform**

> IBM Bob AI Builders Challenge — August Theme: **Advance Space Exploration with AI**

## 🌌 Problem

Spacecraft continuously generate telemetry from multiple systems. Detecting abnormal behavior early is critical because small deviations in temperature, power, communication, or other telemetry can develop into larger mission risks.

Traditional monitoring can require continuous manual analysis of telemetry and alerts.

## 💡 Solution

**SpaceSentinel** is a web-based spacecraft mission monitoring platform that uses synthetic spacecraft telemetry to detect anomalies, assess mission risk, generate predictions, and provide AI-assisted insights.

The platform provides a mission-control style dashboard where users can:

* Monitor live spacecraft telemetry
* Detect abnormal telemetry behavior
* View spacecraft health and mission status
* Calculate an overall mission risk assessment
* Generate predictive insights
* Simulate different spacecraft scenarios
* Review mission and anomaly logs

All spacecraft telemetry and scenarios are simulated for demonstration purposes.

## 🤖 How IBM Bob Was Used

IBM Bob was used as the primary AI development assistant throughout the project.

Bob assisted with:

* Project architecture and application structure
* Frontend and backend development
* FastAPI API implementation
* React/Vite frontend development
* Simulation logic
* Telemetry generation
* Anomaly detection workflow
* Risk assessment functionality
* Debugging and troubleshooting
* CORS configuration
* Deployment preparation
* Documentation and project organization
* Iterative testing and refinement

The development process used AI-assisted iteration to move from the initial concept to a working full-stack prototype.

## 🏗️ Architecture

```text
                    ┌──────────────────────┐
                    │      User / Demo     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   React + Vite UI    │
                    │    GitHub Pages       │
                    └──────────┬───────────┘
                               │ HTTPS API
                               ▼
                    ┌──────────────────────┐
                    │   FastAPI Backend    │
                    │       Render         │
                    └──────────┬───────────┘
                               │
             ┌─────────────────┼─────────────────┐
             ▼                 ▼                 ▼
      Telemetry Engine   Anomaly Detection   Risk Engine
             │                 │                 │
             └─────────────────┼─────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │ Predictions & AI     │
                    │ Insights + Mission   │
                    │ Logs                 │
                    └──────────────────────┘
```

## 🧠 AI & Monitoring Approach

SpaceSentinel processes synthetic telemetry through several monitoring components:

### Telemetry Engine

Generates simulated spacecraft telemetry and maintains the mission history.

### Anomaly Detection

Analyzes telemetry history and identifies abnormal behavior across spacecraft metrics.

### Risk Assessment

Combines active anomalies and their persistence to calculate an overall mission risk level.

### Prediction Engine

Uses telemetry history to generate predictions about potential spacecraft conditions.

### AI Insights

Combines detected anomalies, risk assessment, and predictions to produce mission-oriented insights.

## 🛰️ Simulation

The platform includes an interactive simulation system.

Users can:

1. Start the simulation
2. Select a spacecraft scenario
3. Generate synthetic telemetry
4. Observe the monitoring dashboard
5. Detect anomalies
6. Observe changes in mission risk
7. Review generated mission events

The simulation allows the system to demonstrate how a spacecraft monitoring platform could react to changing telemetry conditions without interacting with real spacecraft.

## 🌐 Live Demo

**Application:**
https://alzadjalinoor277-blip.github.io/space-sentinel/

**Backend API:**
https://space-sentinel.onrender.com

**Health Check:**
https://space-sentinel.onrender.com/api/health

## 📸 IBM Bob Evidence

Screenshots documenting the IBM Bob development process are included in:

`docs/bob-evidence/`

These screenshots demonstrate the AI-assisted development workflow used to build and refine SpaceSentinel.

## 🎥 Demo Video

A short demonstration video shows:

1. SpaceSentinel dashboard
2. Spacecraft telemetry
3. Simulation controls
4. Scenario activation
5. Anomaly detection
6. Risk assessment
7. Mission logs
8. Final working application

**Demo Video:**
[Watch the SpaceSentinel Demo](https://www.youtube.com/watch?v=n_XNagri7q4)

## 🛠️ Technology Stack

**Frontend**

* React
* Vite
* JavaScript
* GitHub Pages

**Backend**

* Python
* FastAPI
* Uvicorn

**AI / Data**

* Scikit-learn
* Pandas
* NumPy
* Predictive analysis
* Anomaly detection

**Deployment**

* GitHub Pages
* Render

**Development**

* IBM Bob
* Git
* GitHub

## 🚀 Running Locally

### Backend

```bash
cd backend

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

### Frontend

```bash
cd frontend

npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## ⚠️ Disclaimer

SpaceSentinel is an educational simulation and proof-of-concept.

It does **not** control or communicate with real spacecraft. All telemetry and spacecraft scenarios are synthetically generated.

## 👤 Author

**Noor Al-Zadjali**

Computer Security Graduate
Oman

GitHub:
https://github.com/alzadjalinoor277-blip

---

Built for the **IBM Bob AI Builders Challenge** 🚀
