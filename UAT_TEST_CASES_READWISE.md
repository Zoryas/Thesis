# ReadWise UAT Test Cases
**Version 1.0** | **Date:** August 2026  
**Educational Reading Assessment Platform**

---

## Test Cases Summary

| Module | Total Cases | Automated | Manual (UAT) | Status |
|--------|-------------|-----------|-------------|--------|
| Authentication & RBAC | 8 | 8 | 0 | Pending |
| User Management (Admin) | 10 | 8 | 2 | Pending |
| Reading Passages Management | 9 | 7 | 2 | Pending |
| Pre-Assessment & Placement | 8 | 6 | 2 | Pending |
| Reading Session & Assessments | 12 | 9 | 3 | Pending |
| Teacher Scoring & Feedback | 8 | 6 | 2 | Pending |
| Student Progress & Reports | 7 | 5 | 2 | Pending |
| Program Week Management | 6 | 5 | 1 | Pending |
| Audit Trail | 6 | 5 | 1 | Pending |
| Data Import/Migration | 4 | 2 | 2 | Pending |
| **TOTAL** | **78** | **61** | **17** | |

---

## 1. Authentication & RBAC

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-001 | Successful login - Teacher | Account exists with teacher role | 1. Navigate to /login 2. Enter valid teacher email + password 3. Click Sign In | Dashboard loads; JWT token created; teacher navigation shown (Students, Passages, Reports) |
| TC-002 | Successful login - Student | Account exists with student role | 1. Navigate to /login 2. Enter valid student email + password 3. Click Sign In | Dashboard loads; JWT token created; student navigation shown (Pre-Assessment, Reading, Progress) |
| TC-003 | Successful login - Admin | Account exists with admin role | 1. Navigate to /login 2. Enter valid admin email + password 3. Click Sign In | Dashboard loads; JWT token created; admin navigation shown (Users, Passages, Settings) |
| TC-004 | Login blocked with wrong password | Account exists | 1. Enter valid email + incorrect password 2. Click Sign In | Error message shown; login attempt recorded; no redirect |
| TC-005 | Account locks after 5 failures | Account exists | Attempt login with wrong password 5 times within rate limit window | 5th attempt: "Too many login attempts" error; subsequent attempts blocked for duration |
| TC-006 | Student cannot access Admin Settings | Logged in as Student | Navigate to /admin via URL | Redirected to student dashboard with 403 Insufficient Permissions error |
| TC-007 | Teacher cannot manage other teachers | Logged in as Teacher | 1. Navigate to Users management via URL 2. Attempt to create teacher account | Page not found or 403 Insufficient Permissions |
| TC-008 | Rate limiting applies per IP:email | Multiple accounts on same IP | Perform 5 login attempts with email1, then attempt login with email2 | email2 login succeeds; rate limit is per email+IP combination, not global |

---

## 2. User Management (Admin)

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-010 | Admin creates teacher account | Logged in as Admin | 1. Admin > Users 2. Click Create 3. Enter email, password, select "Teacher" role 4. Submit | New teacher account created; user can login; audit log entry created |
| TC-011 | Admin creates student account | Logged in as Admin | 1. Admin > Users 2. Click Create 3. Enter email, password, select "Student" role 4. Submit | New student account created; student_id auto-generated (s1, s2...); audit log entry created |
| TC-012 | Admin creates admin account | Logged in as Admin | 1. Admin > Users 2. Click Create 3. Enter email, password, select "Admin" role 4. Submit | New admin account created; new admin has full permissions |
| TC-013 | Duplicate email rejected | Email already exists in system | Attempt to create user with existing email | Error: "Email is already in use." |
| TC-014 | Missing email/password rejected | Form submitted without email or password | 1. Leave email field empty 2. Click Create | Error: "Email and password are required." |
| TC-015 | Admin deactivates student account | Student account is active | 1. Admin > Users 2. Select student 3. Click Deactivate | Student login fails; account marked inactive; audit log created |
| TC-016 | Admin cannot delete own account | Logged in as Admin (self) | 1. Admin > Users 2. Search for own email 3. Click Delete | Error: "You cannot delete the account you are currently using." |
| TC-017 | Admin updates user password | User account exists | 1. Admin > Users 2. Select user 3. Click Reset Password 4. Enter new password 5. Submit | Password updated; user can login with new password; old password no longer works |
| TC-018 | List users filtered by role | Multiple users with different roles exist | 1. Admin > Users 2. Select role filter "Teacher" 3. Apply | Only teacher accounts displayed in list |
| TC-019 | User list shows creation date | Multiple users in system | 1. Admin > Users 2. View user list | Each user shows "Created At" timestamp in ISO format |

