from flask import Blueprint, request

from db import db_cursor
from routes.helpers import api_error, api_ok, require_auth, require_role

teacher_bp = Blueprint("teacher_bp", __name__)


def _load_app_helpers():
    from app import (
        TOTAL_PROGRAM_WEEKS,
        average_numbers,
        build_teacher_report_summary,
        fetch_pending_short_answer,
        fetch_pending_short_answers,
        fetch_student_progress,
        fetch_teacher_student_summaries,
        get_program_settings,
        normalize_class_level,
        normalize_week,
        parse_program_start_date,
    )
    return {
        "TOTAL_PROGRAM_WEEKS": TOTAL_PROGRAM_WEEKS,
        "average_numbers": average_numbers,
        "build_teacher_report_summary": build_teacher_report_summary,
        "fetch_pending_short_answer": fetch_pending_short_answer,
        "fetch_pending_short_answers": fetch_pending_short_answers,
        "fetch_student_progress": fetch_student_progress,
        "fetch_teacher_student_summaries": fetch_teacher_student_summaries,
        "get_program_settings": get_program_settings,
        "normalize_class_level": normalize_class_level,
        "normalize_week": normalize_week,
        "parse_program_start_date": parse_program_start_date,
    }


@teacher_bp.get("/api/teacher/dashboard")
def teacher_dashboard():
    helpers = _load_app_helpers()
    normalize_class_level = helpers["normalize_class_level"]
    fetch_teacher_student_summaries = helpers["fetch_teacher_student_summaries"]

    user, err = require_role("teacher")
    if err:
        return err
    del user

    with db_cursor(True) as (_, cur):
        students = fetch_teacher_student_summaries(cur)
        cur.execute(
            """
            SELECT qa.student_id,s.full_name,p.id AS passage_id,p.title,qa.score_pct,qa.short_answer_text,qa.submitted_at
            FROM quiz_attempts qa
            JOIN (
                SELECT student_id, passage_id, week_no, MAX(id) AS latest_id
                FROM quiz_attempts
                GROUP BY student_id, passage_id, week_no
            ) latest
              ON latest.latest_id = qa.id
            JOIN students s ON s.id=qa.student_id
            JOIN passages p ON p.id=qa.passage_id
            ORDER BY qa.submitted_at DESC, qa.id DESC
            LIMIT 6
            """
        )
        submissions = []
        for row in cur.fetchall():
            submissions.append(
                {
                    "studentId": row["student_id"],
                    "studentName": row["full_name"],
                    "passageId": row["passage_id"],
                    "passageTitle": row["title"],
                    "score": int(row["score_pct"] or 0),
                    "status": "Pending Review" if row.get("short_answer_text") and row.get("teacher_score") is None else "Scored",
                    "submittedAt": row["submitted_at"].isoformat() if row.get("submitted_at") else None,
                }
            )

    level_counts = {"EASY": 0, "MODERATE": 0, "HARD": 0}
    level_students = {"EASY": [], "MODERATE": [], "HARD": []}
    pending_reviews = []
    recommendation_count = 0
    for student in students:
        level = normalize_class_level(student["classLevel"])
        level_counts[level] += 1
        level_students[level].append(student["name"])
        if student["pendingReviewCount"]:
            pending_reviews.append(student)
        if len(student["progress"]) >= 2:
            recommendation_count += 1

    return api_ok(
        {
            "levelCounts": level_counts,
            "levelStudents": level_students,
            "recentSubmissions": submissions,
            "pendingReviews": pending_reviews[:3],
            "recommendationCount": recommendation_count,
            "studentCount": len(students),
        }
    )


@teacher_bp.get("/api/teacher/students")
def teacher_students():
    helpers = _load_app_helpers()
    fetch_teacher_student_summaries = helpers["fetch_teacher_student_summaries"]

    user, err = require_role("teacher")
    if err:
        return err
    del user

    with db_cursor(True) as (_, cur):
        students = fetch_teacher_student_summaries(cur)
    return api_ok({"students": students})


@teacher_bp.get("/api/program/week")
def api_program_week():
    helpers = _load_app_helpers()
    get_program_settings = helpers["get_program_settings"]

    user, err = require_auth()
    if err:
        return err
    if user["role"] not in {"teacher", "student"}:
        return api_error("Insufficient permissions.", 403)
    with db_cursor(True) as (_, cur):
        settings = get_program_settings(cur)
        if not settings:
            return api_error("Program settings not configured.", 500)
    return api_ok({"activeWeek": settings["activeWeek"]})


@teacher_bp.get("/api/program/week/settings")
def api_program_week_settings_get():
    helpers = _load_app_helpers()
    get_program_settings = helpers["get_program_settings"]

    user, err = require_role("teacher")
    if err:
        return err
    del user
    with db_cursor(True) as (_, cur):
        settings = get_program_settings(cur)
        if not settings:
            return api_error("Program settings not configured.", 500)
    return api_ok(settings)


