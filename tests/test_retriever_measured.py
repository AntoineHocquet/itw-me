"""Unit tests for MeasuredCorpusRetriever.

The Histogram passed in is a MagicMock, not a real OTel instrument --
same "fake the vendor boundary" trick used throughout this test suite
(test_llm_openai.py mocks OpenAI, test_generator_langfuse.py mocks
Langfuse). What's worth testing here is this decorator's own logic:
it returns the wrapped result unchanged, and it records latency on
every path, including the one where the wrapped retriever raises.
"""

from unittest.mock import MagicMock

import pytest

from itw_me.adapters.outbound.retriever_measured import MeasuredCorpusRetriever
from itw_me.domain.models import RetrievedChunk
from itw_me.domain.ports import CorpusRetriever


class _StubRetriever(CorpusRetriever):
    def __init__(self, chunks=None, error=None):
        self._chunks = chunks if chunks is not None else []
        self._error = error

    def retrieve(self, query: str, k: int = 4):
        if self._error is not None:
            raise self._error
        return self._chunks


def test_retrieve_returns_the_wrapped_result_unchanged():
    chunks = [
        RetrievedChunk(chunk_id="c1", source_file="cv.md", text="x", score=0.5)
    ]
    measured = MeasuredCorpusRetriever(
        wrapped=_StubRetriever(chunks=chunks),
        retrieval_latency_seconds=MagicMock(),
    )

    assert measured.retrieve("query") == chunks


def test_retrieve_records_a_non_negative_latency():
    histogram = MagicMock()
    measured = MeasuredCorpusRetriever(
        wrapped=_StubRetriever(chunks=[]), retrieval_latency_seconds=histogram
    )

    measured.retrieve("query")

    histogram.record.assert_called_once()
    (elapsed,), _kwargs = histogram.record.call_args
    assert elapsed >= 0


def test_retrieve_records_latency_even_when_the_wrapped_retriever_raises():
    boom = RuntimeError("chroma is down")
    histogram = MagicMock()
    measured = MeasuredCorpusRetriever(
        wrapped=_StubRetriever(error=boom), retrieval_latency_seconds=histogram
    )

    with pytest.raises(RuntimeError, match="chroma is down"):
        measured.retrieve("query")

    histogram.record.assert_called_once()
