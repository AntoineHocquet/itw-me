"""Phase 1 stand-in for AnswerGenerator: no OpenAI key, no tokens spent.

Same idea as retriever_canned.py: a real adapter implementing the
AnswerGenerator port, wired in by the composition root so the whole
hexagon (HTTP -> application -> domain -> ports -> adapters) can be
exercised locally with zero external dependencies. It is the
production counterpart of the FakeGenerator used in tests -- deliberately
similar, because "an adapter you can run the app with" and "an adapter
you can test the app with" are the same idea applied to two different
callers (uvicorn vs pytest).
"""

from itw_me.domain.models import Answer, Question, RetrievedChunk
from itw_me.domain.ports import AnswerGenerator


class CannedAnswerGenerator(AnswerGenerator):
    """Echoes the question back in a fixed template, with no citations.

    input_tokens / output_tokens stay at their default of 0: no LLM
    call happened, so there is nothing to report. Once
    OpenAIAnswerGenerator is implemented (phase 2), switch to it via
    the ITW_ME_FAKE_LLM env var in infrastructure/container.py.
    """

    def generate(
        self,
        question: Question,
        context: list[RetrievedChunk],
        history: list,
    ) -> Answer:
        return Answer(
            text=(
                f"(offline dev mode) You asked: {question.text!r}. "
                "I'm not grounded in the corpus yet -- set "
                "ITW_ME_FAKE_LLM=0 once the real retriever and LLM "
                "adapters are implemented."
            ),
            citations=(),
        )
