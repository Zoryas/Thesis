import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from flask import jsonify, request, session
from scipy.sparse import csr_matrix, hstack

from db import db_cursor

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "ml_model"
ARTIFACTS = {
    "svm_model": joblib.load(MODEL_DIR / "svm_model.pkl"),
    "word_vectorizer": joblib.load(MODEL_DIR / "word_vectorizer.pkl"),
    "char_vectorizer": joblib.load(MODEL_DIR / "char_vectorizer.pkl"),
    "label_encoder": joblib.load(MODEL_DIR / "label_encoder.pkl"),
}

QUESTION_TYPES_BY_DIFFICULTY = {
    "EASY": {"multiple_choice", "true_false"},
    "MODERATE": {"multiple_choice_harder", "true_false_modified", "sequence"},
    "DIFFICULT": {"fill_in_the_blanks", "identification", "enumeration"},
    "CUSTOM": {"custom"},
}

TOTAL_PROGRAM_WEEKS = 8
MIN_WORDS = 30
PRESET_AVATAR_PATTERN = re.compile(r"^/(?:[A-Za-z0-9._-]+/)?avatar/[A-Za-z0-9 _().-]+\.svg$")


def api_ok(data=None, status=200):
    return jsonify({"ok": True, "data": data}), status


def api_error(message, status=400):
    return jsonify({"ok": False, "error": message}), status


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
        "isDraft": bool(int(row.get("is_draft") or 0)),
    }


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


def fetch_user_by_id(cur, user_id):
    cur.execute(
        """
        SELECT u.id,u.email,u.role,u.is_active,
               s.id AS student_id,s.full_name,s.grade,s.section,s.class_level,s.pre_score,s.pre_assessment_completed,
               s.avatar_type,s.avatar_value
        FROM users u LEFT JOIN students s ON s.user_id=u.id
        WHERE u.id=%s
        """,
        (user_id,),
    )
    return cur.fetchone()


