"""The integration layer: question in, grounded answer out.

Owned by Faisal. This is the only place that knows about both halves of the system, so it is
also where the failures between them are handled. Everything it touches is the Protocol types
from contracts.py, never a concrete retriever or generator, which is what lets the real
components drop in without changes here.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

from .contracts import ALLOWED_DOC_IDS, Answer, Generator, Passage, Retriever

log = logging.getLogger(__name__)

MAX_QUESTION_CHARS = 500

NO_ANSWER_TEXT = ("The HR documents provided do not contain enough information to answer "
                  "that question. Try rephrasing, or contact HR directly.")


class PipelineError(RuntimeError):
    """Raised for conditions the caller should fix, such as an unusable question."""


@dataclass
class AskResult:
    """One completed question, with everything the evaluation needs.

    The pipeline returns this rather than a bare Answer so that Russell's evaluation can read
    retrieval and generation timings separately, see how many passages were retrieved, and
    record failures as data instead of as exceptions.
    """

    question: str
    answer: Answer
    passages: list[Passage] = field(default_factory=list)
    retrieval_s: float = 0.0
    generation_s: float = 0.0
    total_s: float = 0.0
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def n_passages(self) -> int:
        return len(self.passages)


class HRAssistant:
    """Wires a Retriever to a Generator and handles what can go wrong between them.

        assistant = HRAssistant(retriever=ArslanRetriever(), generator=ChristianGenerator())
        result = assistant.ask("How do I enroll in benefits?")
        print(result.answer.text, result.answer.citations)
    """

    def __init__(self, retriever: Retriever, generator: Generator, k: int = 4) -> None:
        self.retriever = retriever
        self.generator = generator
        self.k = k

    # -- validation ------------------------------------------------------------------
    @staticmethod
    def _clean_question(question: str) -> str:
        if question is None:
            raise PipelineError("No question was provided.")
        q = " ".join(str(question).split())
        if not q:
            raise PipelineError("The question is empty.")
        if len(q) > MAX_QUESTION_CHARS:
            raise PipelineError(
                f"The question is {len(q)} characters; the limit is {MAX_QUESTION_CHARS}.")
        return q

    @staticmethod
    def _check_passages(passages: list[Passage]) -> list[Passage]:
        """Drop anything malformed before it reaches the generator or a citation.

        A passage whose doc_id is not one of the seven real documents means retrieval has a
        bug, and a fabricated citation is worse than no answer, so it is discarded loudly
        rather than passed through.
        """
        kept = []
        for p in passages:
            if not isinstance(p, Passage):
                log.warning("retriever returned a %s, not a Passage; dropping", type(p).__name__)
                continue
            if p.doc_id not in ALLOWED_DOC_IDS:
                log.warning("unknown doc_id %r; dropping to avoid a false citation", p.doc_id)
                continue
            kept.append(p)
        return kept

    # -- the pipeline ----------------------------------------------------------------
    def ask(self, question: str) -> AskResult:
        """Run one question end to end. Component failures become a result, not a crash."""
        t_start = time.perf_counter()
        q = self._clean_question(question)       # caller error: raises

        # 1. retrieve
        t0 = time.perf_counter()
        try:
            passages = self.retriever.retrieve(q, k=self.k)
        except Exception as exc:                 # component error: reported, not raised
            log.exception("retrieval failed")
            return AskResult(question=q, answer=Answer(text=NO_ANSWER_TEXT,
                                                       insufficient_info=True),
                             retrieval_s=time.perf_counter() - t0,
                             total_s=time.perf_counter() - t_start,
                             error=f"retrieval failed: {type(exc).__name__}: {exc}")
        retrieval_s = time.perf_counter() - t0
        passages = self._check_passages(list(passages or []))

        # 2. nothing relevant: answer honestly without calling the model
        if not passages:
            return AskResult(question=q,
                             answer=Answer(text=NO_ANSWER_TEXT, insufficient_info=True),
                             retrieval_s=retrieval_s,
                             total_s=time.perf_counter() - t_start)

        # 3. generate
        t1 = time.perf_counter()
        try:
            answer = self.generator.generate(q, passages)
        except Exception as exc:
            log.exception("generation failed")
            return AskResult(question=q, passages=passages,
                             answer=Answer(text=NO_ANSWER_TEXT, insufficient_info=True),
                             retrieval_s=retrieval_s,
                             generation_s=time.perf_counter() - t1,
                             total_s=time.perf_counter() - t_start,
                             error=f"generation failed: {type(exc).__name__}: {exc}")
        generation_s = time.perf_counter() - t1

        if not isinstance(answer, Answer):
            return AskResult(question=q, passages=passages,
                             answer=Answer(text=NO_ANSWER_TEXT, insufficient_info=True),
                             retrieval_s=retrieval_s, generation_s=generation_s,
                             total_s=time.perf_counter() - t_start,
                             error=f"generator returned {type(answer).__name__}, expected Answer")

        # Cite only what was actually retrieved, so a citation can never be invented.
        if not answer.sources:
            answer = Answer(text=answer.text, sources=passages,
                            insufficient_info=answer.insufficient_info,
                            model=answer.model, latency_s=answer.latency_s)

        return AskResult(question=q, answer=answer, passages=passages,
                         retrieval_s=retrieval_s, generation_s=generation_s,
                         total_s=time.perf_counter() - t_start)


def format_answer(result: AskResult, show_timing: bool = True) -> str:
    """Render a result for the console. The display half of question entry and display."""
    lines: list[str] = []
    if result.error:
        lines.append(f"[warning] {result.error}")
        lines.append("")
    lines.append(result.answer.text)
    if result.answer.citations:
        lines.append("")
        lines.append("Sources:")
        lines.extend(f"  - {c}" for c in result.answer.citations)
    elif result.answer.insufficient_info:
        lines.append("")
        lines.append("Sources: none; the documents did not cover this question.")
    if show_timing:
        lines.append("")
        lines.append(f"[{result.n_passages} passage(s) | retrieval {result.retrieval_s:.2f}s "
                     f"| generation {result.generation_s:.2f}s "
                     f"| total {result.total_s:.2f}s]")
    return "\n".join(lines)
