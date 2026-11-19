# aai-530-hr-rag-assistant
AAI-530 team final project: an HR onboarding assistant using retrieval-augmented generation over fictional HR documents.

# HR RAG Assistant

AAI-530 team final project: an HR onboarding and policy-question-answering
assistant using retrieval-augmented generation (RAG).

## Project Goal

Build an application that answers employee onboarding questions using a
small collection of fictional HR documents. Responses should identify
supporting sources, acknowledge missing information, and avoid inventing
company policies or employee-specific details.

## Knowledge Base

The sample documents cover:

- First-week onboarding tasks
- Required HR documents
- Benefits enrollment
- Employee training
- Equipment and account requests
- HR policies
- General HR guidance and escalation

These documents are fictional examples for development and evaluation.
They are not an official employee handbook or a source of legal advice.

## Planned Workflow

1. Load the sample text documents.
2. Divide documents into sections while preserving source metadata.
3. Retrieve sections relevant to a user's question.
4. Generate an answer grounded in the retrieved content.
5. Display supporting document titles and sections.
6. Evaluate answer accuracy, source support, and handling of missing information.

## Project Status

The seven fictional HR documents are committed under `data/hr_documents/`.

The component interface, the integration pipeline, the command-line interface and the
contract tests are in place and run against stub components. Retrieval, answer generation
and the evaluation are in development.

## Data and Security

- Keep source documents in the local `data/` directory.
- Do not commit local data, API keys, passwords, or other credentials.
- Store credentials in environment variables or a local `.env` file.
- Do not submit real employee records or sensitive personal information.
- Do not commit generated retrieval indexes or local environments.

Data setup and application installation instructions will be added
as implementation progresses.

## Setup and running

Requires Python 3.10 or newer.

```bash
git clone https://github.com/millerr2009-AAI/aai-530-hr-rag-assistant.git
cd aai-530-hr-rag-assistant
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

API keys go in a local `.env` file, which is gitignored. Copy `.env.example` and fill it in:

```bash
cp .env.example .env
```

Run the assistant against the stub components, which need no API key and no index:

```bash
cd src
python -m hr_assistant.cli --demo -q "How do I enroll in benefits?"
python -m hr_assistant.cli --demo                      # interactive
```

Run the contract tests:

```bash
python -m pytest tests/ -q
```

## Component interface

The data shapes passed between retrieval, generation and the interface are defined in
[`INTERFACE.md`](INTERFACE.md) and in code in `src/hr_assistant/contracts.py`. Build your
component against those types and integration is wiring rather than rewriting.

`src/hr_assistant/stubs.py` provides a fake retriever and generator that satisfy the
contracts, so the pipeline, interface and error handling run before the real components
exist.

## Team

| Member | Responsibility |
|---|---|
| Russell Miller | Test questions, evaluation code, results tables |
| Arslan Isaac | Document loading, chunking, retrieval |
| Christian Lopez | Model setup, prompting, answer generation |
| Faisal Jaffer | Question entry, answer display, pipeline integration, error handling, docs |
