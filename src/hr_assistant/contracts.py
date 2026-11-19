"""Shared data shapes and component interfaces for the HR RAG assistant.

This is the contract between the three components. If everyone builds to it, integration is
wiring rather than rewriting:

    retrieval  (Arslan)     ->  Passage objects
    generation (Christian)  ->  Answer object, built only from the Passages it is given
    integration (Faisal)    ->  calls one, feeds the other, handles the failures

Nothing here imports an LLM, an embedding library, or a vector store on purpose. Both sides
can develop and test against these types without waiting for the other, and `stubs.py`
provides fake implementations so the end-to-end pipeline runs today.

Proposed by Faisal for the integration layer. If a field or signature does not suit your
component, say so and we change it here once, rather than each of us adapting around it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Sequence, runtime_checkable

# The seven fictional HR documents live in data/hr_documents/ as .txt files.
# Their structure is fixed and machine-readable:
#
#     # First-Week Onboarding Tasks          <- document title
#     Document ID: 01_First_Week_Onboarding_Tasks
#     Version: 1.0
#
#     ## Before day one                      <- section heading
#     HR sends a welcome message ...         <- section body
#
# The corpus README asks for one chunk per "## " section, preserving the document title,
# Document ID and section heading as metadata. That yields 36 chunks over 7 documents.

CORPUS_DIR = "data/hr_documents"

ALLOWED_DOC_IDS = (
    "01_First_Week_Onboarding_Tasks",
    "02_Required_HR_Documents",
    "03_Benefits_Enrollment",
    "04_Employee_Training",
    "05_Equipment_and_Account_Requests",
    "06_HR_Policies",
    "07_HR_Knowledge_Base",
)


@dataclass(frozen=True)
class Passage:
    """One retrieved chunk: a single "## " section of one HR document.

    The three metadata fields are not optional extras. They are what the generated answer
    cites, and what the evaluation uses to decide whether retrieval found the right source,
    so a Passage without them cannot be scored.
    """

    text: str           # the section body, without the "## " heading line
    doc_id: str         # e.g. "03_Benefits_Enrollment" (one of ALLOWED_DOC_IDS)
    doc_title: str      # e.g. "Benefits Enrollment"
    section: str        # e.g. "How to enroll"
    score: float = 0.0  # retriever's relevance score; higher is more relevant

    def citation(self) -> str:
        """Human-readable source label, used in answers and in the evaluation table."""
        return f"{self.doc_title} - {self.section}"

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("Passage.text is empty")
        if not self.section.strip():
            raise ValueError(f"Passage.section is empty for doc_id={self.doc_id!r}")


@dataclass(frozen=True)
class Answer:
    """What the generator returns, and what the interface displays.

    `insufficient_info` is deliberately separate from the answer text. The project brief
    requires the assistant to say when the documents do not cover a question, and the
    evaluation needs to count those cases. Parsing them back out of prose would be fragile,
    so the generator sets the flag explicitly.
    """

    text: str
    sources: list[Passage] = field(default_factory=list)
    insufficient_info: bool = False
    model: str = ""              # e.g. "gemini-2.5-flash", recorded for the report
    latency_s: float = 0.0       # generation time only; the pipeline records the total

    @property
    def citations(self) -> list[str]:
        """De-duplicated source labels, in the order the passages were retrieved."""
        seen, out = set(), []
        for p in self.sources:
            if p.citation() not in seen:
                seen.add(p.citation())
                out.append(p.citation())
        return out


@runtime_checkable
class Retriever(Protocol):
    """Arslan's component.

    Implement this however you like: keyword scoring, TF-IDF, embeddings. The pipeline only
    depends on the signature, so the retrieval method can change without touching anything
    downstream.

    Contract:
      - return at most `k` passages, best first
      - return [] when nothing is relevant; do NOT raise, and do NOT invent a passage
      - every returned Passage carries real doc_id, doc_title and section metadata
    """

    def retrieve(self, question: str, k: int = 4) -> list[Passage]:
        ...


@runtime_checkable
class Generator(Protocol):
    """Christian's component.

    Contract:
      - answer ONLY from the passages given; do not use model world-knowledge about HR
      - when `passages` is empty, or they do not contain the answer, return an Answer with
        insufficient_info=True rather than guessing
      - populate `sources` with the passages actually used, so citations are real
      - do not invent contacts, URLs, deadlines, approval times, or benefit amounts
        (this wording comes from the corpus itself: see 07_HR_Knowledge_Base, section
        "RAG response rules")
    """

    def generate(self, question: str, passages: Sequence[Passage]) -> Answer:
        ...
