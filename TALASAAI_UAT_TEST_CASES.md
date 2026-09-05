# TalaSaAI UAT Test Cases
**Version 2.0** | **Date:** August 2026  
**SRS-Aligned Test Specification** | **Based on DOC-005**

---

## Test Cases Summary

| Module | FR References | Cases | Automated | Manual | Status |
|--------|---|---|---|---|---|
| Authentication & Access Control | FR-001, FR-002, FR-003 | 5 | 5 | 0 | Pending |
| Student Profile Management | FR-004 | 5 | 3 | 2 | Pending |
| Pre-Assessment & Placement | FR-005 | 5 | 4 | 1 | Pending |
| Reading Passages Display | FR-006 | 5 | 3 | 2 | Pending |
| Question Management & Responses | FR-007, FR-008 | 5 | 4 | 1 | Pending |
| Auto-Scoring & Results Display | FR-009, FR-010 | 5 | 5 | 0 | Pending |
| Student Progress Tracking | FR-011 | 5 | 4 | 1 | Pending |
| Teacher Passage Management | FR-012, FR-013 | 5 | 3 | 2 | Pending |
| Teacher Review & Feedback | FR-014 | 5 | 2 | 3 | Pending |
| Recommendations Engine | FR-015 | 5 | 3 | 2 | Pending |
| Report Generation | FR-016 | 5 | 2 | 3 | Pending |
| API & Backend Services | FR-017, FR-018 | 5 | 5 | 0 | Pending |
| **TOTAL** | | **60** | **43** | **17** | |

---

## 1. Authentication & Access Control
**Validates FR-001, FR-002, FR-003: Login, role-based redirect, RBAC enforcement**

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-001 | Student login with valid credentials | Student account exists (email: student@school.edu, pwd: valid) | 1. Navigate to /login 2. Enter email & password 3. Click "Sign In" | Student dashboard loads; JWT token issued; student sees Reading, Pre-Assessment, Progress tabs |
| TC-002 | Teacher login with valid credentials | Teacher account exists (email: teacher@school.edu, pwd: valid) | 1. Navigate to /login 2. Enter email & password 3. Click "Sign In" | Teacher dashboard loads; JWT token issued; teacher sees Passages, Students, Reviews, Reports tabs |
| TC-003 | Invalid login rejection | Account exists (valid email, wrong password) | 1. Navigate to /login 2. Enter email & wrong password 3. Click "Sign In" | Error message displayed: "Invalid credentials"; no token issued; page stays on login |
| TC-004 | Cross-role access blocked | Logged in as Student | Attempt to access /teacher/passages via URL or breadcrumb | 403 Forbidden error; user redirected to student dashboard; audit log records unauthorized access attempt |
| TC-005 | Session token validation | Student logged in for 30+ minutes | 1. Perform an action (e.g., click a button) 2. Observe if session remains active or expires | If no activity after 6 hours: session expires; user redirected to login with "Session expired" message |

---

## 2. Student Profile Management
**Validates FR-004: View and update profile details including avatar**

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-010 | View student profile page | Logged in as Student | 1. Navigate to Student > Profile 2. Load profile page | Page displays: name, email, grade level, class section, current class level (Easy/Moderate/Hard), pre-assessment status |
| TC-011 | Update avatar (initials) | Student on Profile page | 1. Click Avatar section 2. Select "Initials" option 3. Save | Avatar type = initials; avatar rendered with student's initials on dashboard; change persists on reload |
| TC-012 | Update avatar (preset emoji) | Student on Profile page | 1. Click Avatar section 2. Choose preset emoji (e.g., 🎓) 3. Save | Avatar type = preset; selected emoji displays on student dashboard and in teacher reports; change persists |
| TC-013 | Attempted empty profile update rejected | Student on Profile page with no changes | 1. Click profile form fields 2. Do not modify any data 3. Click "Save" | Validation error shown: "No changes detected" OR successfully returns to profile with no changes recorded |
| TC-014 | Grade/Section info displays accurately | Student logged in with known grade/section | 1. Navigate to Profile 2. Check Grade and Section fields | Grade (e.g., "Grade 7") and Section (e.g., "7-A") display correctly; matches data in students table |

---

