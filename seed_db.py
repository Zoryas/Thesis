import os
import sys
import mysql.connector
from werkzeug.security import generate_password_hash

os.environ.setdefault("READWISE_SKIP_AUTO_INIT", "1")

from app import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, SEED_ADMINS, SEED_TEACHERS, SEED_STUDENTS


def connect(database=None, autocommit=False):
    cfg = {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "charset": "utf8mb4",
        "use_unicode": True,
        "autocommit": autocommit,
    }
    if database is not None:
        cfg["database"] = database
    return mysql.connector.connect(**cfg)


def ensure_schema():
    admin_conn = connect(database=None, autocommit=False)
    admin_cur = admin_conn.cursor()
    admin_cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    admin_conn.commit()
    admin_cur.close()
    admin_conn.close()

    conn = connect(database=DB_NAME, autocommit=False)
    cur = conn.cursor()
    statements = [
        """CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role ENUM('teacher','student','admin') NOT NULL,
            is_active TINYINT(1) NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
        """ALTER TABLE users MODIFY COLUMN role ENUM('teacher','student','admin') NOT NULL""",
        """CREATE TABLE IF NOT EXISTS program_settings (
            id TINYINT PRIMARY KEY,
            program_start_date DATE NOT NULL,
            manual_override_week TINYINT NULL,
            updated_by INT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT chk_program_settings_id CHECK (id=1),
            FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
        """CREATE TABLE IF NOT EXISTS auth_tokens (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            token VARCHAR(128) UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_auth_tokens_user (user_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
        """CREATE TABLE IF NOT EXISTS students (
            id VARCHAR(20) PRIMARY KEY,
            user_id INT UNIQUE NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            grade VARCHAR(20) NOT NULL,
            section VARCHAR(100) NOT NULL,
            class_level ENUM('EASY','MODERATE','HARD') NOT NULL DEFAULT 'EASY',
            pre_score INT NOT NULL DEFAULT 0,
            pre_assessment_completed TINYINT(1) NOT NULL DEFAULT 0,
            pre_assessment_completed_at TIMESTAMP NULL,
            avatar_type ENUM('initials','preset','upload') NOT NULL DEFAULT 'initials',
            avatar_value MEDIUMTEXT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
        """CREATE TABLE IF NOT EXISTS teachers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL UNIQUE,
            full_name VARCHAR(255) NOT NULL,
            department VARCHAR(100) NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
    ]
    for sql in statements:
        cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()


def seed_users_and_students():
    conn = connect(database=DB_NAME, autocommit=False)
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT id FROM program_settings WHERE id=1")
    if not cur.fetchone():
        cur.execute("SELECT CURRENT_DATE() AS today")
        today = cur.fetchone()["today"]
        cur.execute("INSERT INTO program_settings (id, program_start_date, manual_override_week, updated_by) VALUES (1, %s, NULL, NULL)", (today,))

    for admin in SEED_ADMINS:
        password_hash = generate_password_hash(admin["password"])
        cur.execute("SELECT id FROM users WHERE email=%s", (admin["email"],))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE users SET password_hash=%s, role='admin', is_active=1 WHERE id=%s", (password_hash, row["id"]))
        else:
            cur.execute("INSERT INTO users (email, password_hash, role, is_active) VALUES (%s, %s, 'admin', 1)", (admin["email"], password_hash))

    for teacher in SEED_TEACHERS:
        password_hash = generate_password_hash(teacher["password"])
        cur.execute("SELECT id FROM users WHERE email=%s", (teacher["email"],))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE users SET password_hash=%s, role='teacher', is_active=1 WHERE id=%s", (password_hash, row["id"]))
            user_id = row["id"]
        else:
            cur.execute("INSERT INTO users (email, password_hash, role, is_active) VALUES (%s, %s, 'teacher', 1)", (teacher["email"], password_hash))
            user_id = cur.lastrowid
        cur.execute("SELECT id FROM teachers WHERE user_id=%s", (user_id,))
        if not cur.fetchone():
            cur.execute("INSERT INTO teachers (user_id, full_name, department) VALUES (%s, %s, NULL)", (user_id, teacher["email"].split("@", 1)[0]))

    for student in SEED_STUDENTS:
        password_hash = generate_password_hash(student["password"])
        cur.execute("SELECT id FROM users WHERE email=%s", (student["email"],))
        row = cur.fetchone()
        if row:
            cur.execute("UPDATE users SET password_hash=%s, role='student', is_active=1 WHERE id=%s", (password_hash, row["id"]))
            user_id = row["id"]
        else:
            cur.execute("INSERT INTO users (email, password_hash, role, is_active) VALUES (%s, %s, 'student', 1)", (student["email"], password_hash))
            user_id = cur.lastrowid
        cur.execute("SELECT id FROM students WHERE id=%s", (student["id"],))
        if not cur.fetchone():
            cur.execute(
                """INSERT INTO students (id, user_id, full_name, grade, section, class_level, pre_score, pre_assessment_completed)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (student["id"], user_id, student["name"], student["grade"], student["section"], student["class"], int(student["pre"]), 1 if int(student["pre"]) > 0 else 0),
            )
        else:
            cur.execute(
                """UPDATE students SET user_id=%s, full_name=%s, grade=%s, section=%s, class_level=%s, pre_score=%s, pre_assessment_completed=%s
                   WHERE id=%s""",
                (user_id, student["name"], student["grade"], student["section"], student["class"], int(student["pre"]), 1 if int(student["pre"]) > 0 else 0, student["id"]),
            )

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    seed_demo_data = "--schema-only" not in sys.argv
    print("Ensuring database schema..." + ("" if not seed_demo_data else " seeding demo data..."))
    ensure_schema()
    if seed_demo_data:
        seed_users_and_students()
    print("Database bootstrap completed successfully.")
