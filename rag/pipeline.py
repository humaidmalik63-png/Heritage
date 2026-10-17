"""
End-to-end RAG pipeline.

Wires the grounded pipeline together:

    retriever  ->  generator  ->  grounding validator

Each stage is a separate, swappable component so a language-model provider
can be injected without any network access by default.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from data.evidence.loader import EvidenceRepository
from rag.generator import (
    GroundedAnswer,
    Provider,
    generate_answer,
)
from rag.retriever import GroundedContext, retrieve_context
from rag.validator import ValidationReport, validate_answer

__all__ = ["PipelineResult", "GroundedPipeline"]


@dataclass
class PipelineResult:
    """Full result of one grounded question."""

    question: str
    context: GroundedContext
    answer: GroundedAnswer
    validation: ValidationReport
    stages: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return self.validation.is_valid

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "stages": list(self.stages),
            "is_valid": self.validation.is_valid,
            "context": self.context.to_dict(),
            "answer": self.answer.to_dict(),
            "validation": self.validation.to_dict(),
        }


class GroundedPipeline:
    """Retriever → generator → validator, with an injectable provider."""

    def __init__(
        self,
        repository: Optional[EvidenceRepository] = None,
        provider: Optional[Provider] = None,
    ) -> None:
        self.repository = repository
        self.provider = provider

    def run(self, site_id: str, question: str = "") -> PipelineResult:
        """Run the full grounded pipeline for one site/question pair."""
        # 1. retrieve evidence
        context = retrieve_context(site_id, question, self.repository)

        # 2. generate an answer from that evidence only
        answer = generate_answer(question, context, self.provider)

        # 3. validate the answer against that same evidence
        validation = validate_answer(answer, context)

        return PipelineResult(
            question=question,
            context=context,
            answer=answer,
            validation=validation,
            stages=["retrieve", "generate", "validate"],
        )