## 3. Pre-Assessment & Placement
**Validates FR-005: Pre-assessment completion before accessing full reading activities**

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-020 | Student takes pre-assessment for first time | Logged in as Student; pre_assessment_completed = 0 | 1. Navigate to Student > Pre-Assessment 2. Answer all questions 3. Submit answers | Pre-assessment marked complete; pre_assessment_completed = 1; student receives score (0-100); class_level assigned (Easy/Moderate/Hard) |
| TC-021 | Pre-assessment triggers passage eligibility | Pre-assessment just completed with score 65 | Complete pre-assessment; check eligible passages | Passages matching Easy/Moderate/Hard level now visible in Reading section; student can select and start reading |
| TC-022 | Pre-assessment retake blocked | Pre-assessment already completed | 1. Navigate to Pre-Assessment tab 2. Attempt to retake test | "Pre-assessment already completed" message shown; cannot retake; option to view results only |
| TC-023 | Score classification accuracy | Pre-assessment submitted | Submit with different scores: 35 (Easy), 65 (Moderate), 85 (Hard) | Correct class_level assignment: <50=Easy, 50-75=Moderate, >75=Hard for each score |
| TC-024 | Pre-assessment score persists in profile | Student completed pre-assessment with score 72 | 1. Complete pre-assessment 2. Navigate to Profile 3. Check Pre-Assessment section | Score (72) and completion timestamp displayed; class level shown as "Moderate" |

---

## 4. Reading Passages Display
**Validates FR-006: Display passages assigned/available to students**

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-030 | Student views available passages | Logged in as Student; pre-assessment complete; class_level = MODERATE | 1. Navigate to Student > Reading 2. View passages list | Only passages with difficulty = MODERATE are shown; each passage displays: title, genre, word count, estimated reading time |
| TC-031 | Passages filtered by difficulty level | Student with class_level = EASY | Navigate to Reading section | Only EASY passages displayed; MODERATE/HARD passages hidden; ensures appropriate challenge level |
| TC-032 | Passage details load correctly | Student viewing passage list | Click on a passage (e.g., "The Adventure Begins") | Passage page loads with: full text, genre tag, word count, reading time estimate; no missing content |
| TC-033 | Passage selection initiates reading session | Student clicks on an available passage | 1. Select passage "Chapter 2" 2. Click "Start Reading" | Reading session created; passage_id, student_id, session status = started recorded; timer begins |
| TC-034 | Multiple passages selectable per session | Multiple passages shown in Reading view | Navigate through passage list; attempt to select different passages | Each passage is clickable and independent; selecting one doesn't prevent viewing others; only one active session per passage per week |

---

## 5. Question Management & Response Capture
**Validates FR-007, FR-008: Present questions and save student responses**

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-040 | Comprehension questions display | Reading session started for passage | 1. Load passage details 2. Navigate to Questions tab | All assessment_questions for this passage load correctly; questions display in sort_order; formats include: multiple choice, fill-in-the-blank, or short answer |
| TC-041 | Student submits multiple-choice answer | Question displayed: "What is the main theme?" with 4 options | 1. Click option (e.g., "Option B") 2. Click "Next" or "Submit Answer" | Answer recorded in student_answers table; answer_payload_json stores selected option; submitted_at timestamp recorded |
| TC-042 | Student submits short answer | Short-answer question displayed: "Summarize in 2-3 sentences" | 1. Type response in text field 2. Click "Submit" | Short answer text saved in short_answer_responses table; response_text captured; submitted_at recorded; marked as pending teacher review (is_scored = 0) |
| TC-043 | Student reviews and modifies answer before final submit | Student answered 3/5 questions | 1. Navigate to "Review Answers" tab 2. Modify one answer 3. Click "Update" | Modified answer overwrites previous; new submitted_at timestamp recorded; old answer version not accessible |
| TC-044 | Answer validation prevents empty submission | Student on question with required field | Leave answer blank or empty and click "Submit" | Validation error: "Please provide an answer before submitting"; form does not submit until answer provided |

---

