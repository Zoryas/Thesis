import os
import json
from datetime import datetime, timezone
import mysql.connector
from contextlib import contextmanager


DB_HOST = os.environ.get("READWISE_DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("READWISE_DB_PORT", "3306"))
DB_USER = os.environ.get("READWISE_DB_USER", "root")
DB_PASSWORD = os.environ.get("READWISE_DB_PASSWORD", "")
DB_NAME = os.environ.get("READWISE_DB_NAME", "readwise_db")


def mysql_config(include_db=True):
    cfg = {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "charset": "utf8mb4",
        "use_unicode": True,
    }
    if include_db:
        cfg["database"] = DB_NAME
    return cfg


@contextmanager
def db_cursor(dictionary=False):
    conn = mysql.connector.connect(**mysql_config(True))
    cur = conn.cursor(dictionary=dictionary)
    try:
        yield conn, cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def _json_dumps(val):
    return json.dumps(val, ensure_ascii=False) if val is not None else None


def backfill_from_quiz_attempts(batch_limit=5000):
    """
    One-time backfill from current legacy model (quiz_attempts / student_reading_sessions /
    student_reading_progress_drafts) into the new production relational model tables.

    This script assumes the target tables already exist.
    """
    with db_cursor(True) as (_, cur):
        # Basic backfill: create reading_sessions + student_answers + short_answer_responses
        # from quiz_attempts. We derive week_no, passage_id, student_id, and the reading_time.
        #
        # Note: Legacy schema uses:
        # - quiz_attempts.student_id
        # - quiz_attempts.passage_id
        # - quiz_attempts.week_no
        # - quiz_attempts.responses_json
        # - quiz_attempts.short_answer_text
        # - quiz_attempts.teacher_score / teacher_feedback / teacher_scored_by / teacher_scored_at
        # - quiz_attempts.score_pct
        #
        # New schema (per your ER) is:
        # - reading_sessions(session_id/pk), student_id, passage_id, week_no, started_at, completed_at, status, duration_seconds
        # - student_answers(answer_id/pk), session_id, question_id (nullable/optional initially), answer_payload_json, is_correct_nullable, submitted_at
        # - short_answer_responses, short_answer_scores, scores
        #
        # Since quiz_attempts does not store question-level identity, we store all responses_json
        # as a single student_answers row with question_id=NULL initially, and short_answer_text
        # into short_answer_responses.
        #
        # We also create/update scores rows at the session level.

        cur.execute("SELECT COUNT(*) AS total FROM quiz_attempts")
        total = int(cur.fetchone()["total"] or 0)
        if total == 0:
            return {"totalQuizAttempts": 0, "backfilled": 0}

        cur.execute(
            """
            SELECT
              qa.id AS quiz_attempt_id,
              qa.student_id,
              qa.passage_id,
              qa.week_no,
              qa.reading_time,
              qa.responses_json,
              qa.short_answer_text,
              qa.submitted_at,
              qa.teacher_score,
              qa.teacher_feedback,
              qa.teacher_scored_by,
              qa.teacher_scored_at,
              qa.score_pct
            FROM quiz_attempts qa
            ORDER BY qa.id ASC
            LIMIT %s
            """,
            (batch_limit,),
        )
        rows = cur.fetchall()

        # Deterministic mapping: session_id = quiz_attempt_id (as a BIGINT/identifier) if your
        # schema allows it; otherwise we store a mapping via event_id-like uniqueness.
        # We'll use quiz_attempt_id as session's legacy_reference_id if a column exists; if not,
        # we insert with generated pk and rely on unique constraints later.
        #
        # To avoid assumptions, we check existence of optional legacy columns once.

        def col_exists(table, col):
            cur.execute(
                """
                SELECT 1
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s
                LIMIT 1
                """,
                (DB_NAME, table, col),
            )
            return cur.fetchone() is not None

        has_legacy_session_ref = col_exists("reading_sessions", "legacy_quiz_attempt_id")
        has_legacy_answer_ref = col_exists("student_answers", "legacy_quiz_attempt_id")
        has_legacy_short_answer_ref = col_exists("short_answer_responses", "legacy_quiz_attempt_id")
        has_legacy_score_ref = col_exists("scores", "legacy_quiz_attempt_id")

        backfilled = 0
        for r in rows:
            student_id = r["student_id"]
            passage_id = r["passage_id"]
            week_no = int(r["week_no"])

            # reading time: legacy stores string like "00:12" maybe; convert if possible
            duration_seconds = 0
            reading_time = r.get("reading_time")
            if reading_time:
                s = str(reading_time).strip()
                parts = s.split(":")
                try:
                    if len(parts) == 2:
                        mm = int(parts[0])
                        ss = int(parts[1])
                        duration_seconds = mm * 60 + ss
                    elif len(parts) == 3:
                        hh = int(parts[0])
                        mm = int(parts[1])
                        ss = int(parts[2])
                        duration_seconds = hh * 3600 + mm * 60 + ss
                except Exception:
                    duration_seconds = 0

            submitted_at = r.get("submitted_at")
            started_at = submitted_at
            completed_at = submitted_at
            status = "completed" if completed_at is not None else "in_progress"

            # 1) reading_sessions
            if has_legacy_session_ref:
                # Upsert by legacy_quiz_attempt_id
                cur.execute(
                    """
                    INSERT INTO reading_sessions
                      (legacy_quiz_attempt_id, student_id, passage_id, week_no, started_at, completed_at, duration_seconds, status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE
                      duration_seconds=VALUES(duration_seconds),
                      status=VALUES(status),
                      completed_at=COALESCE(VALUES(completed_at), completed_at)
                    """,
                    (
                        int(r["quiz_attempt_id"]),
                        student_id,
                        passage_id,
                        week_no,
                        started_at,
                        completed_at,
                        duration_seconds,
                        status,
                    ),
                )
            else:
                # Fallback: insert; later unique constraints should prevent duplicates
                cur.execute(
                    """
                    INSERT INTO reading_sessions
                      (student_id, passage_id, week_no, started_at, completed_at, duration_seconds, status)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (student_id, passage_id, week_no, started_at, completed_at, duration_seconds, status),
                )

            # Fetch inserted session id
            if has_legacy_session_ref:
                cur.execute(
                    "SELECT id FROM reading_sessions WHERE legacy_quiz_attempt_id=%s",
                    (int(r["quiz_attempt_id"]),),
                )
            else:
                cur.execute(
                    """
                    SELECT id FROM reading_sessions
                    WHERE student_id=%s AND passage_id=%s AND week_no=%s
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (student_id, passage_id, week_no),
                )
            session_row = cur.fetchone()
            if not session_row:
                continue
            session_id = session_row["id"]

            # 2) student_answers (store all response payload as one blob for now)
            responses_json = r.get("responses_json")
            answer_payload_json = _json_dumps(responses_json if isinstance(responses_json, (list, dict)) else responses_json)

            # is_correct_nullable: legacy doesn't store correctness at question-level; keep NULL initially
            submitted_at_ans = r.get("submitted_at")

            if has_legacy_answer_ref:
                cur.execute(
                    """
                    INSERT INTO student_answers
                      (legacy_quiz_attempt_id, session_id, question_id, answer_payload_json, is_correct_nullable, submitted_at)
                    VALUES (%s,%s,NULL,%s,NULL,%s)
                    ON DUPLICATE KEY UPDATE
                      answer_payload_json=VALUES(answer_payload_json),
                      submitted_at=COALESCE(VALUES(submitted_at), submitted_at)
                    """,
                    (int(r["quiz_attempt_id"]), session_id, answer_payload_json, submitted_at_ans),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO student_answers
                      (session_id, question_id, answer_payload_json, is_correct_nullable, submitted_at)
                    VALUES (%s,NULL,%s,NULL,%s)
                    """,
                    (session_id, answer_payload_json, submitted_at_ans),
                )

            cur.execute(
                """
                SELECT id FROM student_answers
                WHERE session_id=%s
                ORDER BY id DESC
                LIMIT 1
                """,
                (session_id,),
            )
            answer_id_row = cur.fetchone()
            if not answer_id_row:
                continue
            student_answer_id = answer_id_row["id"]

            # 3) short_answer_responses + short_answer_scores
            short_answer_text = r.get("short_answer_text")
            if short_answer_text is not None:
                if has_legacy_short_answer_ref:
                    cur.execute(
                        """
                        INSERT INTO short_answer_responses
                          (legacy_quiz_attempt_id, student_answer_id, response_text, needs_manual_review, submitted_at)
                        VALUES (%s,%s,%s,1,%s)
                        ON DUPLICATE KEY UPDATE
                          response_text=VALUES(response_text),
                          needs_manual_review=VALUES(needs_manual_review),
                          submitted_at=COALESCE(VALUES(submitted_at), submitted_at)
                        """,
                        (
                            int(r["quiz_attempt_id"]),
                            student_answer_id,
                            short_answer_text,
                            submitted_at,
                        ),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO short_answer_responses
                          (student_answer_id, response_text, needs_manual_review, submitted_at)
                        VALUES (%s,%s,1,%s)
                        """,
                        (student_answer_id, short_answer_text, submitted_at),
                    )

                cur.execute(
                    "SELECT id FROM short_answer_responses WHERE student_answer_id=%s ORDER BY id DESC LIMIT 1",
                    (student_answer_id,),
                )
                sar_row = cur.fetchone()
                if sar_row:
                    short_answer_response_id = sar_row["id"]

                    teacher_score = r.get("teacher_score")
                    needs_manual_review = 0 if teacher_score is not None else 1

                    if teacher_score is not None:
                        score_binary = 1 if int(teacher_score) == 1 else 0
                        teacher_id = r.get("teacher_scored_by")
                        feedback = r.get("teacher_feedback")
                        scored_at = r.get("teacher_scored_at")

                        # short_answer_scores
                        if has_legacy_score_ref:
                            cur.execute(
                                """
                                INSERT INTO short_answer_scores
                                  (legacy_quiz_attempt_id, short_answer_response_id, teacher_id, score_binary, feedback, scored_at)
                                VALUES (%s,%s,%s,%s,%s,%s)
                                ON DUPLICATE KEY UPDATE
                                  teacher_id=VALUES(teacher_id),
                                  score_binary=VALUES(score_binary),
                                  feedback=VALUES(feedback),
                                  scored_at=COALESCE(VALUES(scored_at), scored_at)
                                """,
                                (
                                    int(r["quiz_attempt_id"]),
                                    short_answer_response_id,
                                    teacher_id,
                                    score_binary,
                                    feedback,
                                    scored_at,
                                ),
                            )
                        else:
                            cur.execute(
                                """
                                INSERT INTO short_answer_scores
                                  (short_answer_response_id, teacher_id, score_binary, feedback, scored_at)
                                VALUES (%s,%s,%s,%s,%s,%s)
                                """,
                                (
                                    short_answer_response_id,
                                    teacher_id,
                                    score_binary,
                                    feedback,
                                    scored_at,
                                ),
                            )
                    else:
                        # Update needs_manual_review
                        cur.execute(
                            """
                            UPDATE short_answer_responses
                            SET needs_manual_review=%s
                            WHERE id=%s
                            """,
                            (1, short_answer_response_id),
                        )

            # 4) scores (session-level)
            objective_score_pct = int(r.get("score_pct") or 0)
            short_answer_score_pct = None
            total_score_pct = objective_score_pct
            computed_at = datetime.now(timezone.utc)

            if has_legacy_score_ref:
                cur.execute(
                    """
                    INSERT INTO scores
                      (legacy_quiz_attempt_id, session_id, objective_score_pct, short_answer_score_pct, total_score_pct, computed_at)
                    VALUES (%s,%s,%s,%s,%s,%s)
                    ON DUPLICATE KEY UPDATE
                      objective_score_pct=VALUES(objective_score_pct),
                      total_score_pct=VALUES(total_score_pct),
                      computed_at=COALESCE(VALUES(computed_at), computed_at)
                    """,
                    (
                        int(r["quiz_attempt_id"]),
                        session_id,
                        objective_score_pct,
                        short_answer_score_pct,
                        total_score_pct,
                        computed_at,
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO scores
                      (session_id, objective_score_pct, short_answer_score_pct, total_score_pct, computed_at)
                    VALUES (%s,%s,%s,%s,%s)
                    """,
                    (session_id, objective_score_pct, short_answer_score_pct, total_score_pct, computed_at),
                )

            backfilled += 1

        return {"totalQuizAttemptsScanned": len(rows), "backfilled": backfilled, "db": DB_NAME}


def backfill_questions_and_choices():
    """
    Backfill production-model questions/choices from legacy assessment tables:
      - assessments (per passage)
      - assessment_questions (per assessment, with prompt/type/options/answers)

    Targets:
      - questions(passage_id, type, prompt, sequence_no, metadata_json)
      - choices(question_id, choice_text, is_correct, sequence_no)

    Notes:
    - For now, choices are created only for multiple-choice types.
    - is_correct is derived from assessment_questions.answer_index.
      (Your seeds store answerIndex as 0/1/2/3; we assume same for legacy.)
    """
    with db_cursor(True) as (_, cur):
        cur.execute("SELECT COUNT(*) AS c FROM questions")
        if int(cur.fetchone()["c"] or 0) > 0:
            return {"questionsAlreadyBackfilled": True}

        # Insert questions
        cur.execute(
            """
            SELECT
              a.passage_id,
              aq.sort_order,
              aq.type,
              aq.prompt,
              aq.difficulty,
              aq.answer_index,
              aq.answer_key,
              aq.answer_keys_json
            FROM assessment_questions aq
            JOIN assessments a ON a.id=aq.assessment_id
            ORDER BY a.passage_id, aq.sort_order, aq.id
            """
        )
        qrows = cur.fetchall()
        if not qrows:
            return {"questionsBackfilled": 0, "choicesBackfilled": 0, "reason": "No assessment_questions found"}

        inserted_questions = 0
        for r in qrows:
            passage_id = r["passage_id"]
            sequence_no = int(r["sort_order"] or 0)
            qtype = str(r["type"] or "").strip().lower()
            prompt = r["prompt"]

            metadata = {
                "difficulty": r.get("difficulty"),
                "answerIndex": r.get("answer_index"),
                "answerKey": r.get("answer_key"),
                "answerKeys": json.loads(r["answer_keys_json"]) if r.get("answer_keys_json") else [],
            }

            cur.execute(
                """
                INSERT INTO questions (passage_id, type, prompt, sequence_no, metadata_json)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (passage_id, qtype, prompt, sequence_no, json.dumps(metadata, ensure_ascii=False)),
            )
            inserted_questions += 1

        # Insert choices for MC types
        cur.execute(
            """
            SELECT
              a.passage_id,
              aq.sort_order,
              aq.prompt,
              aq.type,
              aq.options_json,
              aq.answer_index
            FROM assessment_questions aq
            JOIN assessments a ON a.id=aq.assessment_id
            """
        )
        qa_rows = cur.fetchall()

        inserted_choices = 0
        for r in qa_rows:
            passage_id = r["passage_id"]
            sequence_no = int(r["sort_order"] or 0)
            prompt = r["prompt"]
            qtype = str(r["type"] or "").strip().lower()

            if qtype not in ("multiple_choice", "multiple_choice_harder"):
                continue

            cur.execute(
                """
                SELECT id
                FROM questions
                WHERE passage_id=%s AND sequence_no=%s AND prompt=%s
                ORDER BY id DESC
                LIMIT 1
                """,
                (passage_id, sequence_no, prompt),
            )
            qrow = cur.fetchone()
            if not qrow:
                continue
            question_id = int(qrow["id"])

            # parse options_json
            options = []
            if r.get("options_json") is not None:
                try:
                    options = json.loads(r["options_json"]) if isinstance(r["options_json"], str) else r["options_json"]
                except Exception:
                    options = []

            try:
                answer_index_int = int(r.get("answer_index")) if r.get("answer_index") is not None else None
            except (TypeError, ValueError):
                answer_index_int = None

            for idx, opt in enumerate(options):
                if opt is None:
                    continue
                is_correct = 1 if (answer_index_int is not None and idx == answer_index_int) else 0
                cur.execute(
                    """
                    INSERT INTO choices (question_id, choice_text, is_correct, sequence_no)
                    VALUES (%s,%s,%s,%s)
                    """,
                    (question_id, str(opt), is_correct, idx),
                )
                inserted_choices += 1

        return {"questionsBackfilled": inserted_questions, "choicesBackfilled": inserted_choices, "db": DB_NAME}


def recommendation_for_score(score):
    normalized_score = int(round(score or 0))
    if normalized_score >= 80:
        return "HARD", "HARD"
    if normalized_score >= 60:
        return "MODERATE", "MODERATE"
    return "EASY", "EASY"


def backfill_recommendations_weekly():
    """
    Backfills week-scoped recommendations from legacy quiz_attempts grouped by (student_id, week_no).
    Computes AVG(score_pct) and resolves suggested_level_id via reading_levels.code.
    Uses ON DUPLICATE KEY UPDATE for deterministic upserts.
    """
    with db_cursor(True) as (_, cur):
        # Build map of reading_levels code -> id
        cur.execute("SELECT id, code FROM reading_levels")
        level_rows = cur.fetchall()
        level_map = {row["code"]: int(row["id"]) for row in level_rows}

        # Query legacy quiz_attempts grouped by student_id, week_no
        cur.execute(
            """
            SELECT
              student_id,
              week_no,
              AVG(score_pct) AS avg_score
            FROM quiz_attempts
            WHERE student_id IS NOT NULL AND week_no IS NOT NULL
            GROUP BY student_id, week_no
            ORDER BY student_id, week_no
            """
        )
        rows = cur.fetchall()

        upserted_count = 0
        for row in rows:
            student_id = str(row["student_id"])
            week_no = int(row["week_no"])
            avg_score = float(row["avg_score"] or 0)

            action, diff_code = recommendation_for_score(avg_score)
            recommendation_text = f"{action} ({diff_code})"
            suggested_level_id = level_map.get(diff_code)

            cur.execute(
                """
                INSERT INTO recommendations (student_id, week_no, source_type, recommendation_text, suggested_level_id)
                VALUES (%s, %s, 'rule', %s, %s)
                ON DUPLICATE KEY UPDATE
                  source_type = VALUES(source_type),
                  recommendation_text = VALUES(recommendation_text),
                  suggested_level_id = VALUES(suggested_level_id)
                """,
                (student_id, week_no, recommendation_text, suggested_level_id),
            )
            upserted_count += 1

        return {"recommendationsUpserted": upserted_count, "groupsFound": len(rows), "db": DB_NAME}


def verify_questions_and_choices(passage_id="p40"):
    with db_cursor(True) as (_, cur):
        cur.execute("SELECT COUNT(*) AS c FROM questions WHERE passage_id=%s", (passage_id,))
        qcount = int(cur.fetchone()["c"] or 0)
        cur.execute(
            """
            SELECT COUNT(*) AS c
            FROM choices c
            JOIN questions q ON q.id=c.question_id
            WHERE q.passage_id=%s
            """,
            (passage_id,),
        )
        chcount = int(cur.fetchone()["c"] or 0)
        return {"passageId": passage_id, "questions": qcount, "choices": chcount}


if __name__ == "__main__":
    print("Quiz-attempt backfill:", backfill_from_quiz_attempts(batch_limit=5000))
    print("Questions/choices backfill:", backfill_questions_and_choices())
    print("Recommendations weekly backfill:", backfill_recommendations_weekly())
    print("Verify (p40):", verify_questions_and_choices("p40"))

