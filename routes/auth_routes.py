import secrets
from flask import Blueprint, request, session
from werkzeug.security import check_password_hash

from db import db_cursor
from routes.helpers import api_error, api_ok, current_user, get_request_token, require_auth, serialize_user

auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.post("/api/auth/login")
def auth_login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")
    role = str(payload.get("role") or "").strip().lower()
    if not email or not password:
        return api_error("Email and password are required.", 400)

    with db_cursor(True) as (_, cur):
        cur.execute(
            """
            SELECT u.id,u.email,u.password_hash,u.role,u.is_active,
                   s.id AS student_id,s.full_name,s.grade,s.section,s.class_level,s.pre_score,s.pre_assessment_completed,
                   s.avatar_type,s.avatar_value
            FROM users u LEFT JOIN students s ON s.user_id=u.id
            WHERE u.email=%s
            """,
            (email,),
        )
        row = cur.fetchone()
        if not row or not row.get("is_active"):
            return api_error("Invalid credentials.", 401)
        if role and role != row["role"]:
            return api_error("Invalid credentials.", 401)
        if not check_password_hash(row["password_hash"], password):
            return api_error("Invalid credentials.", 401)
        token = secrets.token_hex(32)
        cur.execute("INSERT INTO auth_tokens (user_id, token) VALUES (%s, %s)", (row["id"], token))

    session.clear()
    session["user_id"] = row["id"]
    session["role"] = row["role"]
    if row.get("student_id"):
        session["student_id"] = row["student_id"]
    return api_ok({"user": serialize_user(row), "token": token})


@auth_bp.post("/api/auth/logout")
def auth_logout():
    token = get_request_token()
    if token:
        with db_cursor(True) as (_, cur):
            cur.execute("DELETE FROM auth_tokens WHERE token=%s", (token,))
    session.clear()
    return api_ok({"message": "Logged out."})


@auth_bp.get("/api/auth/me")
def auth_me():
    user, err = require_auth()
    if err:
        return err
    return api_ok({"user": serialize_user(user)})
