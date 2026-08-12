"""Tests for the HTTP layer's correlation-id middleware.

This is the first test in this repo to go through `app` (FastAPI's
TestClient drives real ASGI middleware, unlike calling InterviewService
directly) -- which means importing itw_me.adapters.inbound.api here also
triggers infrastructure/container.py's module-level configure_logging()
call, same as running the real app would. That's intentional: it's the
one place this test suite exercises the composition root's startup path
end to end, with ITW_ME_FAKE_LLM defaulting to "1" (canned adapters), so
it stays fully offline.
"""

import uuid

from fastapi.testclient import TestClient

from itw_me.adapters.inbound.api import app
from itw_me.application.request_context import correlation_id_var

client = TestClient(app)


def test_correlation_id_is_generated_when_the_caller_sends_none():
    response = client.post("/interviews")

    assert response.status_code == 200
    returned = response.headers["X-Correlation-Id"]
    # Doesn't need to be a UUID forever, but it should be *something*
    # request-unique today -- parsing it as one is a cheap way to assert
    # "this looks freshly generated" without hardcoding the exact format.
    uuid.UUID(returned)


def test_correlation_id_is_echoed_back_when_the_caller_sends_one():
    response = client.post(
        "/interviews", headers={"X-Correlation-Id": "from-the-caller"}
    )

    assert response.headers["X-Correlation-Id"] == "from-the-caller"


def test_correlation_id_context_does_not_leak_between_requests():
    """Regression guard for exactly the bug the middleware's `finally:
    correlation_id_var.reset(token)` exists to prevent: without it, the
    ContextVar would keep whatever the LAST request set, and the very
    next log line printed by anything -- including code running outside
    any request at all -- would be mislabeled with a stale correlation id.
    """
    client.post("/interviews", headers={"X-Correlation-Id": "should-not-leak"})

    assert correlation_id_var.get() is None
