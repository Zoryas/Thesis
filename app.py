
import csv
from contextlib import contextmanager
from datetime import datetime, timezone
from io import StringIO
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
PRESET_AVATAR_PATTERN = re.compile(r"^/(?:[A-Za-z0-9._-]+/)?avatar/[A-Za-z0-9 _().-]+\.svg$")

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
    {"id": "s4", "email": "new.student@pnhs.edu", "password": "password123", "name": "New Student", "grade": "7", "section": "Sampaguita", "class": "EASY", "pre": 0},
    {"id": "s5", "email": "lea.garcia@pnhs.edu", "password": "password123", "name": "Lea Garcia", "grade": "7", "section": "Rosal", "class": "MODERATE", "pre": 64},
    {"id": "s6", "email": "paolo.mendoza@pnhs.edu", "password": "password123", "name": "Paolo Mendoza", "grade": "7", "section": "Rosal", "class": "HARD", "pre": 81},
    {"id": "s7", "email": "trisha.navarro@pnhs.edu", "password": "password123", "name": "Trisha Navarro", "grade": "7", "section": "Rosal", "class": "EASY", "pre": 43},
    {"id": "s8", "email": "adrian.lopez@pnhs.edu", "password": "password123", "name": "Adrian Lopez", "grade": "7", "section": "Makahiya", "class": "MODERATE", "pre": 59},
    {"id": "s9", "email": "bea.cortez@pnhs.edu", "password": "password123", "name": "Bea Cortez", "grade": "7", "section": "Makahiya", "class": "HARD", "pre": 74},
    {"id": "s10", "email": "noah.flores@pnhs.edu", "password": "password123", "name": "Noah Flores", "grade": "7", "section": "Makahiya", "class": "EASY", "pre": 0},
    {"id": "s11", "email": "jamie.ong@pnhs.edu", "password": "password123", "name": "Jamie Ong", "grade": "7", "section": "Sampaguita", "class": "EASY", "pre": 0},
    {
    "id": "s12",
    "email": "alex.cruz@pnhs.edu",
    "password": "password123",
    "name": "Alex Cruz",
    "grade": "7",
    "section": "Rosal",
    "class": "EASY",
    "pre": 0
}

]

SEED_PASSAGES = [
    {"id": "p1", "title": "The Water Cycle", "genre": "Expository", "label": "EASY", "text": "Water evaporates, condenses into clouds, and returns as rain."},
    {"id": "p2", "title": "The Life of Jose Rizal", "genre": "Narrative", "label": "MODERATE", "text": "Jose Rizal wrote novels that inspired Filipino nationalism."},
    {"id": "p3", "title": "Climate Change and Its Effects", "genre": "Expository", "label": "HARD", "text": "Climate change increases risks like stronger storms and sea-level rise."},
    {"id": "p4", "title": "The Little Prince Summary", "genre": "Narrative", "label": "EASY", "text": "The Little Prince teaches readers about friendship and love."},
    {"id": "p5", "title": "Philippine Biodiversity", "genre": "Expository", "label": "MODERATE", "text": "The Philippines has many endemic species that need protection."},
    {"id": "p6", "title": "Constitutional Rights of Citizens", "genre": "Expository", "label": "HARD", "text": "The Constitution protects rights like due process and free expression."},
    {"id": "p7", "title": "The School Garden", "genre": "Narrative", "label": "EASY", "text": "Our class planted tomatoes and pechay in the school garden. We watered them every morning and removed weeds after lunch. After two months, we harvested enough vegetables to share with the canteen."},
    {"id": "p8", "title": "A Day at the Library", "genre": "Narrative", "label": "EASY", "text": "Maria visited the school library to find books about volcanoes. The librarian helped her choose three books and one magazine. She copied important notes in her notebook and returned the books before going home."},
    {"id": "p9", "title": "Why We Wash Hands", "genre": "Expository", "label": "EASY", "text": "Washing hands with soap removes dirt and germs. We should wash before eating, after using the restroom, and after playing outside. Clean hands help prevent cough, colds, and stomach sickness."},
    {"id": "p10", "title": "The Rice Plant", "genre": "Expository", "label": "EASY", "text": "Farmers prepare the field before planting rice seedlings. The plants grow best with enough sunlight and water. After several months, the grains turn golden and are ready to harvest and dry."},
    {"id": "p11", "title": "Typhoon Preparedness at Home", "genre": "Expository", "label": "MODERATE", "text": "Families can reduce typhoon risks by preparing emergency kits, securing important documents, and identifying safe evacuation routes. Listening to weather bulletins and following local government advisories helps communities respond quickly when storms intensify."},
    {"id": "p12", "title": "The Story of Lapu-Lapu", "genre": "Narrative", "label": "MODERATE", "text": "Lapu-Lapu, a chieftain of Mactan, became known for resisting foreign forces during the Battle of Mactan in 1521. His leadership is remembered as a symbol of courage, local sovereignty, and early resistance in Philippine history."},
    {"id": "p13", "title": "Mangrove Forests and Coastal Protection", "genre": "Expository", "label": "MODERATE", "text": "Mangrove forests protect shorelines by reducing wave energy and helping prevent soil erosion. Their roots also serve as breeding grounds for fish and crabs. Conserving mangroves supports both biodiversity and coastal livelihoods."},
    {"id": "p14", "title": "Digital Citizenship and Online Safety", "genre": "Expository", "label": "HARD", "text": "Responsible digital citizenship involves evaluating online sources, protecting personal data, and communicating respectfully across platforms. Learners should recognize misinformation patterns, report harmful content, and use privacy controls to reduce exposure to cyber threats."},
    {"id": "p15", "title": "Renewable Energy Choices for Communities", "genre": "Expository", "label": "HARD", "text": "Community energy planning requires balancing environmental benefits, infrastructure costs, and long-term reliability. While solar and wind reduce carbon emissions, policy design, grid modernization, and storage technology influence whether transitions remain equitable and sustainable."},
    {"id": "p16", "title": "Constitutional Checks and Balances", "genre": "Expository", "label": "HARD", "text": "Checks and balances distribute governmental authority across branches so no institution can dominate decision-making. Judicial review, legislative oversight, and executive veto powers create procedural friction intended to protect constitutional order and civil liberties."},
]

