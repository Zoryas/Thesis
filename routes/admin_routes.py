import json

from flask import Blueprint, request
from werkzeug.security import generate_password_hash

from db import db_cursor
from routes.helpers import api_error, api_ok, require_role
from routes.passage_routes import save_passage, serialize_passage

admin_bp = Blueprint("admin_bp", __name__)


def _record_audit_log(user_id, student_id, action, details=None, cur=None):
    payload = json.dumps(details or {}, ensure_ascii=False) if details is not None else None
    # When called with an active cursor, attempt the insert but do not let
    # audit log failures bubble up and break the primary operation (create/update).
    if cur is not None:
        try:
            cur.execute(
                "INSERT INTO audit_logs (user_id, student_id, action, details) VALUES (%s, %s, %s, %s)",
                (user_id, student_id, action, payload),
            )
        except Exception as exc:
            # Log to stdout/stderr for visibility during debugging but do not raise.
            try:
                print(f"Warning: failed to write audit log: {exc}")
            except Exception:
                pass
        return

    # If no cursor supplied, try to write the audit log in its own transaction,
    # but swallow errors to avoid affecting the caller.
    try:
        with db_cursor(True) as (_, cur):
            try:
                cur.execute(
                    "INSERT INTO audit_logs (user_id, student_id, action, details) VALUES (%s, %s, %s, %s)",
                    (user_id, student_id, action, payload),
                )
            except Exception as exc:
                try:
                    print(f"Warning: failed to write audit log: {exc}")
                except Exception:
                    pass
    except Exception:
        # Swallow any errors from creating a separate DB transaction for auditing.
        pass


def _next_student_id(cur):
    cur.execute("SELECT COALESCE(MAX(CAST(SUBSTRING(id,2) AS UNSIGNED)),0) AS max_id FROM students WHERE id REGEXP '^s[0-9]+$'")
    row = cur.fetchone()
    return f"s{int(row['max_id'] or 0) + 1}"


def _ensure_unique_email(cur, email):
    if not email:
        return False
    cur.execute("SELECT id FROM users WHERE email=%s", (email.lower(),))
    return cur.fetchone() is None



@admin_bp.get("/api/admin/summary")
def admin_summary():
    user, err = require_role("admin")
    if err:
        return err

    with db_cursor(True) as (_, cur):
        cur.execute("SELECT COUNT(*) AS student_count FROM students")
        student_count = cur.fetchone()["student_count"]

        cur.execute("SELECT COUNT(*) AS teacher_count FROM teachers")
        teacher_count = cur.fetchone()["teacher_count"]

        cur.execute("SELECT COUNT(*) AS passage_count FROM passages")
        passage_count = cur.fetchone()["passage_count"]

        cur.execute(
            "SELECT action, details, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 6"
        )
        actions = [
            {
                "action": row["action"],
                "details": row["details"] or "",
                "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
            }
            for row in cur.fetchall()
        ]

    return api_ok({
        "studentCount": student_count,
        "teacherCount": teacher_count,
        "passageCount": passage_count,
        "recentActions": actions,
    })


@admin_bp.get("/api/admin/users")
def admin_list_users():
    user, err = require_role("admin")
    if err:
        return err

    role_filter = request.args.get("role")
    with db_cursor(True) as (_, cur):
        if role_filter:
            cur.execute(
                "SELECT id, email, role, is_active, created_at FROM users WHERE role=%s ORDER BY created_at DESC",
                (role_filter,)
            )
        else:
            cur.execute(
                "SELECT id, email, role, is_active, created_at FROM users ORDER BY created_at DESC"
            )
        users = [
            {
                "id": row["id"],
                "email": row["email"],
                "role": row["role"],
                "isActive": bool(row["is_active"]),
                "createdAt": row["created_at"].isoformat() if row["created_at"] else None,
            }
            for row in cur.fetchall()
        ]

    return api_ok({"users": users})