@teacher_bp.put("/api/program/week/settings")
def api_program_week_settings_put():
    helpers = _load_app_helpers()
    TOTAL_PROGRAM_WEEKS = helpers["TOTAL_PROGRAM_WEEKS"]
    get_program_settings = helpers["get_program_settings"]
    parse_program_start_date = helpers["parse_program_start_date"]

    user, err = require_role("teacher")
    if err:
        return err

    payload = request.get_json(silent=True)
    if payload is None:
        return api_error("Request body must be valid JSON.", 400)
    if not isinstance(payload, dict):
        return api_error("Request body must be a JSON object.", 400)

    from app import parse_program_start_date

    start_date_raw = payload.get("programStartDate")
    override_week_raw = payload.get("manualOverrideWeek")

    parsed_start_date = parse_program_start_date(start_date_raw)
    if start_date_raw not in (None, "") and parsed_start_date is None:
        return api_error("programStartDate must be in YYYY-MM-DD format.", 400)

    manual_override_week = None
    if override_week_raw not in (None, "", "null"):
        try:
            parsed_override = int(override_week_raw)
        except (TypeError, ValueError):
            return api_error("manualOverrideWeek must be a number between 1 and 8, or null.", 400)
        if parsed_override < 1 or parsed_override > TOTAL_PROGRAM_WEEKS:
            return api_error("manualOverrideWeek must be between 1 and 8, or null.", 400)
        manual_override_week = parsed_override

    with db_cursor(True) as (_, cur):
        cur.execute(
            """
            UPDATE program_settings
            SET program_start_date=%s, manual_override_week=%s, updated_by=%s
            WHERE id=1
            """,
            (parsed_start_date, manual_override_week, user["id"]),
        )
        settings = get_program_settings(cur)

    return api_ok(settings)


@teacher_bp.get("/api/teacher/reports/summary")
def teacher_reports_summary():
    helpers = _load_app_helpers()
    build_teacher_report_summary = helpers["build_teacher_report_summary"]
    get_program_settings = helpers["get_program_settings"]
    normalize_week = helpers["normalize_week"]

    user, err = require_role("teacher")
    if err:
        return err
    del user

    active_week = request.args.get("activeWeek")
    with db_cursor(True) as (_, cur):
        if active_week in (None, "", "null"):
            settings = get_program_settings(cur)
            active_week = settings["activeWeek"] if settings else 1
        summary = build_teacher_report_summary(cur, normalize_week(active_week))
    return api_ok(summary)


@teacher_bp.get("/api/teacher/students/<student_id>")
def teacher_student_detail(student_id):
    helpers = _load_app_helpers()
    fetch_pending_short_answer = helpers["fetch_pending_short_answer"]
    fetch_student_progress = helpers["fetch_student_progress"]

    user, err = require_role("teacher")
    if err:
        return err
    del user

    with db_cursor(True) as (_, cur):
        cur.execute(
            """
            SELECT s.id,s.full_name,s.grade,s.section,s.class_level,s.pre_score,s.pre_assessment_completed,u.email
            FROM students s
            JOIN users u ON u.id=s.user_id
            WHERE s.id=%s
            """,
            (student_id,),
        )
        student = cur.fetchone()
        if not student:
            return api_error("Student not found.", 404)

        progress = fetch_student_progress(cur, student_id)
        pending_short_answer = fetch_pending_short_answer(cur, student_id)

        latest_scored_attempt = None
        cur.execute(
            """
            SELECT qa.id,qa.passage_id,qa.week_no,qa.teacher_score,qa.teacher_feedback,
                   qa.teacher_scored_by,qa.teacher_scored_at,p.title,u.full_name AS scorer_name
            FROM quiz_attempts qa
            JOIN passages p ON p.id = qa.passage_id
            LEFT JOIN students u ON u.user_id = qa.teacher_scored_by
            WHERE qa.student_id=%s
              AND qa.teacher_score IS NOT NULL
            ORDER BY qa.teacher_scored_at DESC, qa.id DESC
            LIMIT 1
            """,
            (student_id,),
        )
        row = cur.fetchone()
        if row:
            latest_scored_attempt = {
                "attemptId": int(row["id"]),
                "passageId": row["passage_id"],
                "passageTitle": row["title"],
                "week": int(row["week_no"]),
                "score": int(row["teacher_score"]),
                "feedback": row.get("teacher_feedback") or "",
                "scoredBy": row.get("scorer_name"),
                "scoredAt": row["teacher_scored_at"].isoformat() if row.get("teacher_scored_at") else None,
            }

    latest = progress[-1] if progress else None
    payload = {
        "student": {
            "id": student["id"],
            "name": student["full_name"],
            "email": student["email"],
            "grade": student["grade"],
            "section": student["section"],
            "classLevel": student["class_level"],
            "preScore": int(student["pre_score"] or 0),
            "preAssessmentCompleted": bool(int(student["pre_assessment_completed"] or 0)),
        },
        "progress": progress,
        "latest": latest,
        "pendingShortAnswer": pending_short_answer,
        "latestScoredAttempt": latest_scored_attempt,
    }
    return api_ok(payload)


