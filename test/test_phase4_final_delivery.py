import unittest

from app import app


class Phase4FinalDeliveryTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def login(self, email, password, role):
        response = self.client.post("/api/auth/login", json={"email": email, "password": password, "role": role})
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["ok"])
        return body["data"]["token"]

    def test_student_login_and_weekly_passages(self):
        token = self.login("juan.delacruz@pnhs.edu", "password123", "student")
        response = self.client.get(
            "/api/student/weekly-passages?week=1",
            headers={"X-Auth-Token": token},
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["ok"])
        self.assertIn("passages", body["data"])
        self.assertIsInstance(body["data"]["passages"], list)

    def test_teacher_dashboard_requires_auth(self):
        response = self.client.get("/api/teacher/dashboard")
        self.assertEqual(response.status_code, 401)

        token = self.login("ms.villanueva@pnhs.edu", "teacher123", "teacher")
        response = self.client.get("/api/teacher/dashboard", headers={"X-Auth-Token": token})
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["ok"])
        self.assertIn("recentSubmissions", body["data"])

    def test_teacher_score_invalid_score_fails(self):
        token = self.login("ms.villanueva@pnhs.edu", "teacher123", "teacher")
        response = self.client.post(
            "/api/teacher/score",
            headers={"X-Auth-Token": token},
            json={"studentId": "s1", "passageId": "p1", "score": 2},
        )
        self.assertEqual(response.status_code, 400)
        body = response.get_json()
        self.assertFalse(body["ok"])
        self.assertIn("score must be", body["error"])

    def test_student_attempts_invalid_passage_fails(self):
        token = self.login("juan.delacruz@pnhs.edu", "password123", "student")
        response = self.client.post(
            "/api/student/attempts",
            headers={"X-Auth-Token": token},
            json={
                "week": 1,
                "passageId": "unknown",
                "score": 100,
                "correct": 3,
                "total": 3,
                "difficulty": 3,
                "shortAnswer": "Test response",
                "readingTime": "5:00",
                "responses": [],
            },
        )
        self.assertEqual(response.status_code, 400)
        body = response.get_json()
        self.assertFalse(body["ok"])
        self.assertIn("Passage is not assigned", body["error"])

    def test_student_attempts_get_returns_latest_result(self):
        token = self.login("juan.delacruz@pnhs.edu", "password123", "student")
        passages_resp = self.client.get(
            "/api/student/weekly-passages?week=1",
            headers={"X-Auth-Token": token},
        )
        self.assertEqual(passages_resp.status_code, 200)
        passages_body = passages_resp.get_json()
        self.assertTrue(passages_body["ok"])
        self.assertGreater(len(passages_body["data"]["passages"]), 0)
        passage_id = passages_body["data"]["passages"][0]["id"]

        response = self.client.post(
            "/api/student/attempts",
            headers={"X-Auth-Token": token},
            json={
                "week": 1,
                "passageId": passage_id,
                "score": 82,
                "correct": 4,
                "total": 5,
                "difficulty": 3,
                "shortAnswer": "",
                "readingTime": "05:00",
                "responses": [],
            },
        )
        self.assertEqual(response.status_code, 201)

        response = self.client.get(
            "/api/student/attempts?passageId=" + passage_id,
            headers={"X-Auth-Token": token},
        )
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["ok"])
        self.assertIsNotNone(body["data"])
        self.assertEqual(body["data"]["score"], 82)
        self.assertEqual(body["data"]["correct"], 4)
        self.assertEqual(body["data"]["total"], 5)

    def test_student_attempt_falls_back_to_reading_session_time(self):
        token = self.login("juan.delacruz@pnhs.edu", "password123", "student")
        passages_resp = self.client.get(
            "/api/student/weekly-passages?week=1",
            headers={"X-Auth-Token": token},
        )
        self.assertEqual(passages_resp.status_code, 200)
        passage_id = passages_resp.get_json()["data"]["passages"][0]["id"]

        reading_time_resp = self.client.post(
            "/api/student/reading-time",
            headers={"X-Auth-Token": token},
            json={
                "week": 1,
                "passageId": passage_id,
                "eventId": "fallback-read-time",
                "readingSeconds": 320,
                "formattedTime": "05:20",
            },
        )
        self.assertEqual(reading_time_resp.status_code, 200)

        response = self.client.post(
            "/api/student/attempts",
            headers={"X-Auth-Token": token},
            json={
                "week": 1,
                "passageId": passage_id,
                "score": 67,
                "correct": 2,
                "total": 3,
                "difficulty": 3,
                "shortAnswer": "",
                "responses": [],
            },
        )
        self.assertEqual(response.status_code, 201)

        get_response = self.client.get(
            "/api/student/attempts?passageId=" + passage_id,
            headers={"X-Auth-Token": token},
        )
        self.assertEqual(get_response.status_code, 200)
        body = get_response.get_json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["data"]["readingTime"], "05:20")

    def test_program_week_accessible_by_student(self):
        token = self.login("juan.delacruz@pnhs.edu", "password123", "student")
        response = self.client.get("/api/program/week", headers={"X-Auth-Token": token})
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body["ok"])
        self.assertIn("activeWeek", body["data"])


if __name__ == "__main__":
    unittest.main()
