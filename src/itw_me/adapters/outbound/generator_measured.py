"""OTel-instrumented decorator adapter for AnswerGenerator (Phase 4).

Same reasoning as retriever_measured.py: wraps ANY AnswerGenerator, so
`container.py` can layer this under/over LangfuseTracedAnswerGenerator
(see there for the ordering decision) without either decorator knowing
the other exists.
"""

from __future__ import annotations

import time

from opentelemetry.metrics import Counter, Histogram

from itw_me.domain.models import Answer, Question, RetrievedChunk
from itw_me.domain.ports import AnswerGenerator


class MeasuredAnswerGenerator(AnswerGenerator):
    def __init__(
        self,
        wrapped: AnswerGenerator,
        llm_latency_seconds: Histogram,
        llm_input_tokens_total: Counter,
        llm_output_tokens_total: Counter,
    ) -> None:
        self._wrapped = wrapped
        self._llm_latency_seconds = llm_latency_seconds
        self._llm_input_tokens_total = llm_input_tokens_total
        self._llm_output_tokens_total = llm_output_tokens_total

    def generate(
        self,
        question: Question,
        context: list[RetrievedChunk],
        history: list,
    ) -> Answer:
        started_at = time.monotonic()
        try:
            answer = self._wrapped.generate(question, context, history)
        finally:
            # Latency is recorded for failures too -- same reasoning as
            # MeasuredCorpusRetriever's identical `finally`.
            self._llm_latency_seconds.record(time.monotonic() - started_at)

        # Token counters, deliberately OUTSIDE the `finally`: there is no
        # `answer` object to read token counts from if generate() raised
        # -- unlike latency, "how many tokens did a call that never
        # produced an Answer use" isn't a coherent question, so this
        # code correctly never reaches these two lines on that path.
        self._llm_input_tokens_total.add(answer.input_tokens)
        self._llm_output_tokens_total.add(answer.output_tokens)
        return answer
