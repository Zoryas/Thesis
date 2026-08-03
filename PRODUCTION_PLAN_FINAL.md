# TalaSaAI — Finalized End-to-End Production Plan (Student → Teacher → DB)

## Goal
Make the system production-ready **end-to-end**, covering:
- **Student flows** (pre-assessment → reading → questions → results → progress/profile)
- **Teacher flows** (dashboard → student list/detail → pending queue → scoring → reports)
- **Database correctness** (writes/updates reflected in subsequent reads)
- **API + UI** correctness and safe error handling

> This plan is derived from the current repo implementation:
> - Backend: monolithic Flask app in `app.py` (MySQL + ML inference)
> - Frontend: vanilla HTML pages in `pages/`, client wrapper `api.js`

---

## Phase 0 — Baseline Verification (must be done before “final”)
### 0.1 Confirm teacher critical workflow
- [x] Pending queue loads: `teacher-student-pending.html?sid=...`
- [x] Open scoring: `teacher-score.html?...&from=pending`
- [x] Save score: `POST /api/teacher/score`
- [x] Redirect back to pending when `from=pending`
- [x] Pending card disappears after scoring (fresh re-fetch)

### 0.2 Confirm “student → teacher → DB” state transition (required)
- [ ] Student submits a short-answer attempt via student flow
- [ ] Record in DB is updated with `short_answer_text` and teacher score remains `NULL`
- [ ] Teacher pending queue includes that item
- [ ] Teacher scoring updates `quiz_attempts.teacher_score` and `teacher_scored_at`
- [ ] Teacher pending queue no longer includes the scored item

**Pass criteria**
- UI/UX transitions are correct
- DB state transitions match UI reads
- No stale/cached data causes incorrect pending counts

---

## Phase 1 — Thorough Testing Coverage (end-to-end system)
This phase defines the verification scope needed to declare the system complete.

### 1.1 Student end-to-end UI flow (all pages)
Validate each page renders correctly and that navigation works with real backend calls:
- `student-dashboard.html`
- `student-passage.html`
- `student-reading.html`
- `student-questions.html`
- `student-results.html`
- `student-progress.html`
- `student-profile.html`

**Pass criteria**
- Each page loads required data (week assignments, passage, questions, results)
- Each user action persists to DB and later pages reflect the updated DB state

### 1.2 Student endpoints (happy + error paths)
Primary endpoints to test (using browser + curl-style negative tests):
- `POST /api/student/pre-assessment`
- `PUT /api/student/profile/avatar`
- `GET /api/student/weekly-passages`
- `GET /api/student/completions`
- `POST /api/student/reading-time`
- `GET /api/student/reading-progress`
- `POST /api/student/reading-progress`
- `POST /api/student/reading-lock`
- `POST /api/student/attempts`
- `GET /api/student/progress`

**Error/edge cases required**
- Missing required fields (400)
- Wrong types (400)
- Unauthorized access for student role (401/403)
- Unassigned passage/invalid week (400)
- Reading progress attempts while locked (ensure behavior is enforced/consistent)

### 1.3 Teacher endpoints (happy + error paths + edge redirect)
Also verify teacher behavior beyond the already-tested critical path:
- `GET /api/teacher/dashboard`
- `GET /api/teacher/students`
- `GET /api/teacher/students/<student_id>`
- `GET /api/teacher/students/<student_id>/pending-short-answers`
- `POST /api/teacher/score`
- `GET /api/teacher/reports/summary`

**Edge cases**
- Score page without `from=pending` redirects to `teacher-student-detail.html?id=...`
- Scoring when there’s no live pending response returns proper error and UI handles it
- Unauthorized teacher access returns 401/403 and UI redirects to login

### 1.4 Database correctness checks (writes reflected in reads)
Test scenario:
1) Student completes reading + submits attempts with short answer
2) Teacher sees it in pending queue
3) Teacher scores it
4) Teacher pending count decreases and the specific card disappears
5) Student results reflect teacher scoring impact (where relevant)

---

## Phase 2 — Security Hardening (production minimum)
### 2.1 Fix auth model consistency
Current backend supports both:
- session cookies
- token header fallback

**Production action**
- Choose one primary auth model for browser clients
- Ensure consistent authorization checks for all endpoints
- Remove or tightly scope unused auth mode to reduce risk

### 2.2 CSRF protection
Because frontend uses `credentials: "include"` (cookie-based), all state-changing endpoints must be CSRF-safe:
- Add CSRF tokens (recommended)
- or migrate to header-token auth and document it

### 2.3 XSS protections
Frontend includes inline scripts and dynamic HTML rendering (some uses `innerHTML`).
**Production action**
- Ensure all dynamic fields are escaped
- Add CSP headers to reduce exploitability

### 2.4 IDOR / ownership policy
Currently, authorization checks ensure role is teacher/student but don’t enforce teacher ownership over students.
**Production action**
- Add relationships (class/section ↔ adviser teacher)
- Enforce access control in the service layer

---

## Phase 3 — Backend Architecture & Operational Readiness
### 3.1 Remove runtime DB schema creation in production
Current `app.py` calls `init_database()` on startup.
**Production action**
- Replace with versioned migrations
- Seed DB with explicit one-time migration jobs

### 3.2 Refactor monolith incrementally
Extract layers without changing endpoint contracts:
- `routes/controllers`: request/response mapping
- `services`: scoring, pending selection, progress rules
- `repositories`: SQL queries
- `ml/`: model loading and inference
- `schemas/`: input validation

### 3.3 Introduce API versioning + standard envelopes
Current responses are `{ok:true,data}` / `{ok:false,error}`.
**Production action**
- Add `/api/v1/...`
- Standardize response envelope including `meta.requestId`

### 3.4 Observability
Add request correlation:
- requestId in logs
- structured log format
- log redaction for PII where required

Health/readiness:
- extend `/api/health` to check DB and ML artifact readiness

---

## Phase 4 — Delivery Definition (“Complete”)
The project can be considered **complete** when:
- [ ] Student → DB → Teacher pending queue transitions are validated
- [ ] Teacher scoring updates DB and removes items from pending queue
- [ ] All UI pages work end-to-end without broken navigation
- [ ] All impacted endpoints pass both happy and negative tests
- [ ] Authorization, CSRF, and XSS mitigations are implemented
- [ ] DB migrations replace startup schema creation
- [ ] Logging/health endpoints are operational
- [ ] API contracts are consistent (versioned + envelope)

---

## Phase 5 — Suggested Runbook Deliverables
- Deployment checklist (env vars, ports, DB migrations, seed job)
- Rollback plan
- Incident response notes:
  - what to check first (DB health, ML load, auth errors, latency spikes)

---

## Appendix A — Where this repo’s logic currently lives
- Backend/API: `app.py`
- Client wrapper: `api.js`
- Teacher pages: `pages/teacher-*.html`
- Student pages: `pages/student-*.html`
- ML artifacts: `ml_model/*`
