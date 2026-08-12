"""Unit tests for TracedCorpusRetriever.

The Tracer passed in is a MagicMock, not a real OTel tracer -- and it
has to be, not just "could be": OTel's trace API only honors the FIRST
`set_tracer_provider()` call in a whole pytest process (see
infrastructure/tracing.py's docstring), so there is no reliable way for
this test to install its own real TracerProvider and have a module-
level `trace.get_tracer(...)` call elsewhere actually use it. Injecting
a fake tracer sidesteps that entirely -- which is the whole reason
TracedCorpusRetriever takes one as a constructor parameter instead of
calling trace.get_tracer(...) directly.
"""

from unittest.mock import MagicMock

import pytest

from itw_me.adapters.outbound.retriever_traced import TracedCorpusRetriever
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


def _build_traced(wrapped: CorpusRetriever):
    fake_span_cm = MagicMock()
    fake_span_cm.__exit__.return_value = False  # never suppress exceptions
    fake_tracer = MagicMock()
    fake_tracer.start_as_current_span.return_value = fake_span_cm

    traced = TracedCorpusRetriever(wrapped=wrapped, tracer=fake_tracer)
    return traced, fake_tracer


def test_retrieve_returns_the_wrapped_result_unchanged():
    chunks = [RetrievedChunk(chunk_id="c1", source_file="cv.md", text="x", score=0.5)]
    traced, _ = _build_traced(_StubRetriever(chunks=chunks))

    assert traced.retrieve("query") == chunks


def test_retrieve_opens_a_span_named_retrieve():
    traced, fake_tracer = _build_traced(_StubRetriever(chunks=[]))

    traced.retrieve("query")

    fake_tracer.start_as_current_span.assert_called_once_with("retrieve")


def test_retrieve_propagates_wrapped_exceptions():
    boom = RuntimeError("chroma is down")
    traced, _ = _build_traced(_StubRetriever(error=boom))

    with pytest.raises(RuntimeError, match="chroma is down"):
        traced.retrieve("query")