@admin_bp.post("/api/admin/users")
def admin_create_user():
    user, err = require_role("admin")
    if err:
        return err

    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        return api_error("Request body must be valid JSON.", 400)

    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password")
    role = payload.get("role", "admin")

    if not email or not password:
        return api_error("Email and password are required.", 400)
    if role not in {"admin", "teacher", "student"}:
        return api_error("Invalid role.", 400)

    with db_cursor(True) as (_, cur):
        if not _ensure_unique_email(cur, email):
            return api_error("Email is already in use.", 400)

        password_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO users (email, password_hash, role, is_active) VALUES (%s, %s, %s, 1)",
            (email, password_hash, role),
        )
        user_id = cur.lastrowid
        cur.execute("SELECT id, email, role, is_active FROM users WHERE id=%s", (user_id,))
        row = cur.fetchone()
        _record_audit_log(user["id"], None, "admin:create_user", {"userId": user_id, "email": email, "role": role}, cur=cur)

    return api_ok({
        "id": row["id"],
        "email": row["email"],
        "role": row["role"],
        "isActive": bool(row["is_active"]),
    })


@admin_bp.delete("/api/admin/users/<int:user_id>")
def admin_delete_user(user_id):
    user, err = require_role("admin")
    if err:
        return err

    with db_cursor(True) as (_, cur):
        if user_id == user["id"]:
            return api_error("You cannot delete the account you are currently using.", 400)

        cur.execute("SELECT id, email FROM users WHERE id=%s", (user_id,))
        row = cur.fetchone()
        if not row:
            return api_error("User not found.", 404)

        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        _record_audit_log(user["id"], None, "admin:delete_user", {"userId": user_id, "email": row["email"]}, cur=cur)

    return api_ok({"id": user_id})


@admin_bp.put("/api/admin/users/<int:user_id>")
def admin_update_user(user_id):
    user, err = require_role("admin")
    if err:
        return err

    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        return api_error("Request body must be valid JSON.", 400)

    allowed = {"role", "isActive", "password"}
    updates = []
    values = []
    if "role" in payload:
        updates.append("role=%s")
        values.append(payload["role"])
    if "isActive" in payload:
        updates.append("is_active=%s")
        values.append(1 if payload["isActive"] else 0)
    if "password" in payload and payload["password"]:
        updates.append("password_hash=%s")
        values.append(generate_password_hash(payload["password"]))

    if not updates:
        return api_error("No allowed fields to update.", 400)

    values.append(user_id)
    with db_cursor(True) as (_, cur):
        cur.execute(
            f"UPDATE users SET {', '.join(updates)} WHERE id=%s",
            tuple(values),
        )

        cur.execute("SELECT id, email, role, is_active FROM users WHERE id=%s", (user_id,))
        row = cur.fetchone()
        if not row:
            return api_error("User not found.", 404)

        _record_audit_log(user["id"], None, "admin:update_user", {"userId": user_id, "payload": payload})

    return api_ok({
        "id": row["id"],
        "email": row["email"],
        "role": row["role"],
        "isActive": bool(row["is_active"]),
    })


@admin_bp.get("/api/admin/students")
def admin_list_students():
    user, err = require_role("admin")
    if err:
        return err

    with db_cursor(True) as (_, cur):
        cur.execute(
            "SELECT s.id AS student_id, u.id AS user_id, u.email, u.is_active, s.full_name, s.grade, s.section, s.class_level, s.pre_score, s.pre_assessment_completed, u.created_at AS user_created_at FROM students s JOIN users u ON u.id=s.user_id ORDER BY u.created_at ASC"
        )
        students = [
            {
                "id": row["student_id"],
                "userId": row["user_id"],
                "email": row["email"],
                "fullName": row["full_name"],
                "grade": row["grade"],
                "section": row["section"],
                "classLevel": row["class_level"],
                "preScore": int(row["pre_score"] or 0),
                "preAssessmentCompleted": bool(row["pre_assessment_completed"]),
                "createdAt": row.get("user_created_at").isoformat() if row.get("user_created_at") else None,
                "isActive": bool(row["is_active"]),
            }
            for row in cur.fetchall()
        ]

    return api_ok({"students": students})


