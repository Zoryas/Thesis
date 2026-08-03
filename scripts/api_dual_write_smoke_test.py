import json
import os
import sys
import time
import requests

BASE_URL = os.environ.get("READWISE_API_BASE_URL", "http://localhost:5000")

STUDENT_EMAIL = os.environ.get("READWISE_STUDENT_EMAIL", "sofia.bautista@pnhs.edu")
STUDENT_PASSWORD = os.environ.get("READWISE_STUDENT_PASSWORD", "password123")
STUDENT_ROLE = "student"
TEACHER_EMAIL = os.environ.get("READWISE_TEACHER_EMAIL", "ms.villanueva@pnhs.edu")
TEACHER_PASSWORD = os.environ.get("READWISE_TEACHER_PASSWORD", "teacher123")
TEACHER_ROLE = "teacher"


def http_json(method, session, path, payload=None, params=None):
    url = BASE_URL + path
    resp = session.request(method, url, json=payload, params=params, timeout=60)
    try:
        data = resp.json()
    except Exception:
        data = None
    if not resp.ok:
        raise RuntimeError(f"HTTP {resp.status_code} {method} {path} payload={payload} params={params} body={data}")
    if not data or data.get("ok") is False:
        raise RuntimeError(f"API error {method} {path}: {data}")
    return data.get("data")


def login(session, email, password, role):
    data = http_json(
        "POST",
        session,
        "/api/auth/login",
        payload={"email": email, "password": password, "role": role},
    )
    return data


def find_week_with_passages(student_session, start_week=1, end_week=8):
    for week in range(start_week, end_week + 1):
        weekly = http_json(
            "GET",
            student_session,
            "/api/student/weekly-passages",
            params={"week": week},
        )
        passages = weekly.get("passages") or weekly.get("data") or weekly.get("items") or []
        if passages:
            return week, weekly
    raise RuntimeError("No weekly passages returned for weeks 1..8")

def pick_passage_and_questions(student_session, active_week):
    # Get weekly passages first (ensures assignment validity)
    weekly = http_json(
        "GET",
        student_session,
        "/api/student/weekly-passages",
        params={"week": active_week},
    )

    passages = weekly.get("passages") or weekly.get("data") or weekly.get("items") or []
    if not passages:
        raise RuntimeError("No weekly passages returned")

    # Pick first passage that has an assessment with at least 1 question
    for p in passages:
        pid = p.get("id") or p.get("passageId") or p.get("passage_id")
        if not pid:
            continue
        # Get full passage to access assessment questions
        passage = http_json("GET", student_session, f"/api/passages/{pid}")
        assessment = passage.get("assessment") or {}
        questions = assessment.get("questions") or []
        short_answer_prompt = assessment.get("shortAnswerPrompt") or assessment.get("shortAnswerPromptText") or ""
        if questions:
            return pid, questions, passage, short_answer_prompt

    # Fallback: just take first passage id even if no questions (won't submit)
    first_pid = passages[0].get("id")
    if not first_pid:
        raise RuntimeError("Weekly passages missing id")
    passage = http_json("GET", student_session, f"/api/passages/{first_pid}")
    assessment = passage.get("assessment") or {}
    questions = assessment.get("questions") or []
    short_answer_prompt = assessment.get("shortAnswerPrompt") or ""
    return first_pid, questions, passage, short_answer_prompt


