# SpaceSentinel — Competition Submission Checklist

**AI Builders Challenge with IBM Bob — August 2026**
**Theme: Advance Space Exploration with AI**

Use this as the final pre-submission gate. Do not submit until every item
is genuinely true.

## Product
- [x] Working prototype (backend + frontend run and communicate)
- [x] Spacecraft telemetry simulation (5 scenarios)
- [x] Hybrid anomaly detection (threshold + statistical + ML)
- [x] Transparent mission risk scoring
- [x] Predictive monitoring with trend + time-to-threshold
- [x] Rule-based explainable AI analysis
- [x] Actionable recommendations per anomaly/insight
- [x] Mission dashboard (Overview page)
- [x] Telemetry charts for all monitored metrics
- [x] Anomaly Center with detail view
- [x] Simulation scenario controls + event timeline
- [x] Responsive, polished dark "mission control" UI
- [x] Automated backend tests (16 passing)
- [x] Security review pass documented

## Repository
- [ ] Public GitHub repository created and pushed (must be done from your
      local machine — see README "Exporting to your machine")
- [x] Clean project structure (`backend/`, `frontend/`, `docs/`, tests)
- [x] `.gitignore` correctly excludes secrets, `node_modules`, `.db` files,
      `.env`
- [x] Meaningful, conventional commit messages

## Documentation
- [x] README with problem statement, solution, theme, architecture, AI/ML
      approach, tech stack, run instructions
- [x] `docs/architecture.md`
- [x] `docs/ai-approach.md`
- [x] `docs/simulation.md`
- [x] `docs/testing.md`
- [x] `docs/development-workflow.md` (honest IBM Bob usage tracking)
- [ ] IBM Bob usage section filled in with real, specific contributions
      (not yet — Bob phase has not run)
- [ ] Screenshots added to README (placeholders currently)

## Competition requirements
- [ ] IBM Bob given a genuine, meaningful implementation task and its
      real contribution documented
- [ ] Required IBM SkillsBuild learning activity completed
- [ ] Public project submission made
- [ ] Public demo video recorded (max 3 minutes) — see suggested flow
      below
- [ ] Submission form / entry completed per official challenge rules

## Suggested 3-minute demo flow

1. (0:00-0:20) Open Overview — show nominal spacecraft status.
2. (0:20-0:40) Show Telemetry page — live charts.
3. (0:40-1:10) Go to Simulation, start it, trigger Thermal Event.
4. (1:10-1:40) Watch telemetry rise, switch to Anomalies — show the new
   anomaly appear with severity escalating.
5. (1:40-2:05) Show Mission Risk climbing on Overview/Simulation.
6. (2:05-2:30) Show AI Analysis page with the generated insight and
   recommended action.
7. (2:30-2:45) Show Predictions page with time-to-threshold estimate.
8. (2:45-3:00) Trigger Multi-Subsystem Anomaly briefly, end on Overview
   dashboard showing the full picture.

This checklist should be revisited immediately before submission.