@teacher_bp.get("/api/teacher/students/<student_id>/pending-short-answers")
def teacher_student_pending_short_answers(student_id):
    helpers = _load_app_helpers()
    fetch_pending_short_answers = helpers["fetch_pending_short_answers"]

    user, err = require_role("teacher")
    if err:
        return err
    del user

    with db_cursor(True) as (_, cur):
        cur.execute(
            """
            SELECT s.id,s.full_name,s.grade,s.section,s.class_level,u.email
            FROM students s
            JOIN users u ON u.id=s.user_id
            WHERE s.id=%s
            """,
            (student_id,),
        )
        student = cur.fetchone()
        if not student:
            return api_error("Student not found.", 404)

        pending_items = fetch_pending_short_answers(cur, student_id)

    return api_ok(
        {
            "student": {
                "id": student["id"],
                "name": student["full_name"],
                "email": student["email"],
                "grade": student["grade"],
                "section": student["section"],
                "classLevel": student["class_level"],
            },
            "pendingShortAnswers": pending_items,
        }
    )


@teacher_bp.post("/api/teacher/score")
def teacher_score_save():
    user, err = require_role("teacher")
    if err:
        return err

    payload = request.get_json(silent=True) or {}
    student_id = str(payload.get("studentId") or "").strip()
    passage_id = str(payload.get("passageId") or "").strip()
    if not student_id or not passage_id:
        return api_error("studentId and passageId are required.", 400)

    score_raw = payload.get("score")
    try:
        score = int(score_raw)
    except (TypeError, ValueError):
        return api_error("score must be an integer (0 or 1).", 400)

    if score not in (0, 1):
        return api_error("score must be 0 (Incorrect) or 1 (Correct).", 400)

    feedback = str(payload.get("feedback") or "").strip()

    with db_cursor(True) as (_, cur):
        cur.execute("SELECT id FROM students WHERE id=%s", (student_id,))
        if not cur.fetchone():
            return api_error("Student not found.", 404)

        cur.execute(
            """
            SELECT id,week_no
            FROM quiz_attempts
            WHERE student_id=%s AND passage_id=%s AND short_answer_text IS NOT NULL
            ORDER BY submitted_at DESC, id DESC
            LIMIT 1
            """,
            (student_id, passage_id),
        )
        attempt = cur.fetchone()
        if not attempt:
            return api_error("No short-answer attempt found for this student and passage.", 404)

        cur.execute(
            """
            UPDATE quiz_attempts
            SET teacher_score=%s,
                teacher_feedback=%s,
                teacher_scored_by=%s,
                teacher_scored_at=NOW()
            WHERE id=%s
            """,
            (score, feedback or None, user["id"], attempt["id"]),
        )

        cur.execute(
            """
            SELECT id
            FROM short_answer_responses
            WHERE legacy_quiz_attempt_id=%s
            ORDER BY id DESC
            LIMIT 1
            """,
            (attempt["id"],),
        )
        sar = cur.fetchone()
        if sar:
            cur.execute(
                """
                INSERT INTO short_answer_scores
                  (legacy_quiz_attempt_id, short_answer_response_id, teacher_id, score_binary, feedback, scored_at)
                VALUES (%s,%s,%s,%s,%s,NOW())
                ON DUPLICATE KEY UPDATE
                  teacher_id=VALUES(teacher_id),
                  score_binary=VALUES(score_binary),
                  feedback=VALUES(feedback),
                  scored_at=VALUES(scored_at)
                """,
                (attempt["id"], int(sar["id"]), user["id"], 1 if score == 1 else 0, feedback or None),
            )

        cur.execute(
            """
            SELECT qa.id,qa.student_id,qa.passage_id,qa.week_no,qa.teacher_score,qa.teacher_feedback,
                   qa.teacher_scored_at,u.full_name AS scorer_name
            FROM quiz_attempts qa
            LEFT JOIN students u ON u.user_id=qa.teacher_scored_by
            WHERE qa.id=%s
            """,
            (attempt["id"],),
        )
        saved = cur.fetchone()

    return api_ok(
        {
            "attemptId": int(saved["id"]),
            "studentId": saved["student_id"],
            "passageId": saved["passage_id"],
            "week": int(saved["week_no"]),
            "score": int(saved["teacher_score"]),
            "feedback": saved.get("teacher_feedback") or "",
            "scoredBy": saved.get("scorer_name"),
            "scoredAt": saved["teacher_scored_at"].isoformat() if saved.get("teacher_scored_at") else None,
        }
    )