---

## 3. Reading Passages Management

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-020 | Admin imports CSV passages (Easy level) | CSV file with 5 passages formatted correctly | 1. Admin > Passages 2. Click Import 3. Upload assessments_easy.csv 4. Confirm | All passages imported; level set to EASY; word count and time estimates calculated |
| TC-021 | Admin imports passages (Moderate level) | CSV file with assessments_moderate.csv | 1. Admin > Passages 2. Upload assessments_moderate.csv | All passages imported; level set to MODERATE |
| TC-022 | Admin imports passages (Hard level) | CSV file with assessments_hard.csv | 1. Admin > Passages 2. Upload assessments_hard.csv | All passages imported; level set to HARD |
| TC-023 | Word count and time estimate calculated | Valid passage text submitted | 1. Create passage with 500-word text 2. Save | Word count: 500; Est. reading time calculated (typically 2 minutes per 100 words) |
| TC-024 | Duplicate passage title rejected | Passage title already exists | 1. Create passage 2. Enter existing title 3. Save | Error: "Passage title must be unique." |
| TC-025 | Admin can edit passage text and assessment | Passage exists with assessment | 1. Admin > Passages 2. Select passage 3. Edit text 4. Update assessment questions 5. Save | Changes saved; version updated; assessment questions refreshed |
| TC-026 | Passage assigned to specific week | Passage created but not yet assigned | 1. Admin > Passages 2. Select passage 3. Assign to Week 3 4. Save | Passage now appears in Week 3 for eligible students |
| TC-027 | Assessment questions stored with passage | Passage uploaded with embedded assessment | Questions stored in assessment_questions table; linked to passage via assessment_id |
| TC-028 | Passages can be marked as draft | Passage created but incomplete | 1. Create passage 2. Mark as Draft 3. Save | Passage hidden from students; visible only to admins/teachers; is_draft = 1 |

---

## 4. Pre-Assessment & Placement

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-030 | Student completes pre-assessment | Logged in as Student; pre-assessment not yet taken | 1. Student Dashboard > Pre-Assessment 2. Answer all questions 3. Submit score: 65 | Pre-assessment marked complete; pre_score = 65; class_level = MODERATE; progress bar updates |
| TC-031 | Low score → EASY classification | Pre-assessment submitted with score 40 | Submit assessment with 40/100 | class_level set to EASY; student assigned to easy passages |
| TC-032 | Medium score → MODERATE classification | Pre-assessment submitted with score 65 | Submit assessment with 65/100 | class_level set to MODERATE; student assigned to moderate passages |
| TC-033 | High score → HARD classification | Pre-assessment submitted with score 85 | Submit assessment with 85/100 | class_level set to HARD; student assigned to hard passages |
| TC-034 | Student cannot retake pre-assessment | Pre-assessment already completed | Student navigates to pre-assessment page | "Pre-assessment already completed" message; cannot retake |
| TC-035 | Pre-assessment completion triggers passage eligibility | Pre-assessment just completed with score 70 | Complete pre-assessment | Eligible passages for MODERATE level now visible in Reading section |
| TC-036 | Pre-assessment score persists in profile | Student completed pre-assessment | Student navigates to Profile > Pre-Assessment | Score (e.g., 70) displayed with completion timestamp |
| TC-037 | Admin can view all pre-assessment results | Multiple students completed pre-assessment | 1. Admin > Dashboard > Pre-Assessment Results 2. View by score/class level | List shows all students with scores, class levels, completion dates |

---

