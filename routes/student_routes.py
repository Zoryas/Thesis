import json
from flask import Blueprint, request

from db import db_cursor
from routes.helpers import (
    api_error,
    api_ok,
    classify_pre_assessment_level,
    fetch_student_progress,
    normalize_avatar_type,
    normalize_class_level,
    normalize_text_value,
    normalize_week,
    pre_assessment_completed,
    require_role,
    sanitize_avatar_value,
    serialize_passage,
    serialize_user,
    student_row,
)


def _record_audit_log(user_id, student_id, action, details=None):
    with db_cursor(True) as (_, cur):
        cur.execute(
            "INSERT INTO audit_logs (user_id, student_id, action, details) VALUES (%s, %s, %s, %s)",
            (user_id, student_id, action, json.dumps(details or {}, ensure_ascii=False) if details is not None else None),
        )

student_bp = Blueprint("student_bp", __name__)


@student_bp.post("/api/student/pre-assessment")
def student_pre_assessment_submit():
    user, err = require_role("student")
    if err:
        return err

    payload = request.get_json(silent=True) or {}
    try:
        score = int(payload.get("score") or 0)
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(100, score))
    class_level = classify_pre_assessment_level(score)

    with db_cursor(True) as (_, cur):
        student = student_row(cur, user)
        if not student:
            return api_error("Student profile not found.", 404)

        cur.execute(
            """
            UPDATE students
            SET pre_score=%s, class_level=%s, pre_assessment_completed=1, pre_assessment_completed_at=NOW()
            WHERE id=%s
            """,
            (score, class_level, student["id"]),
        )
        cur.execute(
            "SELECT u.id,u.email,u.role,u.is_active, s.id AS student_id,s.full_name,s.grade,s.section,s.class_level,s.pre_score,s.pre_assessment_completed, s.avatar_type,s.avatar_value FROM users u LEFT JOIN students s ON s.user_id=u.id WHERE u.id=%s",
            (user["id"],),
        )
        refreshed_user = cur.fetchone()

    return api_ok({"user": serialize_user(refreshed_user), "preScore": score, "classLevel": class_level})


@student_bp.put("/api/student/profile/avatar")
def student_profile_avatar_update():
    user, err = require_role("student")
    if err:
        return err

    payload = request.get_json(silent=True) or {}
    avatar_type = normalize_avatar_type(payload.get("avatarType"))
    if not avatar_type:
        return api_error("avatarType must be initials, preset, or upload.", 400)

    try:
        avatar_value = sanitize_avatar_value(avatar_type, payload.get("avatarValue"))
    except ValueError as error:
        return api_error(str(error), 400)

    with db_cursor(True) as (_, cur):
        student = student_row(cur, user)
        if not student:
            return api_error("Student profile not found.", 404)

        cur.execute(
            "UPDATE students SET avatar_type=%s, avatar_value=%s WHERE id=%s",
            (avatar_type, avatar_value, student["id"]),
        )
        cur.execute(
            "SELECT u.id,u.email,u.role,u.is_active, s.id AS student_id,s.full_name,s.grade,s.section,s.class_level,s.pre_score,s.pre_assessment_completed, s.avatar_type,s.avatar_value FROM users u LEFT JOIN students s ON s.user_id=u.id WHERE u.id=%s",
            (user["id"],),
        )
        refreshed_user = cur.fetchone()

    return api_ok({"user": serialize_user(refreshed_user)})


@student_bp.get("/api/student/weekly-passages")
def student_weekly_passages():
    user, err = require_role("student")
    if err:
        return err
    week = normalize_week(request.args.get("week"))
    with db_cursor(True) as (_, cur):
        student = student_row(cur, user)
        if not student:
            return api_error("Student profile not found.", 404)
        if not pre_assessment_completed(student):
            return api_error("Complete the pre-assessment first.", 403)
        class_level = normalize_class_level(student["class_level"])
        cur.execute(
            """
            SELECT p.id,p.title,p.genre,p.text,p.label,p.words,p.est_minutes,p.confidence,p.is_draft
            FROM weekly_assignments wa JOIN passages p ON p.id=wa.passage_id
            WHERE wa.week_no=%s AND wa.class_level=%s
            ORDER BY wa.id
            """,
            (week, class_level),
        )
        passages = [serialize_passage(row) for row in cur.fetchall()]
    return api_ok({"week": week, "classLevel": class_level, "passages": passages})


