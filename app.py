
from contextlib import contextmanager
from pathlib import Path
import json
import os
import re
import secrets

import joblib
import mysql.connector
import numpy as np
from flask import Flask, jsonify, request, session
from flask_cors import CORS
from scipy.sparse import csr_matrix, hstack
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "ml_model"
MIN_WORDS = 30
TOTAL_PROGRAM_WEEKS = 8
MAX_WEEKLY_PASSAGES_PER_CLASS = 5

DB_HOST = os.environ.get("READWISE_DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("READWISE_DB_PORT", "3306"))
DB_USER = os.environ.get("READWISE_DB_USER", "root")
DB_PASSWORD = os.environ.get("READWISE_DB_PASSWORD", "")
DB_NAME = os.environ.get("READWISE_DB_NAME", "readwise_db")
PRESET_AVATAR_PATTERN = re.compile(r"^/readwise/avatar/[A-Za-z0-9 _().-]+\.svg$")

if not re.fullmatch(r"[A-Za-z0-9_]+", DB_NAME):
    raise RuntimeError("Invalid READWISE_DB_NAME")

app = Flask(__name__)
IS_PRODUCTION = os.environ.get("READWISE_ENV") == "production"

app.config.update(
    SECRET_KEY=os.environ.get("READWISE_SECRET_KEY", "readwise-dev-secret"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="None" if IS_PRODUCTION else "Lax",
    SESSION_COOKIE_SECURE=IS_PRODUCTION,
)

ALLOWED_ORIGINS = os.environ.get("READWISE_ALLOWED_ORIGINS", "http://localhost,http://127.0.0.1")
origins_list = [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()]

CORS(
    app,
    supports_credentials=True,
    origins=origins_list,
    allow_headers=["Content-Type", "X-Auth-Token", "Authorization"],
)

ARTIFACTS = {
    "svm_model": joblib.load(MODEL_DIR / "svm_model.pkl"),
    "word_vectorizer": joblib.load(MODEL_DIR / "word_vectorizer.pkl"),
    "char_vectorizer": joblib.load(MODEL_DIR / "char_vectorizer.pkl"),
    "label_encoder": joblib.load(MODEL_DIR / "label_encoder.pkl"),
}

DB_POOL = None

SEED_TEACHERS = [
    {"email": "ms.villanueva@pnhs.edu", "password": "teacher123"},
    {"email": "teacher@example.com", "password": "abcd"},
]

SEED_STUDENTS = [
    {"id": "s1", "email": "juan.delacruz@pnhs.edu", "password": "password123", "name": "Juan Dela Cruz", "grade": "7", "section": "Sampaguita", "class": "HARD", "pre": 58},
    {"id": "s2", "email": "maria.santos@pnhs.edu", "password": "password123", "name": "Maria Santos", "grade": "7", "section": "Sampaguita", "class": "MODERATE", "pre": 72},
    {"id": "s3", "email": "carlo.reyes@pnhs.edu", "password": "password123", "name": "Carlo Reyes", "grade": "7", "section": "Sampaguita", "class": "EASY", "pre": 45},
]

SEED_PASSAGES = [
    {"id": "p1", "title": "The Water Cycle", "genre": "Expository", "label": "EASY", "text": "Water evaporates, condenses into clouds, and returns as rain."},
    {"id": "p2", "title": "The Life of Jose Rizal", "genre": "Narrative", "label": "MODERATE", "text": "Jose Rizal wrote novels that inspired Filipino nationalism."},
    {"id": "p3", "title": "Climate Change and Its Effects", "genre": "Expository", "label": "HARD", "text": "Climate change increases risks like stronger storms and sea-level rise."},
    {"id": "p4", "title": "The Little Prince Summary", "genre": "Narrative", "label": "EASY", "text": "The Little Prince teaches readers about friendship and love."},
    {"id": "p5", "title": "Philippine Biodiversity", "genre": "Expository", "label": "MODERATE", "text": "The Philippines has many endemic species that need protection."},
    {"id": "p6", "title": "Constitutional Rights of Citizens", "genre": "Expository", "label": "HARD", "text": "The Constitution protects rights like due process and free expression."},
]

SEED_ASSESSMENTS = {
    "p1": {"questions": [{"difficulty": "EASY", "type": "multiple_choice", "prompt": "What causes water to rise into the atmosphere?", "options": ["Condensation", "Evaporation", "Runoff", "Precipitation"], "answerIndex": 1}], "shortAnswerPrompt": ""},
    "p2": {"questions": [{"difficulty": "MODERATE", "type": "multiple_choice_harder", "prompt": "Where was Jose Rizal born?", "options": ["Manila", "Calamba, Laguna", "Baguio", "Cebu"], "answerIndex": 1}], "shortAnswerPrompt": ""},
    "p3": {"questions": [{"difficulty": "DIFFICULT", "type": "multiple_choice_harder", "prompt": "Which is an effect of climate change?", "options": ["Sea-level rise", "Colder oceans", "Lower storms", "Stable weather"], "answerIndex": 0}], "shortAnswerPrompt": "In your own words, explain one effect of climate change on the Philippines."},
    "p4": {"questions": [], "shortAnswerPrompt": ""},
    "p5": {"questions": [], "shortAnswerPrompt": ""},
    "p6": {"questions": [], "shortAnswerPrompt": "Explain what due process of law means in your own words."},
}


def api_ok(data=None, status=200):
    return jsonify({"ok": True, "data": data}), status


def api_error(message, status=400):
    return jsonify({"ok": False, "error": message}), status


def normalize_class_level(value):
    v = str(value or "").strip().upper()
    if v == "DIFFICULT":
        return "HARD"
    return v if v in {"EASY", "MODERATE", "HARD"} else "EASY"


def normalize_avatar_type(value):
    v = str(value or "initials").strip().lower()
    return v if v in {"initials", "preset", "upload"} else None


def sanitize_avatar_value(avatar_type, value):
    if avatar_type == "initials":
        return None

    avatar_value = str(value or "").strip()
    if not avatar_value:
        raise ValueError("avatarValue is required.")

    if avatar_type == "preset":
        if not PRESET_AVATAR_PATTERN.fullmatch(avatar_value):
            raise ValueError("Invalid preset avatar.")
        return avatar_value

    if avatar_type == "upload":
        if not avatar_value.startswith("data:image/"):
            raise ValueError("Invalid uploaded avatar.")
        if len(avatar_value) > 8_000_000:
            raise ValueError("Uploaded avatar is too large.")
        return avatar_value

    raise ValueError("Invalid avatarType.")


def normalize_week(value):
    try:
        week = int(value)
    except (TypeError, ValueError):
        return 1
    return min(TOTAL_PROGRAM_WEEKS, max(1, week))


def count_words(text):
    return len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", str(text or "")))


def estimate_minutes(words):
    return max(1, int(np.ceil((words or 0) / 80.0)))


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


def db_pool():
    global DB_POOL
    if DB_POOL is None:
        DB_POOL = mysql.connector.pooling.MySQLConnectionPool(
            pool_name="readwise_pool", pool_size=6, autocommit=False, **mysql_config(True)
        )
    return DB_POOL


@contextmanager
def db_cursor(dictionary=False):
    conn = db_pool().get_connection()
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


def fetch_user_by_id(cur, user_id):
    cur.execute(
        """
        SELECT u.id,u.email,u.role,u.is_active,
               s.id AS student_id,s.full_name,s.grade,s.section,s.class_level,s.pre_score,
               s.avatar_type,s.avatar_value
        FROM users u LEFT JOIN students s ON s.user_id=u.id
        WHERE u.id=%s
        """,
        (user_id,),
    )
    return cur.fetchone()


def get_request_token():
    header_token = str(request.headers.get("X-Auth-Token") or "").strip()
    if header_token:
        return header_token
    auth_header = str(request.headers.get("Authorization") or "").strip()
    if auth_header.lower().startswith("bearer "):
        bearer_token = auth_header[7:].strip()
        if bearer_token:
            return bearer_token
    return None


def current_user():
    token = get_request_token()
    if token:
        with db_cursor(True) as (_, cur):
            cur.execute(
                """
                SELECT u.id,u.email,u.role,u.is_active,
                       s.id AS student_id,s.full_name,s.grade,s.section,
                       s.class_level,s.pre_score,s.avatar_type,s.avatar_value
                FROM auth_tokens t
                JOIN users u ON u.id=t.user_id
                LEFT JOIN students s ON s.user_id=u.id
                WHERE t.token=%s
                """,
                (token,),
            )
            row = cur.fetchone()
            if row and row.get("is_active"):
                return row
            return None

    uid = session.get("user_id")
    if not uid:
        return None
    with db_cursor(True) as (_, cur):
        row = fetch_user_by_id(cur, uid)
        if not row or not row.get("is_active"):
            return None
        return row


def require_auth():
    user = current_user()
    if not user:
        return None, api_error("Authentication required.", 401)
    return user, None


def require_role(role):
    user, err = require_auth()
    if err:
        return None, err
    if user["role"] != role:
        return None, api_error("Insufficient permissions.", 403)
    return user, None


def serialize_user(row):
    student = None
    if row.get("student_id"):
        student = {
            "id": row["student_id"],
            "name": row.get("full_name"),
            "grade": row.get("grade"),
            "section": row.get("section"),
            "classLevel": row.get("class_level"),
            "preScore": row.get("pre_score"),
            "avatarType": row.get("avatar_type") or "initials",
            "avatarValue": row.get("avatar_value") or "",
        }
    return {"id": row["id"], "email": row["email"], "role": row["role"], "student": student}


def parse_json(value, fallback):
    if value is None:
        return fallback
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return fallback
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return fallback
    return fallback


def serialize_passage(row):
    confidence = float(row["confidence"]) if row.get("confidence") is not None else None
    return {
        "id": row["id"],
        "title": row["title"],
        "genre": row["genre"],
        "text": row["text"],
        "label": row["label"],
        "words": int(row["words"]),
        "time": int(row["est_minutes"]),
        "confidence": confidence,
    }


def fetch_assessment(cur, passage_id):
    cur.execute("SELECT id, short_answer_prompt FROM assessments WHERE passage_id=%s", (passage_id,))
    a = cur.fetchone()
    if not a:
        return {"questions": [], "shortAnswerPrompt": ""}
    cur.execute(
        """
        SELECT difficulty,type,prompt,options_json,answer_index,answer_key,answer_keys_json
        FROM assessment_questions WHERE assessment_id=%s ORDER BY sort_order,id
        """,
        (a["id"],),
    )
    questions = []
    for q in cur.fetchall():
        questions.append(
            {
                "difficulty": q["difficulty"],
                "type": q["type"],
                "prompt": q["prompt"],
                "options": parse_json(q.get("options_json"), []),
                "answerIndex": int(q.get("answer_index") or 0),
                "answerKey": q.get("answer_key") or "",
                "answerKeys": parse_json(q.get("answer_keys_json"), []),
            }
        )
    return {"questions": questions, "shortAnswerPrompt": a.get("short_answer_prompt") or ""}


def upsert_assessment(cur, passage_id, payload):
    payload = payload if isinstance(payload, dict) else {}
    questions = payload.get("questions") if isinstance(payload.get("questions"), list) else []
    short_answer = str(payload.get("shortAnswerPrompt") or payload.get("shortAnswer") or "").strip()

    cur.execute("SELECT id FROM assessments WHERE passage_id=%s", (passage_id,))
    row = cur.fetchone()
    if row:
        aid = row["id"]
        cur.execute("UPDATE assessments SET short_answer_prompt=%s WHERE id=%s", (short_answer, aid))
        cur.execute("DELETE FROM assessment_questions WHERE assessment_id=%s", (aid,))
    else:
        cur.execute("INSERT INTO assessments (passage_id,short_answer_prompt) VALUES (%s,%s)", (passage_id, short_answer))
        aid = cur.lastrowid

    for i, q in enumerate(questions):
        prompt = str(q.get("prompt") or q.get("q") or "").strip()
        if not prompt:
            continue
        options = q.get("options") if isinstance(q.get("options"), list) else q.get("opts")
        if not isinstance(options, list):
            options = []
        options = [str(item).strip() for item in options]
        answer_keys = q.get("answerKeys") if isinstance(q.get("answerKeys"), list) else q.get("answer_keys")
        if not isinstance(answer_keys, list):
            answer_keys = []
        answer_keys = [str(item).strip() for item in answer_keys if str(item).strip()]
        answer_index = q.get("answerIndex", q.get("ans", 0))
        try:
            answer_index = int(answer_index)
        except (TypeError, ValueError):
            answer_index = 0

        cur.execute(
            """
            INSERT INTO assessment_questions (
              assessment_id,sort_order,difficulty,type,prompt,options_json,answer_index,answer_key,answer_keys_json
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                aid,
                i,
                str(q.get("difficulty") or "EASY").upper().replace("HARD", "DIFFICULT"),
                str(q.get("type") or "multiple_choice").strip().lower(),
                prompt,
                json.dumps(options, ensure_ascii=False) if options else None,
                answer_index,
                str(q.get("answerKey") or q.get("answer_key") or "").strip() or None,
                json.dumps(answer_keys, ensure_ascii=False) if answer_keys else None,
            ),
        )


def get_weekly_assignments(cur, week):
    out = {"EASY": [], "MODERATE": [], "HARD": []}
    cur.execute("SELECT class_level, passage_id FROM weekly_assignments WHERE week_no=%s ORDER BY id", (week,))
    for row in cur.fetchall():
        out[normalize_class_level(row["class_level"])] += [row["passage_id"]]
    return out


def student_row(cur, user):
    sid = user.get("student_id")
    if sid:
        cur.execute("SELECT id, full_name, grade, section, class_level, pre_score FROM students WHERE id=%s", (sid,))
    else:
        cur.execute("SELECT id, full_name, grade, section, class_level, pre_score FROM students WHERE user_id=%s", (user["id"],))
    return cur.fetchone()

def init_database():
    conn = mysql.connector.connect(**mysql_config(False))
    cur = conn.cursor()
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    conn.commit()
    cur.close()
    conn.close()

    with db_cursor(True) as (_, cur):
        schema = [
            """CREATE TABLE IF NOT EXISTS users (id INT AUTO_INCREMENT PRIMARY KEY,email VARCHAR(255) UNIQUE NOT NULL,password_hash VARCHAR(255) NOT NULL,role ENUM('teacher','student') NOT NULL,is_active TINYINT(1) NOT NULL DEFAULT 1,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            """CREATE TABLE IF NOT EXISTS auth_tokens (id BIGINT AUTO_INCREMENT PRIMARY KEY,user_id INT NOT NULL,token VARCHAR(128) UNIQUE NOT NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,INDEX idx_auth_tokens_user (user_id)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            """CREATE TABLE IF NOT EXISTS students (id VARCHAR(20) PRIMARY KEY,user_id INT UNIQUE NOT NULL,full_name VARCHAR(255) NOT NULL,grade VARCHAR(20) NOT NULL,section VARCHAR(100) NOT NULL,class_level ENUM('EASY','MODERATE','HARD') NOT NULL DEFAULT 'EASY',pre_score INT NOT NULL DEFAULT 0,avatar_type ENUM('initials','preset','upload') NOT NULL DEFAULT 'initials',avatar_value MEDIUMTEXT NULL,FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            """CREATE TABLE IF NOT EXISTS passages (id VARCHAR(20) PRIMARY KEY,title VARCHAR(255) NOT NULL,genre VARCHAR(100) NOT NULL,text MEDIUMTEXT NOT NULL,label ENUM('EASY','MODERATE','HARD') NOT NULL,words INT NOT NULL,est_minutes INT NOT NULL,confidence DECIMAL(5,2) NULL,created_by INT NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            """CREATE TABLE IF NOT EXISTS assessments (id INT AUTO_INCREMENT PRIMARY KEY,passage_id VARCHAR(20) UNIQUE NOT NULL,short_answer_prompt TEXT NULL,FOREIGN KEY (passage_id) REFERENCES passages(id) ON DELETE CASCADE) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            """CREATE TABLE IF NOT EXISTS assessment_questions (id INT AUTO_INCREMENT PRIMARY KEY,assessment_id INT NOT NULL,sort_order INT NOT NULL DEFAULT 0,difficulty ENUM('EASY','MODERATE','DIFFICULT','CUSTOM') NOT NULL DEFAULT 'EASY',type VARCHAR(60) NOT NULL,prompt TEXT NOT NULL,options_json JSON NULL,answer_index INT NULL,answer_key VARCHAR(255) NULL,answer_keys_json JSON NULL,FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,INDEX idx_q_sort (assessment_id, sort_order)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            """CREATE TABLE IF NOT EXISTS weekly_assignments (id INT AUTO_INCREMENT PRIMARY KEY,week_no TINYINT NOT NULL,class_level ENUM('EASY','MODERATE','HARD') NOT NULL,passage_id VARCHAR(20) NOT NULL,UNIQUE KEY uniq_assign (week_no,class_level,passage_id),FOREIGN KEY (passage_id) REFERENCES passages(id) ON DELETE CASCADE) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            """CREATE TABLE IF NOT EXISTS passage_completions (id BIGINT AUTO_INCREMENT PRIMARY KEY,student_id VARCHAR(20) NOT NULL,week_no TINYINT NOT NULL,passage_id VARCHAR(20) NOT NULL,completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,UNIQUE KEY uniq_complete (student_id,week_no,passage_id),FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,FOREIGN KEY (passage_id) REFERENCES passages(id) ON DELETE CASCADE) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            """CREATE TABLE IF NOT EXISTS quiz_attempts (id BIGINT AUTO_INCREMENT PRIMARY KEY,student_id VARCHAR(20) NOT NULL,passage_id VARCHAR(20) NOT NULL,week_no TINYINT NOT NULL,score_pct INT NOT NULL DEFAULT 0,correct_count INT NOT NULL DEFAULT 0,total_count INT NOT NULL DEFAULT 0,difficulty_rating TINYINT NULL,short_answer_text TEXT NULL,reading_time VARCHAR(20) NULL,responses_json JSON NULL,submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,FOREIGN KEY (passage_id) REFERENCES passages(id) ON DELETE CASCADE,INDEX idx_progress (student_id, week_no)) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
        ]
        for sql in schema:
            cur.execute(sql)

        cur.execute("SHOW COLUMNS FROM students LIKE 'avatar_type'")
        if not cur.fetchone():
            cur.execute(
                "ALTER TABLE students ADD COLUMN avatar_type ENUM('initials','preset','upload') NOT NULL DEFAULT 'initials' AFTER pre_score"
            )

        cur.execute("SHOW COLUMNS FROM students LIKE 'avatar_value'")
        if not cur.fetchone():
            cur.execute(
                "ALTER TABLE students ADD COLUMN avatar_value MEDIUMTEXT NULL AFTER avatar_type"
            )

        def upsert_user(email, password, role):
            cur.execute("SELECT id FROM users WHERE email=%s", (email,))
            row = cur.fetchone()
            hashed = generate_password_hash(password)
            if row:
                cur.execute("UPDATE users SET password_hash=%s,role=%s,is_active=1 WHERE id=%s", (hashed, role, row["id"]))
                return row["id"]
            cur.execute("INSERT INTO users (email,password_hash,role,is_active) VALUES (%s,%s,%s,1)", (email, hashed, role))
            return cur.lastrowid

        for teacher in SEED_TEACHERS:
            upsert_user(teacher["email"], teacher["password"], "teacher")

        for student in SEED_STUDENTS:
            uid = upsert_user(student["email"], student["password"], "student")
            cur.execute(
                """
                INSERT INTO students (id,user_id,full_name,grade,section,class_level,pre_score)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE user_id=VALUES(user_id),full_name=VALUES(full_name),grade=VALUES(grade),section=VALUES(section),class_level=VALUES(class_level),pre_score=VALUES(pre_score)
                """,
                (student["id"], uid, student["name"], student["grade"], student["section"], normalize_class_level(student["class"]), int(student["pre"])),
            )

        cur.execute("SELECT COUNT(*) AS total FROM passages")
        if int(cur.fetchone()["total"]) == 0:
            cur.execute("SELECT id FROM users WHERE email=%s", ("ms.villanueva@pnhs.edu",))
            teacher_id = cur.fetchone()["id"]
            for p in SEED_PASSAGES:
                words = count_words(p["text"])
                cur.execute(
                    "INSERT INTO passages (id,title,genre,text,label,words,est_minutes,created_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (p["id"], p["title"], p["genre"], p["text"], normalize_class_level(p["label"]), words, estimate_minutes(words), teacher_id),
                )
                upsert_assessment(cur, p["id"], SEED_ASSESSMENTS.get(p["id"], {"questions": []}))

        cur.execute("SELECT COUNT(*) AS total FROM weekly_assignments")
        if int(cur.fetchone()["total"]) == 0:
            by_class = {
                "EASY": [p["id"] for p in SEED_PASSAGES if normalize_class_level(p["label"]) == "EASY"],
                "MODERATE": [p["id"] for p in SEED_PASSAGES if normalize_class_level(p["label"]) == "MODERATE"],
                "HARD": [p["id"] for p in SEED_PASSAGES if normalize_class_level(p["label"]) == "HARD"],
            }
            for week in range(1, TOTAL_PROGRAM_WEEKS + 1):
                for class_level, ids in by_class.items():
                    for pid in ids[:MAX_WEEKLY_PASSAGES_PER_CLASS]:
                        cur.execute("INSERT IGNORE INTO weekly_assignments (week_no,class_level,passage_id) VALUES (%s,%s,%s)", (week, class_level, pid))

@app.get("/")
def index():
    return jsonify({"name": "ReadWise API", "status": "running", "endpoints": ["/health", "/predict", "/api/health", "/api/auth/login", "/api/passages"]})


@app.get("/health")
def health():
    return jsonify({"status": "running", "model": "SVM ReadWise Prototype"})


@app.get("/api/health")
def api_health():
    with db_cursor() as (_, cur):
        cur.execute("SELECT 1")
        cur.fetchone()
    return api_ok({"api": "running", "db": "connected"})


@app.get("/api/debug/session")
def api_debug_session():
    user = current_user()
    raw_cookie = request.headers.get("Cookie") or ""
    raw_token = get_request_token() or ""
    return api_ok(
        {
            "hasCookieHeader": bool(raw_cookie),
            "cookieHeaderPreview": raw_cookie[:200],
            "hasTokenHeader": bool(raw_token),
            "tokenPreview": raw_token[:24],
            "sessionKeys": sorted(list(session.keys())),
            "sessionUserId": session.get("user_id"),
            "sessionRole": session.get("role"),
            "sessionStudentId": session.get("student_id"),
            "isAuthenticated": bool(user),
            "currentUser": serialize_user(user) if user else None,
            "origin": request.headers.get("Origin"),
            "referer": request.headers.get("Referer"),
        }
    )


@app.post("/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        return jsonify({"error": "No text provided."}), 400
    if len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text)) < MIN_WORDS:
        return jsonify({"error": "Passage too short. Minimum 30 words."}), 400

    cleaned = re.sub(r"\s+", " ", text.replace("\n", " ").replace("\t", " ")).strip().lower()
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text)
    sentences = [p.strip() for p in re.split(r"[.!?]+", text) if p.strip()]
    sentence_count = max(len(sentences), 1)
    word_count = len(words)
    avg_sentence_length = word_count / sentence_count
    avg_word_length = sum(len(w) for w in words) / max(word_count, 1)
    type_token_ratio = len({w.lower() for w in words}) / max(word_count, 1)

    surface = csr_matrix(np.asarray([[avg_sentence_length, avg_word_length, type_token_ratio, float(word_count)]], dtype=float))
    word_features = ARTIFACTS["word_vectorizer"].transform([cleaned])
    char_features = ARTIFACTS["char_vectorizer"].transform([cleaned])
    feature_matrix = hstack([word_features, char_features, surface], format="csr")

    prediction_code = ARTIFACTS["svm_model"].predict(feature_matrix)[0]
    predicted = ARTIFACTS["label_encoder"].inverse_transform([prediction_code])[0]
    predicted = normalize_class_level(predicted)

    scores = ARTIFACTS["svm_model"].decision_function(feature_matrix)
    values = np.asarray(scores[0] if np.ndim(scores) > 1 else scores, dtype=float)
    if values.ndim == 0:
        values = np.array([-float(values), float(values)])
    shifted = values - np.max(values)
    probs = np.exp(shifted)
    probs /= probs.sum()
    confidence = float(np.max(probs) * 100.0)

    return jsonify(
        {
            "label": predicted,
            "confidence": round(confidence, 1),
            "features": {
                "avg_sentence_length": round(avg_sentence_length, 2),
                "avg_word_length": round(avg_word_length, 2),
                "type_token_ratio": round(type_token_ratio, 3),
                "passage_length": int(word_count),
            },
        }
    )


@app.post("/api/auth/login")
def auth_login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")
    role = str(payload.get("role") or "").strip().lower()
    if not email or not password:
        return api_error("Email and password are required.", 400)

    with db_cursor(True) as (_, cur):
        cur.execute(
            """
            SELECT u.id,u.email,u.password_hash,u.role,u.is_active,
                   s.id AS student_id,s.full_name,s.grade,s.section,s.class_level,s.pre_score,
                   s.avatar_type,s.avatar_value
            FROM users u LEFT JOIN students s ON s.user_id=u.id
            WHERE u.email=%s
            """,
            (email,),
        )
        row = cur.fetchone()
        if not row or not row.get("is_active"):
            return api_error("Invalid credentials.", 401)
        if role and role != row["role"]:
            return api_error("Invalid credentials.", 401)
        if not check_password_hash(row["password_hash"], password):
            return api_error("Invalid credentials.", 401)
        token = secrets.token_hex(32)
        cur.execute("INSERT INTO auth_tokens (user_id, token) VALUES (%s, %s)", (row["id"], token))

    session.clear()
    session["user_id"] = row["id"]
    session["role"] = row["role"]
    if row.get("student_id"):
        session["student_id"] = row["student_id"]
    return api_ok({"user": serialize_user(row), "token": token})


@app.post("/api/auth/logout")
def auth_logout():
    token = get_request_token()
    if token:
        with db_cursor(True) as (_, cur):
            cur.execute("DELETE FROM auth_tokens WHERE token=%s", (token,))
    session.clear()
    return api_ok({"message": "Logged out."})


@app.get("/api/auth/me")
def auth_me():
    user, err = require_auth()
    if err:
        return err
    return api_ok({"user": serialize_user(user)})


@app.put("/api/student/profile/avatar")
def student_profile_avatar_update():
    user, err = require_role("student")
    if err:
        return err

    payload = request.get_json(silent=True) or {}
    avatar_type = normalize_avatar_type(payload.get("avatarType"))
    if not avatar_type:
        return api_error("avatarType must be initials, preset, or upload.", 400)

    try:
        avatar_value = sanitize_avatar_value(avatar_type, payload.get("avatarValue"))
    except ValueError as error:
        return api_error(str(error), 400)

    with db_cursor(True) as (_, cur):
        student = student_row(cur, user)
        if not student:
            return api_error("Student profile not found.", 404)

        cur.execute(
            "UPDATE students SET avatar_type=%s, avatar_value=%s WHERE id=%s",
            (avatar_type, avatar_value, student["id"]),
        )
        refreshed_user = fetch_user_by_id(cur, user["id"])

    return api_ok({"user": serialize_user(refreshed_user)})

@app.get("/api/passages")
def passages_list():
    user, err = require_auth()
    if err:
        return err
    del user
    with db_cursor(True) as (_, cur):
        cur.execute("SELECT id,title,genre,text,label,words,est_minutes,confidence FROM passages ORDER BY created_at DESC,id DESC")
        rows = cur.fetchall()
        passages = [serialize_passage(row) for row in rows]
        for passage in passages:
            passage["assessment"] = fetch_assessment(cur, passage["id"])
    return api_ok(passages)


@app.get("/api/passages/<passage_id>")
def passage_get(passage_id):
    user, err = require_auth()
    if err:
        return err
    del user
    with db_cursor(True) as (_, cur):
        cur.execute("SELECT id,title,genre,text,label,words,est_minutes,confidence FROM passages WHERE id=%s", (passage_id,))
        row = cur.fetchone()
        if not row:
            return api_error("Passage not found.", 404)
        passage = serialize_passage(row)
        passage["assessment"] = fetch_assessment(cur, passage_id)
    return api_ok(passage)


def save_passage(cur, payload, author_id, passage_id=None):
    title = str(payload.get("title") or "").strip()
    genre = str(payload.get("genre") or "Expository").strip() or "Expository"
    text = str(payload.get("text") or "").strip()
    label = normalize_class_level(payload.get("label") or "MODERATE")
    confidence = payload.get("confidence")
    if confidence in (None, ""):
        confidence = None
    else:
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = None

    if not title:
        raise ValueError("Passage title is required.")
    if not text:
        raise ValueError("Passage text is required.")

    words = count_words(text)
    minutes = estimate_minutes(words)
    assessment = payload.get("assessment") or {"questions": [], "shortAnswerPrompt": ""}

    if passage_id:
        cur.execute("SELECT id FROM passages WHERE id=%s", (passage_id,))
        if not cur.fetchone():
            raise LookupError("Passage not found.")
        cur.execute(
            "UPDATE passages SET title=%s,genre=%s,text=%s,label=%s,words=%s,est_minutes=%s,confidence=%s WHERE id=%s",
            (title, genre, text, label, words, minutes, confidence, passage_id),
        )
    else:
        cur.execute("SELECT COALESCE(MAX(CAST(SUBSTRING(id,2) AS UNSIGNED)),0) AS max_id FROM passages WHERE id REGEXP '^p[0-9]+$'")
        passage_id = f"p{int(cur.fetchone()['max_id']) + 1}"
        cur.execute(
            "INSERT INTO passages (id,title,genre,text,label,words,est_minutes,confidence,created_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (passage_id, title, genre, text, label, words, minutes, confidence, author_id),
        )

    upsert_assessment(cur, passage_id, assessment)
    cur.execute("SELECT id,title,genre,text,label,words,est_minutes,confidence FROM passages WHERE id=%s", (passage_id,))
    out = serialize_passage(cur.fetchone())
    out["assessment"] = fetch_assessment(cur, passage_id)
    return out


@app.post("/api/passages")
def passage_create():
    user, err = require_role("teacher")
    if err:
        return err
    payload = request.get_json(silent=True) or {}
    with db_cursor(True) as (_, cur):
        try:
            saved = save_passage(cur, payload, user["id"], None)
        except ValueError as e:
            return api_error(str(e), 400)
    return api_ok(saved, 201)


@app.put("/api/passages/<passage_id>")
def passage_update(passage_id):
    user, err = require_role("teacher")
    if err:
        return err
    payload = request.get_json(silent=True) or {}
    with db_cursor(True) as (_, cur):
        try:
            saved = save_passage(cur, payload, user["id"], passage_id)
        except LookupError:
            return api_error("Passage not found.", 404)
        except ValueError as e:
            return api_error(str(e), 400)
    return api_ok(saved)


@app.delete("/api/passages/<passage_id>")
def passage_delete(passage_id):
    user, err = require_role("teacher")
    if err:
        return err
    del user
    with db_cursor(True) as (_, cur):
        cur.execute("DELETE FROM passages WHERE id=%s", (passage_id,))
        if cur.rowcount == 0:
            return api_error("Passage not found.", 404)
    return api_ok({"deleted": True, "id": passage_id})

@app.get("/api/assignments")
def assignments_get():
    user, err = require_auth()
    if err:
        return err
    del user
    week = normalize_week(request.args.get("week"))
    with db_cursor(True) as (_, cur):
        return api_ok({"week": week, "assignments": get_weekly_assignments(cur, week)})


@app.post("/api/assignments")
def assignments_post():
    user, err = require_role("teacher")
    if err:
        return err
    del user
    payload = request.get_json(silent=True) or {}
    week = normalize_week(payload.get("week"))
    class_level = normalize_class_level(payload.get("classLevel"))
    passage_id = str(payload.get("passageId") or "").strip()
    if not passage_id:
        return api_error("passageId is required.", 400)

    with db_cursor(True) as (_, cur):
        cur.execute("SELECT label FROM passages WHERE id=%s", (passage_id,))
        row = cur.fetchone()
        if not row:
            return api_error("Passage not found.", 404)
        if normalize_class_level(row["label"]) != class_level:
            return api_error("Passage label does not match class level.", 400)

        cur.execute("SELECT 1 FROM weekly_assignments WHERE week_no=%s AND class_level=%s AND passage_id=%s", (week, class_level, passage_id))
        if cur.fetchone():
            return api_ok({"week": week, "assignments": get_weekly_assignments(cur, week), "message": "Passage already assigned."})

        cur.execute("SELECT COUNT(*) AS total FROM weekly_assignments WHERE week_no=%s AND class_level=%s", (week, class_level))
        if int(cur.fetchone()["total"]) >= MAX_WEEKLY_PASSAGES_PER_CLASS:
            return api_error("Class already has 5 passages this week.", 400)

        cur.execute("INSERT INTO weekly_assignments (week_no,class_level,passage_id) VALUES (%s,%s,%s)", (week, class_level, passage_id))
        return api_ok({"week": week, "assignments": get_weekly_assignments(cur, week), "message": "Passage assigned."})


@app.delete("/api/assignments")
def assignments_delete():
    user, err = require_role("teacher")
    if err:
        return err
    del user
    payload = request.get_json(silent=True) or {}
    week = normalize_week(payload.get("week"))
    class_level = normalize_class_level(payload.get("classLevel"))
    passage_id = str(payload.get("passageId") or "").strip()
    if not passage_id:
        return api_error("passageId is required.", 400)
    with db_cursor(True) as (_, cur):
        cur.execute("DELETE FROM weekly_assignments WHERE week_no=%s AND class_level=%s AND passage_id=%s", (week, class_level, passage_id))
        return api_ok({"week": week, "assignments": get_weekly_assignments(cur, week), "message": "Assignment removed."})


@app.get("/api/student/weekly-passages")
def student_weekly_passages():
    user, err = require_role("student")
    if err:
        return err
    week = normalize_week(request.args.get("week"))
    with db_cursor(True) as (_, cur):
        student = student_row(cur, user)
        if not student:
            return api_error("Student profile not found.", 404)
        class_level = normalize_class_level(student["class_level"])
        cur.execute(
            """
            SELECT p.id,p.title,p.genre,p.text,p.label,p.words,p.est_minutes,p.confidence
            FROM weekly_assignments wa JOIN passages p ON p.id=wa.passage_id
            WHERE wa.week_no=%s AND wa.class_level=%s
            ORDER BY wa.id
            """,
            (week, class_level),
        )
        passages = [serialize_passage(row) for row in cur.fetchall()]
    return api_ok({"week": week, "classLevel": class_level, "passages": passages})


@app.get("/api/student/completions")
def student_completions():
    user, err = require_role("student")
    if err:
        return err
    week = normalize_week(request.args.get("week"))
    with db_cursor(True) as (_, cur):
        student = student_row(cur, user)
        if not student:
            return api_error("Student profile not found.", 404)
        cur.execute("SELECT passage_id FROM passage_completions WHERE student_id=%s AND week_no=%s ORDER BY completed_at", (student["id"], week))
        ids = [row["passage_id"] for row in cur.fetchall()]
    return api_ok({"week": week, "completedPassageIds": ids})


@app.post("/api/student/attempts")
def student_attempts():
    user, err = require_role("student")
    if err:
        return err
    payload = request.get_json(silent=True) or {}
    week = normalize_week(payload.get("week"))
    passage_id = str(payload.get("passageId") or "").strip()
    if not passage_id:
        return api_error("passageId is required.", 400)

    score = int(payload.get("score") or 0)
    correct = int(payload.get("correct") or 0)
    total = int(payload.get("total") or 0)
    difficulty = payload.get("difficulty")
    try:
        difficulty = int(difficulty) if difficulty not in (None, "") else None
    except (TypeError, ValueError):
        difficulty = None
    if difficulty is not None:
        difficulty = max(1, min(5, difficulty))

    short_answer = str(payload.get("shortAnswer") or "").strip()
    reading_time = str(payload.get("readingTime") or "").strip()
    responses = payload.get("responses") if isinstance(payload.get("responses"), list) else []

    with db_cursor(True) as (_, cur):
        student = student_row(cur, user)
        if not student:
            return api_error("Student profile not found.", 404)
        class_level = normalize_class_level(student["class_level"])

        cur.execute("SELECT 1 FROM weekly_assignments WHERE week_no=%s AND class_level=%s AND passage_id=%s", (week, class_level, passage_id))
        if not cur.fetchone():
            return api_error("Passage is not assigned to this student for the selected week.", 400)

        cur.execute(
            """
            INSERT INTO quiz_attempts (
              student_id,passage_id,week_no,score_pct,correct_count,total_count,difficulty_rating,
              short_answer_text,reading_time,responses_json
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                student["id"],
                passage_id,
                week,
                max(0, min(100, score)),
                max(0, correct),
                max(0, total),
                difficulty,
                short_answer or None,
                reading_time or None,
                json.dumps(responses, ensure_ascii=False) if responses else None,
            ),
        )
        attempt_id = cur.lastrowid

        cur.execute(
            "INSERT INTO passage_completions (student_id,week_no,passage_id) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE completed_at=completed_at",
            (student["id"], week, passage_id),
        )

        cur.execute("SELECT passage_id FROM passage_completions WHERE student_id=%s AND week_no=%s ORDER BY completed_at", (student["id"], week))
        completed = [row["passage_id"] for row in cur.fetchall()]

    return api_ok({"attemptId": attempt_id, "week": week, "passageId": passage_id, "completedPassageIds": completed}, 201)


@app.get("/api/student/progress")
def student_progress():
    user, err = require_role("student")
    if err:
        return err
    with db_cursor(True) as (_, cur):
        student = student_row(cur, user)
        if not student:
            return api_error("Student profile not found.", 404)
        cur.execute(
            "SELECT week_no, ROUND(AVG(score_pct)) AS score FROM quiz_attempts WHERE student_id=%s GROUP BY week_no ORDER BY week_no",
            (student["id"],),
        )
        rows = cur.fetchall()

    progress = []
    for row in rows:
        score = int(row["score"] or 0)
        if score >= 75:
            recommendation, difficulty = "Step UP", "HARD"
        elif score >= 60:
            recommendation, difficulty = "Maintain", "MODERATE"
        else:
            recommendation, difficulty = "Step DOWN", "EASY"
        progress.append({"week": int(row["week_no"]), "score": score, "difficulty": difficulty, "recommendation": recommendation})
    return api_ok({"progress": progress})


@app.errorhandler(mysql.connector.Error)
def handle_mysql_error(_):
    return api_error("Database operation failed. Check MySQL configuration and service.", 500)


init_database()


if __name__ == "__main__":
    print("Loaded model artifacts from", MODEL_DIR)
    print(f"Connected to MySQL database '{DB_NAME}' on {DB_HOST}:{DB_PORT}")
    app.run(debug=True, host="127.0.0.1", port=5000)