def seed_mc(difficulty, prompt, options, answer_index):
    return {
        "difficulty": difficulty,
        "type": "multiple_choice" if difficulty == "EASY" else "multiple_choice_harder",
        "prompt": prompt,
        "options": options,
        "answerIndex": answer_index,
    }


def seed_tf(difficulty, prompt, answer_key):
    return {
        "difficulty": difficulty,
        "type": "true_false" if difficulty == "EASY" else "true_false_modified",
        "prompt": prompt,
        "answerKey": answer_key,
    }


def seed_sequence(prompt, answer_keys):
    return {
        "difficulty": "MODERATE",
        "type": "sequence",
        "prompt": prompt,
        "options": list(answer_keys),
        "answerKeys": list(answer_keys),
    }


def seed_identification(prompt, answer_keys):
    return {
        "difficulty": "DIFFICULT",
        "type": "identification",
        "prompt": prompt,
        "answerKeys": list(answer_keys),
    }


def seed_fill_blank(prompt, answer_keys):
    return {
        "difficulty": "DIFFICULT",
        "type": "fill_in_the_blanks",
        "prompt": prompt,
        "answerKeys": list(answer_keys),
    }


def seed_enumeration(prompt, answer_keys):
    return {
        "difficulty": "DIFFICULT",
        "type": "enumeration",
        "prompt": prompt,
        "answerKeys": list(answer_keys),
    }


