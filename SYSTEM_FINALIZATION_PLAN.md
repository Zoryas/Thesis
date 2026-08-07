# ReadWise / TalaSaAI Finalization Plan

## Goal
Make the current system fully complete and publish-ready with a clear phased path from prototype to production.

## Phase 0 — Critical Baseline Verification
These items must be verified before any production readiness work.

- [x] Confirm core app startup and backend health
  - [x] Flask app starts successfully
  - [x] `/health` returns a healthy response
  - [x] `/api/health` confirms DB connectivity
  - [x] `/predict` returns a valid prediction payload for a real passage
- [x] Confirm authentication and role-based access
  - [x] Student login succeeds
  - [x] Teacher login succeeds
  - [x] Protected student API responds with real data
  - [x] Protected teacher API responds with real data
- [x] Confirm student end-to-end flow with the live API and no mock fallbacks
  - [x] `student-dashboard.html` loads real assignment data
  - [x] `student-passage.html` shows assigned passages and completed passages correctly
  - [x] `student-reading.html` locks reading, saves time, and moves to questions
  - [x] `student-questions.html` submits answers and short-answer responses
  - [x] `student-results.html` shows score, reading time, and weekly progress
- [x] Confirm teacher critical workflow
  - [x] `teacher-student-pending.html` loads pending short-answer items
  - [x] `teacher-score.html` opens for a pending item
  - [x] scoring saves successfully via `POST /api/teacher/score`
  - [x] pending item disappears after scoring on refresh
- [x] Validate the snapshot student → DB → teacher transition
  - [x] student submission persists to DB
  - [x] teacher sees the pending item
  - [x] teacher scoring updates the DB and removes the item from pending

## Phase 1 — End-to-End Testing and Error Handling
Validate the full system behavior and close obvious edge cases.

### Student API and UI
- [x] Test student-facing endpoints with valid data
  - [x] `GET /api/student/weekly-passages`
  - [x] `GET /api/student/completions`
  - [x] `POST /api/student/reading-time`
  - [x] `POST /api/student/reading-lock`
  - [x] `POST /api/student/attempts`
  - [x] `GET /api/student/progress`
- [x] Test bad student requests and error handling
  - [x] missing/invalid passage ID or week
  - [x] malformed JSON
  - [x] unauthorized access returns 401/403
- [x] Verify student UI pages render gracefully on empty or error responses
  - [x] fallback/empty states shown
  - [x] no uncaught console exceptions

### Teacher API and UI
- [x] Test teacher-facing endpoints
  - [x] `GET /api/teacher/dashboard`
  - [x] `GET /api/teacher/students`
  - [x] `GET /api/teacher/students/<student_id>`
  - [x] `GET /api/teacher/reports/summary`
  - [x] `POST /api/teacher/score`
- [x] Test access control and redirect behavior
  - [x] teacher pages redirect unauthorized users to login
  - [x] scoring without `from=pending` redirects to student detail correctly
  - [x] invalid scores return a consistent error response

### Database and state integrity
- [ ] Confirm lock and submission state is server-authoritative
- [ ] Confirm week/assignment constraints are enforced consistently
- [ ] Verify critical state transitions are idempotent and safe

## Phase 2 — Security and Hardening
Add production-grade protections and tighten runtime policies.

- [ ] Replace dev secret fallback with required `READWISE_SECRET_KEY`
- [ ] Lock CORS to exact production domains via `READWISE_ALLOWED_ORIGINS`
- [ ] Enforce HTTPS-only cookies in production
- [ ] Add login rate limiting / brute-force protection
- [ ] Harden auth and authorization across all endpoints
- [ ] Protect against CSRF or migrate to header-based auth consistently
- [ ] Reduce XSS risk by limiting inline HTML rendering and adding sanitization
- [ ] Add audit logging for key student/teacher state changes

## Phase 3 — Architecture and Operations
Prepare the system for repeatable deployment and support.

- [ ] Separate runtime schema creation from production startup
- [ ] Add versioned DB migrations and seed scripts
- [ ] Add healthcheck endpoints for app and DB readiness
- [ ] Add structured error logging and request correlation
- [ ] Document production startup and deployment runbook
- [ ] Add backup/restore guidance for MySQL data
- [ ] Add smoke-test script for deploy validation

## Phase 4 — Final Delivery Criteria
The system should be considered complete when these final items are met.

- [ ] Functional student and teacher workflows work end-to-end
- [ ] All critical APIs are tested for happy and error paths
- [ ] Authorization and security hardening are verified
- [ ] Production runtime configuration is documented and enforced
- [ ] Monitoring, healthchecks, and deploy/runbook docs exist
- [ ] The system can be started by a production server process like Gunicorn

## Phase 5 — Publish Checklist
- [ ] Confirm environment variables in production
  - `READWISE_ENV=production`
  - `READWISE_SECRET_KEY`
  - `READWISE_DB_HOST`, `READWISE_DB_PORT`, `READWISE_DB_USER`, `READWISE_DB_PASSWORD`, `READWISE_DB_NAME`
  - `READWISE_ALLOWED_ORIGINS`
- [ ] Confirm `render.yaml` or deployment manifest points to `gunicorn app:app`
- [ ] Run a final smoke test against the deployed app
- [ ] Verify login, student flow, teacher flow, and DB persistence in the deployed environment
- [ ] Review deployment rollback/incident steps with the team

## Notes
- This plan is intended as the final completion checklist for this repository.
- Existing docs like `DEPLOYMENT_GAP_CHECKLIST.md`, `PRODUCTION_PLAN_FINAL.md`, and `TALASAAI_FINALIZATION_PRODUCTION_PLAN.md` should be considered implementation references.
