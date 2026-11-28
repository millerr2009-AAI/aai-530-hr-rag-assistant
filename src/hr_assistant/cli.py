"""Question entry and answer display.

Runs today against the stub components, so the interface and the error handling can be
demonstrated before retrieval and generation exist:

    python -m hr_assistant.cli --demo
    python -m hr_assistant.cli --demo --question "How do I enroll in benefits?"

Once the real components land, swap the two lines marked COMPONENT WIRING.
"""

from __future__ import annotations

import argparse
import logging
import sys

from .contracts import Answer, Generator, Passage, Retriever
from .pipeline import HRAssistant, PipelineError, format_answer
from .stubs import StubGenerator, StubRetriever

BANNER = """HR Assistant (retrieval-augmented)
Ask a question about onboarding, benefits, training, equipment, or HR policy.
Type 'quit' or press Ctrl-D to exit.
"""


def build_assistant(use_stubs: bool, k: int = 4) -> HRAssistant:
    """Choose the components. This is the only place that names concrete classes."""
    if use_stubs:
        return HRAssistant(retriever=StubRetriever(), generator=StubGenerator(), k=k)

    # ---- COMPONENT WIRING -------------------------------------------------------
    # from .retrieval import HRRetriever          # Arslan
    # from .generation import GeminiGenerator     # Christian
    # return HRAssistant(retriever=HRRetriever(), generator=GeminiGenerator(), k=k)
    # -----------------------------------------------------------------------------
    raise SystemExit(
        "The real retriever and generator are not wired up yet.\n"
        "Run with --demo to exercise the pipeline against the stub components."
    )


def ask_once(assistant: HRAssistant, question: str, show_timing: bool = True) -> int:
    try:
        result = assistant.ask(question)
    except PipelineError as exc:
        print(f"Cannot answer that: {exc}", file=sys.stderr)
        return 2
    print(format_answer(result, show_timing=show_timing))
    return 0 if result.ok else 1


def interactive(assistant: HRAssistant, show_timing: bool) -> int:
    print(BANNER)
    while True:
        try:
            question = input("question> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if question.lower() in {"quit", "exit", "q"}:
            return 0
        if not question:
            continue
        print()
        ask_once(assistant, question, show_timing)
        print()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Ask the HR documents a question.")
    ap.add_argument("--question", "-q", help="ask one question and exit")
    ap.add_argument("--demo", action="store_true",
                    help="use the stub retriever and generator")
    ap.add_argument("-k", type=int, default=4, help="passages to retrieve (default 4)")
    ap.add_argument("--no-timing", action="store_true", help="hide timing output")
    ap.add_argument("-v", "--verbose", action="store_true", help="show component warnings")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.WARNING if args.verbose else logging.ERROR,
                        format="%(levelname)s %(name)s: %(message)s")

    assistant = build_assistant(use_stubs=args.demo, k=args.k)
    if args.question:
        return ask_once(assistant, args.question, show_timing=not args.no_timing)
    return interactive(assistant, show_timing=not args.no_timing)


if __name__ == "__main__":
    raise SystemExit(main())
