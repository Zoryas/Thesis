from pathlib import Path
import re

import joblib
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from scipy.sparse import csr_matrix, hstack


app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "ml_model"
MIN_WORDS = 30


def load_model_artifacts():
    return {
        "svm_model": joblib.load(MODEL_DIR / "svm_model.pkl"),
        "word_vectorizer": joblib.load(MODEL_DIR / "word_vectorizer.pkl"),
        "char_vectorizer": joblib.load(MODEL_DIR / "char_vectorizer.pkl"),
        "label_encoder": joblib.load(MODEL_DIR / "label_encoder.pkl"),
    }


ARTIFACTS = load_model_artifacts()


def clean_text(text):
    if not isinstance(text, str):
        return ""
    compact = text.replace("\n", " ").replace("\t", " ")
    return re.sub(r"\s+", " ", compact).strip().lower()


def tokenize_words(text):
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", text or "")


def tokenize_sentences(text):
    stripped = (text or "").strip()
    if not stripped:
        return []
    sentences = [part.strip() for part in re.split(r"[.!?]+", stripped) if part.strip()]
    return sentences or [stripped]


def extract_surface_features(text):
    words = tokenize_words(text)
    if not words:
        return [[0.0, 0.0, 0.0, 0.0]]

    sentences = tokenize_sentences(text)
    word_count = len(words)
    sentence_count = max(len(sentences), 1)
    avg_sentence_length = word_count / sentence_count
    avg_word_length = sum(len(word) for word in words) / word_count
    type_token_ratio = len({word.lower() for word in words}) / word_count

    return [[avg_sentence_length, avg_word_length, type_token_ratio, float(word_count)]]


def estimate_confidence(feature_matrix):
    scores = ARTIFACTS["svm_model"].decision_function(feature_matrix)
    score_values = np.asarray(scores[0] if np.ndim(scores) > 1 else scores, dtype=float)
    if score_values.ndim == 0:
        score_values = np.array([-float(score_values), float(score_values)])

    shifted = score_values - np.max(score_values)
    probabilities = np.exp(shifted)
    probabilities /= probabilities.sum()
    return float(np.max(probabilities) * 100.0)


@app.get("/")
def index():
    return jsonify(
        {
            "name": "ReadWise Prediction API",
            "status": "running",
            "endpoints": ["/health", "/predict"],
        }
    )


@app.get("/health")
def health():
    return jsonify({"status": "running", "model": "SVM ReadWise Prototype"})


@app.post("/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()

    if not text:
        return jsonify({"error": "No text provided."}), 400

    if len(tokenize_words(text)) < MIN_WORDS:
        return jsonify({"error": "Passage too short. Minimum 30 words."}), 400

    cleaned = clean_text(text)
    surface_features = extract_surface_features(text)
    surface_sparse = csr_matrix(np.asarray(surface_features, dtype=float))

    word_features = ARTIFACTS["word_vectorizer"].transform([cleaned])
    char_features = ARTIFACTS["char_vectorizer"].transform([cleaned])
    feature_matrix = hstack([word_features, char_features, surface_sparse], format="csr")

    prediction_code = ARTIFACTS["svm_model"].predict(feature_matrix)[0]
    predicted_label = ARTIFACTS["label_encoder"].inverse_transform([prediction_code])[0]
    confidence = estimate_confidence(feature_matrix)
    avg_sentence_length, avg_word_length, type_token_ratio, passage_length = surface_features[0]

    return jsonify(
        {
            "label": predicted_label,
            "confidence": round(confidence, 1),
            "features": {
                "avg_sentence_length": round(avg_sentence_length, 2),
                "avg_word_length": round(avg_word_length, 2),
                "type_token_ratio": round(type_token_ratio, 3),
                "passage_length": int(passage_length),
            },
        }
    )


if __name__ == "__main__":
    print("Loaded model artifacts from", MODEL_DIR)
    app.run(debug=True, host="127.0.0.1", port=5000)
