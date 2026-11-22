"""Validate evaluation preparation files without running the assistant."""

import csv
import json
from pathlib import Path


def main():
    folder = Path(__file__).resolve().parent

    with (folder / "questions.json").open(encoding="utf-8-sig") as file:
        data = json.load(file)

    cases = data["cases"]
    if not cases:
        raise ValueError("No evaluation cases found.")

    question_ids = [case["question_id"] for case in cases]
    if len(question_ids) != len(set(question_ids)):
        raise ValueError("Duplicate question IDs found.")

    required_fields = {
        "question_id",
        "split",
        "category",
        "question",
        "answerability",
        "expected_points",
        "evidence_groups",
        "must_not_claim",
    }

    for case in cases:
        qid = case["question_id"]
        missing = required_fields - case.keys()
        if missing:
            raise ValueError(f"{qid}: missing fields: {sorted(missing)}")

        if not case["question"].strip():
            raise ValueError(f"{qid}: question is empty.")

        if not case["expected_points"]:
            raise ValueError(f"{qid}: expected points are empty.")

        for group in case["evidence_groups"]:
            alternatives = group.get("alternatives", [])
            if not alternatives:
                raise ValueError(f"{qid}: evidence group has no alternatives.")
            for source in alternatives:
                if not source.get("doc_id") or not source.get("section"):
                    raise ValueError(f"{qid}: incomplete evidence metadata.")

    with (folder / "results_template.csv").open(
        encoding="utf-8-sig", newline=""
    ) as file:
        rows = list(csv.DictReader(file))

    template_ids = [row["question_id"] for row in rows]
    if template_ids != question_ids:
        raise ValueError("CSV question IDs or order do not match questions.json.")

    for case, row in zip(cases, rows):
        qid = case["question_id"]
        if row["question"] != case["question"]:
            raise ValueError(f"{qid}: CSV question text does not match JSON.")

        if row["run_status"] != "not_run":
            raise ValueError(f"{qid}: template is not marked not_run.")

        for field in (
            "evidence_coverage",
            "citation_support",
            "information_handling",
        ):
            if row[field] != "not_scored":
                raise ValueError(f"{qid}: {field} is already scored.")

        for field in (
            "answer_text",
            "correctness",
            "completeness",
            "retrieval_s",
            "generation_s",
            "total_s",
        ):
            if row[field].strip():
                raise ValueError(f"{qid}: template field {field} is not blank.")

    if not (folder / "README.md").read_text(encoding="utf-8-sig").strip():
        raise ValueError("Evaluation README is empty.")

    print(f"PASS: {len(cases)} unique evaluation cases validated.")
    print(f"PASS: {len(rows)} matching, unscored CSV rows validated.")
    print("PASS: evaluation README is nonempty.")
    print("No assistant, retrieval, or model requests were run.")


if __name__ == "__main__":
    main()