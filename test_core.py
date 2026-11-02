from grader.core import extract_json, normalize_result, results_to_csv

RUBRIC = {"questions": [{"id": "Q1", "max_marks": 3}, {"id": "Q2", "max_marks": 2}]}


def test_extract_json_handles_fences():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_marks_are_clamped_and_missing_flagged():
    r = normalize_result({"questions": [{"id": "Q1", "marks": 9}]}, RUBRIC)
    assert r["questions"][0]["marks"] == 3
    assert r["questions"][1]["needs_review"] is True
    assert r["total"] == 3 and r["max_total"] == 5 and r["percentage"] == 60.0


def test_csv_has_total_row():
    r = normalize_result({"questions": []}, RUBRIC)
    assert "TOTAL" in results_to_csv({"a.jpg": r})
