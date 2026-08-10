import logging
import os
from uuid import uuid4

from flask import Blueprint, jsonify, redirect, request, session

from db import db_cursor
from routes.helpers import api_error, api_ok, build_prediction_response, current_user, get_request_token, serialize_user

status_bp = Blueprint("status_bp", __name__)

logger = logging.getLogger("readwise.operations")


def build_health_payload(request_id=None, db_status="connected"):
    return {
        "status": "running",
        "model": "SVM ReadWise Prototype",
        "db": db_status,
        "request_id": request_id or "n/a",
    }


@status_bp.get("/")
def index():
    return redirect("/login", code=302)


@status_bp.get("/health")
def health():
    request_id = request.headers.get("X-Request-ID") or request.headers.get("X-Trace-Id")
    return jsonify(build_health_payload(request_id=request_id))


@status_bp.get("/api/health")
def api_health():
    request_id = request.headers.get("X-Request-ID") or request.headers.get("X-Trace-Id")
    try:
        with db_cursor() as (_, cur):
            cur.execute("SELECT 1")
            cur.fetchone()
        payload = build_health_payload(request_id=request_id, db_status="connected")
        return api_ok({"api": "running", "db": "connected", "request_id": request_id or "n/a"})
    except Exception as exc:  # pragma: no cover - defensive operational path
        logger.exception("Database health check failed")
        return api_error(f"Database health check failed: {exc}", 503)


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


def configure_request_logging(app):
    app.logger.setLevel(getattr(logging, os.environ.get("READWISE_LOG_LEVEL", "INFO"), logging.INFO))

    @app.before_request
    def attach_request_context():
        request_id = request.headers.get("X-Request-ID") or request.headers.get("X-Trace-Id") or str(uuid4())
        request.environ["readwise_request_id"] = request_id
        request.environ["readwise_start_time"] = os.times().elapsed
        app.logger.info("request_started", extra={"request_id": request_id, "method": request.method, "path": request.path})

    @app.after_request
    def finalize_request(response):
        request_id = request.environ.get("readwise_request_id")
        if request_id:
            response.headers["X-Request-ID"] = request_id
        app.logger.info("request_finished", extra={"request_id": request_id, "status_code": response.status_code})
        return response