SEED_ASSESSMENTS = {
    "p1": {"questions": [
        seed_mc("EASY", "What process changes liquid water into water vapor?", ["Condensation", "Evaporation", "Runoff", "Precipitation"], 1),
        seed_tf("EASY", "Clouds form when water vapor cools and condenses.", "true"),
        seed_mc("EASY", "What do we call water that soaks into the ground?", ["Runoff", "Precipitation", "Groundwater", "Fog"], 2),
    ], "shortAnswerPrompt": ""},
    "p2": {"questions": [
        seed_mc("MODERATE", "Where was Jose Rizal born?", ["Manila", "Calamba, Laguna", "Baguio", "Cebu"], 1),
        seed_tf("MODERATE", "Rizal continued some of his studies in Spain.", "true"),
        seed_sequence("Arrange these events from Rizal's life in the order they appear in the passage.", ["Studied at Ateneo Municipal", "Pursued medicine and studies abroad", "Published Noli Me Tangere and El Filibusterismo"]),
    ], "shortAnswerPrompt": ""},
    "p3": {"questions": [
        seed_identification("Which greenhouse gas is specifically named in the passage?", ["carbon dioxide", "co2"]),
        seed_fill_blank("The greenhouse effect traps heat in the ______.", ["atmosphere"]),
        seed_enumeration("Name two climate-related risks mentioned in the passage.", ["sea-level rise", "stronger tropical cyclones"]),
    ], "shortAnswerPrompt": "In your own words, explain one effect of climate change on the Philippines."},
    "p4": {"questions": [
        seed_mc("EASY", "What lesson does the fox teach the little prince?", ["Money solves problems", "One sees clearly only with the heart", "Adults are always right", "Travel is better than friendship"], 1),
        seed_tf("EASY", "The little prince meets the pilot in the desert.", "true"),
        seed_mc("EASY", "What living thing does the little prince care for on his home planet?", ["A tree", "A fox", "A single rose", "A sheep"], 2),
    ], "shortAnswerPrompt": ""},
    "p5": {"questions": [
        seed_mc("MODERATE", "The Philippines is identified as one of how many megadiverse countries?", ["10", "17", "25", "30"], 1),
        seed_tf("MODERATE", "The Philippine eagle is an endemic species mentioned in the passage.", "true"),
        seed_sequence("Arrange these ecosystems in the same order used in the passage.", ["Tropical rainforests", "Mangroves", "Coral reefs"]),
    ], "shortAnswerPrompt": ""},
    "p6": {"questions": [
        seed_identification("Which article of the Constitution contains the Bill of Rights?", ["article iii", "article 3", "iii"]),
        seed_fill_blank("No person shall be deprived of life, liberty, or property without ______ process of law.", ["due", "due process"]),
        seed_enumeration("Name two rights mentioned in the passage.", ["freedom of speech", "right to counsel"]),
    ], "shortAnswerPrompt": "Explain what due process of law means in your own words."},
    "p7": {"questions": [
        seed_mc("EASY", "What vegetables did the class plant in the school garden?", ["Tomatoes and pechay", "Eggplant and corn", "Onions and garlic", "Cabbage and carrots"], 0),
        seed_tf("EASY", "The class harvested the vegetables after two months.", "true"),
        seed_mc("EASY", "Who received some of the harvested vegetables?", ["The principal", "The librarian", "The canteen", "The barangay captain"], 2),
    ], "shortAnswerPrompt": ""},
    "p8": {"questions": [
        seed_mc("EASY", "Why did Maria visit the school library?", ["To find books about volcanoes", "To play games", "To practice singing", "To buy school supplies"], 0),
        seed_tf("EASY", "Maria returned the books before going home.", "true"),
        seed_mc("EASY", "Where did Maria write her important notes?", ["On a poster", "In her notebook", "On the wall", "In a newspaper"], 1),
    ], "shortAnswerPrompt": ""},
    "p9": {"questions": [
        seed_mc("EASY", "What removes dirt and germs from our hands?", ["Soap", "Oil", "Dust", "Paper"], 0),
        seed_tf("EASY", "Clean hands can help prevent stomach sickness.", "true"),
        seed_mc("EASY", "When should we wash our hands?", ["Only after sleeping", "Before eating and after using the restroom", "Only on weekends", "Only after class pictures"], 1),
    ], "shortAnswerPrompt": ""},
    "p10": {"questions": [
        seed_mc("EASY", "What do farmers plant in the field?", ["Rice seedlings", "Mango trees", "Corn cobs", "Coconut shells"], 0),
        seed_tf("EASY", "Rice plants grow best without water.", "false"),
        seed_mc("EASY", "What happens to the grains before harvest?", ["They turn golden", "They become blue", "They disappear", "They float away"], 0),
    ], "shortAnswerPrompt": ""},
    "p11": {"questions": [
        seed_mc("MODERATE", "Which action helps families prepare for stronger storms?", ["Ignoring local warnings", "Preparing emergency kits", "Leaving documents outside", "Waiting for rumors"], 1),
        seed_tf("MODERATE", "Listening to weather bulletins can help communities respond quickly.", "true"),
        seed_sequence("Arrange these preparedness actions in a practical order.", ["Prepare an emergency kit", "Secure important documents", "Review evacuation routes"]),
    ], "shortAnswerPrompt": ""},
    "p12": {"questions": [
        seed_mc("MODERATE", "For what is Lapu-Lapu remembered in the passage?", ["Writing a constitution", "Leading resistance in Mactan", "Serving as governor-general", "Building a Spanish fort"], 1),
        seed_tf("MODERATE", "The passage presents Lapu-Lapu as a symbol of courage and local sovereignty.", "true"),
        seed_sequence("Arrange these events in the order described in the passage.", ["Foreign forces arrived in Mactan", "The Battle of Mactan happened in 1521", "Lapu-Lapu was remembered as a symbol of resistance"]),
    ], "shortAnswerPrompt": ""},
    "p13": {"questions": [
        seed_mc("MODERATE", "What do mangrove roots provide for fish and crabs?", ["A place to dry", "Breeding grounds", "More waves", "Less food"], 1),
        seed_tf("MODERATE", "Mangroves help reduce soil erosion.", "true"),
        seed_sequence("Arrange these mangrove benefits in the same order used in the passage.", ["Reduce wave energy", "Help prevent soil erosion", "Support fish and crab breeding grounds"]),
    ], "shortAnswerPrompt": ""},
    "p14": {"questions": [
        seed_identification("What should students protect when practicing responsible digital citizenship?", ["personal data", "personal information"]),
        seed_fill_blank("Students should use privacy ______ to reduce exposure to cyber threats.", ["controls", "settings"]),
        seed_enumeration("Name two responsible online actions mentioned in the passage.", ["evaluating online sources", "reporting harmful content"]),
    ], "shortAnswerPrompt": "Give one example of how a student can verify online information before sharing it."},
    "p15": {"questions": [
        seed_identification("What kind of technology is named as part of renewable energy transitions?", ["storage technology", "energy storage"]),
        seed_fill_blank("Solar and wind can reduce ______ emissions.", ["carbon", "carbon emissions"]),
        seed_enumeration("Name two factors communities should consider in energy planning.", ["infrastructure costs", "long-term reliability"]),
    ], "shortAnswerPrompt": "Why should communities consider both cost and sustainability when choosing energy sources?"},
    "p16": {"questions": [
        seed_identification("Which branch power can stop a bill through a veto?", ["executive", "executive branch"]),
        seed_fill_blank("Checks and balances are meant to protect constitutional ______.", ["order"]),
        seed_enumeration("Name two examples of checks and balances mentioned in the passage.", ["judicial review", "legislative oversight"]),
    ], "shortAnswerPrompt": "Explain one real-life situation where checks and balances can protect citizens."},
}

