"""Domain models for the Interview bounded context.

Pure Python. No FastAPI, no OpenAI, no database imports allowed here.
If you feel tempted to import one of those, you are about to violate
the inward-dependency rule.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


# ---------- Value objects (immutable, no identity) ----------

@dataclass(frozen=True)
class Citation:
    """Points to the corpus chunk an answer was grounded on."""
    source_file: str      # e.g. "cv.md"
    chunk_id: str
    excerpt: str


@dataclass(frozen=True)
class Question:
    text: str
    asked_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass(frozen=True)
class Answer:
    text: str
    citations: tuple[Citation, ...]
    # Observability data is legitimate domain output here:
    # token counts are a fact about how the answer was produced.
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(frozen=True)
class RetrievedChunk:
    """What the retriever port returns. Not yet an Answer."""
    chunk_id: str
    source_file: str
    text: str
    score: float


# ---------- Entities / aggregate ----------

@dataclass
class Exchange:
    """One Q&A turn inside an interview."""
    question: Question
    answer: Answer | None = None


@dataclass
class Interview:
    """Aggregate root: a single visitor's interview session.

    All mutations of exchanges must go through methods on this class,
    never by manipulating .exchanges from outside. That is what makes
    it an aggregate and not just a list holder.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    exchanges: list[Exchange] = field(default_factory=list)

    def ask(self, text: str) -> Question:
        question = Question(text=text)
        self.exchanges.append(Exchange(question=question))
        return question

    def record_answer(self, answer: Answer) -> None:
        if not self.exchanges or self.exchanges[-1].answer is not None:
            raise ValueError("No pending question to answer.")
        self.exchanges[-1].answer = answer

    @property
    def history(self) -> list[Exchange]:
        return list(self.exchanges)  # defensive copy
