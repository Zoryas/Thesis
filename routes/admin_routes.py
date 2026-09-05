import csv
import io
import json

from flask import Blueprint, request
from werkzeug.security import generate_password_hash

from db import db_cursor
from routes.helpers import api_error, api_ok, require_auth, require_role
from routes.passage_routes import fetch_assessment, save_passage, serialize_passage

admin_bp = Blueprint("admin_bp", __name__)


def _ensure_pre_assessment_config(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pre_assessment_config (
          id TINYINT PRIMARY KEY,
          config_json LONGTEXT NOT NULL,
          updated_by INT NULL,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )


@admin_bp.get("/api/pre-assessment/config")
def get_pre_assessment_config():
    user, err = require_auth()
    if err:
        return err
    del user
    with db_cursor(True) as (_, cur):
        _ensure_pre_assessment_config(cur)
        cur.execute("SELECT config_json FROM pre_assessment_config WHERE id=1")
        row = cur.fetchone()
    return api_ok({"config": json.loads(row["config_json"]) if row else None})


@admin_bp.put("/api/pre-assessment/config")
def save_pre_assessment_config():
    user, err = require_role("admin")
    if err:
        return err
    payload = request.get_json(silent=True) or {}
    config = payload.get("config")
    passage_ids = payload.get("passageIds")
    if isinstance(passage_ids, list):
        if len(passage_ids) != 3 or len(set(passage_ids)) != 3:
            return api_error("Choose three different passages.", 400)
        config = []
        with db_cursor(True) as (_, cur):
            for passage_id in passage_ids:
                cur.execute("SELECT id,title,genre,text,label FROM passages WHERE id=%s", (str(passage_id),))
                passage = cur.fetchone()
                if not passage:
                    return api_error("One selected passage was not found.", 404)
                cur.execute("SELECT 1 FROM weekly_assignments WHERE passage_id=%s LIMIT 1", (str(passage_id),))
                if cur.fetchone():
                    return api_error(f"Passage '{passage['title']}' is already assigned to a weekly assessment.", 400)
                assessment = fetch_assessment(cur, passage["id"])
                if not assessment["questions"]:
                    return api_error(f"Passage '{passage['title']}' needs assessment questions first.", 400)
                config.append({
                    "id": passage["id"],
                    "level": passage["label"],
                    "label": f"{passage['label']} Pre-Assessment",
                    "title": passage["title"],
                    "genre": passage["genre"],
                    "text": passage["text"],
                    "questions": assessment["questions"],
                })
    if not isinstance(config, list) or not config:
        return api_error("config must be a non-empty list of assessment steps.", 400)
    for step in config:
        if not isinstance(step, dict) or not step.get("title") or not step.get("text") or not isinstance(step.get("questions"), list) or not step["questions"]:
            return api_error("Each step needs a title, passage text, and at least one question.", 400)
    with db_cursor(True) as (_, cur):
        for step in config:
            passage_id = step.get("id")
            if passage_id:
                cur.execute("SELECT 1 FROM weekly_assignments WHERE passage_id=%s LIMIT 1", (str(passage_id),))
                if cur.fetchone():
                    return api_error("A selected pre-assessment passage is already assigned to a weekly assessment.", 400)
        _ensure_pre_assessment_config(cur)
        cur.execute(
            """
            INSERT INTO pre_assessment_config (id,config_json,updated_by)
            VALUES (1,%s,%s)
            ON DUPLICATE KEY UPDATE config_json=VALUES(config_json),updated_by=VALUES(updated_by)
            """,
            (json.dumps(config, ensure_ascii=False), user["id"]),
        )
    return api_ok({"config": config, "message": "Pre-assessment saved."})


def _read_bulk_csv():
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return None, "Choose a CSV file to upload."
    try:
        text = uploaded.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return None, "The template must be saved as UTF-8 CSV."
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return None, "The CSV file must include a header row."
    return list(reader), None


def _bulk_value(row, *names):
    for name in names:
        if name in row:
            return str(row.get(name) or "").strip()
    return ""


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


@admin_bp.post("/api/admin/students/bulk")
def admin_bulk_create_students():
    user, err = require_role("admin")
    if err:
        return err
    rows, error = _read_bulk_csv()
    if error:
        return api_error(error, 400)

    created = []
    errors = []
    with db_cursor(True) as (_, cur):
        for index, row in enumerate(rows, start=2):
            email = _bulk_value(row, "email", "Email").lower()
            password = _bulk_value(row, "password", "Password")
            full_name = _bulk_value(row, "fullName", "fullname", "full_name", "Full Name")
            grade = _bulk_value(row, "grade", "Grade") or "7"
            section = _bulk_value(row, "section", "Section")
            class_level = _bulk_value(row, "classLevel", "class_level", "Reading Level").upper() or "EASY"
            pre_score_raw = _bulk_value(row, "preScore", "pre_score", "Pre-Score")
            if not email or not password or not full_name:
                errors.append({"row": index, "error": "email, password, and full name are required."})
                continue
            if class_level not in {"EASY", "MODERATE", "HARD"}:
                errors.append({"row": index, "error": "classLevel must be EASY, MODERATE, or HARD."})
                continue
            try:
                pre_score = int(pre_score_raw) if pre_score_raw else 0
            except ValueError:
                errors.append({"row": index, "error": "preScore must be a number."})
                continue
            if not 0 <= pre_score <= 100:
                errors.append({"row": index, "error": "preScore must be between 0 and 100."})
                continue
            if not _ensure_unique_email(cur, email):
                errors.append({"row": index, "error": "Email is already in use."})
                continue
            cur.execute(
                "INSERT INTO users (email,password_hash,role,is_active) VALUES (%s,%s,'student',1)",
                (email, generate_password_hash(password)),
            )
            user_id = cur.lastrowid
            student_id = _next_student_id(cur)
            cur.execute(
                "INSERT INTO students (id,user_id,full_name,grade,section,class_level,pre_score,pre_assessment_completed) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (student_id, user_id, full_name, grade, section, class_level, pre_score, 1 if pre_score_raw else 0),
            )
            _record_audit_log(user["id"], student_id, "admin:bulk_create_student", {"email": email}, cur=cur)
            created.append({"row": index, "id": student_id, "email": email})
    return api_ok({"created": created, "errors": errors, "createdCount": len(created), "errorCount": len(errors)})


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


@admin_bp.post("/api/admin/students/bulk-delete")
def admin_bulk_delete_students():
    user, err = require_role("admin")
    if err:
        return err

    payload = request.get_json(silent=True) or {}
    student_ids = payload.get("studentIds")
    if not isinstance(student_ids, list) or not student_ids:
        return api_error("Select at least one student to delete.", 400)
    student_ids = list(dict.fromkeys(str(student_id).strip() for student_id in student_ids if str(student_id).strip()))
    if not student_ids:
        return api_error("Select at least one student to delete.", 400)

    placeholders = ",".join(["%s"] * len(student_ids))
    with db_cursor(True) as (_, cur):
        cur.execute(f"SELECT id,user_id FROM students WHERE id IN ({placeholders})", tuple(student_ids))
        rows = cur.fetchall()
        if not rows:
            return api_error("No matching students were found.", 404)
        user_ids = [row["user_id"] for row in rows]
        cur.execute(f"DELETE FROM users WHERE id IN ({','.join(['%s'] * len(user_ids))})", tuple(user_ids))
        for row in rows:
            _record_audit_log(user["id"], row["id"], "admin:bulk_delete_student", {}, cur=cur)

    return api_ok({"deleted": len(rows), "requested": len(student_ids), "ids": [row["id"] for row in rows]})


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


@admin_bp.post("/api/admin/teachers/bulk")
def admin_bulk_create_teachers():
    user, err = require_role("admin")
    if err:
        return err
    rows, error = _read_bulk_csv()
    if error:
        return api_error(error, 400)

    created = []
    errors = []
    with db_cursor(True) as (_, cur):
        for index, row in enumerate(rows, start=2):
            email = _bulk_value(row, "email", "Email").lower()
            password = _bulk_value(row, "password", "Password")
            full_name = _bulk_value(row, "fullName", "fullname", "full_name", "Full Name")
            department = _bulk_value(row, "department", "Department")
            if not email or not password or not full_name:
                errors.append({"row": index, "error": "email, password, and full name are required."})
                continue
            if not _ensure_unique_email(cur, email):
                errors.append({"row": index, "error": "Email is already in use."})
                continue
            cur.execute(
                "INSERT INTO users (email,password_hash,role,is_active) VALUES (%s,%s,'teacher',1)",
                (email, generate_password_hash(password)),
            )
            user_id = cur.lastrowid
            cur.execute(
                "INSERT INTO teachers (user_id,full_name,department) VALUES (%s,%s,%s)",
                (user_id, full_name, department or None),
            )
            teacher_id = cur.lastrowid
            _record_audit_log(user["id"], None, "admin:bulk_create_teacher", {"email": email}, cur=cur)
            created.append({"row": index, "id": teacher_id, "email": email})
    return api_ok({"created": created, "errors": errors, "createdCount": len(created), "errorCount": len(errors)})


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
        for passage in passages:
            cur.execute("SELECT week_no FROM weekly_assignments WHERE passage_id=%s ORDER BY week_no", (passage["id"],))
            passage["usedWeeks"] = [int(row["week_no"]) for row in cur.fetchall()]
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
