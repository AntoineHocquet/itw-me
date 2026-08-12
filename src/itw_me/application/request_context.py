"""Cross-cutting request context: correlation and interaction ids.

WHY THIS FILE LIVES IN application/, NOT infrastructure/
----------------------------------------------------------
This is the one file in this phase that exists purely because of the
inward-dependency rule (see docs/phase3_spec.md's Architectural rules):
`domain/` and `application/` may only import stdlib. `contextvars` IS
stdlib, so a module containing nothing but ContextVar declarations is a
perfectly legal citizen of application/ -- but it would NOT be legal to
put these declarations in infrastructure/ and have InterviewService
(application/interview_service.py) import them from there, because that
would be an application -> infrastructure import, which is exactly the
direction this codebase forbids.

The two ids below need to be both *written* and *read* from different
layers:
  - InterviewService (application/) WRITES interaction_id_var, mid-use-case
    (see interview_service.py) -- a same-layer import, always legal.
  - The ASGI middleware (adapters/inbound/api.py) WRITES correlation_id_var
    -- an outer layer (adapters) importing an inner one (application),
    which is always the allowed direction.
  - The JSON log formatter (infrastructure/logging.py) READS both --
    again outer (infrastructure) importing inner (application), allowed.

Note what's NOT here any more: Phase 3 also reserved a `trace_id_var`
here, for Phase 5 to eventually populate. Phase 5 deleted it instead --
`opentelemetry.trace.get_current_span()` already tracks the active span
via this exact same ContextVar mechanism internally, so a hand-rolled
second copy was redundant the moment a real tracer existed. See
infrastructure/logging.py's module docstring for the full story.

Putting the shared state in the innermost layer that needs to touch it,
rather than in whichever layer happens to *use* it most, is what keeps
every import pointing the same way: outward-in, never inward-out.

WHY ContextVar AND NOT A PLAIN MODULE-LEVEL GLOBAL
----------------------------------------------------
A plain global (`correlation_id = None`, then reassign it) would be
shared by every concurrent request -- under uvicorn, many requests are
in flight at once, interleaved on the same event loop, so a plain global
would let one request's correlation id leak into another's log lines.
`contextvars.ContextVar` is stdlib's answer to exactly this problem: each
asyncio Task (and Starlette gives every HTTP request its own Task) gets
its own isolated copy of the ContextVar's value. Setting it in one
request's middleware is invisible to a different request running
"at the same time" on the same event loop.
"""

from __future__ import annotations

from contextvars import ContextVar

# One per HTTP request. Set by the correlation-id middleware in
# adapters/inbound/api.py, as early as possible in the request lifecycle.
correlation_id_var: ContextVar[str | None] = ContextVar(
    "correlation_id", default=None
)

# One per interview turn (Exchange) -- narrower than one request. Today
# there is exactly one turn per request, but the concept is distinct: a
# future batch endpoint or retry could make one request cover several
# turns, each wanting its own interaction_id. Set inside
# InterviewService.ask_question, right after the Exchange is created.
interaction_id_var: ContextVar[str | None] = ContextVar(
    "interaction_id", default=None
)
