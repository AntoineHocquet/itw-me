"""Tests run against the domain + application with fake adapters.

No network, no database, no LLM. This is the payoff of hexagonal
architecture: the whole use case is testable in milliseconds.

The first test passes already. The second is yours once
InterviewService.ask_question is implemented.
"""

import pytest

from itw_me.adapters.outbound.repo_inmemory import InMemoryInterviewRepository
from itw_me.application.interview_service import InterviewService
from itw_me.application.request_context import interaction_id_var
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


class InteractionIdSpyGenerator(AnswerGenerator):
    """A fake generator whose only job is to observe what
    interaction_id_var is bound to *while generate() runs* -- i.e. from
    inside the exact stretch of InterviewService.ask_question that Phase
    3 wraps in interaction_id_var.set()/.reset(). A plain FakeGenerator
    can't answer "was the context var actually set at this point in the
    call", only a spy that reads it live can.
    """

    def __init__(self) -> None:
        self.seen_interaction_id: str | None = None

    def generate(self, question: Question, context, history) -> Answer:
        self.seen_interaction_id = interaction_id_var.get()
        return Answer(text="ok", citations=())


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


def test_ask_question_records_exchange(service: InterviewService):
    interview = service.start_interview()
    answer = service.ask_question(interview.id, "Where do you work?")
    assert "Canned answer" in answer.text
    stored = service._repository.get(interview.id)
    assert len(stored.history) == 1
    assert stored.history[0].answer is not None


def test_ask_question_binds_interaction_id_while_generating():
    spy = InteractionIdSpyGenerator()
    service = InterviewService(
        retriever=FakeRetriever(),
        generator=spy,
        repository=InMemoryInterviewRepository(),
    )
    interview = service.start_interview()

    service.ask_question(interview.id, "Where do you work?")

    stored = service._repository.get(interview.id)
    # The id the generator observed mid-call must be THIS turn's
    # Exchange.id -- not None, not some other turn's -- proving
    # interaction_id_var was bound before generate() ran, to the right
    # value, not just set to *something*.
    assert spy.seen_interaction_id == stored.history[0].id


def test_ask_question_unbinds_interaction_id_once_the_turn_ends():
    service = InterviewService(
        retriever=FakeRetriever(),
        generator=FakeGenerator(),
        repository=InMemoryInterviewRepository(),
    )
    interview = service.start_interview()

    service.ask_question(interview.id, "Where do you work?")

    # Same regression guard as test_api.py's correlation-id equivalent:
    # without the `finally: interaction_id_var.reset(token)` in
    # ask_question, this would still read the just-finished turn's id.
    assert interaction_id_var.get() is None