@student_bp.get("/api/student/completions")
def student_completions():
    user, err = require_role("student")
    if err:
        return err
    week = normalize_week(request.args.get("week"))
    with db_cursor(True) as (_, cur):
        student = student_row(cur, user)
        if not student:
            return api_error("Student profile not found.", 404)
        if not pre_assessment_completed(student):
            return api_error("Complete the pre-assessment first.", 403)
        cur.execute("SELECT passage_id FROM passage_completions WHERE student_id=%s AND week_no=%s ORDER BY completed_at", (student["id"], week))
        ids = [row["passage_id"] for row in cur.fetchall()]
    return api_ok({"week": week, "completedPassageIds": ids})


@student_bp.post("/api/student/reading-time")
def student_reading_time():
    user, err = require_role("student")
    if err:
        return err

    payload = request.get_json(silent=True) or {}
    week = normalize_week(payload.get("week"))
    passage_id = str(payload.get("passageId") or "").strip()
    event_id = str(payload.get("eventId") or "").strip()
    formatted_time = str(payload.get("formattedTime") or "").strip()
    try:
        reading_seconds = int(payload.get("readingSeconds") or 0)
    except (TypeError, ValueError):
        reading_seconds = 0
    reading_seconds = max(0, reading_seconds)

    if not passage_id:
        return api_error("passageId is required.", 400)
    if not event_id:
        return api_error("eventId is required.", 400)

    with db_cursor(True) as (_, cur):
        student = student_row(cur, user)
        if not student:
            return api_error("Student profile not found.", 404)
        if not pre_assessment_completed(student):
            return api_error("Complete the pre-assessment first.", 403)

        class_level = normalize_class_level(student["class_level"])
        cur.execute(
            "SELECT 1 FROM weekly_assignments WHERE week_no=%s AND class_level=%s AND passage_id=%s",
            (week, class_level, passage_id),
        )
        if not cur.fetchone():
            return api_error("Passage is not assigned to this student for the selected week.", 400)

        cur.execute(
            """
            INSERT INTO student_reading_sessions (event_id, student_id, passage_id, week_no, reading_seconds, formatted_time)
            VALUES (%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
              student_id=VALUES(student_id),
              passage_id=VALUES(passage_id),
              week_no=VALUES(week_no),
              reading_seconds=VALUES(reading_seconds),
              formatted_time=VALUES(formatted_time)
            """,
            (event_id, student["id"], passage_id, week, reading_seconds, formatted_time or None),
        )

    return api_ok({"saved": True, "eventId": event_id})


@student_bp.get("/api/student/reading-progress")
def student_reading_progress_get():
    user, err = require_role("student")
    if err:
        return err

    week = normalize_week(request.args.get("week"))
    passage_id = str(request.args.get("passageId") or "").strip()
    if not passage_id:
        return api_error("passageId is required.", 400)

    with db_cursor(True) as (_, cur):
        student = student_row(cur, user)
        if not student:
            return api_error("Student profile not found.", 404)
        if not pre_assessment_completed(student):
            return api_error("Complete the pre-assessment first.", 403)

        class_level = normalize_class_level(student["class_level"])
        cur.execute(
            "SELECT 1 FROM weekly_assignments WHERE week_no=%s AND class_level=%s AND passage_id=%s",
            (week, class_level, passage_id),
        )
        if not cur.fetchone():
            return api_error("Passage is not assigned to this student for the selected week.", 400)

        cur.execute(
            """
            SELECT reading_seconds, last_event_id, is_locked, is_submitted, completed_at, updated_at
            FROM student_reading_progress_drafts
            WHERE student_id=%s AND passage_id=%s AND week_no=%s
            """,
            (student["id"], passage_id, week),
        )
        row = cur.fetchone()

    return api_ok(
        {
            "week": week,
            "passageId": passage_id,
            "readingSeconds": int((row or {}).get("reading_seconds") or 0),
            "lastEventId": (row or {}).get("last_event_id"),
            "isLocked": bool(int((row or {}).get("is_locked") or 0)),
            "isSubmitted": bool(int((row or {}).get("is_submitted") or 0)),
            "completedAt": row["completed_at"].isoformat() if row and row.get("completed_at") else None,
            "updatedAt": row["updated_at"].isoformat() if row and row.get("updated_at") else None,
        }
    )


