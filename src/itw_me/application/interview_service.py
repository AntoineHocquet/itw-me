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
        """TODO(antoine): implement the full flow.

        1. Load the interview from the repository (handle not-found).
        2. interview.ask(text)
        3. Retrieve context chunks via the retriever port.
        4. Generate an answer via the generator port
           (pass interview.history so the LLM has conversation context).
        5. interview.record_answer(answer)
        6. Save the interview.
        7. Return the answer.

        Later (phase 3): this method is your prime instrumentation
        point. One OTel span around the whole flow, child spans for
        retrieve and generate.
        """
        raise NotImplementedError
