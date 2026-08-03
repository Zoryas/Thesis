# TODO - Teacher Pending Short Answers Page

- [x] Read backend/API files to confirm available pending-short-answer data
- [ ] Add backend endpoint for all pending short answers per student (if needed)
- [ ] Add API wrapper in `api.js` for pending-short-answers endpoint
- [ ] Create `pages/teacher-student-pending.html` with improved teacher review UI
- [ ] Update `pages/teacher-student-detail.html` to link to new pending list page
- [ ] Verify links to `teacher-score.html?sid=...&pid=...` work for each pending item
- [ ] Perform quick consistency review for copy and styling

---

# Checklist - Production Relational Model Tables (ER Model)

Critical-path normalized dual-write (verified for s14/p40):
- [x] reading_sessions (dual-write + DB verify)
- [x] student_answers (dual-write + DB verify)
- [x] short_answer_responses (dual-write + DB verify)
- [x] short_answer_scores (dual-write + DB verify)
- [x] scores (dual-write + DB verify)
- [x] reading_history (dual-write + DB verify)

Remaining ER tables (not yet fully implemented/cut over; pending):
- [ ] users
- [ ] teachers
- [ ] students
- [ ] classes
- [ ] sections
- [ ] passages
- [ ] questions
- [ ] choices
- [ ] reading_levels
- [ ] recommendations
- [ ] reports
- [ ] audit_logs
- [ ] notifications
- [ ] settings

Notes:
- This checklist tracks your “4.2 Suggested Tables” list. The current repo work is transitional: critical-path normalized tables are implemented/verified; the rest is still in-progress.