## 5. Reading Session & Assessments

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-040 | Student starts reading session | Logged in as Student; pre-assessment complete; eligible passages available | 1. Student > Reading 2. Select passage 3. Click "Start Reading" | reading_sessions created; session_id generated; status = started; started_at recorded |
| TC-041 | Reading timer starts on session begin | Reading session started | Timer visible on page counting up | Timer increments; duration_seconds captures elapsed time |
| TC-042 | Student submits multiple-choice answers | Reading session in progress | 1. Answer 5 multiple-choice questions 2. Submit | All answers stored in student_answers table; answer_payload_json captures selection |
| TC-043 | Student submits short answer response | Reading session in progress | 1. Read prompt: "Summarize the main theme" 2. Type response 3. Submit | Short answer stored in short_answer_responses table; response_text captured |
| TC-044 | Student can review answers before final submit | Session in progress; some answers submitted | 1. Navigate to Review tab 2. See all answers 3. Modify one answer 4. Resubmit | Answer updated; new submitted_at timestamp recorded |
| TC-045 | Session marked complete on final submit | All questions answered | Click "Complete Reading" button | reading_sessions.status = completed; completed_at = NOW(); reading_sessions.duration_seconds finalized |
| TC-046 | Assessment auto-grades multiple choice | Session submitted with MC answers | Response submitted | is_correct field updated for MC questions based on answer_index match |
| TC-047 | Short answers require teacher scoring | Session submitted with short answers | Session marked complete | short_answer_responses.is_scored = 0 (pending); visible in teacher pending review list |
| TC-048 | Student cannot start session twice for same passage (same week) | Reading session already exists for passage + week | Student attempts to start another session for same passage | Error: "You have already submitted for this passage this week." |
| TC-049 | Session data persists after page reload | Session in progress; answers submitted | 1. Answer question 2. Reload page 3. Navigate back to session | Previous answers still visible; session continues from where student left off |
| TC-050 | Reading time tracked accurately | Student reads for 5 minutes then submits | Complete session | duration_seconds = ~300 (±5 sec tolerance) |
| TC-051 | Student can view reading passage text | Session started | Passage text visible on screen | Full passage text displayed; formatting preserved; font size readable |

---

## 6. Teacher Scoring & Feedback

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-060 | Teacher views pending student submissions | Student submitted session with short answers | 1. Teacher > Pending Reviews 2. View list | Submissions show: student name, passage title, date submitted; sorted by date |
| TC-061 | Teacher scores short answer (Correct) | Session with short answer pending review | 1. Teacher > Pending 2. Select submission 3. Enter score: 100 4. Add feedback: "Excellent summary" 5. Submit | short_answer_responses.score = 100; feedback stored; submission marked is_scored = 1 |
| TC-062 | Teacher scores short answer (Partial credit) | Session with short answer pending review | Teacher scores submission as 75/100 | Score saved; student can view feedback |
| TC-063 | Teacher scores short answer (Zero) | Session with short answer pending review | Teacher scores submission as 0 with feedback "Missing key points" | Score = 0; feedback stored; student sees score but can resubmit if allowed |
| TC-064 | Teacher provides feedback comment | Scoring a submission | 1. Enter score 2. Add comment in feedback field 3. Submit | Feedback text stored and visible to student in progress view |
| TC-065 | Teacher cannot score MC questions manually | MC answers auto-graded | Teacher attempts to modify MC auto-score | MC answers locked; cannot be edited by teacher |
| TC-066 | Teacher dashboard shows class statistics | Multiple student submissions graded | 1. Teacher > Dashboard 2. View class summary | Shows: avg score, total submissions, pending count, by class level breakdown |
| TC-067 | Teacher exports class report as CSV | Scores entered for multiple students | 1. Teacher > Reports 2. Select date range 3. Export CSV | CSV downloads with columns: student name, passage, score, feedback, date |

---

## 7. Student Progress & Reports

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-070 | Student views reading progress | Student completed 3 readings in Week 1 | 1. Student > Progress 2. View Week 1 | Shows 3 completed readings; completion %; class level; avg score |
| TC-071 | Student sees score for submitted reading | Reading session scored | 1. Student > Progress 2. Select reading entry 3. View details | Shows: score, feedback, timestamp; MC score auto-calculated; short answer shows teacher score |
| TC-072 | Student progress filtered by week | Multiple weeks of data | 1. Student > Progress 2. Select Week 3 | Only Week 3 entries displayed |
| TC-073 | Student avatar customizable (initials) | Logged in as Student | 1. Student > Profile 2. Avatar > Initials 3. Save | Avatar type = initials; avatar_value stored; displayed on dashboard |
| TC-074 | Student avatar customizable (preset) | Logged in as Student | 1. Student > Profile 2. Avatar > Select preset emoji 3. Save | avatar_type = preset; avatar_value stores selected emoji |
| TC-075 | Student can view full class/section info | Logged in as Student | 1. Student > Profile 2. View class details | Shows: grade, section, class level (EASY/MODERATE/HARD) |
| TC-076 | Student can generate personal progress summary | Multiple readings completed | 1. Student > Reports 2. Select date range 3. Generate | Report shows: total readings, average score, completion rate, class level recommendations |

---

