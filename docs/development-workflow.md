# SpaceSentinel — Development Workflow

## Tools used and division of labor

This project is being built for the **AI Builders Challenge with IBM Bob**
(August 2026, theme: *Advance Space Exploration with AI*), which requires
IBM Bob to have a genuine, meaningful role in development. This document
tracks, honestly, what was done with which tool. **Nothing in this file
should ever be edited to claim work that didn't actually happen.**

### Completed with Claude Code (this session)

- Project scaffolding (backend FastAPI app, frontend Vite/React/TS app,
  repo structure, `.gitignore`)
- Backend: data models, telemetry simulation engine, hybrid 3-layer
  anomaly detector, transparent risk scorer, trend/prediction module,
  rule-based AI insight generator, SQLite persistence, REST API
- Backend automated test suite (16 pytest tests) and live manual
  end-to-end verification against a running server, including diagnosing
  and fixing a real bug (IsolationForest baseline drift — see
  `docs/testing.md`)
- Frontend: design system (dark space mission-control theme, glassmorphism,
  Inter/JetBrains Mono typography), all 9 pages (Overview, Spacecraft,
  Telemetry, Anomalies, AI Analysis, Predictions, Simulation, Mission Logs,
  Settings), routing, polling data layer, chart components, orbit
  visualization
- Security review pass (CORS scoping, secret-scanning, input validation,
  `.gitignore` audit)
- All project documentation in `docs/` and the root `README.md`

### Planned for IBM Bob

Per the competition requirement, IBM Bob will be given a meaningful,
scoped implementation or improvement task on this codebase — not a token
task. The specific task prompt for Bob will be prepared once the person
running this project confirms they're ready for that phase, and Bob's
actual output will be reviewed, tested, and documented here with specifics
(what was asked, what Bob produced, what if anything was changed
afterward) rather than a generic claim of involvement.

**This section will be updated with real specifics once that phase runs.
Until then, no IBM Bob contribution should be claimed in the submission.**

## Git workflow

Commits follow conventional, descriptive messages (`feat:`, `fix:`,
`test:`, `docs:`) rather than vague messages like "update" or "fix stuff".
See the repository's commit history for the full record.

## Known follow-ups (not blocking the MVP)

- Frontend component test suite (Vitest + React Testing Library)
- WebSocket/SSE push instead of REST polling for lower-latency updates
- Code-splitting the frontend bundle (currently a single ~640KB JS chunk;
  functional but larger than ideal — see `docs/testing.md` performance
  notes)
- Configurable/persisted user settings (the Settings page's refresh-rate
  slider is currently a UI preview, not yet wired to actual poll intervals)
