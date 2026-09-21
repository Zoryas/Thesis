import unittest
from unittest.mock import patch

from flask import Flask, request

from routes import admin_routes
from routes.helpers import enforce_csrf_for_state_change, normalize_text_value


class CsrfProtectionTests(unittest.TestCase):
    def create_app(self):
        app = Flask(__name__)
        app.config["TESTING"] = True

        @app.before_request
        def enforce_csrf():
            if request.method == "POST":
                error = enforce_csrf_for_state_change()
                if error is not None:
                    return error

        @app.post("/mutating")
        def mutating():
            return "ok"

        return app

    def test_same_origin_post_is_allowed(self):
        app = self.create_app()
        with app.test_client() as client:
            response = client.post(
                "/mutating",
                headers={"Origin": "http://localhost"},
                base_url="http://localhost:5000",
            )
        self.assertEqual(response.status_code, 200)

    def test_cross_site_post_is_rejected(self):
        app = self.create_app()
        with app.test_client() as client:
            response = client.post(
                "/mutating",
                headers={"Origin": "https://evil.example"},
                base_url="http://localhost:5000",
            )
        self.assertEqual(response.status_code, 403)

    def test_normalize_text_value_escapes_html_and_collapses_spacing(self):
        value = "  <script>alert('x')</script>   hello   world  "
        normalized = normalize_text_value(value, max_length=80)
        self.assertEqual(normalized, "&lt;script&gt;alert('x')&lt;/script&gt; hello world")

    def test_admin_update_student_rejects_null_prescore(self):
        class FakeCursor:
            def execute(self, query, params=None):
                if "UPDATE students SET" in query and params and params[0] is None:
                    raise TypeError("pre_score cannot be null")
            def fetchone(self):
                return {"user_id": 55}

        class FakeDB:
            def __enter__(self):
                return (None, FakeCursor())
            def __exit__(self, exc_type, exc_val, exc_tb):
                return False

        app = Flask(__name__)
        app.register_blueprint(admin_routes.admin_bp)
        app.config["TESTING"] = True

        with app.test_client() as client:
            with patch.object(admin_routes, "require_role", return_value=({"id": 1, "role": "admin"}, None)), \
                 patch.object(admin_routes, "db_cursor", return_value=FakeDB()):
                response = client.put(
                    "/api/admin/students/s20",
                    json={
                        "email": "student@example.com",
                        "fullName": "Example Student",
                        "grade": "7",
                        "section": "A",
                        "classLevel": "EASY",
                        "preScore": None,
                    },
                )

        self.assertEqual(response.status_code, 400)
        self.assertIn("preScore", response.get_json()["error"])

    def test_admin_update_student_redacts_sensitive_fields_in_audit_log(self):
        class FakeCursor:
            def __init__(self):
                self.last_query = None

            def execute(self, query, params=None):
                self.last_query = query
                return None

            def fetchone(self):
                query = self.last_query or ""
                if "SELECT user_id FROM students WHERE id=%s" in query:
                    return {"user_id": 55}
                if "SELECT id FROM users WHERE email=%s AND id<>%s" in query:
                    return None
                if "SELECT s.id AS student_id" in query:
                    return {
                        "student_id": "s20",
                        "user_id": 55,
                        "email": "student@example.com",
                        "is_active": 1,
                        "full_name": "Example Student",
                        "grade": "7",
                        "section": "A",
                        "class_level": "EASY",
                        "pre_score": 87,
                        "pre_assessment_completed": 1,
                    }
                return None

        class FakeDB:
            def __init__(self):
                self.exited = False

            def __enter__(self):
                return (None, FakeCursor())

            def __exit__(self, exc_type, exc_val, exc_tb):
                self.exited = True
                return False

        app = Flask(__name__)
        app.register_blueprint(admin_routes.admin_bp)
        app.config["TESTING"] = True

        fake_db = FakeDB()
        audit_after_commit = {"value": False}

        def fake_audit(*args, **kwargs):
            audit_after_commit["value"] = fake_db.exited

        with app.test_client() as client:
            with patch.object(admin_routes, "require_role", return_value=({"id": 1, "role": "admin"}, None)), \
                 patch.object(admin_routes, "db_cursor", return_value=fake_db), \
                 patch.object(admin_routes, "_record_audit_log", side_effect=fake_audit) as mock_audit:
                response = client.put(
                    "/api/admin/students/s20",
                    json={
                        "email": "student@example.com",
                        "fullName": "Example Student",
                        "grade": "7",
                        "section": "A",
                        "classLevel": "EASY",
                        "preScore": 87,
                        "password": "secret123",
                    },
                )

        self.assertEqual(response.status_code, 200)
        mock_audit.assert_called_once()
        self.assertTrue(audit_after_commit["value"])
        payload = mock_audit.call_args[0][3]
        self.assertEqual(payload["payload"]["password"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