## 8. Program Week Management

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-080 | Teacher sets program start date | Logged in as Teacher; program_settings not yet configured | 1. Teacher > Settings 2. Set Program Start Date to 2026-08-20 3. Save | program_settings.program_start_date = 2026-08-20; activeWeek auto-calculated as Week 1 |
| TC-081 | System auto-calculates active week | Program start date set to 7 days ago (today = Aug 20) | API call: /api/program/week | Returns activeWeek = 2 (7 days = 1 week into program) |
| TC-082 | Teacher manually overrides active week | Program auto-calculated as Week 2 | 1. Teacher > Settings 2. Set Manual Override Week = 4 3. Save | activeWeek = 4 (override active); passages from Week 4 assigned to students |
| TC-083 | Clearing manual override reverts to auto | Manual override was Week 4 | 1. Teacher > Settings 2. Clear Manual Override 3. Save | activeWeek reverts to auto-calculated based on program_start_date |
| TC-084 | Invalid manual week rejected | Attempting to set manualOverrideWeek = 10 | API call with manualOverrideWeek > 8 | Error: "manualOverrideWeek must be between 1 and 8." |
| TC-085 | Teacher can view week settings | Logged in as Teacher | 1. Teacher > Settings | Displays: current active week, program start date, manual override option |

---

## 9. Audit Trail

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-090 | Audit entry created for user login | User logs in | Login attempt recorded | audit_logs entry: action = "login"; user_id set; details = {email, role}; timestamp recorded |
| TC-091 | Audit entry created for admin user creation | Admin creates new teacher account | Admin creates user | audit_logs entry: action = "admin:create_user"; details = {userId, email, role} |
| TC-092 | Audit entry created for student submission | Student completes reading session | Session submitted | audit_logs entry: action = "student:submit_reading"; details = {passage_id, week_no, score} |
| TC-093 | Audit entry created for teacher scoring | Teacher scores short answer | Score submitted | audit_logs entry: action = "teacher:score_submission"; details = {session_id, score, feedback} |
| TC-094 | Audit records cannot be modified | Audit entry exists | Send PATCH request to modify audit entry | API returns 403 Forbidden; audit_logs record unchanged |
| TC-095 | Admin can export audit trail as CSV | Multiple audit entries over 30 days | 1. Admin > Audit Trail 2. Set date range (last 30 days) 3. Export CSV | CSV downloads with columns: timestamp, user, action, student_id (if applicable), details |

---

## 10. Data Import/Migration

| TC ID | Description | Pre-condition | Steps | Expected Result |
|-------|-------------|---|---|---|
| TC-100 | Import valid passage CSV | Passages CSV file with correct format | 1. Admin > Passages > Import 2. Upload passages.csv | All passages imported; 0 errors; passage count matches file rows |
| TC-101 | Handle duplicate passage title on import | Passage "Chapter 1" already exists in system | Import CSV with duplicate "Chapter 1" | Duplicate flagged; admin offered Skip or Overwrite option; no silent data loss |
| TC-102 | Reject CSV with invalid data format | CSV with malformed date (e.g., "32-13-2026") | Upload CSV with invalid date | Error shown: "Row 5: Invalid date format in column created_at" |
| TC-103 | Post-import reconciliation | Migration of 50 passages completed | 1. Export post-import passage report 2. Compare row count to source CSV | Counts match within 0% variance; any gaps flagged and logged |

---

## Module-Specific Notes & Exclusions

### Features NOT Applicable to ReadWise (from PharmaSync):

| PharmaSync Feature | Why Not Applicable | ReadWise Alternative |
|---|---|---|
| **Stock Management / Inventory** | Educational platform has no physical inventory | Reading passages are digital assets |
| **Expiry Tracking & Alerts** | Educational content doesn't expire | Passages remain available; can be archived if needed |
| **Batch/SKU Management** | No medication batches in education | Passages tagged by week, level, genre |
| **Low-Stock Warnings** | No inventory quantities | No equivalent needed |
| **Delivery/PO Workflow** | No vendor/supplier management | Admin manually creates/imports passages |
| **Dispenser Role** | No medication dispensing | Teachers score/review submissions |
| **Pharmacy-Specific Workflows** | Not applicable to education | Educational workflows (pre-assessment, reading, scoring) |

---

## Recommended Enhancements & Best Practices

### 1. **Error Handling & Validation**
- ✅ Add TC-120: Invalid JSON request body handling (all API endpoints)
- ✅ Add TC-121: Missing required fields in POST/PUT requests
- ✅ Add TC-122: Validate email format on user creation (RFC 5322)
- ✅ Add TC-123: Password strength requirements (min 8 chars, mixed case recommended)

