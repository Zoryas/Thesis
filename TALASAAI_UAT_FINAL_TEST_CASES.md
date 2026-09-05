# Test Plan
## TalaSaAI - QA & UAT Strategy

**DOC-006** | **Version 3.0** | **Date:** August 2026  
**Project Manager:** Mark Nino A. Ritualo | **Sponsor:** University of Cabuyao  
**Status:** For Validation / On Going | **Confidential**

---

## 1. Overview

| Item | Description |
|---|---|
| Project | TalaSaAI - Reading Difficulty Prediction System |
| System | Machine learning and NLP-based web application for Grade 7 English reading support |
| Test Manager | Mark Nino A. Ritualo (Project Manager) |
| Lead Developer | Lester Allen M. Gomba |
| Junior Developer | Mark Gionard G. Almario |
| Document Writer | Princess Diana T. Calendro |
| UAT Lead | Grade 7 English Teacher (Evaluator) |
| UAT Backup | Grade 7 Student Respondents (Pulo National High School) |
| UAT Start | 01 October 2026 |
| UAT End | 15 October 2026 |
| Target Go-Live | 17 October 2026 |
| SRS Reference | TalaSaAI SRS v1.0 (DOC-005) |
| Related Documents | DOC-001 Project Charter; DOC-002 Feasibility Study; DOC-003 Project Plan; DOC-004 Business Requirements Document |

## 2. Objectives

- Validate the 18 functional requirements in DOC-005.
- Verify that Grade 7 English passages are classified as EASY, MODERATE, or DIFFICULT and that the model meets the target of at least 70% accuracy with a strong F1-score.
- Confirm that students can complete pre-assessment, reading, questioning, submission, results, and progress workflows.
- Confirm that teachers can manage passages and assignments, review student work, view recommendations, and generate class reports.
- Verify that student progress records include comprehension scores, completion, reading time, and self-reported difficulty.
- Verify role-based access control and protection of anonymous student data.
- Confirm logging, health checks, backup, retention, and recovery procedures meet the stated reliability and security requirements.
- Validate CSV passage import and reconciliation of imported records.

## 3. Test Scope

### 3.1 In Scope

| Module | Test Types | Priority |
|---|---|---|
| Authentication & RBAC | Functional, Security | Critical |
| Student Profile & Avatar | Functional, Regression | High |
| Pre-Assessment & Placement | Functional, Data Integrity | Critical |
| Reading Passages & Assignments | Functional, Integration | Critical |
| Reading Lock, Timer & Progress | Functional, Data Integrity, Regression | Critical |
| Questions, Responses & Results | Functional, Integration | Critical |
| Scoring & Teacher Review | Functional, Data Integrity | High |
| Teacher Dashboard & Student Records | Functional | High |
| Recommendations | Functional, Integration | High |
| Reports & Export | Functional | Medium |
| Logging, Health Checks & Security | Reliability, Security | Critical |
| CSV Import & Data Reconciliation | Functional, Migration | Critical |

### 3.2 Out of Scope

- Long-term literacy growth beyond the three-week study period described in DOC-001.
- Non-English passages.
- Texts under 30 words.
- Control-group comparison and multi-school or multi-grade deployment.
- Broader classroom instruction, remediation, or diagnostic assessment.
- Penetration testing, which is deferred to post-launch security review.
- Mobile browser testing; UAT is desktop-focused.
- Load testing beyond the stated capacity of approximately 30 concurrent users.

## 4. Test Types

| Test Type | Description | Owner | Tooling |
|---|---|---|---|
| Unit Testing | Validate classification helpers, scoring logic, validation, and API utilities in isolation. | Junior Developer | PyTest |
| Integration Testing | Validate Flask API, database, assessment, scoring, and recommendation interactions. | Lead Developer | PyTest + Postman |
| System / E2E | Simulate complete student and teacher journeys from login through reporting and review. | Lead Developer | Playwright / Selenium |
| User Acceptance Testing | Grade 7 English teacher and student respondents validate usability and classroom workflows. | Teacher Evaluator | Manual |
| Regression Testing | Re-run affected automated and smoke checks after defect fixes. | Lead Developer | PyTest + Playwright |
| Security Testing | Validate authentication, RBAC, token/header handling, CSRF/origin checks, anonymous IDs, and audit events. | Lead Developer | PyTest + API probes |
| Migration Testing | Import Phil-IRI and approved passage CSV data and reconcile source rows with stored records. | Lead Developer | Custom scripts |
| Reliability Testing | Validate health endpoints, backup/restore guidance, retention, and recovery readiness. | Project Manager / Lead Developer | Smoke scripts + deployment checks |

## 5. Entry & Exit Criteria

### 5.1 UAT Entry Criteria

