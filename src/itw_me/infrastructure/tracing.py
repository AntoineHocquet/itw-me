"""Distributed tracing (Phase 5 -- VOLT's Step 3, "Workflow Visibility,"
exactly).

METRICS ARE PULLED, TRACES ARE PUSHED -- WHY THAT DIFFERENCE BITES YOU
IN A TEST SUITE
------------------------------------------------------------------------
Phase 4's Prometheus setup is a PULL model: this process just keeps
numbers in memory and answers "/metrics" when asked. If nobody asks, no
network call ever happens, and nothing can time out.

Tracing here is a PUSH model: `BatchSpanProcessor` batches finished spans
and pushes them, over HTTP, to an OTLP collector (Jaeger). If nothing is
listening -- true for every test run, and true for local dev without
`docker compose up` -- every export attempt fails with connection-
refused. That alone is harmless (spans are simply dropped). The part
that bites: `BatchSpanProcessor` registers an `atexit` handler that
tries to FLUSH any pending spans on process exit, and the underlying
HTTP client retries failed exports with growing backoff BEFORE giving
up. Left at the SDK's defaults, this was measured (by actually running
it, not by reading the docs) to add 6+ seconds to every single test run
that imports this module -- happening silently, after all assertions
already passed, as the interpreter shuts down.

The fix: cap both the per-export HTTP timeout (`timeout=`) AND the
processor's own export budget (`export_timeout_millis=`) low. With both
at ~1 second, a missing collector fails in milliseconds instead of
seconds -- verified the same way the problem was found, by actually
timing it. A real Jaeger container answers in milliseconds anyway, so
this costs nothing once one is actually running; it only bounds the
worst case when one isn't.
"""

from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_EXPORT_TIMEOUT_SECONDS = 1


def configure_tracing(otlp_traces_endpoint: str) -> None:
    """Call once, at composition-root startup (see container.py) -- the
    same "configure once here, use get_tracer(...)/get_current_span()
    everywhere" shape as configure_logging()/configure_metrics().

    `otlp_traces_endpoint` is passed in already resolved, not read here
    via `os.getenv`, for the same reason configure_logging() and
    configure_metrics() take their config as plain parameters: this
    codebase's rules say environment variables are read only at the
    composition root, and passing plain values keeps this function
    trivially unit-testable without touching real env state.
    """
    resource = Resource.create({"service.name": "itw-me"})
    exporter = OTLPSpanExporter(
        endpoint=otlp_traces_endpoint, timeout=_EXPORT_TIMEOUT_SECONDS
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(
            exporter,
            export_timeout_millis=_EXPORT_TIMEOUT_SECONDS * 1000,
        )
    )

    # Global, process-wide, by design -- same shape as
    # metrics.set_meter_provider(). One sharp edge worth knowing, since
    # it is NOT the same as logging's root-logger reconfiguration: the
    # OTel trace API only honors the FIRST set_tracer_provider() call in
    # a process. Any later call is silently ignored (a warning is
    # logged, nothing else happens) -- there is no "last call wins" the
    # way there is for logging.basicConfig()-style setup. This is why
    # this codebase's own tests never call this function directly (see
    # tests/test_retriever_traced.py and friends): they inject a
    # `Tracer` built from their OWN local TracerProvider instead of
    # fighting over the one global slot every other test importing
    # api.py/container.py has already claimed.
    trace.set_tracer_provider(provider)
