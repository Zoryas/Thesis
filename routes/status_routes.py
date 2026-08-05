from flask import Blueprint, jsonify, request, session

from db import db_cursor
from routes.helpers import api_error, api_ok, build_prediction_response, current_user, get_request_token, serialize_user

status_bp = Blueprint("status_bp", __name__)


@status_bp.get("/")
def index():
    return jsonify(
        {
            "name": "ReadWise API",
            "status": "running",
            "endpoints": [
                "/health",
                "/predict",
                "/api/health",
                "/api/auth/login",
                "/api/passages",
            ],
        }
    )


@status_bp.get("/health")
def health():
    return jsonify({"status": "running", "model": "SVM ReadWise Prototype"})


@status_bp.get("/api/health")
def api_health():
    with db_cursor() as (_, cur):
        cur.execute("SELECT 1")
        cur.fetchone()
    return api_ok({"api": "running", "db": "connected"})


@status_bp.get("/api/debug/session")
def api_debug_session():
    user = current_user()
    raw_cookie = request.headers.get("Cookie") or ""
    raw_token = get_request_token() or ""
    return api_ok(
        {
            "hasCookieHeader": bool(raw_cookie),
            "cookieHeaderPreview": raw_cookie[:200],
            "hasTokenHeader": bool(raw_token),
            "tokenPreview": raw_token[:24],
            "sessionKeys": sorted(list(session.keys())),
            "sessionUserId": session.get("user_id"),
            "sessionRole": session.get("role"),
            "sessionStudentId": session.get("student_id"),
            "isAuthenticated": bool(user),
            "currentUser": serialize_user(user) if user else None,
            "origin": request.headers.get("Origin"),
            "referer": request.headers.get("Referer"),
        }
    )


@status_bp.post("/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    try:
        return jsonify(build_prediction_response(payload.get("text", "")))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
