"""Fake retriever and generator that satisfy the contracts.

These exist so the pipeline, the interface and the error handling can be built and tested
before the real components land. They are NOT the real implementations:

    StubRetriever  -> replaced by Arslan's retrieval
    StubGenerator  -> replaced by Christian's answer generation

Delete this module once both are in, or keep it for tests that should not call an API.
"""

from __future__ import annotations

from typing import Sequence

from .contracts import Answer, Passage

# Real text, copied from data/hr_documents/, so display and citation formatting can be
# checked against the shape of actual content.
_FAKE_CORPUS = [
    Passage(
        text=("Meet the manager and team; review the role, working hours, and first-week "
              "goals. Complete identity and employment-eligibility verification through the "
              "approved HR process."),
        doc_id="01_First_Week_Onboarding_Tasks",
        doc_title="First-Week Onboarding Tasks",
        section="Day 1: orientation",
        score=0.91,
    ),
    Passage(
        text=("Review and enroll through the benefits portal during the enrollment window. "
              "Qualifying life events may allow changes outside that window."),
        doc_id="03_Benefits_Enrollment",
        doc_title="Benefits Enrollment",
        section="How to enroll",
        score=0.78,
    ),
]


class StubRetriever:
    """Returns canned passages. Ignores the question except to simulate 'no results'."""

    def __init__(self, always_empty: bool = False) -> None:
        self.always_empty = always_empty

    def retrieve(self, question: str, k: int = 4) -> list[Passage]:
        if self.always_empty or "zzz" in question.lower():
            return []
        return _FAKE_CORPUS[:k]


class StubGenerator:
    """Echoes the retrieved passages. Flags insufficient info when given nothing."""

    model_name = "stub"

    def generate(self, question: str, passages: Sequence[Passage]) -> Answer:
        if not passages:
            return Answer(
                text=("The HR documents provided do not contain enough information to "
                      "answer that question."),
                sources=[], insufficient_info=True, model=self.model_name,
            )
        joined = " ".join(p.text for p in passages)
        return Answer(
            text=f"[stub answer for {question!r}] {joined[:200]}",
            sources=list(passages), insufficient_info=False, model=self.model_name,
        )


class ExplodingRetriever:
    """Raises on every call, so the pipeline's error handling can be tested."""

    def retrieve(self, question: str, k: int = 4) -> list[Passage]:
        raise RuntimeError("simulated retrieval failure (index not built)")
