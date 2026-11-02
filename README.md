# Handwritten Exam Grader

AI-assisted grading of handwritten exam papers. It reads scanned/photographed answer sheets (JPG, PNG, PDF), transcribes each answer, scores it against your rubric with partial credit, and flags unclear handwriting for human review.

> ⚠️ AI marking can make mistakes. Treat results as a first pass; a teacher should review flagged answers and spot-check the rest.

## Setup
```bash
git clone https://github.com/<you>/exam-grader.git && cd exam-grader
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your-key   # or copy .env.example
```

## Run
**Web app:** `streamlit run app.py`

**Command line** (one file per student):
```bash
python cli.py --rubric samples/rubric.json --papers scans/ --out results
```
Outputs `results/results.json` and `results/results.csv`.

## Rubric format
See `samples/rubric.json`: each question has `id`, `max_marks`, optional `model_answer` and `marking_points`.

## Deploy
- **GitHub:** push this repo; CI runs tests on every push.
- **Live app (free):** on [share.streamlit.io](https://share.streamlit.io) connect the repo, set `app.py` as the entry point, and add `ANTHROPIC_API_KEY` under *Secrets*. Never commit your key.

## Privacy
Student papers are sent to the Anthropic API for processing. Get consent and follow your school's data policy.

## Test
`pip install pytest && pytest`
