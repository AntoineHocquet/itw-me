"""Structured JSON logging (Phase 3 -- VOLT's Step 1, "logging and
correlation foundation").

The core idea, if you only read one paragraph of this file: Python's
stdlib `logging` module already separates "how do I write a log line"
(any module, anywhere, calls `logging.getLogger(__name__).info(...)`)
from "what does a log line actually look like" (decided once, centrally,
by whatever Formatter is attached to the root logger). That separation
is exactly what lets application/interview_service.py call plain stdlib
`logging` directly -- logging usage is not a vendor dependency, only the
*formatting policy* below is infrastructure's job to decide.

Phase 5 update on `trace_id`: originally (Phase 3) this formatter read a
hand-rolled `trace_id_var` ContextVar, reserved for exactly this phase to
populate. It turned out unnecessary and was DELETED rather than kept:
`opentelemetry.trace.get_current_span()` already tracks "the currently
active span," and it already does so via the exact same `contextvars`
mechanism `trace_id_var` was hand-rolling -- OTel ships its own version
of the thing Phase 3 built from scratch, because every tracing SDK needs
it. Once Phase 5 introduces a real tracer, asking OTel directly is both
less code and automatically correct the moment ANY span is active,
anywhere, with no separate "remember to also update trace_id_var" step
at each of the several places Phase 5 creates spans. Keeping the old
ContextVar around, now permanently unused, would have been strictly
worse than deleting it.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

from opentelemetry import trace as otel_trace

from itw_me.application.request_context import correlation_id_var, interaction_id_var

# Every attribute a stdlib LogRecord carries out of the box (see the
# logging module's source for the authoritative list). Anything a log
# call attaches beyond this set arrived via `logger.info(msg, extra={...})`
# -- see _JsonFormatter.format below for what happens to it. Hardcoding
# this set is the price of supporting arbitrary `extra=` fields without
# every call site having to register them somewhere first.
_RESERVED_RECORD_ATTRS = frozenset(
    {
        "name", "msg", "args", "levelname", "levelno", "pathname",
        "filename", "module", "exc_info", "exc_text", "stack_info",
        "lineno", "funcName", "created", "msecs", "relativeCreated",
        "thread", "threadName", "processName", "process", "taskName",
        "message",
    }
)


class _JsonFormatter(logging.Formatter):
    """Renders one JSON object per log line instead of logging's default
    plain-text layout.

    `environment` is a constructor parameter, not something this class
    reads via `os.getenv` itself: per this repo's architectural rules,
    environment variables are read only at the composition root
    (infrastructure/container.py) -- this formatter receives the already-
    resolved value, which also makes it trivial to unit test without
    touching real environment state (see tests/test_logging.py).
    """

    def __init__(self, environment: str) -> None:
        super().__init__()
        self._environment = environment

    def format(self, record: logging.LogRecord) -> str:
        # get_current_span() NEVER returns None -- with no span active,
        # it returns a sentinel "non-recording" span whose context has
        # is_valid=False. Checking that, rather than checking for None,
        # is the correct way to ask "is there really a trace right now"
        # with this API. trace_id is a 128-bit int; formatting it as 32
        # lowercase hex digits matches the form every tracing backend
        # (Jaeger included) displays and searches by.
        span_context = otel_trace.get_current_span().get_span_context()
        trace_id = format(span_context.trace_id, "032x") if span_context.is_valid else None

        payload = {
            # record.created is a Unix timestamp (float seconds since the
            # epoch -- timezone-agnostic by construction). Deliberately
            # NOT using logging.Formatter's own formatTime(): its default
            # renders in *local* time, which is exactly the kind of
            # ambiguity a correlation-friendly log line should never have
            # -- two services in different timezones would print
            # different-looking timestamps for the same instant.
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "service": "itw-me",
            "environment": self._environment,
            "logger": record.name,
            "message": record.getMessage(),
            # .get() returns the ContextVar's default (None) when nothing
            # upstream has set it -- e.g. any log line emitted outside an
            # HTTP request (a script, a background job) simply gets
            # correlation_id: null, rather than raising.
            "correlation_id": correlation_id_var.get(),
            "interaction_id": interaction_id_var.get(),
            "trace_id": trace_id,
        }

        # Fold in whatever a call site attached via `extra={...}` -- e.g.
        # interview_service.py's `logger.info("...", extra={"input_tokens": n})`.
        # This is what makes the logging "structured": ad hoc fields ride
        # along on the LogRecord itself (that's what `extra` does under
        # the hood), and this formatter surfaces anything it doesn't
        # already recognize, without needing to know about it in advance.
        for key, value in record.__dict__.items():
            if key not in _RESERVED_RECORD_ATTRS and key not in payload:
                payload[key] = value

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        # default=str: a log line should never crash the process because
        # someone passed a UUID or datetime into `extra=`. Worst case, an
        # unusual object degrades to its str() instead of failing to log
        # at all -- and failing to log a real error because the LOGGING
        # itself blew up is a strictly worse outcome.
        return json.dumps(payload, default=str)


def configure_logging(environment: str, level: int = logging.INFO) -> None:
    """Install the JSON formatter on the root logger. Call this exactly
    once, at process startup (see infrastructure/container.py) -- every
    `logging.getLogger(__name__)` call anywhere in the codebase (domain
    excluded, by convention: the domain stays silent, see below) inherits
    this configuration automatically. No other module needs to know this
    function exists.

    Why domain/ has no log statements: domain code is pure business logic
    that the tests already exercise directly, with no I/O -- logging is
    itself a side effect, and it belongs at the boundary where side
    effects already live (application orchestration, adapters), not
    inside the aggregate whose whole value proposition is "no I/O".

    THE UVICORN GOTCHA THIS FUNCTION WORKS AROUND
    ----------------------------------------------
    uvicorn configures its OWN handlers on the "uvicorn", "uvicorn.error",
    and "uvicorn.access" loggers at startup, and sets propagate=False on
    them. propagate=False means "stop here, never hand this record up to
    the root logger" -- so without the loop below, uvicorn's own request
    line (the classic `INFO: 127.0.0.1:0 - "POST /interviews HTTP/1.1"
    200 OK`) would keep printing in uvicorn's plain-text format forever,
    no matter what we do to the root logger. Clearing their handlers and
    flipping propagate back on routes uvicorn's own logging through this
    exact same JSON formatter, so "every log line is JSON" is actually
    true, not just true for lines this codebase prints itself.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter(environment=environment))

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(level)

    for uvicorn_logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uvicorn_logger = logging.getLogger(uvicorn_logger_name)
        uvicorn_logger.handlers = []
        uvicorn_logger.propagate = True
