# Component interface

This is the agreed shape of the data passing between our three components. Building to it
means integration is wiring rather than rewriting.

Proposed by Faisal for the integration layer. **If something here does not suit your
component, say so and we change it once, here, rather than each of us adapting around it.**

## Who owns what

| Component | Owner | Produces | Lives in |
|---|---|---|---|
| Document loading, chunking, retrieval | Arslan | `list[Passage]` | `src/hr_assistant/retrieval.py` |
| Prompting and answer generation | Christian | `Answer` | `src/hr_assistant/generation.py` |
| Interface, pipeline, error handling, docs | Faisal | `AskResult` | `src/hr_assistant/pipeline.py`, `cli.py` |
| Test questions, evaluation, results tables | Russell | metrics | `evaluation/` |

Only the pipeline imports both halves. Neither of you needs the other's code to work.

## The two types

```python
@dataclass(frozen=True)
class Passage:
    text: str           # the section body, without the "## " heading
    doc_id: str         # "03_Benefits_Enrollment"
    doc_title: str      # "Benefits Enrollment"
    section: str        # "How to enroll"
    score: float = 0.0  # higher is more relevant

@dataclass(frozen=True)
class Answer:
    text: str
    sources: list[Passage]        # the passages actually used
    insufficient_info: bool       # True when the documents do not cover the question
    model: str                    # "gemini-2.5-flash"
    latency_s: float
```

The three metadata fields on `Passage` are not optional extras. They are what the answer
cites and what the evaluation scores retrieval against, so a `Passage` without them cannot
be graded.

`insufficient_info` is a separate flag rather than something to detect in the answer text.
The brief requires the assistant to say when the documents do not cover a question, and
Russell's evaluation has to count those cases; parsing that back out of prose is fragile.

## The two functions

```python
# Arslan
def retrieve(question: str, k: int = 4) -> list[Passage]: ...

# Christian
def generate(question: str, passages: Sequence[Passage]) -> Answer: ...
```

**Retriever contract**
- at most `k` passages, best first
- return `[]` when nothing is relevant; do not raise, and do not invent a passage
- every `Passage` carries real `doc_id`, `doc_title`, `section`

**Generator contract**
- answer only from the passages given; no model world-knowledge about HR
- empty `passages`, or passages that do not contain the answer, means
  `insufficient_info=True`, not a guess
- populate `sources` with the passages actually used
- do not invent contacts, URLs, deadlines, approval times, or benefit amounts

That last rule is not mine. It is in the corpus: see `07_HR_Knowledge_Base.txt`, section
**"RAG response rules"**, which also asks answers to cite document title and section and to
distinguish examples from official policy. That section is effectively a spec for the
generator prompt.

## The corpus

`data/hr_documents/` holds the seven `.txt` files. The `.docx` copies are the same content
and are not committed; use the `.txt` for ingestion.

Every document has the same machine-readable shape:

```
# First-Week Onboarding Tasks          <- doc_title
Document ID: 01_First_Week_Onboarding_Tasks
Version: 1.0

## Before day one                      <- section
HR sends a welcome message ...         <- text
```

Splitting on `^## ` gives **36 chunks across 7 documents**, averaging 36 words, which matches
the corpus README's "one section per chunk". The whole corpus is about **1,773 tokens**.

Note `.gitignore` now excludes `data/*` rather than `data/`, with `!data/hr_documents/`.
Git cannot re-include a path inside an excluded directory, so the original pattern made the
corpus impossible to commit. Local scratch files and generated indexes under `data/` are
still ignored.

## Build against the stubs

`stubs.py` has a fake retriever and generator satisfying both contracts, so the pipeline runs
now:

```bash
cd src
python -m hr_assistant.cli --demo -q "How do I enroll in benefits?"
python -m hr_assistant.cli --demo                 # interactive
```

When your component is ready, uncomment the two `COMPONENT WIRING` lines in `cli.py`.

## Check your component before integrating

```bash
pip install pytest
python -m pytest tests/ -q
```

`tests/test_contract.py` covers the happy path, empty retrieval, retriever exceptions,
generator exceptions, fabricated `doc_id`s, and unusable questions. Point them at your class
instead of the stub and they should still pass.

## One thing worth deciding early

The entire corpus is ~1,773 tokens, so all seven documents fit in a single Gemini prompt with
room to spare. A system that skips retrieval and pastes everything in would probably score
*higher* on answer accuracy than our RAG pipeline, because nothing can be retrieved wrongly.

Rather than a problem, this is worth running as a **comparison arm** in the evaluation: RAG
versus full-context. We would be able to report what retrieval costs in accuracy against what
it buys in precise citations and roughly 95% fewer input tokens per query, which is a stronger
finding than "our system answered questions". Given the Gemini free tier's low daily request
cap, the token saving is a real measured result rather than a theoretical one.

Worth agreeing on before the evaluation code is locked down.
