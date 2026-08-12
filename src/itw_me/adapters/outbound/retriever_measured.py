"""OTel-instrumented decorator adapter for CorpusRetriever (Phase 4).

Decorator adapter, not "instrument inside ChromaCorpusRetriever": this
wraps ANY CorpusRetriever -- Chroma, canned, or a future replacement --
so retrieval latency is measured identically no matter which concrete
retriever container.py chose, and neither retriever_chroma.py nor
retriever_canned.py needs to know OpenTelemetry exists. Phase 5 reuses
this exact shape (a decorator wrapping the same port) for tracing spans,
per docs/phase5_spec.md.
"""

from __future__ import annotations

import time

from opentelemetry.metrics import Histogram

from itw_me.domain.models import RetrievedChunk
from itw_me.domain.ports import CorpusRetriever


class MeasuredCorpusRetriever(CorpusRetriever):
    def __init__(
        self, wrapped: CorpusRetriever, retrieval_latency_seconds: Histogram
    ) -> None:
        self._wrapped = wrapped
        self._retrieval_latency_seconds = retrieval_latency_seconds

    def retrieve(self, query: str, k: int = 4) -> list[RetrievedChunk]:
        started_at = time.monotonic()
        try:
            return self._wrapped.retrieve(query, k)
        finally:
            # In `finally`, not after a bare return: a failed retrieval
            # still took time, and "how long do failures take" is
            # exactly the kind of thing a latency histogram should be
            # able to answer -- excluding failures would quietly bias
            # this metric toward only the fast, successful path.
            self._retrieval_latency_seconds.record(time.monotonic() - started_at)
