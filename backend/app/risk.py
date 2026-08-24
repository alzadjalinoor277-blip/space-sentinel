"""
Mission risk scoring for SpaceSentinel.

The risk score (0-100) is a transparent, deterministic function of the
currently active anomalies -- not a random or hidden number. It considers:

  1. Severity of each active anomaly (weighted).
  2. Detection confidence (low-confidence anomalies contribute less).
  3. Number of distinct subsystems affected (correlated failures compound risk).
  4. Persistence: anomalies that keep reappearing contribute more than a
     single blip.

Score bands:
  0-29   LOW
  30-59  MODERATE
  60-79  HIGH
  80-100 CRITICAL
"""
from __future__ import annotations

import time
from collections import Counter

from .models import Anomaly, RiskAssessment, RiskBreakdown, RiskLevel, Severity, Subsystem

SEVERITY_WEIGHT = {
    Severity.NORMAL: 0.0,
    Severity.INFO: 8.0,
    Severity.WARNING: 22.0,
    Severity.CRITICAL: 40.0,
}

SUBSYSTEM_TO_BREAKDOWN_KEY = {
    Subsystem.THERMAL: "thermal",
    Subsystem.POWER: "power",
    Subsystem.RADIATION: "radiation",
    Subsystem.COMMUNICATION: "communication",
    Subsystem.NAVIGATION: "navigation",
    Subsystem.PROPULSION: "propulsion",
    Subsystem.COMPUTE: "power",  # compute load folded into power domain for the gauge
}


def _level(score: float) -> RiskLevel:
    if score >= 80:
        return RiskLevel.CRITICAL
    if score >= 60:
        return RiskLevel.HIGH
    if score >= 30:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def score_risk(active_anomalies: list[Anomaly], anomaly_persistence: dict[str, int]) -> RiskAssessment:
    breakdown = {k: 0.0 for k in ("thermal", "power", "radiation", "communication", "navigation", "propulsion")}
    total = 0.0
    contributing_ids = []

    affected_subsystems = {a.subsystem for a in active_anomalies}
    multi_subsystem_bonus = max(0, len(affected_subsystems) - 1) * 6.0

    for a in active_anomalies:
        base = SEVERITY_WEIGHT[a.severity] * a.confidence
        persistence = anomaly_persistence.get(a.metric, 1)
        persistence_multiplier = min(1.5, 1 + (persistence - 1) * 0.08)
        contribution = base * persistence_multiplier

        key = SUBSYSTEM_TO_BREAKDOWN_KEY.get(a.subsystem, "power")
        breakdown[key] = min(100.0, breakdown[key] + contribution)
        total += contribution
        contributing_ids.append(a.id)

    total += multi_subsystem_bonus
    score = float(min(100.0, total))
    level = _level(score)

    if not active_anomalies:
        explanation = "All subsystems nominal. No active anomalies contributing to mission risk."
    else:
        top = max(active_anomalies, key=lambda a: SEVERITY_WEIGHT[a.severity] * a.confidence)
        explanation = (
            f"Risk driven primarily by {top.subsystem.value.title()} subsystem "
            f"({top.severity.value.lower()} severity, {int(top.confidence * 100)}% confidence)"
        )
        if len(affected_subsystems) > 1:
            explanation += f", with {len(affected_subsystems)} subsystems currently affected."
        else:
            explanation += "."

    return RiskAssessment(
        timestamp=time.time(),
        score=round(score, 1),
        level=level,
        breakdown=RiskBreakdown(**{k: round(v, 1) for k, v in breakdown.items()}),
        contributing_anomaly_ids=contributing_ids,
        explanation=explanation,
    )
