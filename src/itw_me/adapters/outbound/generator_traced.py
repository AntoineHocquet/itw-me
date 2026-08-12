"""OTel-instrumented tracing decorator adapter for AnswerGenerator
(Phase 5).

Same reasoning as retriever_traced.py. Where this one gets wired in
`container.py`, relative to MeasuredAnswerGenerator and
LangfuseTracedAnswerGenerator, is its own decision -- see the comment at
that wiring point.
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.trace import Tracer

from itw_me.domain.models import Answer, Question, RetrievedChunk
from itw_me.domain.ports import AnswerGenerator


class TracedAnswerGenerator(AnswerGenerator):
    def __init__(self, wrapped: AnswerGenerator, tracer: Tracer | None = None) -> None:
        self._wrapped = wrapped
        self._tracer = tracer or trace.get_tracer("itw_me")

    def generate(
        self,
        question: Question,
        context: list[RetrievedChunk],
        history: list,
    ) -> Answer:
        with self._tracer.start_as_current_span("generate"):
            return self._wrapped.generate(question, context, history)
