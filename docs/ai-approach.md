# SpaceSentinel — AI / ML Approach

This document exists to be precise about what is, and is not, "AI" in this
prototype. Nothing here is hidden or exaggerated.

## 1. Anomaly Detection (hybrid, `backend/app/anomaly.py`)

| Layer | Technique | What it catches |
|---|---|---|
| 1 — Threshold | Deterministic min/max rules per metric | Hard safety-limit breaches |
| 2 — Statistical | Rolling-window z-score comparing a recent-sample mean against an older baseline mean/std | Sustained trends/ramps that haven't hit a hard limit yet |
| 3 — Machine Learning | **scikit-learn `IsolationForest`**, trained once at startup on synthetic samples drawn from the nominal operating envelope (Gaussian around each metric's setpoint/noise) | Multivariate outliers — combinations of metrics that look unusual together even if no single metric is extreme |

When multiple layers flag the same metric in the same tick, confidence and
severity are boosted (`_merge` in `anomaly.py`) — this is simple rule-based
score fusion, not a learned ensemble.

**Why a fixed ML baseline instead of continuous retraining:** an earlier
version retrained IsolationForest on a trailing window of live telemetry.
That caused the model to "learn" a slow thermal ramp as the new normal
after enough time passed, silently losing sensitivity — the opposite of
what a safety system should do. The fixed baseline (trained once on known-
good synthetic data) keeps recognizing sustained drift as abnormal for as
long as it deviates from true nominal.

## 2. Mission Risk Scoring (`backend/app/risk.py`)

**This is not a random number and not a model.** It is a fully transparent,
documented formula:

```
contribution(anomaly) = severity_weight(anomaly.severity)
                         × anomaly.confidence
                         × persistence_multiplier(anomaly.metric)

risk_score = sum(contribution) + multi_subsystem_bonus
```

- `severity_weight`: INFO=8, WARNING=22, CRITICAL=40 (NORMAL=0)
- `persistence_multiplier`: grows (capped at 1.5x) the longer an anomaly
  has been continuously active, so a one-tick blip weighs less than a
  sustained condition
- `multi_subsystem_bonus`: +6 per additional distinct subsystem affected,
  reflecting that correlated cross-subsystem failures are riskier than
  isolated ones
- Final score is clamped to [0, 100] and mapped to LOW / MODERATE / HIGH /
  CRITICAL bands

## 3. Predictive Monitoring (`backend/app/prediction.py`)

Ordinary least-squares linear regression fit to the last ~60 telemetry
samples per watched metric. Reports:
- trend direction (increasing / decreasing / stable)
- rate per minute
- projected value 10 minutes out
- estimated time-to-threshold-crossing, when the trend points toward the
  configured limit
- a confidence score derived from the linear fit's R²

This is a simple statistical projection over noisy simulated data. It is
explicitly **not** presented as flight-grade predictive accuracy anywhere
in the UI or docs.

## 4. AI Analysis / Explanations (`backend/app/ai_analysis.py`)

**This is a deterministic, rule-based natural-language generator — a
template-and-evidence composer, not a call to any large language model.**
It takes the current active anomalies, risk assessment, and predictions,
and composes human-readable analysis + recommended actions from a fixed
set of templates keyed on subsystem and severity. This keeps every
sentence traceable back to the exact evidence that produced it, which is
the point of "explainable AI" for a safety-relevant system — and it means
the system never fabricates evidence it doesn't have.

## Summary of honesty commitments

- The system never claims real-time control of an actual spacecraft.
- The system never claims a specific numeric prediction accuracy that
  hasn't been measured against ground truth (there is no ground truth in
  a simulation).
- "AI Analysis" text is rule-based NLG, clearly documented as such, not an
  LLM.
- The only trained machine-learning model in the system is the
  IsolationForest anomaly detector, and its training data and process are
  documented above.
