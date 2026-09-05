import csv
import json
from io import StringIO
from flask import Blueprint, request

from db import db_cursor
from routes.helpers import (
    api_error,
    api_ok,
    build_prediction_response,
    count_words,
    estimate_minutes,
    normalize_assessment_payload,
    normalize_class_level,
    normalize_week,
    require_auth,
    require_role,
)

passage_bp = Blueprint("passage_bp", __name__)


def _pre_assessment_passage_ids(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pre_assessment_config (
          id TINYINT PRIMARY KEY,
          config_json LONGTEXT NOT NULL,
          updated_by INT NULL,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    )
    cur.execute("SELECT config_json FROM pre_assessment_config WHERE id=1")
    row = cur.fetchone()
    if not row:
        return set()
    try:
        config = json.loads(row["config_json"])
    except (TypeError, ValueError):
        return set()
    return {str(step.get("id")) for step in config if isinstance(step, dict) and step.get("id")}


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
                "options": json.loads(q.get("options_json") or "[]"),
                "answerIndex": int(q.get("answer_index") or 0),
                "answerKey": q.get("answer_key") or "",
                "answerKeys": json.loads(q.get("answer_keys_json") or "[]"),
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
    cur.execute("SELECT id,title,genre,text,label,words,est_minutes,confidence,is_draft FROM passages WHERE id=%s", (passage_id,))
    out = serialize_passage(cur.fetchone())
    out["assessment"] = fetch_assessment(cur, passage_id)
    return out


@passage_bp.get("/api/passages")
def passages_list():
    user, err = require_auth()
    if err:
        return err
    del user
    with db_cursor(True) as (_, cur):
        cur.execute("SELECT id,title,genre,text,label,words,est_minutes,confidence,is_draft FROM passages ORDER BY created_at DESC,id DESC")
        rows = cur.fetchall()
        passages = [serialize_passage(row) for row in rows]
        usage_weeks = get_passage_usage_weeks(cur)
        for passage in passages:
            passage["assessment"] = fetch_assessment(cur, passage["id"])
            passage["usedWeeks"] = usage_weeks.get(passage["id"], [])
    return api_ok(passages)


@passage_bp.get("/api/passages/<passage_id>")
def passage_get(passage_id):
    user, err = require_auth()
    if err:
        return err
    del user
    with db_cursor(True) as (_, cur):
        cur.execute("SELECT id,title,genre,text,label,words,est_minutes,confidence,is_draft FROM passages WHERE id=%s", (passage_id,))
        row = cur.fetchone()
        if not row:
            return api_error("Passage not found.", 404)
        passage = serialize_passage(row)
        passage["assessment"] = fetch_assessment(cur, passage_id)
        cur.execute("SELECT week_no FROM weekly_assignments WHERE passage_id=%s ORDER BY week_no,id", (passage_id,))
        passage["usedWeeks"] = [int(item["week_no"]) for item in cur.fetchall()]
    return api_ok(passage)


@passage_bp.post("/api/passages")
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


@passage_bp.put("/api/passages/<passage_id>")
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


@passage_bp.post("/api/passages/import-csv")
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
                results.append({"rowNumber": row_number, "title": title, "status": "error", "error": str(error)})

    if not results:
        return api_error("CSV file has no importable rows.", 400)

    return api_ok({"importedCount": imported_count, "failedCount": failed_count, "results": results})


@passage_bp.delete("/api/passages/<passage_id>")
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


@passage_bp.get("/api/assignments")
def assignments_get():
    user, err = require_auth()
    if err:
        return err
    del user
    week = normalize_week(request.args.get("week"))
    with db_cursor(True) as (_, cur):
        return api_ok({"week": week, "assignments": get_weekly_assignments(cur, week)})


@passage_bp.post("/api/assignments")
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
        if passage_id in _pre_assessment_passage_ids(cur):
            return api_error("This passage is assigned to the pre-assessment and cannot be assigned to a weekly assessment.", 400)

        cur.execute("SELECT 1 FROM weekly_assignments WHERE week_no=%s AND class_level=%s AND passage_id=%s", (week, class_level, passage_id))
        if cur.fetchone():
            return api_ok({"week": week, "assignments": get_weekly_assignments(cur, week), "message": "Passage already assigned."})

        cur.execute("SELECT COUNT(*) AS total FROM weekly_assignments WHERE week_no=%s AND class_level=%s", (week, class_level))
        if int(cur.fetchone()["total"]) >= 5:
            return api_error("Class already has 5 passages this week.", 400)

        cur.execute("INSERT INTO weekly_assignments (week_no,class_level,passage_id) VALUES (%s,%s,%s)", (week, class_level, passage_id))
        return api_ok({"week": week, "assignments": get_weekly_assignments(cur, week), "message": "Passage assigned."})


@passage_bp.delete("/api/assignments")
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
