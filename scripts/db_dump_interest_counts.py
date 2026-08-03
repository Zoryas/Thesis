import os
import mysql.connector

DB_HOST = os.environ.get("READWISE_DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("READWISE_DB_PORT", "3306"))
DB_USER = os.environ.get("READWISE_DB_USER", "root")
DB_PASSWORD = os.environ.get("READWISE_DB_PASSWORD", "")
DB_NAME = os.environ.get("READWISE_DB_NAME", "readwise_db")

INTEREST = [
    "users","teachers","students","classes","sections","reading_levels","passages","assessments","assessment_questions",
    "questions","choices","reading_sessions","student_answers","short_answer_responses","short_answer_scores","scores",
    "recommendations","reading_history","reports","audit_logs","notifications","settings"
]

def main():
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
    )
    cur = conn.cursor()
    cur.execute("SHOW TABLES")
    tables = [r[0] for r in cur.fetchall()]

    existing = [t for t in INTEREST if t in tables]

    print(f"Total tables in db: {len(tables)}")
    print("Existing (interest):")
    print(existing)

    print("\nCounts (interest tables):")
    for t in existing:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            c = cur.fetchone()[0]
        except Exception as e:
            c = f"ERR:{e}"
        print(f"{t}: {c}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