@student_bp.post("/api/student/reading-progress")
def student_reading_progress_post():
    user, err = require_role("student")
    if err:
        return err

    payload = request.get_json(silent=True) or {}
    week = normalize_week(payload.get("week"))
    passage_id = str(payload.get("passageId") or "").strip()
    event_id = str(payload.get("eventId") or "").strip()
    try:
        reading_seconds = int(payload.get("readingSeconds") or 0)
    except (TypeError, ValueError):
        reading_seconds = 0
    reading_seconds = max(0, reading_seconds)

    if not passage_id:
        return api_error("passageId is required.", 400)

    with db_cursor(True) as (_, cur):
        student = student_row(cur, user)
        if not student:
            return api_error("Student profile not found.", 404)
        if not pre_assessment_completed(student):
            return api_error("Complete the pre-assessment first.", 403)

        class_level = normalize_class_level(student["class_level"])
        cur.execute(
            "SELECT 1 FROM weekly_assignments WHERE week_no=%s AND class_level=%s AND passage_id=%s",
            (week, class_level, passage_id),
        )
        if not cur.fetchone():
            return api_error("Passage is not assigned to this student for the selected week.", 400)

        cur.execute(
            """
            INSERT INTO student_reading_progress_drafts (student_id, passage_id, week_no, reading_seconds, last_event_id, is_locked, is_submitted, completed_at)
            VALUES (%s,%s,%s,%s,%s,0,0,NULL)
            ON DUPLICATE KEY UPDATE
              reading_seconds=IF(is_locked=1, reading_seconds, GREATEST(reading_seconds, VALUES(reading_seconds))),
              last_event_id=VALUES(last_event_id)
            """,
            (student["id"], passage_id, week, reading_seconds, event_id or None),
        )

        cur.execute(
            """
            SELECT reading_seconds, last_event_id, is_locked, completed_at, updated_at
            FROM student_reading_progress_drafts
            WHERE student_id=%s AND passage_id=%s AND week_no=%s
            """,
            (student["id"], passage_id, week),
        )
        row = cur.fetchone()

    return api_ok(
        {
            "saved": True,
            "week": week,
            "passageId": passage_id,
            "readingSeconds": int((row or {}).get("reading_seconds") or 0),
            "lastEventId": (row or {}).get("last_event_id"),
            "isLocked": bool(int((row or {}).get("is_locked") or 0)),
            "completedAt": row["completed_at"].isoformat() if row and row.get("completed_at") else None,
            "updatedAt": row["updated_at"].isoformat() if row and row.get("updated_at") else None,
        }
    )


@student_bp.post("/api/student/reading-lock")
def student_reading_lock_post():
    user, err = require_role("student")
    if err:
        return err

    payload = request.get_json(silent=True) or {}
    week = normalize_week(payload.get("week"))
    passage_id = str(payload.get("passageId") or "").strip()

    if not passage_id:
        return api_error("passageId is required.", 400)

    with db_cursor(True) as (_, cur):
        student = student_row(cur, user)
        if not student:
            return api_error("Student profile not found.", 404)
        if not pre_assessment_completed(student):
            return api_error("Complete the pre-assessment first.", 403)

        class_level = normalize_class_level(student["class_level"])
        cur.execute(
            "SELECT 1 FROM weekly_assignments WHERE week_no=%s AND class_level=%s AND passage_id=%s",
            (week, class_level, passage_id),
        )
        if not cur.fetchone():
            return api_error("Passage is not assigned to this student for the selected week.", 400)

        cur.execute(
            """
            INSERT INTO student_reading_progress_drafts (student_id, passage_id, week_no, reading_seconds, last_event_id, is_locked, completed_at)
            VALUES (%s,%s,%s,0,NULL,1,NOW())
            ON DUPLICATE KEY UPDATE
              is_locked=1,
              completed_at=COALESCE(completed_at, NOW())
            """,
            (student["id"], passage_id, week),
        )

        cur.execute(
            """
            SELECT reading_seconds, last_event_id, is_locked, completed_at, updated_at
            FROM student_reading_progress_drafts
            WHERE student_id=%s AND passage_id=%s AND week_no=%s
            """,
            (student["id"], passage_id, week),
        )
        row = cur.fetchone()

    return api_ok(
        {
            "saved": True,
            "week": week,
            "passageId": passage_id,
            "readingSeconds": int((row or {}).get("reading_seconds") or 0),
            "lastEventId": (row or {}).get("last_event_id"),
            "isLocked": bool(int((row or {}).get("is_locked") or 0)),
            "completedAt": row["completed_at"].isoformat() if row and row.get("completed_at") else None,
            "updatedAt": row["updated_at"].isoformat() if row and row.get("updated_at") else None,
        }
    )


