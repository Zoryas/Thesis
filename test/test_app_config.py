import unittest

from app_config import get_allowed_origins


class AppConfigTests(unittest.TestCase):
    def test_production_uses_railway_public_domain_when_explicit_origins_missing(self):
        env = {"READWISE_ENV": "production", "RAILWAY_PUBLIC_DOMAIN": "myapp.up.railway.app"}
        origins = get_allowed_origins(True, env=env)
        self.assertIn("https://myapp.up.railway.app", origins)

    def test_production_falls_back_to_localhost_when_no_origin_env_available(self):
        env = {"READWISE_ENV": "production"}
        origins = get_allowed_origins(True, env=env)
        self.assertIn("http://localhost", origins)

    def test_explicit_origins_are_preserved(self):
        env = {"READWISE_ALLOWED_ORIGINS": "https://a.example.com, https://b.example.com"}
        origins = get_allowed_origins(False, env=env)
        self.assertEqual(origins, ["https://a.example.com", "https://b.example.com"])

    def test_localhost_aliases_expand_to_127_0_0_1_and_localhost(self):
        env = {"READWISE_ALLOWED_ORIGINS": "http://localhost:5000"}
        origins = get_allowed_origins(False, env=env)
        self.assertIn("http://localhost:5000", origins)
        self.assertIn("http://127.0.0.1:5000", origins)


if __name__ == "__main__":
    unittest.main()
