"""Langfuse-backed LLM tracing, layered on any AnswerGenerator.

This is the training repo's answer to VOLT's existing Langfuse
integration: LLM-specific observability (prompt, retrieved context,
tokens, latency) that the generic OpenTelemetry work in Phases 3-6
doesn't capture. See docs/langfuse_spec.md for why this adapter exists
outside that numbered sequence entirely.

Every langfuse import stays in this file. Unlike opentelemetry, the
Langfuse SDK gets no exception to the inward-dependency rule -- it is
vendor-specific end to end, so it must never reach application/ or
domain/, and container.py only imports this module when Langfuse is
actually configured (see there).

Note on the SDK version: Langfuse's Python client (v3+) was rewritten on
top of OpenTelemetry -- there is no `client.trace()`/`client.generation()`
anymore. `start_as_current_observation(as_type="generation")` is the
current equivalent: a context manager that creates one observation
(Langfuse's word for a span/trace node) and ends it on exit.
"""

from __future__ import annotations

from langfuse import Langfuse

from itw_me.domain.models import Answer, Question, RetrievedChunk
from itw_me.domain.ports import AnswerGenerator


class LangfuseTracedAnswerGenerator(AnswerGenerator):
    """Decorator adapter: wraps any AnswerGenerator, traces every call
    to Langfuse, and returns exactly what the wrapped generator returned.

    Composed in container.py only when LANGFUSE_PUBLIC_KEY and
    LANGFUSE_SECRET_KEY are both set -- absent those, this class is
    never instantiated, and the `langfuse` import above is never even
    reached, so it stays a true no-op for offline/test runs.
    """

    def __init__(
        self,
        wrapped: AnswerGenerator,
        public_key: str,
        secret_key: str,
        host: str | None = None,
        model: str | None = None,
    ) -> None:
        self._wrapped = wrapped
        self._model = model
        self._client = Langfuse(public_key=public_key, secret_key=secret_key, host=host)

    def generate(
        self,
        question: Question,
        context: list[RetrievedChunk],
        history: list,
    ) -> Answer:
        # Unlike a Prometheus label, a Langfuse observation is exactly the
        # place raw prompt/answer content belongs -- cardinality is not a
        # concern here, visibility is the point.
        with self._client.start_as_current_observation(
            name="generate",
            as_type="generation",
            model=self._model,
            input={
                "question": question.text,
                "history_length": len(history),
                "retrieved_chunks": [
                    f"{chunk.source_file}#{chunk.chunk_id}" for chunk in context
                ],
            },
        ) as generation:
            try:
                answer = self._wrapped.generate(question, context, history)
            except Exception as exc:
                # Record the failure in Langfuse, but never swallow it --
                # this adapter observes, it does not change error-handling
                # behavior. The observation still ends (and reports the
                # exception) when the `with` block exits here.
                generation.update(level="ERROR", status_message=str(exc))
                raise

            generation.update(
                output=answer.text,
                usage_details={
                    "input": answer.input_tokens,
                    "output": answer.output_tokens,
                },
            )
            return answer
