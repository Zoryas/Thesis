import os
import mysql.connector


def main():
    DB_HOST = os.environ.get("READWISE_DB_HOST", "127.0.0.1")
    DB_PORT = int(os.environ.get("READWISE_DB_PORT", "3306"))
    DB_USER = os.environ.get("READWISE_DB_USER", "root")
    DB_PASSWORD = os.environ.get("READWISE_DB_PASSWORD", "")
    DB_NAME = os.environ.get("READWISE_DB_NAME", "readwise_db")

    student_id = os.environ.get("VERIFY_STUDENT_ID", "s14")
    passage_id = os.environ.get("VERIFY_PASSAGE_ID", "p40")

    cnx = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )
    cur = cnx.cursor(dictionary=True)

    cur.execute(
        "SELECT id FROM quiz_attempts WHERE student_id=%s AND passage_id=%s ORDER BY id DESC LIMIT 1",
        (student_id, passage_id),
    )
    row = cur.fetchone()
    legacy_id = row["id"] if row else None

    print("=== DB Verification (normalized dual-write) ===")
    print("student_id:", student_id)
    print("passage_id:", passage_id)
    print("latest legacy quiz_attempt id:", legacy_id)

    def has_column(table, column):
        cur.execute(f"SHOW COLUMNS FROM {table} LIKE %s", (column,))
        return cur.fetchone() is not None

    def count_with_any_legacy_key(table):
        if legacy_id is None:
            return 0

        candidate_cols = [
            "legacy_quiz_attempt_id",
            "quiz_attempt_id",
            "attempt_id",
            "session_id",  # last resort
            "reading_session_id",
        ]
        for col in candidate_cols:
            if has_column(table, col):
                cur.execute(f"SELECT COUNT(*) AS c FROM {table} WHERE {col}=%s", (legacy_id,))
                return cur.fetchone()["c"]

        raise RuntimeError(f"Could not find any legacy key column in {table}. Tried: {candidate_cols}")

    # reading_history is keyed by session_id, not legacy_quiz_attempt_id
    def count_reading_history_for_legacy():
        if legacy_id is None:
            return 0
        cur.execute(
            """
            SELECT rh.id
            FROM reading_sessions rs
            JOIN reading_history rh ON rh.session_id = rs.id
            WHERE rs.legacy_quiz_attempt_id=%s
            ORDER BY rh.id
            """,
            (legacy_id,),
        )
        rows = cur.fetchall()
        return len(rows)

    tables = [
        "reading_sessions",
        "student_answers",
        "short_answer_responses",
        "short_answer_scores",
        "scores",
    ]

    for t in tables:
        print(f"{t}: {count_with_any_legacy_key(t)}")

    print(f"reading_history: {count_reading_history_for_legacy()}")

    # Check recommendations for student_id
    if has_column("recommendations", "student_id") and has_column("recommendations", "week_no"):
        cur.execute("SELECT COUNT(*) AS c FROM recommendations WHERE student_id=%s", (student_id,))
        rec_count = cur.fetchone()["c"]
        print(f"recommendations (student {student_id}): {rec_count}")

    # Also show a small join sample for scores/short_answer_scores if present.
    if legacy_id is not None:
        cur.execute(
            "SELECT sar.id, sar.student_answer_id, sar.response_text, sas.score_binary, sas.feedback, sas.scored_at "
            "FROM short_answer_responses sar "
            "LEFT JOIN short_answer_scores sas ON sas.short_answer_response_id = sar.id "
            "WHERE sar.legacy_quiz_attempt_id=%s "
            "ORDER BY sar.id DESC LIMIT 3",
            (legacy_id,),
        )
        sample = cur.fetchall()
        print("short_answer (latest 3):", sample)

    cnx.close()


if __name__ == "__main__":
    main()
