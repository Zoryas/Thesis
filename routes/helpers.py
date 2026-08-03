import secrets
from flask import jsonify, request, session
from db import db_cursor


def api_ok(data=None, status=200):
    return jsonify({"ok": True, "data": data}), status


def api_error(message, status=400):
    return jsonify({"ok": False, "error": message}), status


def serialize_passage(row):
    confidence = float(row["confidence"]) if row.get("confidence") is not None else None
    return {
        "id": row["id"],
        "title": row["title"],
        "genre": row["genre"],
        "text": row["text"],
        "label": row["label"],
        "words": int(row["words"]),
        "time": int(row["est_minutes"]),
        "confidence": confidence,
        "isDraft": bool(int(row.get("is_draft") or 0)),
    }


def get_request_token():
    header_token = str(request.headers.get("X-Auth-Token") or "").strip()
    if header_token:
        return header_token
    auth_header = str(request.headers.get("Authorization") or "").strip()
    if auth_header.lower().startswith("bearer "):
        bearer_token = auth_header[7:].strip()
        if bearer_token:
            return bearer_token
    return None


def fetch_user_by_id(cur, user_id):
    cur.execute(
        """
        SELECT u.id,u.email,u.role,u.is_active,
               s.id AS student_id,s.full_name,s.grade,s.section,s.class_level,s.pre_score,s.pre_assessment_completed,
               s.avatar_type,s.avatar_value
        FROM users u LEFT JOIN students s ON s.user_id=u.id
        WHERE u.id=%s
        """,
        (user_id,),
    )
    return cur.fetchone()


def current_user():
    uid = session.get("user_id")
    if uid:
        with db_cursor(True) as (_, cur):
            row = fetch_user_by_id(cur, uid)
            if row and row.get("is_active"):
                return row

    token = get_request_token()
    if token:
        with db_cursor(True) as (_, cur):
            cur.execute(
                """
                SELECT u.id,u.email,u.role,u.is_active,
                       s.id AS student_id,s.full_name,s.grade,s.section,
                       s.class_level,s.pre_score,s.pre_assessment_completed,s.avatar_type,s.avatar_value
                FROM auth_tokens t
                JOIN users u ON u.id=t.user_id
                LEFT JOIN students s ON s.user_id=u.id
                WHERE t.token=%s
                """,
                (token,),
            )
            row = cur.fetchone()
            if row and row.get("is_active"):
                return row

    return None


def require_auth():
    user = current_user()
    if not user:
        return None, api_error("Authentication required.", 401)
    return user, None


def require_role(role):
    user, err = require_auth()
    if err:
        return None, err
    if user["role"] != role:
        return None, api_error("Insufficient permissions.", 403)
    return user, None


def serialize_user(row):
    student = None
    if row.get("student_id"):
        student = {
            "id": row["student_id"],
            "name": row.get("full_name"),
            "grade": row.get("grade"),
            "section": row.get("section"),
            "classLevel": row.get("class_level"),
            "preScore": row.get("pre_score"),
            "preAssessmentCompleted": bool(int(row.get("pre_assessment_completed") or 0)),
            "avatarType": row.get("avatar_type") or "initials",
            "avatarValue": row.get("avatar_value") or "",
        }
    return {"id": row["id"], "email": row["email"], "role": row["role"], "student": student}


def student_row(cur, user):
    sid = user.get("student_id")
    if sid:
        cur.execute("SELECT id, full_name, grade, section, class_level, pre_score, pre_assessment_completed FROM students WHERE id=%s", (sid,))
    else:
        cur.execute("SELECT id, full_name, grade, section, class_level, pre_score, pre_assessment_completed FROM students WHERE user_id=%s", (user["id"],))
    return cur.fetchone()


def pre_assessment_completed(student):
    if not student:
        return False
    return bool(int(student.get("pre_assessment_completed") or 0))


def recommendation_for_score(score):
    from app import recommendation_for_score as _recommendation_for_score
    return _recommendation_for_score(score)


def fetch_student_progress(cur, student_id):
    from app import fetch_student_progress as _fetch_student_progress
    return _fetch_student_progress(cur, student_id)
