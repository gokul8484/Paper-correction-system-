"""Core logic: transcribe handwritten answers and grade them against a rubric."""
import base64
import csv
import io
import json
import mimetypes
import os
import re
from pathlib import Path

DEFAULT_MODEL = os.getenv("GRADER_MODEL", "claude-sonnet-5-5")

SYSTEM_PROMPT = """You are a careful, fair exam marker.
You receive scanned or photographed handwritten answer sheets and a rubric.
For each question: transcribe what the student wrote, compare it with the
model answer and marking points, award marks (partial credit allowed, never
above max_marks), and give one short feedback sentence.
If handwriting is unreadable, say so, set "needs_review" to true and be
conservative. Respond with ONLY valid JSON, no markdown fences."""

JSON_SHAPE = """{
  "student_name": "string or null",
  "questions": [
    {"id": "Q1", "transcription": "...", "marks": 0, "max_marks": 0,
     "feedback": "...", "confidence": 0.0, "needs_review": false}
  ]
}"""


def load_rubric(path):
    rubric = json.loads(Path(path).read_text(encoding="utf-8"))
    if "questions" not in rubric or not rubric["questions"]:
        raise ValueError("Rubric must contain a non-empty 'questions' list")
    for q in rubric["questions"]:
        for key in ("id", "max_marks"):
            if key not in q:
                raise ValueError(f"Rubric question missing '{key}': {q}")
    return rubric


def _file_block(path):
    path = Path(path)
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    data = base64.standard_b64encode(path.read_bytes()).decode()
    kind = "document" if mime == "application/pdf" else "image"
    return {"type": kind, "source": {"type": "base64", "media_type": mime, "data": data}}


def extract_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model response")
    return json.loads(text[start : end + 1])


def normalize_result(result, rubric):
    """Clamp marks to rubric limits, fill missing questions, compute totals."""
    by_id = {q["id"]: q for q in result.get("questions", [])}
    out, total, max_total = [], 0.0, 0.0
    for rq in rubric["questions"]:
        got = by_id.get(rq["id"], {})
        max_marks = float(rq["max_marks"])
        marks = max(0.0, min(float(got.get("marks", 0) or 0), max_marks))
        missing = rq["id"] not in by_id
        out.append(
            {
                "id": rq["id"],
                "transcription": got.get("transcription", ""),
                "marks": marks,
                "max_marks": max_marks,
                "feedback": got.get("feedback", "No answer found."),
                "confidence": float(got.get("confidence", 0) or 0),
                "needs_review": bool(got.get("needs_review", False)) or missing,
            }
        )
        total += marks
        max_total += max_marks
    return {
        "student_name": result.get("student_name"),
        "questions": out,
        "total": total,
        "max_total": max_total,
        "percentage": round(100 * total / max_total, 1) if max_total else 0.0,
    }


def grade_paper(image_paths, rubric, client=None, model=DEFAULT_MODEL):
    """Grade one student's paper (one or more page images/PDFs)."""
    if client is None:
        import anthropic  # lazy import so tests run without the SDK

        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    content = [_file_block(p) for p in image_paths]
    content.append(
        {
            "type": "text",
            "text": "Rubric:\n"
            + json.dumps(rubric, indent=2)
            + "\n\nGrade the student's paper above. Return JSON shaped like:\n"
            + JSON_SHAPE,
        }
    )
    resp = client.messages.create(
        model=model,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    return normalize_result(extract_json(text), rubric)


def results_to_csv(results):
    """results: {paper_name: normalized_result} -> CSV string."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["paper", "student", "question", "marks", "max_marks", "needs_review", "feedback"])
    for name, r in results.items():
        for q in r["questions"]:
            w.writerow([name, r["student_name"], q["id"], q["marks"], q["max_marks"], q["needs_review"], q["feedback"]])
        w.writerow([name, r["student_name"], "TOTAL", r["total"], r["max_total"], "", f'{r["percentage"]}%'])
    return buf.getvalue()