QUESTION_TYPES_BY_DIFFICULTY = {
    "EASY": {"multiple_choice", "true_false"},
    "MODERATE": {"multiple_choice_harder", "true_false_modified", "sequence"},
    "DIFFICULT": {"fill_in_the_blanks", "identification", "enumeration"},
    "CUSTOM": {"custom"},
}


def api_ok(data=None, status=200):
    return jsonify({"ok": True, "data": data}), status


def api_error(message, status=400):
    return jsonify({"ok": False, "error": message}), status


def normalize_class_level(value):
    v = str(value or "").strip().upper()
    if v == "MEDIUM":
        return "MODERATE"
    if v == "DIFFICULT":
        return "HARD"
    return v if v in {"EASY", "MODERATE", "HARD"} else "EASY"


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


def count_words(text):
    return len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", str(text or "")))


def estimate_minutes(words):
    return max(1, int(np.ceil((words or 0) / 80.0)))


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
               s.id AS student_id,s.full_name,s.grade,s.section,s.class_level,s.pre_score,s.pre_assessment_completed,
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
            "preAssessmentCompleted": bool(int(row.get("pre_assessment_completed") or 0)),
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
        "isDraft": bool(int(row.get("is_draft") or 0)),
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


def upsert_assessment(cur, passage_id, payload, passage_label, allow_empty=False):
    normalized = normalize_assessment_payload(payload, passage_label, allow_empty=allow_empty)
    questions = normalized["questions"]
    short_answer = normalized["shortAnswerPrompt"]

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
        cur.execute(
            """
            INSERT INTO assessment_questions (
              assessment_id,sort_order,difficulty,type,prompt,options_json,answer_index,answer_key,answer_keys_json
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                aid,
                i,
                q["difficulty"],
                q["type"],
                q["prompt"],
                json.dumps(q["options"], ensure_ascii=False) if q["options"] else None,
                q["answerIndex"],
                q["answerKey"] or None,
                json.dumps(q["answerKeys"], ensure_ascii=False) if q["answerKeys"] else None,
            ),
        )


def get_weekly_assignments(cur, week):
    out = {"EASY": [], "MODERATE": [], "HARD": []}
    cur.execute("SELECT class_level, passage_id FROM weekly_assignments WHERE week_no=%s ORDER BY id", (week,))
    for row in cur.fetchall():
        out[normalize_class_level(row["class_level"])] += [row["passage_id"]]
    return out


def get_passage_usage_weeks(cur):
    usage = {}
    cur.execute("SELECT passage_id, week_no FROM weekly_assignments ORDER BY week_no, id")
    for row in cur.fetchall():
        usage.setdefault(row["passage_id"], []).append(int(row["week_no"]))
    return usage


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
    progress = []
    for row in cur.fetchall():
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
    return progress


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
            "SELECT COUNT(*) AS total FROM quiz_attempts WHERE student_id=%s AND short_answer_text IS NOT NULL",
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
        f"to Week {latest['week']} ({latest['score']}%)."
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
        SELECT qa.passage_id,qa.short_answer_text,qa.submitted_at,p.title,p.label,a.short_answer_prompt
        FROM quiz_attempts qa
        JOIN passages p ON p.id=qa.passage_id
        LEFT JOIN assessments a ON a.passage_id=qa.passage_id
        WHERE qa.student_id=%s AND qa.short_answer_text IS NOT NULL
        ORDER BY qa.submitted_at DESC
        LIMIT 1
        """,
        (student_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "passageId": row["passage_id"],
        "passageTitle": row["title"],
        "label": row["label"],
        "prompt": row.get("short_answer_prompt") or "",
        "response": row.get("short_answer_text") or "",
        "submittedAt": row["submitted_at"].isoformat() if row.get("submitted_at") else None,
    }

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
            """CREATE TABLE IF NOT EXISTS students (id VARCHAR(20) PRIMARY KEY,user_id INT UNIQUE NOT NULL,full_name VARCHAR(255) NOT NULL,grade VARCHAR(20) NOT NULL,section VARCHAR(100) NOT NULL,class_level ENUM('EASY','MODERATE','HARD') NOT NULL DEFAULT 'EASY',pre_score INT NOT NULL DEFAULT 0,pre_assessment_completed TINYINT(1) NOT NULL DEFAULT 0,pre_assessment_completed_at TIMESTAMP NULL,avatar_type ENUM('initials','preset','upload') NOT NULL DEFAULT 'initials',avatar_value MEDIUMTEXT NULL,FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
            """CREATE TABLE IF NOT EXISTS passages (id VARCHAR(20) PRIMARY KEY,title VARCHAR(255) NOT NULL,genre VARCHAR(100) NOT NULL,text MEDIUMTEXT NOT NULL,label ENUM('EASY','MODERATE','HARD') NOT NULL,words INT NOT NULL,est_minutes INT NOT NULL,confidence DECIMAL(5,2) NULL,is_draft TINYINT(1) NOT NULL DEFAULT 0,created_by INT NULL,created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""",
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

        cur.execute("SHOW COLUMNS FROM students LIKE 'pre_assessment_completed'")
        if not cur.fetchone():
            cur.execute(
                "ALTER TABLE students ADD COLUMN pre_assessment_completed TINYINT(1) NOT NULL DEFAULT 0 AFTER pre_score"
            )

        cur.execute("SHOW COLUMNS FROM students LIKE 'pre_assessment_completed_at'")
        if not cur.fetchone():
            cur.execute(
                "ALTER TABLE students ADD COLUMN pre_assessment_completed_at TIMESTAMP NULL AFTER pre_assessment_completed"
            )

        cur.execute("SHOW COLUMNS FROM passages LIKE 'is_draft'")
        if not cur.fetchone():
            cur.execute(
                "ALTER TABLE passages ADD COLUMN is_draft TINYINT(1) NOT NULL DEFAULT 0 AFTER confidence"
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
            pre_score = int(student["pre"])
            pre_completed = 1 if pre_score > 0 else 0
            cur.execute(
                """
                INSERT INTO students (id,user_id,full_name,grade,section,class_level,pre_score,pre_assessment_completed)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON DUPLICATE KEY UPDATE
                  user_id=VALUES(user_id),
                  full_name=VALUES(full_name),
                  grade=VALUES(grade),
                  section=VALUES(section),
                  class_level=VALUES(class_level),
                  pre_score=VALUES(pre_score),
                  pre_assessment_completed=VALUES(pre_assessment_completed)
                """,
                (student["id"], uid, student["name"], student["grade"], student["section"], normalize_class_level(student["class"]), pre_score, pre_completed),
            )
            if pre_completed:
                cur.execute(
                    "UPDATE students SET pre_assessment_completed_at=COALESCE(pre_assessment_completed_at, NOW()) WHERE id=%s",
                    (student["id"],),
                )

        cur.execute("SELECT id FROM users WHERE email=%s", ("ms.villanueva@pnhs.edu",))
        teacher_id = cur.fetchone()["id"]

        def should_refresh_seed_assessment(passage_id, seed_assessment):
            cur.execute("SELECT id, short_answer_prompt FROM assessments WHERE passage_id=%s", (passage_id,))
            assessment_row = cur.fetchone()
            if not assessment_row:
                return True

            cur.execute("SELECT COUNT(*) AS total FROM assessment_questions WHERE assessment_id=%s", (assessment_row["id"],))
            total_questions = int(cur.fetchone()["total"] or 0)
            has_seed_short_answer = bool(str(seed_assessment.get("shortAnswerPrompt") or "").strip())
            current_short_answer = str(assessment_row.get("short_answer_prompt") or "").strip()

            # Upgrade the original sparse demo seeds (0-1 questions) to the richer seeded library.
            if total_questions <= 1:
                return True
            if has_seed_short_answer and total_questions <= 1 and not current_short_answer:
                return True
            return False

        for p in SEED_PASSAGES:
            words = count_words(p["text"])
            cur.execute(
                "INSERT IGNORE INTO passages (id,title,genre,text,label,words,est_minutes,created_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (p["id"], p["title"], p["genre"], p["text"], normalize_class_level(p["label"]), words, estimate_minutes(words), teacher_id),
            )
            seed_assessment = SEED_ASSESSMENTS.get(p["id"], {"questions": []})
            if should_refresh_seed_assessment(p["id"], seed_assessment):
                upsert_assessment(cur, p["id"], seed_assessment, p["label"])

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
    try:
        return jsonify(build_prediction_response(payload.get("text", "")))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400


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
                   s.id AS student_id,s.full_name,s.grade,s.section,s.class_level,s.pre_score,s.pre_assessment_completed,
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


@app.post("/api/student/pre-assessment")
def student_pre_assessment_submit():
    user, err = require_role("student")
    if err:
        return err

    payload = request.get_json(silent=True) or {}
    try:
        score = int(payload.get("score") or 0)
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(100, score))
    class_level = classify_pre_assessment_level(score)

    with db_cursor(True) as (_, cur):
        student = student_row(cur, user)
        if not student:
            return api_error("Student profile not found.", 404)

        cur.execute(
            """
            UPDATE students
            SET pre_score=%s, class_level=%s, pre_assessment_completed=1, pre_assessment_completed_at=NOW()
            WHERE id=%s
            """,
            (score, class_level, student["id"]),
        )
        refreshed_user = fetch_user_by_id(cur, user["id"])

    return api_ok(
        {
            "user": serialize_user(refreshed_user),
            "preScore": score,
            "classLevel": class_level,
        }
    )


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
        cur.execute(
            "SELECT id,title,genre,text,label,words,est_minutes,confidence,is_draft FROM passages ORDER BY created_at DESC,id DESC"
        )
        rows = cur.fetchall()
        passages = [serialize_passage(row) for row in rows]
        usage_weeks = get_passage_usage_weeks(cur)
        for passage in passages:
            passage["assessment"] = fetch_assessment(cur, passage["id"])
            passage["usedWeeks"] = usage_weeks.get(passage["id"], [])
    return api_ok(passages)


@app.get("/api/passages/<passage_id>")
def passage_get(passage_id):
    user, err = require_auth()
    if err:
        return err
    del user
    with db_cursor(True) as (_, cur):
        cur.execute(
            "SELECT id,title,genre,text,label,words,est_minutes,confidence,is_draft FROM passages WHERE id=%s",
            (passage_id,),
        )
        row = cur.fetchone()
        if not row:
            return api_error("Passage not found.", 404)
        passage = serialize_passage(row)
        passage["assessment"] = fetch_assessment(cur, passage_id)
        cur.execute("SELECT week_no FROM weekly_assignments WHERE passage_id=%s ORDER BY week_no,id", (passage_id,))
        passage["usedWeeks"] = [int(item["week_no"]) for item in cur.fetchall()]
    return api_ok(passage)


def save_passage(cur, payload, author_id, passage_id=None, allow_empty_assessment=False, is_draft=False):
    title = str(payload.get("title") or "").strip()
    genre = str(payload.get("genre") or "Expository").strip() or "Expository"
    text = str(payload.get("text") or "").strip()
    label = normalize_class_level(payload.get("label") or "MODERATE")
    draft_value = 1 if is_draft else 0
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
    assessment = normalize_assessment_payload(
        payload.get("assessment") or {"questions": [], "shortAnswerPrompt": ""},
        label,
        allow_empty=allow_empty_assessment,
    )

    if passage_id:
        cur.execute("SELECT id FROM passages WHERE id=%s", (passage_id,))
        if not cur.fetchone():
            raise LookupError("Passage not found.")
        cur.execute(
            "UPDATE passages SET title=%s,genre=%s,text=%s,label=%s,words=%s,est_minutes=%s,confidence=%s,is_draft=%s WHERE id=%s",
            (title, genre, text, label, words, minutes, confidence, draft_value, passage_id),
        )
    else:
        cur.execute("SELECT COALESCE(MAX(CAST(SUBSTRING(id,2) AS UNSIGNED)),0) AS max_id FROM passages WHERE id REGEXP '^p[0-9]+$'")
        passage_id = f"p{int(cur.fetchone()['max_id']) + 1}"
        cur.execute(
            "INSERT INTO passages (id,title,genre,text,label,words,est_minutes,confidence,is_draft,created_by) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (passage_id, title, genre, text, label, words, minutes, confidence, draft_value, author_id),
        )

    upsert_assessment(cur, passage_id, assessment, label, allow_empty=allow_empty_assessment)
    cur.execute(
        "SELECT id,title,genre,text,label,words,est_minutes,confidence,is_draft FROM passages WHERE id=%s",
        (passage_id,),
    )
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
            saved = save_passage(cur, payload, user["id"], None, allow_empty_assessment=False, is_draft=False)
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
            saved = save_passage(cur, payload, user["id"], passage_id, allow_empty_assessment=False, is_draft=False)
        except LookupError:
            return api_error("Passage not found.", 404)
        except ValueError as e:
            return api_error(str(e), 400)
    return api_ok(saved)


@app.post("/api/passages/import-csv")
def passage_import_csv():
    user, err = require_role("teacher")
    if err:
        return err

    upload = request.files.get("file")
    if not upload or not upload.filename:
        return api_error("CSV file is required.", 400)

    try:
        csv_text = upload.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return api_error("CSV must be UTF-8 encoded.", 400)

    reader = csv.DictReader(StringIO(csv_text))
    if not reader.fieldnames:
        return api_error("CSV header row is required.", 400)

    normalized_headers = [str(name or "").strip().lower() for name in reader.fieldnames]
    missing_headers = [header for header in ("title", "text") if header not in normalized_headers]
    if missing_headers:
        return api_error("Missing required CSV header(s): " + ", ".join(missing_headers), 400)

    imported_count = 0
    failed_count = 0
    results = []

    with db_cursor(True) as (_, cur):
        for row_number, raw_row in enumerate(reader, start=2):
            normalized_row = {}
            for key, value in (raw_row or {}).items():
                normalized_key = str(key or "").strip().lower()
                normalized_row[normalized_key] = str(value or "").strip()

            if not any(normalized_row.values()):
                continue

            title = normalized_row.get("title", "")
            text = normalized_row.get("text", "")
            genre = normalized_row.get("genre", "") or "Expository"
            short_answer_prompt = normalized_row.get("short_answer_prompt", "")

            if not title:
                failed_count += 1
                results.append({"rowNumber": row_number, "status": "error", "error": "Passage title is required."})
                continue

            if not text:
                failed_count += 1
                results.append({"rowNumber": row_number, "title": title, "status": "error", "error": "Passage text is required."})
                continue

            try:
                prediction = build_prediction_response(text)
                saved = save_passage(
                    cur,
                    {
                        "title": title,
                        "genre": genre,
                        "text": text,
                        "label": prediction["label"],
                        "confidence": prediction["confidence"],
                        "assessment": {
                            "questions": [],
                            "shortAnswerPrompt": short_answer_prompt,
                        },
                    },
                    user["id"],
                    None,
                    allow_empty_assessment=True,
                    is_draft=True,
                )
                imported_count += 1
                results.append(
                    {
                        "rowNumber": row_number,
                        "status": "imported",
                        "id": saved["id"],
                        "title": saved["title"],
                        "label": saved["label"],
                        "confidence": saved["confidence"],
                        "isDraft": saved["isDraft"],
                    }
                )
            except ValueError as error:
                failed_count += 1
                results.append(
                    {
                        "rowNumber": row_number,
                        "title": title,
                        "status": "error",
                        "error": str(error),
                    }
                )

    if not results:
        return api_error("CSV file has no importable rows.", 400)

    return api_ok(
        {
            "importedCount": imported_count,
            "failedCount": failed_count,
            "results": results,
        }
    )
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
        cur.execute("SELECT label,is_draft FROM passages WHERE id=%s", (passage_id,))
        row = cur.fetchone()
        if not row:
            return api_error("Passage not found.", 404)
        if bool(int(row.get("is_draft") or 0)):
            return api_error("Complete the assessment before assigning this passage.", 400)
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
        if not pre_assessment_completed(student):
            return api_error("Complete the pre-assessment first.", 403)
        class_level = normalize_class_level(student["class_level"])
        cur.execute(
            """
            SELECT p.id,p.title,p.genre,p.text,p.label,p.words,p.est_minutes,p.confidence,p.is_draft
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
        if not pre_assessment_completed(student):
            return api_error("Complete the pre-assessment first.", 403)
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
        if not pre_assessment_completed(student):
            return api_error("Complete the pre-assessment first.", 403)
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


@app.get("/api/teacher/dashboard")
def teacher_dashboard():
    user, err = require_role("teacher")
    if err:
        return err
    del user

    with db_cursor(True) as (_, cur):
        students = fetch_teacher_student_summaries(cur)
        cur.execute(
            """
            SELECT qa.student_id,s.full_name,p.id AS passage_id,p.title,qa.score_pct,qa.short_answer_text,qa.submitted_at
            FROM quiz_attempts qa
            JOIN students s ON s.id=qa.student_id
            JOIN passages p ON p.id=qa.passage_id
            ORDER BY qa.submitted_at DESC, qa.id DESC
            LIMIT 6
            """
        )
        submissions = []
        for row in cur.fetchall():
            submissions.append(
                {
                    "studentId": row["student_id"],
                    "studentName": row["full_name"],
                    "passageId": row["passage_id"],
                    "passageTitle": row["title"],
                    "score": int(row["score_pct"] or 0),
                    "status": "Pending Review" if row.get("short_answer_text") else "Scored",
                    "submittedAt": row["submitted_at"].isoformat() if row.get("submitted_at") else None,
                }
            )

    level_counts = {"EASY": 0, "MODERATE": 0, "HARD": 0}
    level_students = {"EASY": [], "MODERATE": [], "HARD": []}
    pending_reviews = []
    recommendation_count = 0
    for student in students:
        level = normalize_class_level(student["classLevel"])
        level_counts[level] += 1
        level_students[level].append(student["name"])
        if student["pendingReviewCount"]:
            pending_reviews.append(student)
        if len(student["progress"]) >= 2:
            recommendation_count += 1

    return api_ok(
        {
            "levelCounts": level_counts,
            "levelStudents": level_students,
            "recentSubmissions": submissions,
            "pendingReviews": pending_reviews[:3],
            "recommendationCount": recommendation_count,
            "studentCount": len(students),
        }
    )


@app.get("/api/teacher/students")
def teacher_students():
    user, err = require_role("teacher")
    if err:
        return err
    del user

    with db_cursor(True) as (_, cur):
        students = fetch_teacher_student_summaries(cur)
    return api_ok({"students": students})


@app.get("/api/teacher/reports/summary")
def teacher_reports_summary():
    user, err = require_role("teacher")
    if err:
        return err
    del user

    active_week = normalize_week(request.args.get("activeWeek"))
    with db_cursor(True) as (_, cur):
        summary = build_teacher_report_summary(cur, active_week)
    return api_ok(summary)


@app.get("/api/teacher/students/<student_id>")
def teacher_student_detail(student_id):
    user, err = require_role("teacher")
    if err:
        return err
    del user

    with db_cursor(True) as (_, cur):
        cur.execute(
            """
            SELECT s.id,s.full_name,s.grade,s.section,s.class_level,s.pre_score,s.pre_assessment_completed,u.email
            FROM students s
            JOIN users u ON u.id=s.user_id
            WHERE s.id=%s
            """,
            (student_id,),
        )
        student = cur.fetchone()
        if not student:
            return api_error("Student not found.", 404)

        progress = fetch_student_progress(cur, student_id)
        pending_short_answer = fetch_pending_short_answer(cur, student_id)

    latest = progress[-1] if progress else None
    payload = {
        "student": {
            "id": student["id"],
            "name": student["full_name"],
            "email": student["email"],
            "grade": student["grade"],
            "section": student["section"],
            "classLevel": student["class_level"],
            "preScore": int(student["pre_score"] or 0),
            "preAssessmentCompleted": bool(int(student["pre_assessment_completed"] or 0)),
        },
        "progress": progress,
        "latest": latest,
        "pendingShortAnswer": pending_short_answer,
    }
    return api_ok(payload)


@app.get("/api/student/progress")
def student_progress():
    user, err = require_role("student")
    if err:
        return err
    with db_cursor(True) as (_, cur):
        student = student_row(cur, user)
        if not student:
            return api_error("Student profile not found.", 404)
        if not pre_assessment_completed(student):
            return api_error("Complete the pre-assessment first.", 403)
        progress = fetch_student_progress(cur, student["id"])
    return api_ok({"progress": progress})


@app.errorhandler(mysql.connector.Error)
def handle_mysql_error(_):
    return api_error("Database operation failed. Check MySQL configuration and service.", 500)


init_database()


if __name__ == "__main__":
    print("Loaded model artifacts from", MODEL_DIR)
    print(f"Connected to MySQL database '{DB_NAME}' on {DB_HOST}:{DB_PORT}")
    app.run(debug=True, host="127.0.0.1", port=5000)
