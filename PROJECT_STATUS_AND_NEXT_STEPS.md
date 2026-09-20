# TalaSaAI Project Status and Next Steps

## 1. Project Goal

The project is building a reading-performance and recommendation system that helps teachers monitor student growth, evaluate reading readiness, and identify whether a learner should stay at the current level, move up, or move down based on performance trends.

The implementation is centered on the following core ideas:
- track student performance over time
- compare baseline and latest scores
- measure learning growth using gain and normalized gain
- estimate reading speed using WPM
- explain the recommendation logic in a teacher-friendly and student-appropriate way
- provide a hybrid decision pipeline that combines text-based passage difficulty and student performance data

---

## 2. Current Status

### Completed work
- Growth metrics are implemented and displayed in the teacher dashboard and student detail views.
- Student growth summary includes:
  - Baseline Score
  - Latest Score
  - Gain
  - Normalized Gain
  - WPM
- Rule-based and hybrid recommendation logic has been mapped into the teacher-facing flow.
- Missing-data handling was added so incomplete student records do not produce misleading values.
- Invalid or zero reading-time values are handled safely so WPM does not produce false results.
- Teacher-facing wording and metric labels were refined for consistency.
- Code validation was run successfully for the backend and the affected teacher UI pages.

### Verified evidence
- Python compile completed successfully for the backend files.
- JavaScript validation for the affected teacher pages completed successfully.
- Edge-case helper checks confirmed the following outputs:
  - gain = 34.0
  - normalized = 0.507
  - valid WPM = 120.0
  - zero-time WPM = None
  - missing-word WPM = None

---

## 3. What is still required

### Phase 3: Final validation and hardening
- Perform live browser validation through the teacher dashboard using real student records.
- Confirm that the values populate correctly in a real environment rather than only in code.
- Re-check the following scenarios:
  - no pre-assessment score
  - no weekly score yet
  - missing reading-time data
  - zero or invalid WPM input
  - student without a recommendation history
- Confirm that report generation still renders correctly after final changes.

### Phase 4: Production polish
- Final wording review across all teacher screens.
- Final consistency pass on status labels and UI phrasing.
- Check that the dashboard, detail page, and reports use consistent growth language.
- Review export/report formatting for readability and clarity.

### Phase 5: Launch readiness
- Final browser-based QA signoff.
- Final regression pass across teacher workflow.
- Confirm export files remain correct and usable.
- Final launch checklist approval.
- Prepare final project summary and handoff documentation.

---

## 4. Technical Requirements We Need to Keep in Mind

### Student performance model
Each student should have a longitudinal performance profile that includes:
- pre_assessment_score
- weekly_average_score
- latest_score
- gain
- normalized_gain
- words_per_minute (WPM)
- reading_time
- comprehension_accuracy
- current_class_level
- recommendation_status

### Hybrid system requirement
The system should be described as a hybrid model, not a single model:
- The SVM model classifies passage difficulty based on passage text features.
- The rule-based learner layer evaluates the student’s performance profile.
- The recommendation engine decides whether the student should stay, move up, or move down.

### Growth monitoring rule
Growth must be interpreted over time using more than a single test result:
- compare baseline to latest score
- compute gain
- compute normalized gain
- track WPM and reading time
- monitor whether performance is improving, stabilizing, or declining over consecutive weeks

### Key formulas
- Accuracy = correct answers / total questions x 100
- WPM = total words / reading time in minutes
- Weekly score = average of relevant session scores for the week
- Gain = latest score - baseline score
- Normalized gain = (latest score - baseline score) / (100 - baseline score)

---

## 5. Ideal SOP / Narrative Explanation

The system uses a hybrid approach to monitor and adapt student reading performance. Passage difficulty is estimated using an SVM model that analyzes the linguistic features of each passage, while student growth is evaluated through a rule-based learner model that combines baseline readiness, weekly performance, comprehension accuracy, reading time, and words per minute. Student learning is tracked longitudinally through baseline score, latest score, gain, normalized gain, and trend across weeks. The recommendation engine then compares current student performance against the student’s current class level and decides whether the learner should remain at the same level, move up, or move down. Growth is therefore not based on a single score alone, but on sustained patterns across multiple indicators and instructional signals.

---

## 6. Worked Example

### Example Student A
- Baseline score: 52%
- Week 1: 58%, accuracy 63%, WPM 109
- Week 2: 68%, accuracy 72%, WPM 118
- Week 3: 82%, accuracy 80%, WPM 125
- Current level: Easy

### Interpretation
- The student shows steady improvement across three weeks.
- The gain from baseline is significant.
- The student is becoming both more accurate and faster.
- The system can justify a recommendation to move the learner up to the next level.

This example demonstrates that the recommendation is based on a pattern of ongoing improvement rather than a single isolated result.

---

## 7. Final Deliverables Needed Before Launch

- Final teacher dashboard QA signoff
- Final student detail QA signoff
- Final reports QA signoff
- Final export validation
- Final launch-readiness checklist
- Final documentation summary for project handoff

---

## 8. Current Recommendation

The project is in a strong implementation state for the teacher-facing growth and recommendation workflow. The remaining work is primarily final validation, final polish, and formal signoff. Once live browser QA passes and the final wording review is complete, the system is ready to move into launch readiness.