@admin_bp.post("/api/admin/students")
def admin_create_student():
    user, err = require_role("admin")
    if err:
        return err

    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        return api_error("Request body must be valid JSON.", 400)

    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")
    full_name = str(payload.get("fullName") or "").strip()
    grade = str(payload.get("grade") or "7").strip() or "7"
    section = str(payload.get("section") or "").strip()
    class_level = str(payload.get("classLevel") or "EASY").strip().upper()
    pre_score = payload.get("preScore")
    has_pre_score = "preScore" in payload
    is_active = bool(payload.get("isActive", True))

    if not email or not password or not full_name:
        return api_error("Email, password, and full name are required.", 400)

    if class_level not in {"EASY", "MODERATE", "HARD"}:
        class_level = "EASY"

    try:
        pre_score = int(pre_score or 0)
    except (TypeError, ValueError):
        pre_score = 0
    pre_score = max(0, min(100, pre_score))
    pre_assessment_completed = 1 if has_pre_score else 0

    with db_cursor(True) as (_, cur):
        if not _ensure_unique_email(cur, email):
            return api_error("Email is already in use.", 400)

        cur.execute(
            "INSERT INTO users (email, password_hash, role, is_active) VALUES (%s, %s, 'student', %s)",
            (email, generate_password_hash(password), 1 if is_active else 0),
        )
        user_id = cur.lastrowid
        student_id = _next_student_id(cur)
        cur.execute(
            "INSERT INTO students (id, user_id, full_name, grade, section, class_level, pre_score, pre_assessment_completed) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (student_id, user_id, full_name, grade, section or "", class_level, pre_score, pre_assessment_completed),
        )
        _record_audit_log(user["id"], student_id, "admin:create_student", {"email": email, "grade": grade, "section": section}, cur=cur)

    return api_ok({"id": student_id, "userId": user_id, "email": email, "fullName": full_name, "grade": grade, "section": section, "classLevel": class_level, "preScore": pre_score, "isActive": is_active})


@admin_bp.put("/api/admin/students/<student_id>")
def admin_update_student(student_id):
    user, err = require_role("admin")
    if err:
        return err

    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        return api_error("Request body must be valid JSON.", 400)

    full_name = payload.get("fullName")
    grade = payload.get("grade")
    section = payload.get("section")
    class_level = payload.get("classLevel")
    pre_score = payload.get("preScore")
    is_active = payload.get("isActive")
    email = payload.get("email")
    password = payload.get("password")

    if email is not None:
        email = str(email or "").strip().lower()
        if not email:
            return api_error("Student email cannot be empty.", 400)

    if class_level is not None:
        class_level = str(class_level or "EASY").strip().upper()
        if class_level not in {"EASY", "MODERATE", "HARD"}:
            class_level = "EASY"

    has_pre_score = "preScore" in payload
    if pre_score is not None:
        try:
            pre_score = int(pre_score)
        except (TypeError, ValueError):
            return api_error("preScore must be a number.", 400)
        pre_score = max(0, min(100, pre_score))

    with db_cursor(True) as (_, cur):
        cur.execute("SELECT user_id FROM students WHERE id=%s", (student_id,))
        row = cur.fetchone()
        if not row:
            return api_error("Student not found.", 404)
        user_id = row["user_id"]

        if email is not None:
            cur.execute("SELECT id FROM users WHERE email=%s AND id<>%s", (email, user_id))
            if cur.fetchone():
                return api_error("Email is already in use.", 400)
            cur.execute("UPDATE users SET email=%s WHERE id=%s", (email, user_id))

        if password:
            cur.execute("UPDATE users SET password_hash=%s WHERE id=%s", (generate_password_hash(password), user_id))

        student_updates = []
        student_values = []
        if full_name is not None:
            student_updates.append("full_name=%s")
            student_values.append(str(full_name or "").strip())
        if grade is not None:
            student_updates.append("grade=%s")
            student_values.append(str(grade or "").strip())
        if section is not None:
            student_updates.append("section=%s")
            student_values.append(str(section or "").strip())
        if class_level is not None:
            student_updates.append("class_level=%s")
            student_values.append(class_level)
        if has_pre_score:
            student_updates.append("pre_score=%s")
            student_updates.append("pre_assessment_completed=%s")
            student_values.append(pre_score)
            student_values.append(1)

        if student_updates:
            student_values.append(student_id)
            cur.execute(
                f"UPDATE students SET {', '.join(student_updates)} WHERE id=%s",
                tuple(student_values),
            )

        if is_active is not None:
            cur.execute("UPDATE users SET is_active=%s WHERE id=%s", (1 if bool(is_active) else 0, user_id))

        cur.execute(
            "SELECT s.id AS student_id, u.id AS user_id, u.email, u.is_active, s.full_name, s.grade, s.section, s.class_level, s.pre_score, s.pre_assessment_completed FROM students s JOIN users u ON u.id=s.user_id WHERE s.id=%s",
            (student_id,),
        )
        row = cur.fetchone()
        _record_audit_log(user["id"], student_id, "admin:update_student", {"payload": payload})

    return api_ok({
        "id": row["student_id"],
        "userId": row["user_id"],
        "email": row["email"],
        "fullName": row["full_name"],
        "grade": row["grade"],
        "section": row["section"],
        "classLevel": row["class_level"],
        "preScore": int(row["pre_score"] or 0),
        "preAssessmentCompleted": bool(row["pre_assessment_completed"]),
        "isActive": bool(row["is_active"]),
    })