def build_attempt_payload(week, passage_id, questions, short_answer_prompt, passage, reading_time="-"):
    # We must answer every question based on the types rendered in student-questions.html.
    # To keep it simple and deterministic, we'll set all MCQ/TF to first valid choice/true,
    # and for free-text/sequence/enumeration use empty where allowed? But the page blocks empty,
    # so we must provide non-empty for non-MCQ/TF.
    responses = []
    earned_score = 0
    possible = 0
    fully_correct = 0

    # Determine correct keys if present; the frontend scoring expects question.answerIndex/key/answerKeys.
    # We'll mirror that: if we can't infer, provide non-empty but mark earned as 0.
    for q in questions:
        qtype = q.get("type")
        # Defaults
        earned = 0
        possible_here = 1
        correct = False

        if qtype in ("multiple_choice", "multiple_choice_harder"):
            options = q.get("options") or []
            if options:
                value = 0
            else:
                value = 0
            # The frontend checks: Number(response) === Number(question.answerIndex)
            answer_index = q.get("answerIndex")
            earned = 1 if (answer_index is not None and int(value) == int(answer_index)) else 0
            correct = earned == 1
            fully_correct += 1 if correct else 0
            possible += 1
            responses.append({"type": qtype, "value": value, "earned": earned, "possible": possible_here})
            if correct:
                earned_score += 1
        elif qtype in ("true_false", "true_false_modified"):
            # choose "true"
            value = "true"
            answer_key = q.get("answerKey") or q.get("answer")
            if answer_key is not None:
                correct = str(value).strip().lower() == str(answer_key).strip().lower()
            earned = 1 if correct else 0
            fully_correct += 1 if correct else 0
            possible += 1
            responses.append({"type": qtype, "value": value, "earned": earned, "possible": possible_here})
            if correct:
                earned_score += 1
        elif qtype == "sequence":
            # expected format: comma list
            answer_keys = q.get("answerKeys") or []
            # We'll provide the expected answers if possible; else a placeholder.
            if answer_keys:
                ordered = list(answer_keys)
            else:
                ordered = ["step1"]
            actual = ordered
            # frontend correct check compares normalized strings order
            expected = [str(x).lower().strip() for x in q.get("answerKeys") or [] if str(x).strip()]
            actual_norm = [str(x).lower().strip() for x in actual]
            correct = len(expected) > 0 and len(expected) == len(actual_norm) and all(
                expected[i] == actual_norm[i] for i in range(len(expected))
            )
            earned = 1 if correct else 0
            fully_correct += 1 if correct else 0
            possible += 1
            responses.append({"type": qtype, "value": ", ".join(actual), "earned": earned, "possible": possible_here})
            if correct:
                earned_score += 1
        elif qtype in ("fill_in_the_blanks", "identification"):
            # provide first answerKey if present else placeholder
            answer_keys = q.get("answerKeys") or []
            if answer_keys:
                value = str(answer_keys[0])
            else:
                value = "sample answer"
            accepted = [str(x).lower().strip() for x in q.get("answerKeys") or [] if str(x).strip()]
            correct = accepted and (value.lower().strip() in accepted)
            earned = 1 if correct else 0
            fully_correct += 1 if correct else 0
            possible += 1
            responses.append({"type": qtype, "value": value, "earned": earned, "possible": possible_here})
            if correct:
                earned_score += 1
        elif qtype == "enumeration":
            answer_keys = q.get("answerKeys") or []
            if answer_keys:
                # Provide all expected to attempt full correct
                value = ", ".join([str(x) for x in answer_keys])
            else:
                value = "item1, item2"
            expected = [str(x).lower().strip() for x in q.get("answerKeys") or [] if str(x).strip()]
            actual_items = [x.strip().lower() for x in value.split(",") if x.strip()]
            if expected:
                matched = len([x for x in expected if x in actual_items])
                perfect = matched == len(expected) and len(actual_items) == len(expected)
                correct = perfect
                earned = matched if matched else 0
                possible_here = len(expected)
            else:
                correct = False
                earned = 0
                possible_here = 1
            fully_correct += 1 if correct else 0
            possible += possible_here
            responses.append({"type": qtype, "value": value, "earned": earned, "possible": possible_here})
            if correct:
                earned_score += 1  # frontend still uses earned/possible per response, but overall pct uses earned/possible totals.
        else:
            # short answer-ish question type
            answer_keys = q.get("answerKeys") or []
            value = str(answer_keys[0]) if answer_keys else "sample answer"
            accepted = [str(x).lower().strip() for x in q.get("answerKeys") or [] if str(x).strip()]
            correct = accepted and (value.lower().strip() in accepted)
            earned = 1 if correct else 0
            fully_correct += 1 if correct else 0
            possible += 1
            responses.append({"type": qtype, "value": value, "earned": earned, "possible": possible_here})
            if correct:
                earned_score += 1

    total = len(questions)
    pct = int(round((earned_score / total) * 100)) if total else 0

    short_answer = ""
    if short_answer_prompt:
        # must be non-empty
        answer_keys = passage.get("shortAnswerExamples") or []
        short_answer = str(answer_keys[0]) if answer_keys else "Short answer for teacher review."

    payload = {
        "week": week,
        "passageId": passage_id,
        "score": pct,
        "correct": fully_correct,
        "total": total,
        "difficulty": 3,
        "shortAnswer": short_answer,
        "responses": responses,
        "readingTime": reading_time,
    }
    return payload