@student_bp.post("/api/student/attempts")
def student_attempts():
    user, err = require_role("student")
    if err:
        return err
    payload = request.get_json(silent=True) or {}
    week = normalize_week(payload.get("week"))
    passage_id = str(payload.get("passageId") or "").strip()
    if not passage_id:
        return api_error("passageId is required.", 400)

    score = int(payload.get("score") or 0)
    correct = int(payload.get("correct") or 0)
    total = int(payload.get("total") or 0)
    difficulty = payload.get("difficulty")
    try:
        difficulty = int(difficulty) if difficulty not in (None, "") else None
    except (TypeError, ValueError):
        difficulty = None
    if difficulty is not None:
        difficulty = max(1, min(5, difficulty))

    short_answer = normalize_text_value(payload.get("shortAnswer") or "", max_length=4000)
    reading_time = str(payload.get("readingTime") or "").strip()
    responses = payload.get("responses") if isinstance(payload.get("responses"), list) else []

    with db_cursor(True) as (_, cur):
        student = student_row(cur, user)
        if not student:
            return api_error("Student profile not found.", 404)
        if not pre_assessment_completed(student):
            return api_error("Complete the pre-assessment first.", 403)
        class_level = normalize_class_level(student["class_level"])

        cur.execute(
            "SELECT 1 FROM weekly_assignments WHERE week_no=%s AND class_level=%s AND passage_id=%s",
            (week, class_level, passage_id),
        )
        if not cur.fetchone():
            return api_error("Passage is not assigned to this student for the selected week.", 400)

        cur.execute(
            """
            INSERT INTO quiz_attempts (
              student_id,passage_id,week_no,score_pct,correct_count,total_count,difficulty_rating,
              short_answer_text,reading_time,responses_json
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE
              score_pct=VALUES(score_pct),
              correct_count=VALUES(correct_count),
              total_count=VALUES(total_count),
              difficulty_rating=VALUES(difficulty_rating),
              short_answer_text=VALUES(short_answer_text),
              reading_time=VALUES(reading_time),
              responses_json=VALUES(responses_json),
              submitted_at=CURRENT_TIMESTAMP
            """,
            (
                student["id"],
                passage_id,
                week,
                max(0, min(100, score)),
                max(0, correct),
                max(0, total),
                difficulty,
                short_answer or None,
                reading_time or None,
                json.dumps(responses, ensure_ascii=False) if responses else None,
            ),
        )

        cur.execute(
            """
            SELECT id
            FROM quiz_attempts
            WHERE student_id=%s AND passage_id=%s AND week_no=%s
            ORDER BY id DESC
            LIMIT 1
            """,
            (student["id"], passage_id, week),
        )
        attempt_id = int(cur.fetchone()["id"])

        cur.execute(
            "INSERT INTO passage_completions (student_id,week_no,passage_id) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE completed_at=completed_at",
            (student["id"], week, passage_id),
        )

        cur.execute(
            """
            INSERT INTO student_reading_progress_drafts (student_id, passage_id, week_no, reading_seconds, last_event_id, is_locked, is_submitted, completed_at)
            VALUES (%s,%s,%s,0,NULL,1,1,NOW())
            ON DUPLICATE KEY UPDATE
              is_locked=1,
              is_submitted=1,
              completed_at=COALESCE(completed_at, NOW())
            """,
            (student["id"], passage_id, week),
        )

        cur.execute(
            """
            INSERT INTO reading_sessions
              (legacy_quiz_attempt_id, student_id, passage_id, week_no, started_at, completed_at, duration_seconds, status)
            VALUES (%s,%s,%s,%s,NULL,NOW(),0,'completed')
            ON DUPLICATE KEY UPDATE
              student_id=VALUES(student_id),
              passage_id=VALUES(passage_id),
              week_no=VALUES(week_no),
              completed_at=COALESCE(VALUES(completed_at), completed_at),
              status='completed',
              duration_seconds=0
            """,
            (attempt_id, student["id"], passage_id, week),
        )
        cur.execute(
            "SELECT id FROM reading_sessions WHERE legacy_quiz_attempt_id=%s",
            (attempt_id,),
        )
        session_id = int(cur.fetchone()["id"])

        responses_payload = json.dumps(responses, ensure_ascii=False) if responses else None
        cur.execute(
            """
            INSERT INTO student_answers
              (legacy_quiz_attempt_id, session_id, question_id, answer_payload_json, is_correct_nullable, submitted_at)
            VALUES (%s,%s,NULL,%s,NULL,NOW())
            ON DUPLICATE KEY UPDATE
              session_id=VALUES(session_id),
              answer_payload_json=VALUES(answer_payload_json),
              submitted_at=VALUES(submitted_at)
            """,
            (attempt_id, session_id, responses_payload),
        )
        cur.execute(
            "SELECT id FROM student_answers WHERE legacy_quiz_attempt_id=%s ORDER BY id DESC LIMIT 1",
            (attempt_id,),
        )
        student_answer_id = int(cur.fetchone()["id"])

        if short_answer:
            cur.execute(
                """
                INSERT INTO short_answer_responses
                  (legacy_quiz_attempt_id, student_answer_id, response_text, needs_manual_review, submitted_at)
                VALUES (%s,%s,%s,0,NOW())
                ON DUPLICATE KEY UPDATE
                  student_answer_id=VALUES(student_answer_id),
                  response_text=VALUES(response_text),
                  needs_manual_review=VALUES(needs_manual_review),
                  submitted_at=COALESCE(VALUES(submitted_at), submitted_at)
                """,
                (attempt_id, student_answer_id, short_answer),
            )
        else:
            cur.execute("DELETE FROM short_answer_responses WHERE legacy_quiz_attempt_id=%s", (attempt_id,))

        objective_score_pct = max(0, min(100, score))
        cur.execute(
            """
            INSERT INTO scores
              (legacy_quiz_attempt_id, session_id, objective_score_pct, short_answer_score_pct, total_score_pct, computed_at)
            VALUES (%s,%s,%s,NULL,%s,NOW())
            ON DUPLICATE KEY UPDATE
              objective_score_pct=VALUES(objective_score_pct),
              total_score_pct=VALUES(total_score_pct),
              computed_at=VALUES(computed_at)
            """,
            (attempt_id, session_id, objective_score_pct, objective_score_pct),
        )

        cur.execute("SELECT id FROM reading_history WHERE session_id=%s LIMIT 1", (session_id,))
        if not cur.fetchone():
            history_summary = {
                "weekNo": week,
                "passageId": passage_id,
                "scorePct": int(objective_score_pct),
                "shortAnswerPresent": bool(short_answer),
                "readingTime": reading_time or None,
                "submittedAt": "",
            }
            cur.execute(
                """
                INSERT INTO reading_history (student_id, session_id, summary_json)
                VALUES (%s,%s,%s)
                """,
                (student["id"], session_id, json.dumps(history_summary, ensure_ascii=False)),
            )

        cur.execute(
            "SELECT passage_id FROM passage_completions WHERE student_id=%s AND week_no=%s ORDER BY completed_at",
            (student["id"], week),
        )
        completed = [row["passage_id"] for row in cur.fetchall()]

    _record_audit_log(user["id"], student["id"], "student_submission", {"passageId": passage_id, "week": week, "hasShortAnswer": bool(short_answer)})
    return api_ok({"attemptId": attempt_id, "week": week, "passageId": passage_id, "completedPassageIds": completed}, 201)


@student_bp.get("/api/student/progress")
def student_progress():
    user, err = require_role("student")
    if err:
        return err
    with db_cursor(True) as (_, cur):
        student = student_row(cur, user)
        if not student:
            return api_error("Student profile not found.", 404)
        if not pre_assessment_completed(student):
            return api_error("Complete the pre-assessment first.", 403)
        progress = fetch_student_progress(cur, student["id"])
    return api_ok({"progress": progress})