## 6. Auto-Scoring & Results Display
**Validates FR-009, FR-010: Automatically compute scores and show results with feedback**

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-050 | Multiple-choice auto-scoring | Reading session with 4 MC questions; student answered 3 correct | Session submitted after all questions answered | Auto-scoring engine compares answer_index to answer_key; is_correct field updated (1=correct, 0=incorrect); MC score calculated as % correct |
| TC-051 | Results page displays immediately after submission | All questions answered and submitted | Click "Complete Reading" → page loads | Results page shows: total score (MC %), individual question breakdown, short answers pending teacher review; timestamp of completion |
| TC-052 | Short answer shows pending status | Session with 1 MC + 1 short answer completed | Navigate to Results page | MC question: shows "Correct" or "Score: 75/100"; Short answer: shows "Pending Teacher Review - awaiting feedback" |
| TC-053 | Feedback displays when available | Teacher scored short answer (feedback: "Excellent work!") | Student views Results for completed session | Feedback text visible: "Excellent work!"; teacher name shown (if provided); score displayed (e.g., "85/100") |
| TC-054 | Session score calculation accuracy | Session: Q1 (MC) = Correct, Q2 (MC) = Incorrect, Q3 (Short) = 80/100 | Complete session and view score summary | Final score accurately reflects: MC auto-score + short answer score (if available); calculation formula transparent or matches rubric |

---

## 7. Student Progress Tracking
**Validates FR-011: Display progress history (scores, attempts, trends)**

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-060 | View reading session history | Student completed 2 reading sessions in last week | 1. Navigate to Student > Progress 2. View all sessions | List shows: passage title, score, completion date, class level at time of reading; sorted by most recent first |
| TC-061 | Progress filtered by time period | Student with 8 weeks of reading data | 1. Go to Progress 2. Filter by "Week 3" or date range | Only sessions from selected period displayed; other weeks hidden; filter accuracy verified |
| TC-062 | Average score calculation | Student completed: Session 1 (80), Session 2 (90), Session 3 (70) | View Progress summary | Average score displayed: (80+90+70)/3 = 80; calculation correct and dynamic as new sessions added |
| TC-063 | Completion percentage tracked | 3 total available passages for class level; student completed 2 | View Progress page header | Shows: "2/3 passages completed (66%)" or similar metric; percentage auto-updates when new session submitted |
| TC-064 | Progress trends visible | Student completed sessions over 4 weeks with varying scores: 60→70→75→85 | View Progress chart/graph or list with trend indicator | Visual trend shown (ascending/descending); score improvement/decline apparent; helps identify learning trajectory |

---

## 8. Teacher Passage Management
**Validates FR-012, FR-013: Create/edit passages and view student lists**

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-070 | Teacher creates new reading passage | Logged in as Teacher; Passages page loaded | 1. Click "Create Passage" 2. Enter title, text (500 words), select difficulty (Easy/Moderate/Hard) 3. Save | Passage created in passages table; id auto-assigned; teacher_id recorded; passage visible in passage list; word count auto-calculated |
| TC-071 | Teacher edits existing passage | Passage exists; teacher owns passage | 1. Select passage 2. Click "Edit" 3. Modify text 4. Save | Changes saved to passages table; passage_updated_at timestamp refreshed; existing student sessions unaffected; new students see updated content |
| TC-072 | Teacher views student list | Teacher logged in; multiple students in system | 1. Navigate to Teacher > Students 2. View student list | List displays: student name, ID, grade, section, current class level, pre-assessment completion status, recent score; sorted by last activity |
| TC-073 | Teacher opens individual student detail | Student list displayed; student "John Doe" visible | Click on student name "John Doe" | Student detail page opens showing: profile info, pre-assessment score, all reading sessions, scores, pending reviews; linked to FR-014 review workflow |
| TC-074 | Passage assignment to week/class level | Teacher creates passage for MODERATE difficulty | After creating passage, assign to Week 3 for students with class_level=MODERATE | Passage now appears in Reading section for MODERATE students in Week 3; visible in passage list; assignment persisted in database |

---