### 2. **Security Hardening**
- ✅ Add TC-130: SQL injection prevention (test special chars in inputs)
- ✅ Add TC-131: XSS prevention in feedback comments (test `<script>` tags)
- ✅ Add TC-132: CSRF token validation on state-changing requests
- ✅ Add TC-133: Token expiration (JWT should have exp claim; test after expiry)
- ✅ Add TC-134: Invalid token handling (malformed/tampered token rejection)

### 3. **Performance & Load Testing**
- ✅ Add TC-140: Load test: 100 concurrent student logins
- ✅ Add TC-141: Load test: Teacher dashboard with 500+ students
- ✅ Add TC-142: Database query performance (audit trail export >10k records)
- ✅ Add TC-143: Large passage import (1000+ records)

### 4. **Data Consistency & Integrity**
- ✅ Add TC-150: Foreign key constraint validation (delete user → cascade to students)
- ✅ Add TC-151: Concurrent session handling (student login on 2 devices simultaneously)
- ✅ Add TC-152: Transaction rollback on partial failures (failed migration)
- ✅ Add TC-153: Database backup/restore verification

### 5. **Edge Cases & Boundary Testing**
- ✅ Add TC-160: Pre-assessment score = 0 (minimum boundary)
- ✅ Add TC-161: Pre-assessment score = 100 (maximum boundary)
- ✅ Add TC-162: Reading passage with 0 words (edge case)
- ✅ Add TC-163: Student ID generation at s999999 (numeric overflow)
- ✅ Add TC-164: 8-week program boundary (week 8 completion)
- ✅ Add TC-165: Multiple passages assigned to same week

### 6. **Integration & API Testing**
- ✅ Add TC-170: API authentication via Bearer token vs X-Auth-Token header
- ✅ Add TC-171: CORS headers validation for cross-origin requests
- ✅ Add TC-172: Rate limiting at API endpoint level (not just login)
- ✅ Add TC-173: Pagination for large result sets (students list, audit trail)

### 7. **User Experience & Accessibility**
- ✅ Add TC-180: Mobile responsiveness on reading session page
- ✅ Add TC-181: Screen reader compatibility for progress charts
- ✅ Add TC-182: Session timeout warning (auto-logout after 30 min inactivity)
- ✅ Add TC-183: Graceful handling of lost connection during reading session

### 8. **Reporting & Analytics**
- ✅ Add TC-190: Teacher report generation includes all score types (auto + manual)
- ✅ Add TC-191: Progress report accurately reflects unscored submissions
- ✅ Add TC-192: Admin analytics show user creation/deletion trends
- ✅ Add TC-193: Audit trail filtering by date range with timezone support

### 9. **Environment & Configuration**
- ✅ Add TC-200: READWISE_RATE_LIMIT_WINDOW_SECONDS env var respected
- ✅ Add TC-201: READWISE_RATE_LIMIT_MAX_ATTEMPTS env var respected
- ✅ Add TC-202: Database connection pooling under load
- ✅ Add TC-203: Timezone handling for timestamps (UTC storage, local display)

### 10. **Regression & Smoke Tests**
- ✅ Add TC-210: Smoke test: login → create passage → assign to week → student reads → teacher scores
- ✅ Add TC-211: Regression: pre-assessment score change doesn't retroactively change past readings
- ✅ Add TC-212: Regression: deleting teacher doesn't delete their scored submissions

---

## Defect Log

| Bug ID | TC Ref | Description | Severity | Assigned To | Status | Fixed |
|--------|--------|---|---|---|---|---|
| — | — | No defects logged — UAT not yet started | — | — | — | — |

---

## Test Execution Notes

### Automated Tests (61 total)
- Unit tests: Authentication, RBAC, data validation
- Integration tests: API endpoints, database operations
- SQL injection / XSS payload testing
- JWT token validation and expiration

### Manual UAT Tests (17 total)
- User role workflows (teacher, student, admin perspectives)
- Report generation and export accuracy
- UI responsiveness and accessibility
- Complex multi-step scenarios (pre-assessment → reading → teacher scoring)

### Performance Baselines to Establish
- Login response time: < 500ms
- Reading session load: < 1000ms
- Report export (10k records): < 5s
- Concurrent users handling: 100+ simultaneous logins

---

## Approval & Sign-Off

**Document Version:** 1.0  
**Date Prepared:** August 20, 2026  
**Status:** Ready for UAT Execution  
**Next Steps:** Begin test execution on staging environment; report results weekly

