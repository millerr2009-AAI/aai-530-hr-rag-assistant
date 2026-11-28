"""Contract tests.

Run these against YOUR component to check it satisfies the shared interface before
integration. They need no API key and no index.

    python -m pytest tests/ -q          (from the repo root, with src/ on the path)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from hr_assistant.contracts import ALLOWED_DOC_IDS, Answer, Generator, Passage, Retriever
from hr_assistant.pipeline import HRAssistant, PipelineError
from hr_assistant.stubs import ExplodingRetriever, StubGenerator, StubRetriever


def test_stubs_satisfy_the_protocols():
    assert isinstance(StubRetriever(), Retriever)
    assert isinstance(StubGenerator(), Generator)


def test_passage_requires_real_metadata():
    with pytest.raises(ValueError):
        Passage(text="", doc_id="06_HR_Policies", doc_title="HR Policies", section="x")
    with pytest.raises(ValueError):
        Passage(text="body", doc_id="06_HR_Policies", doc_title="HR Policies", section=" ")


def test_citation_format():
    p = Passage(text="body", doc_id="03_Benefits_Enrollment",
                doc_title="Benefits Enrollment", section="How to enroll")
    assert p.citation() == "Benefits Enrollment - How to enroll"


def test_citations_are_deduplicated_and_ordered():
    a = Passage(text="t", doc_id="06_HR_Policies", doc_title="HR Policies", section="Leave")
    ans = Answer(text="x", sources=[a, a])
    assert ans.citations == ["HR Policies - Leave"]


def test_happy_path_returns_sources():
    r = HRAssistant(StubRetriever(), StubGenerator()).ask("How do I enroll in benefits?")
    assert r.ok and r.n_passages > 0 and r.answer.citations


def test_empty_retrieval_flags_insufficient_info_without_calling_the_model():
    r = HRAssistant(StubRetriever(always_empty=True), StubGenerator()).ask("anything")
    assert r.answer.insufficient_info and r.answer.citations == [] and r.ok


def test_retrieval_failure_is_reported_not_raised():
    r = HRAssistant(ExplodingRetriever(), StubGenerator()).ask("How do I request a laptop?")
    assert not r.ok and "retrieval failed" in r.error
    assert r.answer.insufficient_info          # degrades safely rather than inventing


def test_generation_failure_is_reported_not_raised():
    class Boom:
        def generate(self, question, passages):
            raise RuntimeError("API quota exhausted")
    r = HRAssistant(StubRetriever(), Boom()).ask("How do I enroll in benefits?")
    assert not r.ok and "generation failed" in r.error and r.answer.insufficient_info


def test_fabricated_doc_ids_are_dropped():
    """A citation to a document that does not exist is worse than no answer."""
    class Liar:
        def retrieve(self, question, k=4):
            return [Passage(text="made up", doc_id="99_Not_Real",
                            doc_title="Fake", section="Nope")]
    r = HRAssistant(Liar(), StubGenerator()).ask("anything")
    assert r.n_passages == 0 and r.answer.insufficient_info


@pytest.mark.parametrize("bad", ["", "   ", None])
def test_unusable_questions_raise(bad):
    with pytest.raises(PipelineError):
        HRAssistant(StubRetriever(), StubGenerator()).ask(bad)


def test_allowed_doc_ids_match_the_corpus_on_disk():
    corpus = Path(__file__).resolve().parents[1] / "data" / "hr_documents"
    on_disk = {p.stem for p in corpus.glob("*.txt")}
    assert on_disk == set(ALLOWED_DOC_IDS), f"corpus/contract mismatch: {on_disk}"