- All Must Have requirements in DOC-005 are implemented and have passed unit or integration validation.
- At least 75% unit test coverage is achieved and verified.
- No open Critical or High defects block the core student or teacher workflows.
- Staging environment is stable for 48 hours.
- Representative Phil-IRI and approved passage data is loaded.
- Test accounts exist for students and teachers, including varied pre-assessment levels.
- Weekly assignments, assessment questions, and teacher review data are available for testing.
- The UAT environment, database, HTTPS configuration, and backup procedure are documented.

### 5.2 UAT Exit Criteria

- All core student and teacher user stories pass acceptance review.
- All Must Have functional requirements have evidence of validation.
- No open Critical or High defects remain.
- The Grade 7 English teacher signs off the UAT results.
- Student respondents complete the agreed reading and assessment workflow review.
- CSV migration reconciles 100% of expected import records, or every exception is documented and approved.
- Results, progress, recommendations, and reports are reconciled against the test data.

## 6. Defect Severity

| Severity | Definition | Response Time | Resolution Target |
|---|---|---|---|
| Critical | System crash, data loss, RBAC breach, corrupted assessment result, or unrecoverable student record. | Immediate | Before UAT resumes |
| High | Core student or teacher workflow blocked, incorrect score, incorrect assignment, or failed teacher review. | Within 24 hours | Within 3 working days |
| Medium | Workaround available; minor report, progress, recommendation, or validation defect. | Within 48 hours | Before go-live |
| Low | Cosmetic issue or minor usability improvement with no data or workflow impact. | Logged | Post-go-live acceptable |

## 7. Schedule

| Activity | Start | End | Owner |
|---|---|---|---|
| Unit and integration validation | 23 August 2026 | 12 September 2026 | Lead Developer / Junior Developer |
| System and E2E workflow preparation | 23 August 2026 | 19 September 2026 | Lead Developer |
| UAT plan and acceptance review | 14 September 2026 | 19 September 2026 | Project Manager / Teacher Evaluator |
| UAT execution | 21 September 2026 | 25 September 2026 | Teacher Evaluator, Student Respondents, Project Team |
| Defect fixes and regression re-run | 21 September 2026 | 26 September 2026 | Lead Developer / Junior Developer |
| Teacher sign-off and go/no-go review | 26 September 2026 | 26 September 2026 | Project Manager / Teacher Evaluator |
| Target go-live and monitoring | 17 October 2026 | 17 October 2026 | Project Manager / Lead Developer |

## 8. Risks and Assumptions

- Training data may be insufficient or inconsistently labeled; labels should be reviewed using Phil-IRI criteria before model evaluation.
- Low model accuracy may require additional passages, feature tuning, cross-validation, or retraining.
- Delayed student participation may reduce the validity of progress results; backup sessions should be arranged.
- Internet or technical interruptions may require documented offline recording and later reconciliation.
- Student data is expected to remain anonymous and access-controlled throughout testing.
- Teacher evaluators and student respondents are expected to participate during the planned UAT window.

## 9. Implementation References

The test plan is supported by the repository implementation and verification materials:

- Student UI: `pages/student-dashboard.html`, `pages/student-passage.html`, `pages/student-reading.html`, `pages/student-questions.html`, `pages/student-results.html`, `pages/student-progress.html`, `pages/student-profile.html`, `pages/student-pre-assessment.html`
- Teacher UI: `pages/teacher-dashboard.html`, `pages/teacher-passages.html`, `pages/teacher-submit.html`, `pages/teacher-students.html`, `pages/teacher-student-detail.html`, `pages/teacher-student-pending.html`, `pages/teacher-score.html`, `pages/teacher-recommendations.html`, `pages/teacher-reports.html`
- API client: `api.js`
- Backend routes: `routes/auth_routes.py`, `routes/student_routes.py`, `routes/teacher_routes.py`, `routes/passage_routes.py`, `routes/admin_routes.py`
- Database and seed support: `db.py`, `seed_db.py`, `migrations/`
- Automated tests: `test/`
- Operational checks: `scripts/phase3_smoke_test.py`, `scripts/api_dual_write_smoke_test.py`, `scripts/final_publish_check.py`

## 10. Document Control Notes

- The supplied project documents contain a schedule conflict: the Project Charter lists deployment as 22 September to 10 September, while the BRD requires deployment by 30 September and the target go-live is 17 October. The Project Manager must approve one authoritative deployment date.
- The supplied feasibility and SRS documents mention PostgreSQL, while the current repository uses a MySQL connector and MySQL-oriented schema scripts. The deployment database platform must be confirmed before UAT entry.
- The supplied documents use both a three-week and four-week study duration. This plan uses the three-week duration from the Project Charter unless the Project Manager formally revises it.
