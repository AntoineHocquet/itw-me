"""Tests for the structured JSON logging formatter.

Deliberately testing `_JsonFormatter` directly rather than going through
`configure_logging()`: that function mutates the ROOT logger's handlers
process-wide (see its docstring), which is exactly the right thing for a
composition root to do once at startup, and exactly the wrong thing for
a test to do -- it would leak into every other test that runs afterwards
in the same pytest session. Constructing the formatter directly and
calling `.format()` on a hand-built LogRecord exercises the same
formatting logic with zero global side effects.
"""

import json
import logging

from itw_me.application.request_context import (
    correlation_id_var,
    interaction_id_var,
)
from itw_me.infrastructure.logging import _JsonFormatter


def _make_record(msg: str = "hello", **extra) -> logging.LogRecord:
    record = logging.LogRecord(
        name="itw_me.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )
    # This is exactly what `logger.info(msg, extra={...})` does under the
    # hood -- stdlib logging just setattr()s each key/value onto the
    # LogRecord it builds. Doing it by hand here keeps this test from
    # needing a real logger/handler pipeline just to build one record.
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_format_emits_valid_json_with_core_fields():
    formatter = _JsonFormatter(environment="test")

    payload = json.loads(formatter.format(_make_record("hello world")))

    assert payload["level"] == "INFO"
    assert payload["service"] == "itw-me"
    assert payload["environment"] == "test"
    assert payload["logger"] == "itw_me.test"
    assert payload["message"] == "hello world"
    # No request in flight while building this record -- the ContextVars
    # fall back to their declared default, None, rather than raising.
    assert payload["correlation_id"] is None
    assert payload["interaction_id"] is None
    assert payload["trace_id"] is None


def test_format_reads_ids_from_context_vars():
    formatter = _JsonFormatter(environment="test")

    # .set()/.reset() around the assertion, not a bare assignment: this
    # is the same discipline production code follows (see
    # interview_service.py and api.py) -- and skipping the reset here
    # would leak "corr-1"/"turn-1" into every test that runs after this
    # one in the same session.
    correlation_token = correlation_id_var.set("corr-1")
    interaction_token = interaction_id_var.set("turn-1")
    try:
        payload = json.loads(formatter.format(_make_record()))
    finally:
        correlation_id_var.reset(correlation_token)
        interaction_id_var.reset(interaction_token)

    assert payload["correlation_id"] == "corr-1"
    assert payload["interaction_id"] == "turn-1"


def test_format_includes_extra_fields_alongside_the_core_ones():
    formatter = _JsonFormatter(environment="test")

    payload = json.loads(
        formatter.format(_make_record("generating answer", input_tokens=42))
    )

    assert payload["input_tokens"] == 42
    assert payload["message"] == "generating answer"


def test_format_never_raises_on_a_non_json_serializable_extra_value():
    class Unserializable:
        def __str__(self) -> str:
            return "<unserializable>"

    formatter = _JsonFormatter(environment="test")

    payload = json.loads(
        formatter.format(_make_record("oops", weird=Unserializable()))
    )

    assert payload["weird"] == "<unserializable>"


def test_format_reads_trace_id_from_the_currently_active_span():
    """Phase 5. Uses a REAL, throwaway TracerProvider -- unlike the
    decorator tests (test_retriever_traced.py etc.), which have to mock
    the tracer because OTel's trace API only honors one
    set_tracer_provider() call per process. That limitation is about
    provider REGISTRATION; it has nothing to do with what this test
    needs, which is just "some real span, currently active, anywhere" --
    `local_provider.get_tracer(...)` builds a tracer bound directly to a
    provider THIS test constructed, entirely bypassing the global
    registry, so there's no conflict with whatever other tests already
    claimed that global slot.
    """
    from opentelemetry.sdk.trace import TracerProvider

    formatter = _JsonFormatter(environment="test")
    local_tracer = TracerProvider().get_tracer("test")

    with local_tracer.start_as_current_span("test-span") as span:
        payload = json.loads(formatter.format(_make_record()))
        expected_trace_id = format(span.get_span_context().trace_id, "032x")

    assert payload["trace_id"] == expected_trace_id
    # 32 lowercase hex digits -- the form Jaeger and friends search by,
    # not Python's own default int/hex representation.
    assert len(payload["trace_id"]) == 32
    assert payload["trace_id"] == payload["trace_id"].lower()


def test_format_trace_id_is_none_once_the_span_has_ended():
    from opentelemetry.sdk.trace import TracerProvider

    formatter = _JsonFormatter(environment="test")
    local_tracer = TracerProvider().get_tracer("test")

    with local_tracer.start_as_current_span("test-span"):
        pass  # span is active only inside this block

    payload = json.loads(formatter.format(_make_record()))

    assert payload["trace_id"] is None
