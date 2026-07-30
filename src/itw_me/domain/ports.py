"""Ports: interfaces the domain needs the outside world to fulfill.

The domain defines these; adapters implement them. Note the naming:
ports are named after what the domain needs (retrieve, generate, save),
not after the technology that will implement them.
"""

from abc import ABC, abstractmethod

from itw_me.domain.models import Answer, Interview, Question, RetrievedChunk


class CorpusRetriever(ABC):
    """Driven port: fetch relevant corpus chunks for a question."""

    @abstractmethod
    def retrieve(self, query: str, k: int = 4) -> list[RetrievedChunk]:
        ...


class AnswerGenerator(ABC):
    """Driven port: produce an answer given a question and context."""

    @abstractmethod
    def generate(
        self,
        question: Question,
        context: list[RetrievedChunk],
        history: list,  # list[Exchange]; kept loose to avoid circularity fuss
    ) -> Answer:
        ...


class InterviewRepository(ABC):
    """Driven port: persistence for the Interview aggregate."""

    @abstractmethod
    def get(self, interview_id: str) -> Interview | None:
        ...

    @abstractmethod
    def save(self, interview: Interview) -> None:
        ...
