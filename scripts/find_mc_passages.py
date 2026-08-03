import os
import mysql.connector

DB_HOST = os.environ.get("READWISE_DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("READWISE_DB_PORT", "3306"))
DB_USER = os.environ.get("READWISE_DB_USER", "root")
DB_PASSWORD = os.environ.get("READWISE_DB_PASSWORD", "")
DB_NAME = os.environ.get("READWISE_DB_NAME", "readwise_db")

SQL = """
SELECT a.passage_id, COUNT(*) AS mc_count
FROM assessment_questions aq
JOIN assessments a ON a.id=aq.assessment_id
WHERE aq.type IN ('multiple_choice','multiple_choice_harder')
GROUP BY a.passage_id
ORDER BY mc_count DESC
LIMIT 10
"""

def main():
    conn = mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
    )
    cur = conn.cursor(dictionary=True)
    cur.execute(SQL)
    rows = cur.fetchall()
    for r in rows:
        print(r)
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
