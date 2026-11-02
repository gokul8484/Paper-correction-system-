import json
import tempfile
from pathlib import Path

import streamlit as st

from grader import grade_paper, normalize_result, results_to_csv

st.set_page_config(page_title="Handwritten Exam Grader", page_icon="📝")
st.title("📝 Handwritten Exam Grader")
st.caption("Upload a rubric and scanned answer sheets. Always review flagged answers yourself.")

rubric_file = st.file_uploader("Rubric (JSON)", type="json")
papers = st.file_uploader("Answer sheets", type=["jpg", "jpeg", "png", "webp", "pdf"], accept_multiple_files=True)

if st.button("Grade", disabled=not (rubric_file and papers)):
    rubric = json.load(rubric_file)
    results = {}
    bar = st.progress(0.0)
    for i, up in enumerate(papers):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / up.name
            p.write_bytes(up.getvalue())
            try:
                results[up.name] = grade_paper([p], rubric)
            except Exception as e:  # show error, keep going
                st.error(f"{up.name}: {e}")
        bar.progress((i + 1) / len(papers))
    st.session_state["results"] = results

results = st.session_state.get("results")
if results:
    for name, r in results.items():
        with st.expander(f"{name} — {r['total']}/{r['max_total']} ({r['percentage']}%)"):
            for q in r["questions"]:
                flag = " ⚠️ review" if q["needs_review"] else ""
                st.markdown(f"**{q['id']}**: {q['marks']}/{q['max_marks']}{flag}")
                st.write(q["feedback"])
                st.caption(f"Read as: {q['transcription']}")
    st.download_button("Download CSV", results_to_csv(results), "results.csv", "text/csv")