@admin_bp.delete("/api/admin/students/<student_id>")
def admin_delete_student(student_id):
    user, err = require_role("admin")
    if err:
        return err

    with db_cursor(True) as (_, cur):
        cur.execute("SELECT user_id FROM students WHERE id=%s", (student_id,))
        row = cur.fetchone()
        if not row:
            return api_error("Student not found.", 404)
        user_id = row["user_id"]
        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        if cur.rowcount == 0:
            return api_error("Student not found.", 404)
        _record_audit_log(user["id"], student_id, "admin:delete_student", {})

    return api_ok({"deleted": True, "id": student_id})


@admin_bp.get("/api/admin/teachers")
def admin_list_teachers():
    user, err = require_role("admin")
    if err:
        return err

    with db_cursor(True) as (_, cur):
        cur.execute(
            "SELECT t.id AS teacher_id, u.id AS user_id, u.email, u.is_active, t.full_name, t.department FROM teachers t JOIN users u ON u.id=t.user_id ORDER BY t.id"
        )
        teachers = [
            {
                "id": row["teacher_id"],
                "userId": row["user_id"],
                "email": row["email"],
                "fullName": row["full_name"],
                "department": row["department"],
                "isActive": bool(row["is_active"]),
            }
            for row in cur.fetchall()
        ]

    return api_ok({"teachers": teachers})


@admin_bp.post("/api/admin/teachers")
def admin_create_teacher():
    user, err = require_role("admin")
    if err:
        return err

    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        return api_error("Request body must be valid JSON.", 400)

    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")
    full_name = str(payload.get("fullName") or "").strip()
    department = str(payload.get("department") or "").strip()
    is_active = bool(payload.get("isActive", True))

    if not email or not password or not full_name:
        return api_error("Email, password, and full name are required.", 400)

    with db_cursor(True) as (_, cur):
        if not _ensure_unique_email(cur, email):
            return api_error("Email is already in use.", 400)

        cur.execute(
            "INSERT INTO users (email, password_hash, role, is_active) VALUES (%s, %s, 'teacher', %s)",
            (email, generate_password_hash(password), 1 if is_active else 0),
        )
        user_id = cur.lastrowid
        cur.execute(
            "INSERT INTO teachers (user_id, full_name, department) VALUES (%s, %s, %s)",
            (user_id, full_name, department or None),
        )
        teacher_id = cur.lastrowid
        _record_audit_log(user["id"], None, "admin:create_teacher", {"email": email, "department": department})

    return api_ok({"id": teacher_id, "userId": user_id, "email": email, "fullName": full_name, "department": department, "isActive": is_active})


