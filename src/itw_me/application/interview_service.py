"""Application layer: orchestrates the domain and the ports.

This is the use case "a visitor asks a question in an interview".
It knows the *order* of operations but contains no business rules
(those live in the domain) and no technology (that lives in adapters).
"""

from itw_me.domain.models import Answer, Interview
from itw_me.domain.ports import (
    AnswerGenerator,
    CorpusRetriever,
    InterviewRepository,
)


class InterviewService:
    def __init__(
        self,
        retriever: CorpusRetriever,
        generator: AnswerGenerator,
        repository: InterviewRepository,
    ) -> None:
        self._retriever = retriever
        self._generator = generator
        self._repository = repository

    def start_interview(self) -> Interview:
        interview = Interview()
        self._repository.save(interview)
        return interview

    def ask_question(self, interview_id: str, text: str) -> Answer:
        """Run one interview turn: load -> ask -> retrieve -> generate -> record -> save.

        This is the use case in its entirety. Notice what is absent:
        no HTTP, no Chroma, no OpenAI client. Those live behind the
        ports (self._retriever, self._generator, self._repository),
        which are injected by the composition root (infrastructure/
        container.py). Swap every adapter for a fake, as the tests
        do, and this method's logic is unaffected -- that is the
        entire point of hexagonal architecture.

        Later (phase 3): this method is the prime instrumentation
        point. One OTel span around the whole flow, child spans for
        retrieve and generate.
        """
        # 1. Load the interview. Not-found is a domain-level fact, not
        # an HTTP concept, so we signal it with a plain exception
        # (ValueError) rather than importing HTTPException here. The
        # inbound adapter (api.py) is the one that knows what a 404
        # is, and it's the one that translates this into it.
        interview = self._repository.get(interview_id)
        if interview is None:
            raise ValueError(f"No interview found with id {interview_id!r}")

        # Snapshot the conversation *before* appending the current
        # question: the generator port receives the new question
        # separately, so history here means "everything already
        # answered", not "including the turn we're about to produce".
        history = interview.history

        # 2. Record the question on the aggregate. This is where the
        # domain enforces its own rules (e.g. Interview.ask appending
        # a pending Exchange) -- the service just calls the method,
        # it doesn't reimplement the invariant.
        question = interview.ask(text)

        # 3. Retrieve context chunks via the retriever port.
        context = self._retriever.retrieve(text)

        # 4. Generate an answer via the generator port, passing the
        # prior history so the LLM (or fake) has conversation context.
        answer = self._generator.generate(question, context, history)

        # 5. Record the answer on the aggregate (enforces that there
        # was a pending question -- see Interview.record_answer).
        interview.record_answer(answer)

        # 6. Persist the whole interview, not just the answer: the
        # repository port only knows how to save/load Interview
        # aggregates, matching the "aggregate root" rule in domain/models.py.
        self._repository.save(interview)

        # 7. Return the answer; the inbound adapter maps it to a DTO.
        return answer
