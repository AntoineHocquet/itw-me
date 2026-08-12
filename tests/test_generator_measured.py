"""Unit tests for MeasuredAnswerGenerator.

Same approach as test_retriever_measured.py: fake Counter/Histogram
instruments, real decorator logic under test. The one behavior worth
calling out explicitly: token counters must NOT be touched when the
wrapped generator raises -- there is no Answer to read token counts
from on that path, unlike latency, which is meaningful either way.
"""

from unittest.mock import MagicMock

import pytest

from itw_me.adapters.outbound.generator_measured import MeasuredAnswerGenerator
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


def _build(wrapped: AnswerGenerator):
    llm_latency_seconds = MagicMock()
    llm_input_tokens_total = MagicMock()
    llm_output_tokens_total = MagicMock()
    measured = MeasuredAnswerGenerator(
        wrapped=wrapped,
        llm_latency_seconds=llm_latency_seconds,
        llm_input_tokens_total=llm_input_tokens_total,
        llm_output_tokens_total=llm_output_tokens_total,
    )
    return measured, llm_latency_seconds, llm_input_tokens_total, llm_output_tokens_total


def test_generate_returns_the_wrapped_answer_unchanged():
    answer = Answer(text="hi", citations=(), input_tokens=10, output_tokens=5)
    measured, *_ = _build(_StubGenerator(answer=answer))

    result = measured.generate(Question(text="q"), context=[], history=[])

    assert result == answer


def test_generate_records_latency_and_token_counts_on_success():
    answer = Answer(text="hi", citations=(), input_tokens=10, output_tokens=5)
    measured, latency, input_tokens, output_tokens = _build(
        _StubGenerator(answer=answer)
    )

    measured.generate(Question(text="q"), context=[], history=[])

    latency.record.assert_called_once()
    input_tokens.add.assert_called_once_with(10)
    output_tokens.add.assert_called_once_with(5)


def test_generate_records_latency_but_not_tokens_when_the_wrapped_generator_raises():
    boom = RuntimeError("llm is down")
    measured, latency, input_tokens, output_tokens = _build(
        _StubGenerator(error=boom)
    )

    with pytest.raises(RuntimeError, match="llm is down"):
        measured.generate(Question(text="q"), context=[], history=[])

    latency.record.assert_called_once()
    input_tokens.add.assert_not_called()
    output_tokens.add.assert_not_called()
