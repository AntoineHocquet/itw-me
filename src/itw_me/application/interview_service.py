"""Application layer: orchestrates the domain and the ports.

This is the use case "a visitor asks a question in an interview".
It knows the *order* of operations but contains no business rules
(those live in the domain) and no technology (that lives in adapters).

Phase 3 note on the `logging` import below: `logging` is stdlib, so using
it directly here does NOT violate the "application/ imports only domain
and stdlib" rule -- see infrastructure/logging.py's module docstring for
the full reasoning. What WOULD violate that rule is importing anything
from infrastructure/ (e.g. the JSON formatter) -- this module only ever
calls the generic, vendor-neutral `logging.getLogger(...).info(...)`
API, exactly like it would if there were no formatter at all. Whether
those calls end up as JSON on stdout, plain text, or nowhere is decided
entirely elsewhere (infrastructure/container.py), which is the whole
point of stdlib logging's logger/handler split.
"""

import logging

from itw_me.application.request_context import interaction_id_var
from itw_me.domain.models import Answer, Interview
from itw_me.domain.ports import (
    AnswerGenerator,
    CorpusRetriever,
    InterviewRepository,
)

logger = logging.getLogger(__name__)


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

        Phase 3 instrumentation point: steps 3-6 below run with
        interaction_id_var bound to this turn's Exchange.id, so every
        log line any of retrieve/generate/record/save emits -- from this
        method OR from inside the adapters those ports call -- carries
        the same interaction_id without having to thread it through
        every function signature by hand. (Phase 5 will add OTel spans
        around this same stretch of code, for the same reason: this is
        the one place that already knows "everything from here to here
        is one turn".)
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

        # `interview.ask` just appended a brand-new Exchange (with its
        # own fresh `id`, see domain/models.py) to the aggregate. We read
        # it back via `.history` -- the same read-only view used above,
        # never `.exchanges` directly -- to stay consistent with "outside
        # code only reads the aggregate through its exposed surface".
        current_exchange_id = interview.history[-1].id

        # Bind this turn's id into the request-scoped ContextVar (see
        # application/request_context.py for why it lives there) so it
        # rides along on every log line for the rest of this turn --
        # `logger.info(...)` calls below AND, transitively, anything the
        # adapters behind self._retriever/self._generator log too.
        #
        # `.set()` returns a Token specifically so it can be undone with
        # `.reset(token)` -- NOT setting it back to `None` by hand, which
        # would be wrong the moment this code is ever called re-entrantly
        # (e.g. nested inside another traced operation later on): reset()
        # restores the exact prior value, whatever it was, while a bare
        # `.set(None)` would clobber it.
        token = interaction_id_var.set(current_exchange_id)
        try:
            # 3. Retrieve context chunks via the retriever port.
            logger.info(
                "retrieving corpus chunks",
                extra={"question_length": len(text)},
            )
            context = self._retriever.retrieve(text)

            # 4. Generate an answer via the generator port, passing the
            # prior history so the LLM (or fake) has conversation context.
            logger.info(
                "generating answer",
                extra={"retrieved_chunk_count": len(context)},
            )
            answer = self._generator.generate(question, context, history)

            # 5. Record the answer on the aggregate (enforces that there
            # was a pending question -- see Interview.record_answer).
            interview.record_answer(answer)

            # 6. Persist the whole interview, not just the answer: the
            # repository port only knows how to save/load Interview
            # aggregates, matching the "aggregate root" rule in
            # domain/models.py.
            self._repository.save(interview)
            logger.info(
                "recorded answer",
                extra={
                    "input_tokens": answer.input_tokens,
                    "output_tokens": answer.output_tokens,
                    "citation_count": len(answer.citations),
                },
            )
        finally:
            # However this turn ends -- success, or self._retriever /
            # self._generator raising -- the interaction_id must stop
            # applying once the turn is over. Without this, a later,
            # unrelated log line (e.g. the next request reusing this
            # same OS thread's context in a sync test, or any code that
            # runs after this method returns) could be mislabeled with a
            # turn that already finished.
            interaction_id_var.reset(token)

        # Deliberately NOT logging the question or answer text here: the
        # same discipline metrics labels already follow elsewhere in this
        # codebase (never put unbounded/free-text values where they'll
        # be indexed or aggregated) -- lengths and counts tell you the
        # shape of what happened without a log aggregator ending up
        # holding a copy of every visitor's question forever.

        # 7. Return the answer; the inbound adapter maps it to a DTO.
        return answer
