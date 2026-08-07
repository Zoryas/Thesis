import unittest

from flask import Flask, jsonify

from routes.status_routes import build_health_payload
from app import configure_request_logging


class Phase3OperationsTests(unittest.TestCase):
    def test_build_health_payload_contains_request_and_db_state(self):
        payload = build_health_payload(request_id="req-123", db_status="connected")
        self.assertEqual(payload["status"], "running")
        self.assertEqual(payload["db"], "connected")
        self.assertEqual(payload["request_id"], "req-123")

    def test_request_logging_injects_request_id_header(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        configure_request_logging(app)

        @app.get("/ping")
        def ping():
            return jsonify({"ok": True})

        with app.test_client() as client:
            response = client.get("/ping", headers={"X-Request-ID": "abc-456"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Request-ID"], "abc-456")


if __name__ == "__main__":
    unittest.main()
