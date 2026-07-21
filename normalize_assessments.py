import csv
from pathlib import Path

src = Path("imports/reading_assessment_30_with_assessment.csv")
easy_out = Path("imports/assessments_easy.csv")
mod_out = Path("imports/assessments_moderate.csv")
hard_out = Path("imports/assessments_hard.csv")

hdr = [
    "title",
    "genre",
    "text",
    "short_answer_prompt",
    "q1_type",
    "q1_prompt",
    "q1_options",
    "q1_answerindex",
    "q1_answerkey",
    "q1_answerkeys",
    "q2_type",
    "q2_prompt",
    "q2_options",
    "q2_answerindex",
    "q2_answerkey",
    "q2_answerkeys",
    "q3_type",
    "q3_prompt",
    "q3_options",
    "q3_answerindex",
    "q3_answerkey",
    "q3_answerkeys",
]

groups = {"EASY": [], "MODERATE": [], "HARD": []}

with src.open("r", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))

for r in rows:
    lvl = (r.get("label") or "").strip().upper()
    if lvl not in groups:
        continue

    o = {k: (r.get(k, "") or "") for k in hdr}

    if lvl == "EASY":
        o["q1_type"] = "multiple_choice"
        o["q2_type"] = "true_false"
        o["q3_type"] = "multiple_choice"

        if not o["q1_options"].strip():
            o["q1_options"] = "Option A|Option B|Option C|Option D"
        if not str(o["q1_answerindex"]).strip():
            o["q1_answerindex"] = "0"
        o["q1_answerkey"] = ""
        o["q1_answerkeys"] = ""

        o["q2_options"] = ""
        o["q2_answerindex"] = ""
        o["q2_answerkey"] = "false" if str(o["q2_answerkey"]).strip().lower() == "false" else "true"
        o["q2_answerkeys"] = ""

        if not o["q3_options"].strip():
            o["q3_options"] = "Option A|Option B|Option C|Option D"
        if not str(o["q3_answerindex"]).strip():
            o["q3_answerindex"] = "0"
        o["q3_answerkey"] = ""
        o["q3_answerkeys"] = ""

    elif lvl == "MODERATE":
        o["q1_type"] = "multiple_choice_harder"
        o["q2_type"] = "true_false_modified"
        o["q3_type"] = "sequence"

        if not o["q1_options"].strip():
            o["q1_options"] = "Option A|Option B|Option C|Option D"
        if not str(o["q1_answerindex"]).strip():
            o["q1_answerindex"] = "0"
        o["q1_answerkey"] = ""
        o["q1_answerkeys"] = ""

        o["q2_options"] = ""
        o["q2_answerindex"] = ""
        o["q2_answerkey"] = "false" if str(o["q2_answerkey"]).strip().lower() == "false" else "true"
        if o["q2_answerkey"] == "false" and not str(o["q2_answerkeys"]).strip():
            o["q2_answerkeys"] = "Corrected statement"

        if not o["q3_options"].strip():
            o["q3_options"] = "Step 1|Step 2|Step 3"
        if not str(o["q3_answerkeys"]).strip():
            o["q3_answerkeys"] = o["q3_options"]
        o["q3_answerindex"] = ""
        o["q3_answerkey"] = ""

    else:
        o["q1_type"] = "identification"
        o["q2_type"] = "fill_in_the_blanks"
        o["q3_type"] = "enumeration"

        o["q1_options"] = ""
        o["q1_answerindex"] = ""
        if not str(o["q1_answerkey"]).strip() and not str(o["q1_answerkeys"]).strip():
            o["q1_answerkeys"] = "Sample answer"

        o["q2_options"] = ""
        o["q2_answerindex"] = ""
        if not str(o["q2_answerkey"]).strip() and not str(o["q2_answerkeys"]).strip():
            o["q2_answerkeys"] = "Sample answer"

        o["q3_options"] = ""
        o["q3_answerindex"] = ""
        if not str(o["q3_answerkey"]).strip() and not str(o["q3_answerkeys"]).strip():
            o["q3_answerkeys"] = "Sample answer"

    groups[lvl].append(o)

for p, lvl in [(easy_out, "EASY"), (mod_out, "MODERATE"), (hard_out, "HARD")]:
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr)
        w.writeheader()
        w.writerows(groups[lvl])

print("EASY", len(groups["EASY"]), str(easy_out))
print("MODERATE", len(groups["MODERATE"]), str(mod_out))
print("HARD", len(groups["HARD"]), str(hard_out))
