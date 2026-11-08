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

Initial repository setup and knowledge-base review are underway.

The model, retrieval tools, user interface, and evaluation approach
have not yet been selected.

## Data and Security

- Keep source documents in the local `data/` directory.
- Do not commit local data, API keys, passwords, or other credentials.
- Store credentials in environment variables or a local `.env` file.
- Do not submit real employee records or sensitive personal information.
- Do not commit generated retrieval indexes or local environments.

Data setup and application installation instructions will be added
as implementation progresses.

## Team

Team members and responsibilities will be added after confirmation.
