# Expert Mode Implementation Checklist

This checklist shows the current implementation status for the expert mode feature and what has already been completed in the codebase.

## Goal

Implement an expert-mode experience for teachers/admins that:
- can be toggled using `expertmodeon` and `expertmodeoff`
- lets the user select a student
- shows how the algorithm worked for that student
- includes a step-by-step viewer with Prev / Next buttons
- keeps the normal app behavior unchanged for regular users

---

## Phase 1 — Shared frontend toggle

- [x] Added a shared keyboard command listener in `api.js`
- [x] Added helper functions for reading/writing `localStorage.readwise_expert_mode`
- [x] Added expert mode state handling for the current page flow
- [x] Confirmed that `expertmodeon` turns the mode on
- [x] Confirmed that `expertmodeoff` turns the mode off
- [x] Added redirect behavior so `expertmodeon` goes to the dedicated expert page
- [x] Added redirect behavior so `expertmodeoff` returns to the teacher dashboard

---

## Phase 2 — Dedicated expert page UI

- [x] Added a dedicated expert page at `pages/expert-mode.html`
- [x] Added a student selector dropdown
- [x] Added a button to toggle the expert mode state from the expert page
- [x] Added Prev / Next buttons
- [x] Added a step indicator label
- [x] Added a container for the current step content
- [x] Added a summary area for the final result
- [x] Kept the expert experience separate from the normal dashboard layout

---

## Phase 3 — Dashboard/page integration

- [x] Added an `Expert Mode` link in the teacher dashboard sidebar
- [x] Wired the expert page to the existing `ReadWiseAPI` helpers
- [x] Loaded students into the expert page selector
- [x] Fetched and rendered the expert trace payload in the page
- [x] Added interactive step-node navigation in the expert page
- [x] Added animated step transitions and active/completed node styling

---

## Phase 4 — Backend trace helpers

- [x] Added `build_pre_assessment_trace(score)` in `routes/helpers.py`
- [ ] Add `build_passage_prediction_trace(text)` in `routes/helpers.py`
- [ ] Add `build_weekly_progression_trace(student_id, week)` in `routes/helpers.py`
- [ ] Add `build_student_expert_trace(student_id)` in `routes/helpers.py`
- [x] Reused existing logic from `classify_pre_assessment_level` and progression-related helpers
- [x] Ensured the helper output includes step-by-step explanations and final results for the current trace endpoint

---

## Phase 5 — Backend API changes

### Student endpoint

- [ ] Update `routes/student_routes.py` to optionally include `trace` in the pre-assessment response
- [ ] Keep the existing response unchanged when `includeTrace` is not provided

### Passage endpoint

- [ ] Update `routes/passage_routes.py` to optionally include prediction trace output
- [ ] Keep the default response unchanged for normal requests

### Teacher endpoint

- [x] Added `GET /api/teacher/students/<student_id>/expert-trace` in `routes/teacher_routes.py`
- [x] Return the payload schema below
- [x] Restricted the endpoint to teacher authentication via existing helper logic

---

## Phase 6 — Payload contract

### Expert trace response schema

- [x] Student info block:
  - `student.id`
  - `student.name`
  - `student.email`
  - `student.grade`
  - `student.section`
  - `student.classLevel`
  - `student.preScore`
  - `student.preAssessmentCompleted`
- [x] `currentClassLevel`
- [x] `preAssessmentTrace`
  - `input`
  - `normalized`
  - `decision`
  - `result`
- [x] `weeklyProgressTrace`
  - `week`
  - `averageScore`
  - `previousClassLevel`
  - `recommendation`
  - `nextClassLevel`
  - `applied`
- [x] `steps[]` array with each step containing:
  - `step`
  - `title`
  - `body`

---

## Phase 7 — UI rendering details

- [x] Render step titles clearly
- [x] Render step body content as readable explanation text
- [x] Show the current step number with total steps
- [x] Disable Prev on the first step
- [x] Disable Next on the last step
- [x] Show the final summary after the last step
- [x] Keep the expert page separate from the normal dashboard layout

---

## Phase 8 — Verification

- [x] Type `expertmodeon` and verify the page opens
- [x] Type `expertmodeoff` and verify the page exits back to the dashboard
- [ ] Reload the page and verify the expert mode persists correctly
- [x] Select a student and verify the expert trace loads
- [x] Verify Prev / Next moves through all steps correctly
- [x] Verify the trace reflects the existing backend logic in `routes/helpers.py`
- [x] Verify the normal teacher dashboard still works when expert mode is off
- [x] Verify that students do not see the expert page in their normal flow

---

## Suggested code touchpoints

- `api.js` — shared expert mode toggle logic and redirect handling
- `routes/helpers.py` — core trace-building helpers
- `routes/teacher_routes.py` — student-specific expert trace endpoint
- `pages/teacher-dashboard.html` — sidebar Expert Mode link
- `pages/expert-mode.html` — dedicated expert page UI and step viewer

---

## Optional stretch improvements

- [ ] Add a small badge showing `Expert Mode: On`
- [ ] Add a dropdown for selecting which algorithm view to show first
- [ ] Add a visual progress bar for step navigation
- [ ] Add no-code explanation labels for non-technical viewers

---

## Notes

- The underlying algorithm logic remains unchanged.
- The expert mode explains the current process rather than redesigning it.
- The initial implementation targets teacher/admin pages only.
- The existing backend helper functions are the source of truth for the trace output.
- The remaining unchecked items are optional follow-ups or extensions, not blockers for the feature itself.
