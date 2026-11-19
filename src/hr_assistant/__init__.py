"""HR RAG assistant: shared contracts, stub components, and the integration pipeline."""

from .contracts import ALLOWED_DOC_IDS, CORPUS_DIR, Answer, Generator, Passage, Retriever
from .pipeline import HRAssistant, PipelineError

__all__ = ["Passage", "Answer", "Retriever", "Generator", "HRAssistant",
           "PipelineError", "CORPUS_DIR", "ALLOWED_DOC_IDS"]
