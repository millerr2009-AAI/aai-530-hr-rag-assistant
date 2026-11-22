# HR RAG Assistant Evaluation

Owner: Russell Miller

## Purpose

Evaluate the fictional HR onboarding assistant on retrieval evidence,
answer correctness, completeness, citation support, and handling of
unavailable or ambiguous information.

These documents are fictional examples, not official HR policy or legal advice.

## Current status

- Eight development cases are defined in questions.json.
- No evaluation results have been recorded by this evaluation workflow.
- End-to-end testing requires the integrated retriever and generator.
- Questions and scoring guidance can be reviewed before integration.

## Evaluation cases

| ID | Focus |
|---|---|
| DEV01 | New-hire paperwork submission |
| DEV02 | Benefits enrollment procedure |
| DEV03 | Training completion verification |
| DEV04 | Access failure and training-deadline synthesis |
| DEV05 | Unspecified benefits enrollment deadline |
| DEV06 | Unavailable employee-specific approval status |
| DEV07 | Ambiguous submission request |
| DEV08 | Payroll-contact retrieval regression |

All current cases are development cases. They may be used for debugging
and must not be described as held-out or unseen tests.

DEV08 preserves the payroll-contact question marked for review in
Arslan's recorded notebook output. That existing result is not a new
run of this evaluation.

## Reference-answer separation

questions.json contains evaluation-only expected points, evidence labels,
and prohibited claims.

Pass only the question to the assistant. Do not include expected answers,
evidence labels, answerability categories, or scoring instructions in the
retrieval query or generation prompt.

## Evaluation procedure

1. Record the Git commit, corpus version, model, retrieval settings,
   and relevant generation settings.
2. Run each question once for the initial baseline.
3. Save the answer, retrieved passages, reported sources, insufficient-info
   flag, timings, and any error before scoring.
4. Compare retrieved passages with the expected evidence groups.
5. Review answer correctness, completeness, and citation support manually.
6. Record unavailable-information and clarification behavior separately.
7. Keep failed runs. Do not silently replace them with successful retries.
8. Label reruns and revised configurations separately from the baseline.

Do not run API-based generation until its configuration and expected
request count have been checked.

## Retrieval evidence coverage

Each evidence group represents a required evidence need.

A group is covered when at least one of its alternative document-ID and
section pairs appears in the retrieved passages.

- all: every required group is covered
- some: at least one, but not every, required group is covered
- none: no required groups are covered
- not_applicable: the case has no required evidence groups
- not_scored: the run has not been reviewed

Evidence-group coverage is a reference-label check, not proof of complete
semantic relevance. If an unlisted passage supplies equivalent evidence,
record the reason and review the reference labels consistently across runs.

## Manual answer scoring

### Correctness

- 0: Incorrect, contradicts the corpus, or makes a material unsupported claim.
- 1: Partly correct but contains an error or misleading statement.
- 2: Correct and appropriately qualified against the corpus.
- Blank: Not scored.

### Completeness

- 0: Provides none of the essential expected guidance.
- 1: Provides some, but not all, essential expected guidance.
- 2: Covers all essential expected guidance.
- Blank: Not scored.

Equivalent wording is acceptable. Do not require verbatim reference answers.

### Citation support

- supported: material factual claims have supporting citations
- partly_supported: some claims lack support or citations are too broad
- unsupported: cited passages do not support the material claims
- missing: factual claims require citations but none are supplied
- not_applicable: no source-backed claim is needed, such as a pure clarification
- not_scored: not reviewed

A nonempty source list does not by itself establish citation support.
Check the actual passage text and the claims attributed to it.

### Unavailable information and ambiguity

Record handling as appropriate, inappropriate, not_applicable, or not_scored.

- DEV05: Do not invent an enrollment deadline; identify the authoritative location.
- DEV06: Do not invent employee approval status; direct to the appropriate owner
  or authoritative system.
- DEV07: Request clarification rather than assume the submission item.

A useful answer may provide supported guidance while acknowledging that
the requested exact value or personal status is unavailable.

Do not equate insufficient_info=True with a correct response.

## Error attribution

Keep these situations distinct:

- corpus_gap: the requested fact is unavailable in the corpus
- retrieval_gap: required evidence exists but was not retrieved
- generation_error: supplied evidence is mishandled or unsupported claims are added
- clarification_needed: the question lacks information needed for a definitive answer
- operational_error: retrieval or generation fails
- integration_error: components do not satisfy the agreed interface

Multiple labels may apply. Explain the classification in reviewer notes.

result.ok indicates whether the pipeline reported an error. It is not
an answer-accuracy score.

## Reporting

Report raw counts and denominators with any percentages.

Report retrieval coverage separately from answer correctness and citation support.
List operational failures separately rather than silently excluding them.

Report timing only for the configuration and environment actually tested.
Do not claim token savings unless token usage was recorded.

Keep Arslan's original notebook results separate from new evaluation runs.

A full-context comparison is optional and has not yet been implemented.

## Integration dependencies

The proposed pipeline expects shared Passage and Answer objects from
hr_assistant.contracts.

Arslan's notebook currently defines its own Passage class and a standalone
retrieve function. End-to-end evaluation requires an agreed adapter or
shared-interface implementation.

Do not modify teammates' components as part of evaluation without coordination.