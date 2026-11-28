"""Record evaluation responses and smoke-test the runner without an API."""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace


def evidence_coverage(case, passages):
    groups = case["evidence_groups"]
    if not groups:
        return "not_applicable"

    retrieved = {(p.doc_id, p.section) for p in passages}
    covered = [
        any(
            (source["doc_id"], source["section"]) in retrieved
            for source in group["alternatives"]
        )
        for group in groups
    ]

    if all(covered):
        return "all"
    return "some" if any(covered) else "none"


def passage_record(passage):
    return {
        "doc_id": passage.doc_id,
        "doc_title": passage.doc_title,
        "section": passage.section,
        "text": passage.text,
        "score": passage.score,
    }


def evaluate(assistant, cases, run_label):
    records = []

    for case in cases:
        record = {
            "question_id": case["question_id"],
            "question": case["question"],
            "run_label": run_label,
            "run_status": "completed",
            "correctness": None,
            "completeness": None,
            "citation_support": "not_scored",
            "information_handling": "not_scored",
            "reviewer_notes": "",
        }

        try:
            result = assistant.ask(case["question"])
            record.update({
                "answer_text": result.answer.text,
                "retrieved_passages": [
                    passage_record(p) for p in result.passages
                ],
                "reported_sources": [
                    passage_record(p) for p in result.answer.sources
                ],
                "evidence_coverage": evidence_coverage(
                    case, result.passages
                ),
                "insufficient_info": result.answer.insufficient_info,
                "model": result.answer.model,
                "pipeline_ok": result.ok,
                "retrieval_s": result.retrieval_s,
                "generation_s": result.generation_s,
                "total_s": result.total_s,
                "error": result.error,
            })
            if not result.ok:
                record["run_status"] = "pipeline_error"

        except Exception as exc:
            record.update({
                "run_status": "runner_exception",
                "evidence_coverage": "not_scored",
                "pipeline_ok": False,
                "error": f"{type(exc).__name__}: {exc}",
            })

        records.append(record)

    return records


class SmokeAssistant:
    """Predetermined fake results. No retrieval, generation, or network calls."""

    def ask(self, question):
        if question == "Smoke exception":
            raise RuntimeError("Intentional smoke-test exception")

        passage = SimpleNamespace(
            doc_id="SMOKE_DOCUMENT",
            doc_title="Synthetic smoke fixture",
            section="Example section",
            text="Fake evidence used only to test the evaluation runner.",
            score=1.0,
        )

        has_passage = question == "Smoke evidence"
        passages = [passage] if has_passage else []

        return SimpleNamespace(
            answer=SimpleNamespace(
                text="SMOKE TEST ONLY: predetermined fake response.",
                sources=passages,
                insufficient_info=not has_passage,
                model="SMOKE_ONLY_NO_MODEL",
            ),
            passages=passages,
            retrieval_s=0.0,
            generation_s=0.0,
            total_s=0.0,
            error=None,
            ok=True,
        )


def smoke_test():
    group = {
        "alternatives": [{
            "doc_id": "SMOKE_DOCUMENT",
            "section": "Example section",
        }]
    }
    missing_group = {
        "alternatives": [{
            "doc_id": "MISSING_DOCUMENT",
            "section": "Missing section",
        }]
    }

    cases = [
        {
            "question_id": "SMOKE01",
            "question": "Smoke evidence",
            "evidence_groups": [group],
        },
        {
            "question_id": "SMOKE02",
            "question": "Smoke evidence",
            "evidence_groups": [group, missing_group],
        },
        {
            "question_id": "SMOKE03",
            "question": "Smoke empty",
            "evidence_groups": [group],
        },
        {
            "question_id": "SMOKE04",
            "question": "Smoke clarification",
            "evidence_groups": [],
        },
        {
            "question_id": "SMOKE05",
            "question": "Smoke exception",
            "evidence_groups": [group],
        },
    ]

    records = evaluate(SmokeAssistant(), cases, "smoke_test")
    expected = ["all", "some", "none", "not_applicable", "not_scored"]
    actual = [record["evidence_coverage"] for record in records]

    if actual != expected:
        raise AssertionError(f"Coverage mismatch: {actual}")

    if records[-1]["run_status"] != "runner_exception":
        raise AssertionError("Exception handling failed.")

    if any(record["correctness"] is not None for record in records):
        raise AssertionError("Manual scores must remain unscored.")

    output_folder = Path(__file__).resolve().parent / "smoke_test"
    output_folder.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_file = output_folder / f"smoke_{timestamp}.json"

    with output_file.open("x", encoding="utf-8") as file:
        json.dump({
            "run_label": "smoke_test",
            "uses_real_components": False,
            "records": records,
        }, file, indent=2)

    print("PASS: all/some/none/not_applicable coverage checks.")
    print("PASS: exceptions are recorded without stopping the run.")
    print("PASS: manual answer scores remain unscored.")
    print(f"Saved synthetic test output: {output_file}")
    print("No real retrieval, generation, or model requests were run.")


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def load_cases(path=None):
    path = Path(path) if path else Path(__file__).resolve().parent / "questions.json"
    with path.open(encoding="utf-8") as file:
        return json.load(file)["cases"]


def build_assistant(mode):
    from hr_assistant.pipeline import HRAssistant

    if mode == "stub":
        from hr_assistant.stubs import StubGenerator, StubRetriever
        return HRAssistant(StubRetriever(), StubGenerator())

    raise NotImplementedError(
        "Real retriever and generator are not wired in yet. "
        "Import them here once Arslan's and Christian's classes are merged."
    )


def save_run(records, label, uses_real_components):
    folder = Path(__file__).resolve().parent / "runs"
    folder.mkdir(exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_file = folder / f"{label}_{timestamp}.json"
    with output_file.open("x", encoding="utf-8") as file:
        json.dump({
            "run_label": label,
            "uses_real_components": uses_real_components,
            "records": records,
        }, file, indent=2)
    return output_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--stub", action="store_true",
                        help="Run all cases against stub components (plumbing check only).")
    parser.add_argument("--run", action="store_true",
                        help="Run all cases against the real components.")
    parser.add_argument("--label", default=None)
    args = parser.parse_args()

    if args.smoke_test:
        smoke_test()
    elif args.stub or args.run:
        mode = "stub" if args.stub else "real"
        label = args.label or ("stub_run" if args.stub else "real_run")
        records = evaluate(build_assistant(mode), load_cases(), label)
        path = save_run(records, label, uses_real_components=(mode == "real"))
        done = sum(r["run_status"] == "completed" for r in records)
        print(f"{done}/{len(records)} cases completed. Saved: {path}")
    else:
        parser.error("Choose --smoke-test, --stub, or --run.")