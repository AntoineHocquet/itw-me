"""Unit tests for LangfuseTracedAnswerGenerator.

We patch the Langfuse class itself (imported into generator_langfuse.py),
the same trick test_llm_openai.py uses for the OpenAI client: no network,
no real Langfuse project needed. `start_as_current_observation` is a
context manager, so the fake client returns a fake context manager whose
`__enter__` yields a fake generation object -- that's what `.update()`
calls land on. What's worth testing here is this adapter's own logic:
delegating to the wrapped generator, returning its answer unchanged,
reporting usage on the generation, and still propagating (after
recording) an exception from the wrapped generator.
"""

from unittest.mock import MagicMock, patch

import pytest

from itw_me.adapters.outbound.generator_langfuse import LangfuseTracedAnswerGenerator
from itw_me.domain.models import Answer, Question
from itw_me.domain.ports import AnswerGenerator


class _StubGenerator(AnswerGenerator):
    def __init__(self, answer=None, error=None):
        self._answer = answer
        self._error = error

    def generate(self, question, context, history):
        if self._error is not None:
            raise self._error
        return self._answer


def _build_traced(wrapped: AnswerGenerator):
    fake_generation = MagicMock()
    fake_observation_cm = MagicMock()
    fake_observation_cm.__enter__.return_value = fake_generation
    fake_observation_cm.__exit__.return_value = False  # never suppress exceptions

    fake_client = MagicMock()
    fake_client.start_as_current_observation.return_value = fake_observation_cm

    with patch(
        "itw_me.adapters.outbound.generator_langfuse.Langfuse",
        return_value=fake_client,
    ):
        traced = LangfuseTracedAnswerGenerator(
            wrapped=wrapped, public_key="pk", secret_key="sk"
        )
    return traced, fake_client, fake_generation


def test_generate_returns_the_wrapped_answer_unchanged():
    answer = Answer(text="I work in Berlin.", citations=(), input_tokens=10, output_tokens=5)
    traced, _, _ = _build_traced(_StubGenerator(answer=answer))

    result = traced.generate(Question(text="Where do you work?"), context=[], history=[])

    assert result == answer


def test_generate_reports_usage_and_output_on_the_generation():
    answer = Answer(text="I work in Berlin.", citations=(), input_tokens=10, output_tokens=5)
    traced, _, fake_generation = _build_traced(_StubGenerator(answer=answer))

    traced.generate(Question(text="Where do you work?"), context=[], history=[])

    fake_generation.update.assert_called_once_with(
        output="I work in Berlin.",
        usage_details={"input": 10, "output": 5},
    )


def test_generate_propagates_wrapped_exception_after_recording_it():
    boom = RuntimeError("LLM is down")
    traced, _, fake_generation = _build_traced(_StubGenerator(error=boom))

    with pytest.raises(RuntimeError, match="LLM is down"):
        traced.generate(Question(text="Anything?"), context=[], history=[])

    fake_generation.update.assert_called_once_with(
        level="ERROR", status_message="LLM is down"
    )
