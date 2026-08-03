# Remaining Steps — Production Relational Model (ER) Completion Checklist

## Status
- **Critical path + Phase A (`questions`/`choices`)** are complete (tables exist + backfill verified for MC/non-MC passages).
- Remaining steps below are for finishing the rest of the ER model, adding missing persistence, parity verification, and (optional) cutover.

---

## 0) Confirm current state (tables + counts)
- [ ] **Confirm current state**: verify which ER tables are already created/backfilled vs. only partially present (use MySQL `SHOW TABLES` + targeted `COUNT(*)` checks).

---

## 1) Backfill + verify `recommendations` and `reading_levels` mapping
- [x] **Backfill + verify `recommendations`**
  - [x] Create `recommendations` rows from existing logic/rules (or ML output) into the normalized table.
  - [x] Add verification script: recommendations exist for students with completed weeks.
- [x] **Backfill + verify `reading_levels` thresholds & mapping**
  - [x] Ensure `reading_levels` values and thresholds match production rule expectations.
  - [x] Ensure student mapping to reading level is consistent (from existing `class_level` / pre-score / scoring).

---

## 2) Complete identity hierarchy normalization parity
- [ ] **Complete identity hierarchy normalization parity**
  - [ ] Ensure `teachers`, `classes`, `sections` are fully derived/consistent for all seed + real records.
  - [ ] Add backfill/repair script if any students/teachers can’t be mapped (FK-safe).

---

## 3) Backfill + verify `reports`, `audit_logs`, `notifications`
- [ ] **Backfill + verify `reports`**
  - [ ] Decide where teacher report data should originate (current endpoints).
  - [ ] Persist generated report payloads into `reports` table.
  - [ ] Add verification script: reports exist after teacher report generation.
- [ ] **Backfill + verify `audit_logs`**
  - [ ] Add writes for key actions (login, reading complete, teacher scoring, settings changes).
  - [ ] Ensure audit rows are appended with correct `entity_type/entity_id` and before/after JSON.
- [ ] **Backfill + verify `notifications`**
  - [ ] Wire notification creation to existing flows (e.g., pending teacher review).
  - [ ] Verify “read/unread” behavior updates persist to `notifications`.

---

## 4) Replace/extend singleton `program_settings` into generalized `settings`
- [ ] **Replace/extend singleton `program_settings` into generalized `settings`**
  - [ ] Introduce normalized `settings` (scope + key + value_json).
  - [ ] Maintain compatibility adapter so existing endpoints keep working.
  - [ ] Add migration/backfill for existing `program_settings` row into `settings`.

---

## 5) Fill remaining ER gap tables (`choices` non-MC, metadata consistency, etc.)
- [ ] **Fill remaining ER gap tables**
  - [ ] Ensure `questions`/`choices` coverage matches all question types:
    - [ ] Decide whether `choices` should also represent non-MC accepted answers (or keep MC-only and rely on metadata).
  - [ ] Ensure `questions.type` + `metadata_json` mapping is consistent with your frontend/ML/teacher scoring needs.

---

## 6) Create end-to-end parity verification suite
- [ ] **Create end-to-end parity verification suite**
  - [ ] Dual-write smoke tests extended to cover more paths:
    - [ ] submissions for multiple passages/weeks
    - [ ] teacher scoring after submission
    - [ ] reading completion edge cases
  - [ ] DB verification suite:
    - [ ] normalized row counts for sessions/answers/scores/read_history
    - [ ] `questions/choices` counts for at least 1 MC passage and at least 1 non-MC passage

---

## 7) Optional cutover plan
- [ ] **Optional (but recommended) cutover plan**
  - [ ] Switch reads to normalized tables in teacher/student endpoints (currently still partially legacy).
  - [ ] Monitor correctness + timing, then deprecate `quiz_attempts` usage if parity is verified.

---

## Notes (current milestones)
- [x] ER Phase A: Added `questions` + `choices` tables + backfill from legacy assessments.
- [x] Verified normalized `questions/choices` for MC passage (`p48` has choices).
- [x] Verified `p40` has `choices=0` correctly because it contains only non-MC types.
