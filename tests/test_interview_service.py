"""Tests run against the domain + application with fake adapters.

No network, no database, no LLM. This is the payoff of hexagonal
architecture: the whole use case is testable in milliseconds.

The first test passes already. The second is yours once
InterviewService.ask_question is implemented.
"""

import pytest

from itw_me.adapters.outbound.repo_inmemory import InMemoryInterviewRepository
from itw_me.application.interview_service import InterviewService
from itw_me.domain.models import Answer, Question, RetrievedChunk
from itw_me.domain.ports import AnswerGenerator, CorpusRetriever


class FakeRetriever(CorpusRetriever):
    def retrieve(self, query: str, k: int = 4) -> list[RetrievedChunk]:
        return [
            RetrievedChunk(
                chunk_id="c1",
                source_file="cv.md",
                text="Antoine works at dida on the VOLT project.",
                score=0.9,
            )
        ]


class FakeGenerator(AnswerGenerator):
    def generate(self, question: Question, context, history) -> Answer:
        return Answer(text=f"Canned answer to: {question.text}", citations=())


@pytest.fixture
def service() -> InterviewService:
    return InterviewService(
        retriever=FakeRetriever(),
        generator=FakeGenerator(),
        repository=InMemoryInterviewRepository(),
    )


def test_start_interview_persists_it(service: InterviewService):
    interview = service.start_interview()
    assert interview.id
    assert service._repository.get(interview.id) is not None


@pytest.mark.skip(reason="Enable once ask_question is implemented")
def test_ask_question_records_exchange(service: InterviewService):
    interview = service.start_interview()
    answer = service.ask_question(interview.id, "Where do you work?")
    assert "Canned answer" in answer.text
    stored = service._repository.get(interview.id)
    assert len(stored.history) == 1
    assert stored.history[0].answer is not None
