# ReadWise Deployment Gap Checklist

This file summarizes what has already been tested and what still needs full coverage before production deployment.

## 1) Testing Status (Completed So Far)

- [x] Backend compile check (`python -m py_compile app.py`)
- [x] Reading lock API critical paths validated:
  - [x] Happy path
  - [x] Duplicate/idempotent lock call
  - [x] Malformed payload handling
  - [x] Unassigned passage handling
  - [x] Unauthenticated handling
- [x] Timer speed issue fixed and verified
- [x] Lock persistence manually verified in normal session and incognito (same account)
- [x] Core behavior confirmed by user: locked passages remain locked when reopening reading URL

---

## 2) Remaining Areas for Thorough Testing

## A. Frontend / Web UI (Full Flow Coverage)

### Student Pages
- [~] `pages/student-dashboard.html`
  - [x] Week display correctness
  - [x] Assigned passages list correctness
  - [x] Navigation links work (Dashboard, My Passage, Pre-Assessment verified)
- [~] `pages/student-passage.html`
  - [x] Assigned-only passage visibility/access (Week 3 Difficult shows 2 assigned passages)
  - [x] Week filtering consistency (header and assigned count consistent with dashboard)
- [~] `pages/student-reading.html`
  - [x] Lock redirect behavior on reopen (validated earlier and user-confirmed)
  - [x] Unassigned passage hard-block (validated earlier)
  - [x] Timer behavior under refresh/re-entry (timer speed issue fixed and verified earlier)
  - [x] Done Reading -> Questions transition (verified in current UI pass via Start Reading leading to locked Questions page)
- [x] `pages/student-questions.html`
  - [x] Access gating depends on lock state (locked notice visible; passage return blocked)
  - [x] Direct link behavior (locked/unlocked)  
  - [x] Submit flow transitions (answers submitted successfully to results)
- [x] `pages/student-results.html`
  - [x] Result rendering after submit (Pending/Under Review state shown for short-answer workflow)
  - [x] Re-entry behavior after completion (returning to locked questions shows no passage re-entry and preserves assessment state)

### Teacher Pages
- [x] `pages/teacher-dashboard.html`
  - [x] Summary cards/charts load correctly
- [x] `pages/teacher-passages.html`
  - [x] Passage listing/weekly assignment panels load correctly (including Active Week selector and class assignment cards)
  - [ ] Passage editing/deletion workflow
- [x] `pages/teacher-submit.html`
  - [x] Submit page loads core sections (CSV import panel, passage input, prediction results)
  - [ ] Assignment workflow and validation states

---

## B. Backend / API (Endpoint + Edge Case Coverage with Curl)

### Auth
- [ ] `POST /api/auth/login` (valid/invalid credentials)
- [ ] `POST /api/auth/logout`
- [ ] `GET /api/auth/me`

### Program Week Settings
- [ ] `GET /api/program/week`
- [ ] `GET /api/program/week/settings`
- [ ] `PUT /api/program/week/settings` (valid/invalid payload)

### Assignments
- [ ] `GET /api/assignments`
- [ ] `POST /api/assignments` (valid/duplicate/class mismatch/max per week)
- [ ] `DELETE /api/assignments`

### Student Reading & Attempts
- [ ] `GET /api/student/weekly-passages`
- [ ] `GET /api/student/completions`
- [ ] `GET /api/student/reading-progress`
- [ ] `POST /api/student/reading-progress`
- [ ] `POST /api/student/reading-lock`
- [ ] `POST /api/student/attempts`
- [ ] Race/edge checks:
  - [ ] Duplicate events
  - [ ] Malformed JSON/payload types
  - [ ] Unauthorized requests
  - [ ] State transition integrity (`is_locked`, `is_submitted`, `completed_at`)

### Teacher Reports
- [ ] `GET /api/teacher/dashboard`
- [ ] `GET /api/teacher/students`
- [ ] `GET /api/teacher/students/<student_id>`
- [ ] `GET /api/teacher/reports/summary`

---

## 3) Deployment Gaps / Hardening Checklist

## Security
- [ ] Use strong production `READWISE_SECRET_KEY` (no default dev secret)
- [ ] Restrict CORS origins to exact production domains
- [ ] Ensure HTTPS-only cookies in production
- [ ] Add login rate-limiting / brute-force protection
- [ ] Add audit logs for key student/teacher actions

## Data Integrity
- [ ] Confirm all critical runtime state is server-authoritative
- [ ] Verify lock and submission transitions are atomic
- [ ] Ensure assignment-by-week constraints are enforced consistently

## Reliability
- [ ] Add structured error logging and monitoring
- [ ] Add DB backup and restore procedure
- [ ] Add retry/backoff strategy for transient failures
- [ ] Define incident rollback plan for bad deployments

## Performance
- [ ] Add DB indexes review for high-traffic queries
- [ ] Load test critical endpoints (login, weekly-passages, reading-progress, attempts)
- [ ] Verify acceptable response times under concurrent students

## Operations
- [ ] Finalize `.env`/secret management
- [ ] Add production startup/runbook docs
- [ ] Add healthcheck and smoke-test script
- [ ] Define release checklist and sign-off process

---

## 4) Suggested Finalization Path

1. Run full frontend thorough test checklist (student + teacher pages).
2. Run full API curl suite (happy + error + edge + race checks).
3. Fix findings and retest affected paths.
4. Complete security and operations hardening.
5. Execute pre-release smoke test and deploy.

---

## 5) Notes

- Current lock continuity goal is now working and confirmed.
- This checklist is for moving from “feature works” to “production-ready for school deployment.”
