# SpaceSentinel — Testing

## Backend automated tests

Location: `backend/tests/test_backend.py` (pytest + FastAPI TestClient)

Run:
```bash
cd backend
pip install -r requirements.txt --break-system-packages
python3 -m pytest tests/ -v
```

Coverage (16 tests):
- Telemetry engine: nominal bounds under normal scenario; directional
  drift for thermal, power-instability, and communication-degradation
  scenarios
- Anomaly detection: threshold layer flags a genuine breach; steady
  nominal telemetry produces zero critical anomalies (no false alarms)
- Risk scoring: zero risk with no anomalies; risk increases with severity
- Predictions: increasing trend detected under a thermal event; predictions
  are produced once enough history exists
- API contract tests: health, spacecraft, telemetry (including invalid
  `limit` returns 400), full simulation lifecycle (start → scenario →
  stop), 404 on unknown anomaly id

All 16 tests pass as of the last run, with no warnings.

## Manual end-to-end verification performed during development

1. Started the backend, ran the Normal Mission scenario for 20s — risk
   stayed at 0/LOW, telemetry stayed within nominal bounds, one AI insight
   ("All Systems Nominal") returned.
2. Triggered `THERMAL_EVENT` and let it run ~2 minutes — confirmed
   temperature climbed, the anomaly detector correctly attributed the
   anomaly to the THERMAL subsystem (this required a fix — see below),
   severity escalated INFO → WARNING, risk score climbed from 0 to
   MODERATE, and the AI Analysis page produced a thermal-specific insight
   citing the correct evidence.
3. Triggered `MULTI_SUBSYSTEM_ANOMALY` and confirmed multiple subsystems
   (THERMAL, POWER) were flagged concurrently, risk score reflected the
   multi-subsystem bonus, and mission logs recorded both the scenario
   activation and each new/resolved anomaly.
4. Verified CORS headers are correctly returned for the frontend's origin
   (`http://127.0.0.1:5173`).
5. Verified the frontend dev server serves the SPA shell correctly and the
   production build (`npm run build`) completes with zero TypeScript
   errors.

### Bug found and fixed during manual testing

The initial IsolationForest implementation retrained on a trailing window
of live telemetry every 15 ticks. During a sustained thermal ramp, the
model adapted to the drifting values as "normal" and stopped flagging
them, and the statistical layer's single-sample z-score (measured against
a window that already included the drift) also lost sensitivity. Fixed by:
(a) training the IsolationForest once on a fixed synthetic nominal
baseline instead of continuously retraining, and (b) changing the
statistical layer to compare a recent-sample mean against an older
baseline window rather than a single point against the whole window. Both
fixes were verified live against a running thermal-event scenario before
being considered complete.

## Frontend

- `npm run build` (TypeScript project build + Vite production build) — 0
  errors.
- Manual verification: dev server serves correctly, SPA title renders,
  live pages fetch from the backend and update on the documented polling
  intervals.

## Not yet covered (documented as a known gap)

- No frontend component/unit test suite (e.g. Vitest + React Testing
  Library) is included in this MVP. Given the competition timeline, manual
  verification against the live backend was prioritized. Adding component
  tests is listed as a follow-up in `docs/development-workflow.md`.
