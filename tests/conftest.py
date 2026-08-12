"""Session-wide pytest fixtures.

The one fixture here exists to work around a real, somewhat well-known
OpenTelemetry SDK quirk, not to configure anything test-specific.
"""

from opentelemetry import trace
import pytest


@pytest.fixture(scope="session", autouse=True)
def _shut_down_tracer_provider_cleanly():
    """Prevents a harmless-but-alarming traceback at the end of every
    test run.

    infrastructure/tracing.py's BatchSpanProcessor runs a background
    thread that periodically tries to export spans, on its own schedule,
    independent of the main thread. Without this fixture: pytest finishes,
    reports "N passed," and the interpreter starts shutting down --
    closing stdout/stderr as part of that. If the background thread's
    next scheduled export attempt (which fails: no Jaeger is running in
    tests) happens to fire during that window, it tries to log the
    failure through a stream that Python has already closed, and you get
    a `ValueError: I/O operation on closed file` traceback, AFTER the
    test results, that looks like something broke even though every
    test still passed (exit code 0 either way -- this is purely cosmetic,
    but "purely cosmetic" and "looks like a failure" are a bad pair for
    anyone new to the repo running `pytest` for the first time).

    The fix: explicitly shut the provider down ourselves, once, at the
    very end of the session -- while stdout/stderr are still open. This
    joins the background thread (so it cannot fire again later) and logs
    its one "failed to export" message safely, right here, instead of
    racing interpreter teardown. `getattr(..., "shutdown", None)` guards
    the (untaken, in this codebase's own test suite, since
    tests/test_api.py always imports the app) case where no test ever
    triggered container.py's configure_tracing() at all -- the default
    no-op provider has no such method to call.
    """
    yield
    shutdown = getattr(trace.get_tracer_provider(), "shutdown", None)
    if shutdown is not None:
        shutdown()
