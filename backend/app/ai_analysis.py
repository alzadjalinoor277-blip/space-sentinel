"""
AI Analysis for SpaceSentinel.

Generates explainable natural-language mission insights from the current
detection + risk + prediction state. This is a deterministic, rule-based
natural language generator (template + evidence composition) -- NOT a
call to a large language model. It is labeled as such throughout the UI
and docs so the AI approach is never misrepresented.
"""
from __future__ import annotations

import time

from .engine import new_id
from .models import AIInsight, Anomaly, Prediction, RiskAssessment, Subsystem

SUBSYSTEM_CONTEXT = {
    Subsystem.THERMAL: "thermal regulation",
    Subsystem.POWER: "power distribution",
    Subsystem.RADIATION: "radiation shielding",
    Subsystem.COMMUNICATION: "communications link",
    Subsystem.COMPUTE: "onboard compute",
    Subsystem.PROPULSION: "propulsion and propellant",
    Subsystem.NAVIGATION: "navigation and orbital tracking",
}


def generate_insights(
    anomalies: list[Anomaly],
    risk: RiskAssessment,
    predictions: list[Prediction],
) -> list[AIInsight]:
    if not anomalies:
        return [_nominal_insight(risk)]

    insights: list[AIInsight] = []
    by_subsystem: dict[Subsystem, list[Anomaly]] = {}
    for a in anomalies:
        by_subsystem.setdefault(a.subsystem, []).append(a)

    for subsystem, group in by_subsystem.items():
        insights.append(_subsystem_insight(subsystem, group, predictions, risk))

    if len(by_subsystem) > 1:
        insights.insert(0, _multi_subsystem_insight(by_subsystem, risk))

    return insights


def _nominal_insight(risk: RiskAssessment) -> AIInsight:
    return AIInsight(
        id=new_id("ai"),
        timestamp=time.time(),
        title="All Systems Nominal",
        confidence=0.95,
        analysis=(
            "No anomalies detected across monitored subsystems. Telemetry is within "
            "expected operating ranges and mission risk is low."
        ),
        recommended_action="Continue routine monitoring. No operator action required.",
        related_subsystems=[],
        related_anomaly_ids=[],
    )


def _subsystem_insight(
    subsystem: Subsystem,
    group: list[Anomaly],
    predictions: list[Prediction],
    risk: RiskAssessment,
) -> AIInsight:
    top = max(group, key=lambda a: a.anomaly_score)
    context = SUBSYSTEM_CONTEXT.get(subsystem, subsystem.value.lower())
    related_pred = next((p for p in predictions if p.subsystem == subsystem and p.time_to_threshold_minutes), None)

    confidence = top.confidence
    analysis = (
        f"The {context} subsystem is showing {top.severity.value.lower()}-level abnormal behavior "
        f"in {top.metric.replace('_', ' ')}, correlated across {len(group)} anomaly signal(s). "
        f"{top.explanation}"
    )
    if related_pred:
        analysis += f" {related_pred.insight}"

    return AIInsight(
        id=new_id("ai"),
        timestamp=time.time(),
        title=f"{subsystem.value.title()} Subsystem Anomaly Detected",
        confidence=round(confidence, 2),
        analysis=analysis,
        recommended_action=top.recommended_action,
        related_subsystems=[subsystem],
        related_anomaly_ids=[a.id for a in group],
    )


def _multi_subsystem_insight(by_subsystem: dict[Subsystem, list[Anomaly]], risk: RiskAssessment) -> AIInsight:
    subsystems = list(by_subsystem.keys())
    names = ", ".join(s.value.title() for s in subsystems)
    all_ids = [a.id for group in by_subsystem.values() for a in group]
    avg_conf = sum(a.confidence for group in by_subsystem.values() for a in group) / max(1, len(all_ids))

    return AIInsight(
        id=new_id("ai"),
        timestamp=time.time(),
        title="Correlated Multi-Subsystem Anomaly Pattern",
        confidence=round(min(0.97, avg_conf + 0.05), 2),
        analysis=(
            f"Anomalies are occurring simultaneously across {len(subsystems)} subsystems "
            f"({names}), raising mission risk to {risk.level.value} ({risk.score:.0f}/100). "
            "Correlated cross-subsystem anomalies are more significant than isolated single-metric "
            "deviations and may share a common root cause."
        ),
        recommended_action=(
            "Prioritize investigation of the highest-severity subsystem first, then verify whether "
            "other affected subsystems share a common upstream cause (e.g. power bus, thermal load)."
        ),
        related_subsystems=subsystems,
        related_anomaly_ids=all_ids,
    )
