import unittest

from flask import Flask, request

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


if __name__ == "__main__":
    unittest.main()
