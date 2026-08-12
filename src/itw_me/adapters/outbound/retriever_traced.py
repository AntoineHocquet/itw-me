"""OTel-instrumented tracing decorator adapter for CorpusRetriever
(Phase 5).

Same decorator shape Phase 4 used for metrics (MeasuredCorpusRetriever)
-- wraps ANY CorpusRetriever, so neither retriever_chroma.py nor
retriever_canned.py needs to know tracing exists. What's different from
Measured*: a `Tracer` is a cheap, idempotent handle (unlike a Counter or
Histogram, it carries no name/description metadata to get wrong), so
there's no `Instruments`-style canonical bundle to match here -- just a
constructor default. It's still a constructor parameter, not a bare
module-level `trace.get_tracer(...)` call, specifically so tests can
inject a `Tracer` built from their OWN local TracerProvider (see
tests/test_retriever_traced.py) instead of depending on whichever
TracerProvider happened to be installed globally first -- OTel's trace
API only honors the first `set_tracer_provider()` call per process, so
there is no reliable way to swap in a test-local one after the fact.
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.trace import Tracer

from itw_me.domain.models import RetrievedChunk
from itw_me.domain.ports import CorpusRetriever


class TracedCorpusRetriever(CorpusRetriever):
    def __init__(self, wrapped: CorpusRetriever, tracer: Tracer | None = None) -> None:
        self._wrapped = wrapped
        self._tracer = tracer or trace.get_tracer("itw_me")

    def retrieve(self, query: str, k: int = 4) -> list[RetrievedChunk]:
        # `start_as_current_span` as a context manager, not a manual
        # start()/end() pair: on a normal return it closes the span with
        # OK status; if the wrapped call raises, it records the
        # exception on the span AND marks it ERROR automatically, then
        # re-raises -- unlike Phase 3/4's logging and metrics, which
        # both needed an explicit try/finally to get that same coverage.
        # Tracing's context manager gives you that for free.
        with self._tracer.start_as_current_span("retrieve"):
            return self._wrapped.retrieve(query, k)