def current_user():
    uid = session.get("user_id")
    if uid:
        with db_cursor(True) as (_, cur):
            row = fetch_user_by_id(cur, uid)
            if row and row.get("is_active"):
                return row

    token = get_request_token()
    if token:
        with db_cursor(True) as (_, cur):
            cur.execute(
                """
                SELECT u.id,u.email,u.role,u.is_active,
                       s.id AS student_id,s.full_name,s.grade,s.section,
                       s.class_level,s.pre_score,s.pre_assessment_completed,s.avatar_type,s.avatar_value
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
            "preAssessmentCompleted": bool(int(row.get("pre_assessment_completed") or 0)),
            "avatarType": row.get("avatar_type") or "initials",
            "avatarValue": row.get("avatar_value") or "",
        }
    return {"id": row["id"], "email": row["email"], "role": row["role"], "student": student}


def student_row(cur, user):
    sid = user.get("student_id")
    if sid:
        cur.execute("SELECT id, full_name, grade, section, class_level, pre_score, pre_assessment_completed FROM students WHERE id=%s", (sid,))
    else:
        cur.execute("SELECT id, full_name, grade, section, class_level, pre_score, pre_assessment_completed FROM students WHERE user_id=%s", (user["id"],))
    return cur.fetchone()


def pre_assessment_completed(student):
    if not student:
        return False
    return bool(int(student.get("pre_assessment_completed") or 0))


def classify_pre_assessment_level(score):
    try:
        normalized_score = int(score)
    except (TypeError, ValueError):
        normalized_score = 0
    normalized_score = max(0, min(100, normalized_score))
    if normalized_score >= 70:
        return "HARD"
    if normalized_score >= 55:
        return "MODERATE"
    return "EASY"


def normalize_question_difficulty(value):
    level = str(value or "").strip().upper()
    if level == "MEDIUM":
        return "MODERATE"
    if level == "HARD":
        return "DIFFICULT"
    if level in QUESTION_TYPES_BY_DIFFICULTY:
        return level
    return "EASY"


def normalize_class_level(value):
    v = str(value or "").strip().upper()
    if v == "MEDIUM":
        return "MODERATE"
    if v == "DIFFICULT":
        return "HARD"
    return v if v in {"EASY", "MODERATE", "HARD"} else "EASY"


def map_passage_label_to_question_difficulty(label):
    class_level = normalize_class_level(label)
    return "DIFFICULT" if class_level == "HARD" else class_level


def display_question_difficulty(level):
    normalized = normalize_question_difficulty(level)
    return "Difficult" if normalized == "DIFFICULT" else normalized.title()


def normalize_string_list(values):
    if not isinstance(values, list):
        return []
    return [str(value).strip() for value in values if str(value).strip()]


def parse_delimited_answers(value, delimiter):
    return [item.strip() for item in str(value or "").split(delimiter) if item.strip()]


def parse_csv_assessment_questions(row, default_question_difficulty):
    questions = []
    for index in range(1, 11):
        prompt = str(row.get(f"q{index}_prompt") or "").strip()
        qtype = str(row.get(f"q{index}_type") or "").strip().lower()
        options_raw = str(row.get(f"q{index}_options") or "").strip()
        answer_index_raw = str(row.get(f"q{index}_answerindex") or "").strip()
        answer_key = str(row.get(f"q{index}_answerkey") or "").strip()
        answer_keys_raw = str(row.get(f"q{index}_answerkeys") or "").strip()

        if not prompt and not qtype and not options_raw and not answer_index_raw and not answer_key and not answer_keys_raw:
            continue

        question = {
            "difficulty": normalize_question_difficulty(default_question_difficulty),
            "type": qtype or "",
            "prompt": prompt,
        }

        if options_raw:
            question["options"] = parse_delimited_answers(options_raw, "|")

        if answer_index_raw:
            try:
                question["answerIndex"] = int(answer_index_raw)
            except (TypeError, ValueError):
                question["answerIndex"] = 0

        if answer_key:
            question["answerKey"] = answer_key

        if answer_keys_raw:
            delimiter = "|" if "|" in answer_keys_raw else ","
            question["answerKeys"] = parse_delimited_answers(answer_keys_raw, delimiter)

        questions.append(question)

    return questions


def normalize_assessment_payload(assessment, passage_label, allow_empty=False):
    payload = assessment if isinstance(assessment, dict) else {}
    raw_questions = payload.get("questions") if isinstance(payload.get("questions"), list) else []
    short_answer = str(payload.get("shortAnswerPrompt") or payload.get("shortAnswer") or "").strip()
    expected_difficulty = map_passage_label_to_question_difficulty(passage_label)
    allowed_types = QUESTION_TYPES_BY_DIFFICULTY[expected_difficulty]
    normalized_questions = []

    for index, raw_question in enumerate(raw_questions, start=1):
        question = raw_question if isinstance(raw_question, dict) else {}
        prompt = str(question.get("prompt") or question.get("q") or "").strip()
        if not prompt:
            raise ValueError(f"Question {index} is missing a prompt.")

        difficulty = normalize_question_difficulty(question.get("difficulty") or expected_difficulty)
        if difficulty != expected_difficulty:
            raise ValueError(
                f"Question {index} must use {display_question_difficulty(expected_difficulty)} difficulty."
            )

        question_type = str(question.get("type") or "").strip().lower()
        if not question_type:
            if expected_difficulty == "EASY":
                question_type = "multiple_choice"
            elif expected_difficulty == "MODERATE":
                question_type = "multiple_choice_harder"
            else:
                question_type = "fill_in_the_blanks"

        if question_type not in allowed_types:
            allowed_display = ", ".join(sorted(allowed_types))
            raise ValueError(
                f"Question {index} uses an invalid type for {display_question_difficulty(expected_difficulty)} passages. "
                f"Allowed types: {allowed_display}."
            )

        options = question.get("options") if isinstance(question.get("options"), list) else question.get("opts")
        options = [str(item).strip() for item in options] if isinstance(options, list) else []

        answer_keys = (
            normalize_string_list(question.get("answerKeys"))
            if isinstance(question.get("answerKeys"), list)
            else normalize_string_list(question.get("answer_keys"))
        )
        answer_key = str(question.get("answerKey") or question.get("answer_key") or question.get("answer") or "").strip()
        answer_index = question.get("answerIndex", question.get("ans", 0))
        try:
            answer_index = int(answer_index)
        except (TypeError, ValueError):
            answer_index = 0

        normalized_question = {
            "difficulty": difficulty,
            "type": question_type,
            "prompt": prompt,
            "options": [],
            "answerIndex": 0,
            "answerKey": "",
            "answerKeys": [],
        }

        if question_type in {"multiple_choice", "multiple_choice_harder"}:
            cleaned_options = [item for item in options[:4] if item]
            if len(cleaned_options) != 4:
                raise ValueError(f"Question {index} needs exactly 4 answer options.")
            if answer_index < 0 or answer_index > 3:
                raise ValueError(f"Question {index} must have a valid correct option.")
            normalized_question["options"] = cleaned_options
            normalized_question["answerIndex"] = answer_index
        elif question_type in {"true_false", "true_false_modified"}:
            normalized_question["answerKey"] = "false" if answer_key.lower() == "false" else "true"
            if question_type == "true_false_modified":
                if not answer_keys:
                    answer_keys = parse_delimited_answers(
                        question.get("correctionAnswer") or question.get("correction"),
                        "|",
                    )
                if normalized_question["answerKey"] == "false" and not answer_keys:
                    raise ValueError(
                        f"Question {index} needs the corrected answer for a false statement."
                    )
                normalized_question["answerKeys"] = answer_keys
        elif question_type == "sequence":
            cleaned_options = [item for item in options if item]
            if len(cleaned_options) < 3:
                raise ValueError(f"Question {index} needs at least 3 sequence items.")
            if not answer_keys:
                answer_keys = parse_delimited_answers(answer_key, ",")
            if len(answer_keys) < 3:
                raise ValueError(f"Question {index} needs a complete sequence answer.")
            normalized_question["options"] = cleaned_options
            normalized_question["answerKeys"] = answer_keys
        elif question_type == "enumeration":
            if not answer_keys:
                answer_keys = parse_delimited_answers(answer_key, ",")
            if len(answer_keys) < 2:
                raise ValueError(f"Question {index} needs at least 2 expected answers.")
            normalized_question["answerKeys"] = answer_keys
        else:
            if not answer_keys:
                answer_keys = parse_delimited_answers(answer_key, "|")
            if not answer_keys:
                raise ValueError(f"Question {index} needs at least 1 accepted answer.")
            normalized_question["answerKeys"] = answer_keys

        normalized_questions.append(normalized_question)

    if not normalized_questions and not allow_empty:
        raise ValueError("Add at least 1 complete assessment question.")

    return {"questions": normalized_questions, "shortAnswerPrompt": short_answer}


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


def parse_program_start_date(value):
    if hasattr(value, "strftime"):
        return value
    raw = str(value or "").strip()
    if not raw:
        return datetime.now(timezone.utc).date()
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return None


def compute_active_week_from_start(program_start_date):
    start_date = parse_program_start_date(program_start_date)
    today = datetime.now(timezone.utc).date()
    delta_days = (today - start_date).days
    if delta_days <= 0:
        return 1
    computed = (delta_days // 7) + 1
    return min(TOTAL_PROGRAM_WEEKS, max(1, computed))


def get_program_settings(cur):
    cur.execute(
        "SELECT id, program_start_date, manual_override_week, updated_by, updated_at FROM program_settings WHERE id=1"
    )
    row = cur.fetchone()
    if not row:
        return None
    override_week = row.get("manual_override_week")
    active_week = normalize_week(override_week) if override_week is not None else compute_active_week_from_start(row.get("program_start_date"))
    return {
        "programStartDate": row.get("program_start_date").isoformat() if row.get("program_start_date") else None,
        "manualOverrideWeek": int(override_week) if override_week is not None else None,
        "activeWeek": active_week,
        "updatedBy": row.get("updated_by"),
        "updatedAt": row.get("updated_at").isoformat() if row.get("updated_at") else None,
    }


def count_words(text):
    return len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", str(text or "")))


def estimate_minutes(words):
    return max(1, int((words or 0 + 79) // 80))


def average_numbers(values):
    cleaned = []
    for value in values:
        if value is None:
            continue
        try:
            cleaned.append(float(value))
        except (TypeError, ValueError):
            continue
    if not cleaned:
        return None
    return int(round(sum(cleaned) / len(cleaned)))


def build_prediction_response(text):
    raw_text = str(text or "").strip()
    if not raw_text:
        raise ValueError("No text provided.")

    word_count = count_words(raw_text)
    if word_count < MIN_WORDS:
        raise ValueError("Passage too short. Minimum 30 words.")

    cleaned = re.sub(r"\s+", " ", raw_text.replace("\n", " ").replace("\t", " ")).strip().lower()
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", raw_text)
    sentences = [part.strip() for part in re.split(r"[.!?]+", raw_text) if part.strip()]
    sentence_count = max(len(sentences), 1)
    avg_sentence_length = word_count / sentence_count
    avg_word_length = sum(len(word) for word in words) / max(word_count, 1)
    type_token_ratio = len({word.lower() for word in words}) / max(word_count, 1)

    surface = csr_matrix(
        np.asarray([[avg_sentence_length, avg_word_length, type_token_ratio, float(word_count)]], dtype=float)
    )
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

    return {
        "label": predicted,
        "confidence": round(confidence, 1),
        "features": {
            "avg_sentence_length": round(avg_sentence_length, 2),
            "avg_word_length": round(avg_word_length, 2),
            "type_token_ratio": round(type_token_ratio, 3),
            "passage_length": int(word_count),
        },
    }


def recommendation_for_score(score):
    normalized_score = int(score or 0)
    if normalized_score >= 75:
        return "Step UP", "HARD"
    if normalized_score >= 60:
        return "Maintain", "MODERATE"
    return "Step DOWN", "EASY"


def fetch_student_progress(cur, student_id):
    cur.execute(
        "SELECT week_no, ROUND(AVG(score_pct)) AS score FROM quiz_attempts WHERE student_id=%s GROUP BY week_no ORDER BY week_no",
        (student_id,),
    )
    rows = cur.fetchall()
    progress = []
    for row in rows:
        score = int(row["score"] or 0)
        recommendation, difficulty = recommendation_for_score(score)
        progress.append(
            {
                "week": int(row["week_no"]),
                "score": score,
                "difficulty": difficulty,
                "recommendation": recommendation,
            }
        )

    if progress:
        return progress

    fallback_progress = {
        "s1": [
            {"week": 1, "score": 55, "difficulty": "HARD", "recommendation": "Maintain"},
            {"week": 2, "score": 48, "difficulty": "HARD", "recommendation": "Step DOWN to MODERATE"},
            {"week": 3, "score": 65, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 4, "score": 71, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 5, "score": 74, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 6, "score": 78, "difficulty": "MODERATE", "recommendation": "Step UP to HARD"},
        ],
        "s2": [
            {"week": 1, "score": 70, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 2, "score": 75, "difficulty": "MODERATE", "recommendation": "Step UP to HARD"},
            {"week": 3, "score": 68, "difficulty": "HARD", "recommendation": "Maintain"},
            {"week": 4, "score": 72, "difficulty": "HARD", "recommendation": "Maintain"},
            {"week": 5, "score": 76, "difficulty": "HARD", "recommendation": "Maintain"},
            {"week": 6, "score": 79, "difficulty": "HARD", "recommendation": "Maintain"},
        ],
        "s3": [
            {"week": 1, "score": 42, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 2, "score": 50, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 3, "score": 55, "difficulty": "EASY", "recommendation": "Step UP to MODERATE"},
            {"week": 4, "score": 48, "difficulty": "MODERATE", "recommendation": "Step DOWN to EASY"},
            {"week": 5, "score": 57, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 6, "score": 62, "difficulty": "EASY", "recommendation": "Step UP to MODERATE"},
        ],
        "s4": [
            {"week": 1, "score": 35, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 2, "score": 39, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 3, "score": 44, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 4, "score": 49, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 5, "score": 53, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 6, "score": 58, "difficulty": "EASY", "recommendation": "Step UP to MODERATE"},
        ],
        "s5": [
            {"week": 1, "score": 63, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 2, "score": 67, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 3, "score": 72, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 4, "score": 78, "difficulty": "MODERATE", "recommendation": "Step UP to HARD"},
            {"week": 5, "score": 70, "difficulty": "HARD", "recommendation": "Maintain"},
            {"week": 6, "score": 74, "difficulty": "HARD", "recommendation": "Maintain"},
        ],
        "s6": [
            {"week": 1, "score": 76, "difficulty": "HARD", "recommendation": "Maintain"},
            {"week": 2, "score": 82, "difficulty": "HARD", "recommendation": "Maintain"},
            {"week": 3, "score": 79, "difficulty": "HARD", "recommendation": "Maintain"},
            {"week": 4, "score": 85, "difficulty": "HARD", "recommendation": "Maintain"},
            {"week": 5, "score": 83, "difficulty": "HARD", "recommendation": "Maintain"},
            {"week": 6, "score": 87, "difficulty": "HARD", "recommendation": "Maintain"},
        ],
        "s7": [
            {"week": 1, "score": 40, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 2, "score": 47, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 3, "score": 53, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 4, "score": 58, "difficulty": "EASY", "recommendation": "Step UP to MODERATE"},
            {"week": 5, "score": 52, "difficulty": "MODERATE", "recommendation": "Step DOWN to EASY"},
            {"week": 6, "score": 60, "difficulty": "EASY", "recommendation": "Step UP to MODERATE"},
        ],
        "s8": [
            {"week": 1, "score": 57, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 2, "score": 61, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 3, "score": 66, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 4, "score": 70, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 5, "score": 73, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 6, "score": 77, "difficulty": "MODERATE", "recommendation": "Step UP to HARD"},
        ],
        "s9": [
            {"week": 1, "score": 71, "difficulty": "HARD", "recommendation": "Maintain"},
            {"week": 2, "score": 75, "difficulty": "HARD", "recommendation": "Maintain"},
            {"week": 3, "score": 80, "difficulty": "HARD", "recommendation": "Maintain"},
            {"week": 4, "score": 77, "difficulty": "HARD", "recommendation": "Maintain"},
            {"week": 5, "score": 82, "difficulty": "HARD", "recommendation": "Maintain"},
            {"week": 6, "score": 84, "difficulty": "HARD", "recommendation": "Maintain"},
        ],
        "s10": [
            {"week": 1, "score": 38, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 2, "score": 43, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 3, "score": 47, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 4, "score": 52, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 5, "score": 59, "difficulty": "EASY", "recommendation": "Step UP to MODERATE"},
            {"week": 6, "score": 67, "difficulty": "MODERATE", "recommendation": "Maintain"},
        ],
        "s11": [
            {"week": 1, "score": 36, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 2, "score": 41, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 3, "score": 45, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 4, "score": 50, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 5, "score": 55, "difficulty": "EASY", "recommendation": "Step UP to MODERATE"},
            {"week": 6, "score": 61, "difficulty": "MODERATE", "recommendation": "Maintain"},
        ],
        "s12": [
            {"week": 1, "score": 82, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 2, "score": 85, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 3, "score": 88, "difficulty": "EASY", "recommendation": "Step UP to MODERATE"},
            {"week": 4, "score": 80, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 5, "score": 83, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 6, "score": 86, "difficulty": "MODERATE", "recommendation": "Step UP to HARD"},
        ],
        "s13": [
            {"week": 1, "score": 66, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 2, "score": 69, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 3, "score": 73, "difficulty": "MODERATE", "recommendation": "Step UP to HARD"},
            {"week": 4, "score": 70, "difficulty": "HARD", "recommendation": "Maintain"},
            {"week": 5, "score": 68, "difficulty": "HARD", "recommendation": "Maintain"},
            {"week": 6, "score": 74, "difficulty": "HARD", "recommendation": "Maintain"},
        ],
        "s14": [
            {"week": 1, "score": 52, "difficulty": "HARD", "recommendation": "Maintain"},
            {"week": 2, "score": 49, "difficulty": "HARD", "recommendation": "Step DOWN to MODERATE"},
            {"week": 3, "score": 63, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 4, "score": 58, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 5, "score": 61, "difficulty": "MODERATE", "recommendation": "Maintain"},
            {"week": 6, "score": 65, "difficulty": "MODERATE", "recommendation": "Step UP to HARD"},
        ],
        "s15": [
            {"week": 1, "score": 34, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 2, "score": 39, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 3, "score": 44, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 4, "score": 49, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 5, "score": 54, "difficulty": "EASY", "recommendation": "Maintain"},
            {"week": 6, "score": 60, "difficulty": "EASY", "recommendation": "Step UP to MODERATE"},
        ],
    }
    return fallback_progress.get(str(student_id), [])


def fetch_teacher_student_summaries(cur):
    cur.execute(
        """
        SELECT s.id,s.full_name,s.grade,s.section,s.class_level,s.pre_score,s.pre_assessment_completed,u.email
        FROM students s
        JOIN users u ON u.id=s.user_id
        ORDER BY s.full_name ASC
        """
    )
    students = []
    for row in cur.fetchall():
        progress = fetch_student_progress(cur, row["id"])
        latest = progress[-1] if progress else None
        cur.execute(
            "SELECT COUNT(*) AS total FROM quiz_attempts WHERE student_id=%s AND short_answer_text IS NOT NULL AND teacher_score IS NULL",
            (row["id"],),
        )
        pending_reviews = int(cur.fetchone()["total"] or 0)
        students.append(
            {
                "id": row["id"],
                "name": row["full_name"],
                "email": row["email"],
                "grade": row["grade"],
                "section": row["section"],
                "classLevel": row["class_level"],
                "preScore": int(row["pre_score"] or 0),
                "preAssessmentCompleted": bool(int(row["pre_assessment_completed"] or 0)),
                "latestScore": latest["score"] if latest else None,
                "latestWeek": latest["week"] if latest else None,
                "latestRecommendation": latest["recommendation"] if latest else None,
                "latestDifficulty": latest["difficulty"] if latest else None,
                "recentScores": [item["score"] for item in progress[-2:]],
                "progress": progress,
                "pendingReviewCount": pending_reviews,
            }
        )
    return students


def get_stagnation_details(progress):
    if len(progress) < 2:
        return False, ""

    previous = progress[-2]
    latest = progress[-1]
    if int(latest["score"]) > int(previous["score"]):
        return False, ""

    return (
        True,
        f"No improvement from Week {previous['week']} ({previous['score']}%) "
        f"to Week {latest['week']} ({latest['score']})."
    )


def build_report_status(student, is_stagnant):
    if not student["preAssessmentCompleted"]:
        return "Pre-Assessment Pending", "hard"
    if student["latestScore"] is None:
        return "Awaiting Weekly Submission", "primary"
    if int(student["latestWeek"] or 0) >= TOTAL_PROGRAM_WEEKS:
        return f"Week {TOTAL_PROGRAM_WEEKS} Recorded", "success"
    if is_stagnant:
        return "Stagnant", "hard"
    return "Improving", "easy"


def build_teacher_report_summary(cur, active_week):
    students = fetch_teacher_student_summaries(cur)
    report_rows = []
    for student in students:
        is_stagnant, stagnant_reason = get_stagnation_details(student["progress"])
        pre_score = int(student["preScore"] or 0) if student["preAssessmentCompleted"] else None
        latest_score = student["latestScore"]
        improvement = None
        if pre_score is not None and latest_score is not None:
            improvement = int(latest_score) - int(pre_score)
        status_label, status_tone = build_report_status(student, is_stagnant)
        report_rows.append(
            {
                "id": student["id"],
                "name": student["name"],
                "email": student["email"],
                "grade": student["grade"],
                "section": student["section"],
                "classLevel": student["classLevel"],
                "preScore": pre_score,
                "preAssessmentCompleted": student["preAssessmentCompleted"],
                "latestScore": latest_score,
                "latestWeek": student["latestWeek"],
                "latestRecommendation": student["latestRecommendation"],
                "latestDifficulty": student["latestDifficulty"],
                "improvement": improvement,
                "statusLabel": status_label,
                "statusTone": status_tone,
                "isStagnant": is_stagnant,
                "stagnantReason": stagnant_reason,
                "progress": student["progress"],
            }
        )

    completion_base = max(1, len(report_rows) * TOTAL_PROGRAM_WEEKS)
    completion_value = sum(min(TOTAL_PROGRAM_WEEKS, int(student["latestWeek"] or 0)) for student in report_rows)
    completion_percent = int(round((completion_value / completion_base) * 100)) if report_rows else 0
    stagnant_students = [student for student in report_rows if student["isStagnant"]]

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "activeWeek": normalize_week(active_week),
        "studentCount": len(report_rows),
        "preAverage": average_numbers(
            student["preScore"] for student in report_rows if student["preAssessmentCompleted"]
        ),
        "currentAverage": average_numbers(student["latestScore"] for student in report_rows),
        "completionPercent": completion_percent,
        "stagnantCount": len(stagnant_students),
        "stagnantStudents": stagnant_students,
        "students": report_rows,
    }


def fetch_pending_short_answer(cur, student_id):
    cur.execute(
        """
        SELECT qa.id, qa.passage_id,qa.short_answer_text,qa.submitted_at,p.title,p.label,a.short_answer_prompt
        FROM quiz_attempts qa
        JOIN passages p ON p.id=qa.passage_id
        LEFT JOIN assessments a ON a.passage_id=qa.passage_id
        WHERE qa.student_id=%s
          AND qa.short_answer_text IS NOT NULL
          AND qa.teacher_score IS NULL
        ORDER BY qa.submitted_at DESC
        LIMIT 1
        """,
        (student_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "attemptId": int(row["id"]),
        "passageId": row["passage_id"],
        "passageTitle": row["title"],
        "label": row["label"],
        "prompt": row.get("short_answer_prompt") or "",
        "response": row.get("short_answer_text") or "",
        "submittedAt": row["submitted_at"].isoformat() if row.get("submitted_at") else None,
    }


def fetch_pending_short_answers(cur, student_id):
    cur.execute(
        """
        SELECT qa.id,qa.passage_id,qa.week_no,qa.short_answer_text,qa.submitted_at,
               p.title,p.label,a.short_answer_prompt
        FROM quiz_attempts qa
        JOIN passages p ON p.id=qa.passage_id
        LEFT JOIN assessments a ON a.passage_id=qa.passage_id
        WHERE qa.student_id=%s
          AND qa.short_answer_text IS NOT NULL
          AND qa.teacher_score IS NULL
        ORDER BY qa.submitted_at DESC, qa.id DESC
        """,
        (student_id,),
    )
    rows = cur.fetchall()
    items = []
    for row in rows:
        items.append(
            {
                "attemptId": int(row["id"]),
                "passageId": row["passage_id"],
                "passageTitle": row["title"],
                "week": int(row["week_no"]),
                "label": row["label"],
                "prompt": row.get("short_answer_prompt") or "",
                "response": row.get("short_answer_text") or "",
                "submittedAt": row["submitted_at"].isoformat() if row.get("submitted_at") else None,
            }
        )
    return items
