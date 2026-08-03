# TalaSaAI Production Finalization — Remaining Checkboxes

## 0) Confirmed by current testing
- [x] Teacher critical workflow works:
  - `teacher-student-pending.html?sid=...` loads pending queue
  - “Open Scoring View” → `teacher-score.html?sid=...&pid=...&from=pending`
  - “Save Score” → `POST /api/teacher/score`
  - Redirect back to `teacher-student-pending.html?sid=...` when `from=pending`
  - Scored item disappears from the pending list (re-fetched)

## 1) Critical-path (remaining, still unverified)
- [ ] Unauthorized handling:
  - [ ] `/api/teacher/students/<sid>/pending-short-answers` returns 401/403 when not teacher
  - [ ] `/api/teacher/score` returns 401/403 when not teacher
  - [ ] teacher pages redirect to `login.html` on unauthorized

- [ ] Error states (UI + API):
  - [ ] Missing/invalid `sid` in `teacher-student-pending.html`
  - [ ] Missing/invalid `pid` in `teacher-score.html`
  - [ ] Scoring when there is **no live pending** short-answer (UI shows disabled/handled state and API returns expected error)

- [ ] Alternate redirect path:
  - [ ] Scoring from `teacher-score.html` **without** `from=pending` redirects to `teacher-student-detail.html?id=<sid>`

## 2) API edge cases (server-side)
- [ ] `POST /api/teacher/score` validation:
  - [ ] `score=2` / `score=-1`
  - [ ] `score="abc"` (non-integer)
  - [ ] missing `studentId` or `passageId`
  - [ ] confirm response shape is consistent: `{ ok: false, error: ... }`

- [ ] Pending query correctness:
  - [ ] Confirm pending list includes only:
    - `short_answer_text IS NOT NULL`
    - `teacher_score IS NULL`

## 3) Broader UI smoke (minimal)
- [ ] Navigate through teacher pages (no console/runtime break):
  - [ ] `teacher-dashboard.html`
  - [ ] `teacher-students.html`
  - [ ] `teacher-student-detail.html` (from queue/detail navigation)
  - [ ] `teacher-reports.html` and/or `teacher-recommendations.html` (one of them at minimum)

## 4) Production readiness (from plan doc — longer checklist)
If you choose to continue beyond the teacher critical path, remaining items from `TALASAAI_FINALIZATION_PRODUCTION_PLAN.md` typically include:
- [ ] Remove/limit inline scripts (reduce XSS risk)
- [ ] Backend layering/refactor (`app.py` monolith → routes/services/repositories)
- [ ] API versioning + response envelope standardization
- [ ] Structured logging + request correlation IDs
- [ ] CSRF/XSS/SQLi hardening verification
- [ ] Health checks standardization (`/health`, `/api/health`) across environments
- [ ] Add automated tests (unit/integration/e2e + curl contract tests)
- [ ] Run security headers/CSP verification and TLS/env policy

## Status summary
- **Now done:** Teacher pending → score → save → redirect workflow
- **Next required to finalize as “production-ready baseline”:** sections **1** and **2** checkboxes above (at least the non-trivial error/unauthorized/alternate redirect ones)
