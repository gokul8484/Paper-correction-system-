"""Usage: python cli.py --rubric samples/rubric.json --papers scans/ --out results"""
import argparse
import json
from pathlib import Path

from grader import grade_paper, load_rubric, results_to_csv

EXTS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}


def main():
    ap = argparse.ArgumentParser(description="Grade handwritten exam papers")
    ap.add_argument("--rubric", required=True)
    ap.add_argument("--papers", required=True, help="Folder; each file = one student's paper")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()

    rubric = load_rubric(args.rubric)
    files = sorted(p for p in Path(args.papers).iterdir() if p.suffix.lower() in EXTS)
    results = {}
    for f in files:
        print(f"Grading {f.name} ...")
        results[f.name] = grade_paper([f], rubric)
        print(f"  -> {results[f.name]['total']}/{results[f.name]['max_total']}")

    Path(args.out).mkdir(exist_ok=True)
    Path(args.out, "results.json").write_text(json.dumps(results, indent=2))
    Path(args.out, "results.csv").write_text(results_to_csv(results))
    print(f"Saved to {args.out}/")


if __name__ == "__main__":
    main()