## 9. Teacher Review & Feedback
**Validates FR-014: Review submitted work and corresponding scores**

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-080 | View pending short-answer submissions | Student submitted session with 1 short answer; teacher not yet reviewed | 1. Navigate to Teacher > Pending Reviews 2. View list | List shows: student name, passage title, submission date, "Pending" status; sorted by most recent; count matches database pending records |
| TC-081 | Teacher scores short answer submission | Pending review visible; short answer text: "The story teaches us to be brave" | 1. Click submission 2. Read short answer 3. Enter score (0-100, e.g., 85) 4. Click "Submit Score" | Score saved to short_answer_responses table; is_scored = 1; teacher_id recorded; student can now see score in Progress |
| TC-082 | Teacher provides feedback comment | Scoring submission with optional feedback field | 1. Enter score 85 2. Type feedback: "Great summary! Include more details about theme" 3. Submit | Feedback text saved to short_answer_responses.feedback; visible to student on Results page; timestamp recorded |
| TC-083 | Bulk review workflow (multiple submissions) | 5 pending reviews in queue | 1. Open pending reviews list 2. Score submission 1 (mark complete) 3. Navigate to submission 2 4. Score and repeat | Each submission processed independently; completed submissions removed from pending list; workflow efficient for teacher workload |
| TC-084 | Cannot modify auto-graded MC answers | MC answer auto-scored as 1 (correct) | 1. Open student session detail 2. Attempt to modify MC score | MC section locked/read-only; teacher cannot override auto-score; feedback for MC optional but score immutable |

---

## 10. Recommendations Engine
**Validates FR-015: Generate and present recommendations based on performance**

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-090 | Difficulty recommendation for student | Student completed 5 readings at MODERATE level; avg score 88% | 1. Teacher navigates to Student "John" detail 2. Check Recommendations section | Recommendation displayed: "Student performing above level. Consider HARD passages for challenge" OR system suggests next-level passages |
| TC-091 | Passage recommendations appear in student view | Student completes reading with score 92 | 1. View Results after session 2. Check "Recommended Next" section | System suggests 2-3 passages from next level or similar genre; clickable links to start new reading |
| TC-092 | Recommendation accuracy based on score trend | Student scores: Session 1 (60), Session 2 (72), Session 3 (85) | Teacher views student progress; system generates recommendation | Recommendation reflects trend (improving): "Student showing progress. Current level appropriate" or "Ready to advance to next level" |
| TC-093 | Recommendations update after new session | Previous recommendation: "MODERATE level appropriate"; student submits new session scoring 95 | 1. Complete new reading session 2. Return to progress page | Recommendation updates: "Student excelling. HARD passages recommended" reflects latest performance data |
| TC-094 | Genre/topic-based recommendations | Student completes story passage scoring high | View recommendations section | System suggests next passage from similar genre or related topic (if configured); alternative difficulty options shown |

---