@admin_bp.put("/api/admin/teachers/<int:teacher_id>")
def admin_update_teacher(teacher_id):
    user, err = require_role("admin")
    if err:
        return err

    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, dict):
        return api_error("Request body must be valid JSON.", 400)

    email = payload.get("email")
    password = payload.get("password")
    full_name = payload.get("fullName")
    department = payload.get("department")
    is_active = payload.get("isActive")

    if email is not None:
        email = str(email or "").strip().lower()
        if not email:
            return api_error("Teacher email cannot be empty.", 400)

    with db_cursor(True) as (_, cur):
        cur.execute("SELECT user_id FROM teachers WHERE id=%s", (teacher_id,))
        row = cur.fetchone()
        if not row:
            return api_error("Teacher not found.", 404)
        user_id = row["user_id"]

        if email is not None:
            cur.execute("SELECT id FROM users WHERE email=%s AND id<>%s", (email, user_id))
            if cur.fetchone():
                return api_error("Email is already in use.", 400)
            cur.execute("UPDATE users SET email=%s WHERE id=%s", (email, user_id))

        if password:
            cur.execute("UPDATE users SET password_hash=%s WHERE id=%s", (generate_password_hash(password), user_id))

        teacher_updates = []
        teacher_values = []
        if full_name is not None:
            teacher_updates.append("full_name=%s")
            teacher_values.append(str(full_name or "").strip())
        if department is not None:
            teacher_updates.append("department=%s")
            teacher_values.append(str(department or "").strip() or None)

        if teacher_updates:
            teacher_values.append(teacher_id)
            cur.execute(
                f"UPDATE teachers SET {', '.join(teacher_updates)} WHERE id=%s",
                tuple(teacher_values),
            )

        if is_active is not None:
            cur.execute("UPDATE users SET is_active=%s WHERE id=%s", (1 if bool(is_active) else 0, user_id))

        cur.execute(
            "SELECT t.id AS teacher_id, u.id AS user_id, u.email, u.is_active, t.full_name, t.department FROM teachers t JOIN users u ON u.id=t.user_id WHERE t.id=%s",
            (teacher_id,),
        )
        row = cur.fetchone()
        _record_audit_log(user["id"], None, "admin:update_teacher", {"payload": payload})

    return api_ok({
        "id": row["teacher_id"],
        "userId": row["user_id"],
        "email": row["email"],
        "fullName": row["full_name"],
        "department": row["department"],
        "isActive": bool(row["is_active"]),
    })


@admin_bp.delete("/api/admin/teachers/<int:teacher_id>")
def admin_delete_teacher(teacher_id):
    user, err = require_role("admin")
    if err:
        return err

    with db_cursor(True) as (_, cur):
        cur.execute("SELECT user_id FROM teachers WHERE id=%s", (teacher_id,))
        row = cur.fetchone()
        if not row:
            return api_error("Teacher not found.", 404)
        user_id = row["user_id"]
        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
        if cur.rowcount == 0:
            return api_error("Teacher not found.", 404)
        _record_audit_log(user["id"], None, "admin:delete_teacher", {})

    return api_ok({"deleted": True, "id": teacher_id})


@admin_bp.get("/api/admin/passages")
def admin_list_passages():
    user, err = require_role("admin")
    if err:
        return err

    with db_cursor(True) as (_, cur):
        cur.execute("SELECT id,title,genre,text,label,words,est_minutes,confidence,is_draft FROM passages ORDER BY created_at DESC,id DESC")
        passages = [serialize_passage(row) for row in cur.fetchall()]
    return api_ok(passages)


@admin_bp.post("/api/admin/passages")
def admin_create_passage():
    user, err = require_role("admin")
    if err:
        return err

    payload = request.get_json(silent=True) or {}
    with db_cursor(True) as (_, cur):
        try:
            saved = save_passage(cur, payload, user["id"], None, allow_empty_assessment=False, is_draft=bool(payload.get("isDraft")))
        except ValueError as e:
            return api_error(str(e), 400)
    _record_audit_log(user["id"], None, "admin:create_passage", {"title": payload.get("title")})
    return api_ok(saved, 201)


@admin_bp.put("/api/admin/passages/<passage_id>")
def admin_update_passage(passage_id):
    user, err = require_role("admin")
    if err:
        return err

    payload = request.get_json(silent=True) or {}
    with db_cursor(True) as (_, cur):
        try:
            saved = save_passage(cur, payload, user["id"], passage_id, allow_empty_assessment=False, is_draft=bool(payload.get("isDraft")))
        except LookupError:
            return api_error("Passage not found.", 404)
        except ValueError as e:
            return api_error(str(e), 400)
    _record_audit_log(user["id"], None, "admin:update_passage", {"passageId": passage_id})
    return api_ok(saved)


@admin_bp.delete("/api/admin/passages/<passage_id>")
def admin_delete_passage(passage_id):
    user, err = require_role("admin")
    if err:
        return err

    with db_cursor(True) as (_, cur):
        cur.execute("DELETE FROM passages WHERE id=%s", (passage_id,))
        if cur.rowcount == 0:
            return api_error("Passage not found.", 404)
        _record_audit_log(user["id"], None, "admin:delete_passage", {"passageId": passage_id})

    return api_ok({"deleted": True, "id": passage_id})