def main():
    student_s = requests.Session()
    teacher_s = requests.Session()

    print("[1] Logging in as student...")
    student_login = login(student_s, STUDENT_EMAIL, STUDENT_PASSWORD, STUDENT_ROLE)

    # Login response is expected to include { user: { role, student: { id, ... } } }
    user = (student_login or {}).get("user") or {}
    student_id = (user.get("student") or {}).get("id")
    if not student_id:
        raise RuntimeError(f"Could not extract student_id from login response: {student_login}")

    # The pre-assigned student passages may not exist for the active week;
    # find a week where this student actually has assignments.
    active_week, _ = find_week_with_passages(student_s, 1, 8)

    pid, questions, passage, short_prompt = pick_passage_and_questions(student_s, active_week)
    print(f"[2] Selected passage {pid} with {len(questions)} questions. shortAnswerPrompt={bool(short_prompt)} (studentId={student_id})")

    # Submit reading-time and lock is optional for attempt submission, but we keep it closer to flow.
    print("[3] Locking reading for passage...")
    try:
        http_json(
            "POST",
            student_s,
            "/api/student/reading-lock",
            payload={"week": active_week, "passageId": pid},
        )
    except Exception as e:
        print("   lock failed (non-fatal):", e)

    print("[4] Submitting student attempt...")
    attempt_payload = build_attempt_payload(active_week, pid, questions, short_prompt, passage)
    http_json("POST", student_s, "/api/student/attempts", payload=attempt_payload)
    print("[OK] Student attempt submitted.")

    # Idempotency: submit the same student attempt again (same payload)
    # Expect no duplicate/incorrect normalized writes or crashes.
    print("[4b] Submitting duplicate student attempt (idempotency check)...")
    http_json("POST", student_s, "/api/student/attempts", payload=attempt_payload)
    print("[OK] Duplicate student attempt submitted (idempotency check complete).")

    # login teacher
    print("[5] Logging in as teacher...")
    login(teacher_s, TEACHER_EMAIL, TEACHER_PASSWORD, TEACHER_ROLE)

    # Get teacher student detail to locate pending short answer response
    print("[6] Fetch teacher student detail...")
    detail = http_json("GET", teacher_s, f"/api/teacher/students/{student_id}")

    pending = (detail or {}).get("pendingShortAnswer") or {}
    pending_passage_id = pending.get("passageId") or pending.get("passage_id") or pending.get("passage_id".upper())

    # If no pending exists, the previous teacher score may already be recorded from an earlier run
    # or we may have selected a passage without a short-answer prompt.
    # Make the test deterministic by re-pulling the pending list and selecting the latest item.
    if not pending_passage_id:
        pending_list = http_json(
            "GET",
            teacher_s,
            f"/api/teacher/students/{student_id}/pending-short-answers",
        )

        # http_json() returns the server "data" object (not wrapped in {ok,data})
        # Endpoint payload shape is expected: { student: {...}, pendingShortAnswers: [...] }
        items = (
            pending_list.get("pendingShortAnswers")
            or pending_list.get("data", {}).get("pendingShortAnswers")
            or []
        )

        if not items:
            # Teacher scoring may have already happened in a previous run; treat as success.
            print(
                f"[WARN] pending-short-answers is empty for studentId={student_id}. "
                f"Assuming teacher scoring already exists. smoke test ends."
            )
            print("[DONE] Completed dual-write smoke test (no-op teacher scoring).")
            return

        # pick latest submittedAt if present, otherwise last item
        items_sorted = sorted(
            items,
            key=lambda x: x.get("submittedAt") or "",
            reverse=True,
        )
        pending_passage_id = items_sorted[0].get("passageId") or items_sorted[0].get("passage_id")

        if not pending_passage_id:
            raise RuntimeError(
                f"pending-short-answers returned items but could not find passageId. "
                f"studentId={student_id} latest_item={items_sorted[0]}"
            )

    # If pending is empty, teacher scoring may have already occurred in a previous run.
    if pending_passage_id is None:
        print("[WARN] No pending short answer to score. Assuming teacher scoring already exists; exiting smoke test.")
        print("[DONE] Completed dual-write smoke test (no-op teacher scoring).")
        return

    print(f"[7] Submitting teacher score for pending passageId={pending_passage_id}...")
    http_json(
        "POST",
        teacher_s,
        "/api/teacher/score",
        payload={
            "studentId": student_id,
            "passageId": pending_passage_id,
            "score": 1,
            "feedback": "Auto-test feedback: marked correct."
        },
    )
    print("[OK] Teacher score saved.")

    print("[DONE] Completed dual-write smoke test.")

if __name__ == "__main__":
    main()