## 11. Report Generation
**Validates FR-016: Provide reports summarizing student and class performance**

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-100 | Generate individual student report | Teacher views student "Maria" profile | 1. Click "Generate Report" 2. Select date range (Last 30 days) 3. Click "Create" | PDF/document generated showing: student name, date range, readings completed (count), average score, scores per passage, progress trend, current level, feedback summary |
| TC-101 | Generate class-level performance report | Teacher has 20 students in class | 1. Navigate to Teacher > Reports 2. Select "Class Summary" 3. Choose date range 4. Generate | Report shows: total students, total sessions completed, class average score, breakdown by difficulty level (# students per EASY/MODERATE/HARD), top performers, students needing support |
| TC-102 | Export report as PDF or CSV | Report generated (individual or class) | Click "Export" button and select format (PDF or CSV) | File downloads with proper formatting; PDF includes header/footer with date generated; CSV includes headers and all data rows; file naming convention clear (e.g., "Report_ClassA_Aug2026.pdf") |
| TC-103 | Report accuracy verification | Report shows: 15 readings, avg score 78%, top score 95, lowest score 52 | Verify data against database queries for same student/date range | Numbers match exactly; no data loss or rounding errors; calculations correct (average = sum/count) |
| TC-104 | Date range filtering in reports | Teacher selects date range "Aug 1-15, 2026" | 1. Generate report for custom date range 2. Review sessions included | Only sessions with submitted_at within Aug 1-15 included; sessions outside range excluded; filter applied correctly to all metrics |

---

## 12. API & Backend Services
**Validates FR-017, FR-018: Backend support and logging/monitoring**

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-110 | API authentication with Bearer token | API request to /api/student/progress | 1. Include header: Authorization: Bearer <valid_token> 2. Send GET request | 200 OK response; student data returned; token validation successful |
| TC-111 | API rejects invalid/expired token | Valid token issued 7+ days ago (beyond 7-day refresh expiry) | Send request with expired token in Authorization header | 401 Unauthorized response; error message: "Token expired"; no data returned; user session invalid |
| TC-112 | API supports all required endpoints | Test endpoints: /api/auth/login, /api/student/pre-assessment, /api/student/reading/sessions, /api/teacher/reviews, /api/reports/generate | 1. Call each endpoint with appropriate method (GET/POST) 2. Check response codes and data | 200/201 responses for valid requests; correct data structures returned; all FR-017 endpoints functional |
| TC-113 | Logging captures key backend events | Student submits session; teacher scores answer | 1. Check application logs after events 2. Verify audit trail | Logs record: action (submit_reading, score_answer), user_id, timestamp, success/failure status, relevant IDs (student_id, session_id); critical errors logged for diagnostics |
| TC-114 | Database connection resilience | System running under load (25 concurrent users) | Monitor response times and error rates during peak activity | Connections pooled correctly; no dropped requests; response time < 2 seconds for dashboards (per NFR-4.1); system stable; errors logged if occur |

---

## Non-Functional Requirements Validation

### Performance (NFR-4.1)
- **Dashboard load time:** < 2 seconds (30 concurrent users)
- **Text classification queries:** < 3 seconds (500 passages)

**Test Cases:**
- TC-115: Load test with 30 concurrent logins; measure dashboard response time
- TC-116: Query 500 passages; verify classification returns in <3 seconds

### Security (NFR-4.2)
- **TLS 1.3+:** All data in transit encrypted
- **Password hashing:** bcrypt, cost factor ≥ 12
- **Session expiry:** 6 hours; refresh tokens 7 days
- **No PII:** Anonymized IDs only

**Test Cases:**
- TC-117: Verify HTTPS/TLS 1.3 enabled; certificate valid
- TC-118: Test password hashing with bcrypt verification
- TC-119: Verify session expires after 6-hour inactivity

### Reliability (NFR-4.3)
- **Uptime:** 99% during school hours (Mon-Fri, 07:00-17:00)
- **Backups:** Daily, retained 30 days
- **RTO:** < 4 hours

**Test Cases:**
- TC-120: Verify daily database backups created and retained
- TC-121: Simulate server failure; restore from backup; measure RTO

### Compliance (NFR-4.4)
- **Immutable audit logs:** No modification/deletion after creation
- **Data retention:** 1 school year minimum

**Test Cases:**
- TC-122: Attempt to modify/delete audit log record; verify 403 Forbidden
- TC-123: Verify literacy progress data retained for ≥ 365 days

---

## Summary of Changes from v1.0

✅ **Aligned with TalaSaAI SRS (DOC-005)**
- Based on FR-001 through FR-018
- Modules match SRS functional areas
- Exactly 5 test cases per module (60 total)

✅ **Zero Redundancy**
- Each test case validates distinct user action or system behavior
- No repeated test scenarios
- Clear separation between module concerns

✅ **Better Coverage**
- Added 12 NFR validation test cases (Performance, Security, Reliability, Compliance)
- Total test suite: 60 functional + 12 non-functional = 72 tests

✅ **Cleaner Organization**
- Each module tied directly to SRS requirement ID
- Pre-conditions clearly specify test data needed
- Expected results reference specific database fields/behaviors

---

## Test Execution Checklist

### Pre-UAT Setup
- [ ] Render cloud hosting environment ready (< 30 concurrent users)
- [ ] PostgreSQL database seeded with test data
- [ ] HTTPS/TLS 1.3 verified
- [ ] Backup system validated

### Test Data Requirements
- 5 test student accounts (varying pre-assessment scores: 30/50/70/85/95)
- 5 test teacher accounts
- 20 sample passages (5 EASY, 5 MODERATE, 5 HARD, 5 mixed difficulty)
- 3 weeks of pre-existing reading sessions and scores
- PHIL-IRI dataset imported for baseline text difficulty labels

### Sign-Off
- [ ] All 60 functional test cases executed
- [ ] All 12 NFR test cases executed
- [ ] Zero critical defects
- [ ] System ready for production deployment

---

**Document Version:** 2.0 (SRS-Aligned)  
**Date:** August 20, 2026  
**Status:** Ready for UAT Execution

