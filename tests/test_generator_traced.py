"""Unit tests for TracedAnswerGenerator. Same approach and same reasoning
as test_retriever_traced.py -- see there for why the tracer is a
MagicMock rather than a real OTel one.
"""

from unittest.mock import MagicMock

import pytest

from itw_me.adapters.outbound.generator_traced import TracedAnswerGenerator
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
    fake_span_cm = MagicMock()
    fake_span_cm.__exit__.return_value = False
    fake_tracer = MagicMock()
    fake_tracer.start_as_current_span.return_value = fake_span_cm

    traced = TracedAnswerGenerator(wrapped=wrapped, tracer=fake_tracer)
    return traced, fake_tracer


def test_generate_returns_the_wrapped_answer_unchanged():
    answer = Answer(text="hi", citations=(), input_tokens=10, output_tokens=5)
    traced, _ = _build_traced(_StubGenerator(answer=answer))

    result = traced.generate(Question(text="q"), context=[], history=[])

    assert result == answer


def test_generate_opens_a_span_named_generate():
    traced, fake_tracer = _build_traced(_StubGenerator(answer=Answer(text="hi", citations=())))

    traced.generate(Question(text="q"), context=[], history=[])

    fake_tracer.start_as_current_span.assert_called_once_with("generate")


def test_generate_propagates_wrapped_exceptions():
    boom = RuntimeError("llm is down")
    traced, _ = _build_traced(_StubGenerator(error=boom))

    with pytest.raises(RuntimeError, match="llm is down"):
        traced.generate(Question(text="q"), context=[], history=[])
