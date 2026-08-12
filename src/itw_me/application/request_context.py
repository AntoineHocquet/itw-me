"""Cross-cutting request context: correlation, interaction, and trace ids.

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

The three ids below need to be both *written* and *read* from different
layers:
  - InterviewService (application/) WRITES interaction_id_var, mid-use-case
    (see interview_service.py) -- a same-layer import, always legal.
  - The ASGI middleware (adapters/inbound/api.py) WRITES correlation_id_var
    -- an outer layer (adapters) importing an inner one (application),
    which is always the allowed direction.
  - The JSON log formatter (infrastructure/logging.py) READS all three --
    again outer (infrastructure) importing inner (application), allowed.

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

# Reserved for Phase 5 (see docs/phase5_spec.md) -- nothing writes to this
# yet, so infrastructure/logging.py's formatter always reads back `None`
# for it today. It is declared here now, ahead of need, specifically so
# that adding real distributed tracing later is a pure *write-side*
# change (wherever spans get created, call trace_id_var.set(...)) with
# zero changes required to the logging code that already reads it.
trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)
