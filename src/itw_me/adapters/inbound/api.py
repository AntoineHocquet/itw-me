"""Inbound (driving) adapter: HTTP API.

FastAPI's job here is translation only: HTTP in, domain call, HTTP out.
No business logic in this file, ever. If an endpoint function grows
beyond ~10 lines, something is leaking in.
"""

import uuid

from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
from pydantic import BaseModel

from itw_me.application.request_context import correlation_id_var
from itw_me.infrastructure.container import build_interview_service

app = FastAPI(title="itw-me")

# Wired once at startup: the composition root decides which adapters
# this service gets. The API doesn't know and doesn't care.
service = build_interview_service()


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Phase 3, VOLT Step 1's "introduce correlation IDs": every request
    gets a correlation_id, reused across service boundaries if the
    caller already has one, minted fresh otherwise -- then echoed back
    on the response so the caller (a browser, a load test, another
    service) can quote it back to you when reporting a problem.

    WHY THIS WORKS WITHOUT PASSING correlation_id THROUGH EVERY
    FUNCTION SIGNATURE
    -------------------------------------------------------------
    `@app.middleware("http")` wraps the ENTIRE rest of the request --
    everything `call_next(request)` runs, including InterviewService and
    every adapter it calls, executes as normal Python function calls
    nested inside this `try` block, all within the same asyncio Task.
    `correlation_id_var.set(...)` therefore stays visible for the whole
    request without itw-me's application/domain code needing to know
    this middleware -- or even HTTP -- exists. That is the same trick
    interaction_id_var uses one layer down, in
    application/interview_service.py.

    Why reset() in a `finally`, not just letting the variable "expire":
    Starlette happens to give each request its own Task already, so in
    practice nothing would leak even without this. But relying on that
    implementation detail, rather than being explicit, is exactly the
    kind of thing that quietly breaks when a framework internal changes
    -- resetting explicitly costs nothing and removes the dependency.
    """
    incoming_correlation_id = request.headers.get("X-Correlation-Id")
    correlation_id = incoming_correlation_id or str(uuid.uuid4())

    token = correlation_id_var.set(correlation_id)
    try:
        response = await call_next(request)
    finally:
        correlation_id_var.reset(token)

    response.headers["X-Correlation-Id"] = correlation_id
    return response


@app.get("/metrics")
def metrics_endpoint() -> Response:
    """Phase 4, VOLT Step 2's "expose a Prometheus metrics endpoint."

    Deliberately NOT `opentelemetry.exporter.prometheus`-specific code:
    that package's whole job (see infrastructure/telemetry.py) is
    registering itw-me's instruments with `prometheus_client`'s global
    `REGISTRY` -- a *plain* Prometheus concept with no OTel involvement.
    `generate_latest(REGISTRY)` renders whatever is currently registered
    there (itw-me's six instruments, plus a few standard Python process
    metrics prometheus_client adds for free) as the Prometheus text
    exposition format. This route is the entire "server" side of a pull-
    based metrics system: it does no polling, no batching, no pushing --
    it just answers "what do the counters/histograms say right now"
    whenever asked, which is all a Prometheus scrape ever does.
    """
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


class AskRequest(BaseModel):
    text: str


class AskResponse(BaseModel):
    answer: str
    citations: list[str]


@app.post("/interviews")
def start_interview():
    interview = service.start_interview()
    return {"interview_id": interview.id}


@app.post("/interviews/{interview_id}/questions", response_model=AskResponse)
def ask(interview_id: str, req: AskRequest):
    """Translate HTTP <-> domain, nothing more.

    The pattern: try/except around the service call, HTTPException
    only in the except. InterviewService.ask_question raises a plain
    ValueError when the interview id is unknown -- that's a domain-level
    fact ("this aggregate does not exist"), and it's this adapter's job,
    not the domain's, to know that the HTTP vocabulary for that is 404.
    """
    try:
        answer = service.ask_question(interview_id, req.text)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    # DTO mapping: the API's response shape (AskResponse) is deliberately
    # its own type, not the domain's Answer. Citation is rendered as the
    # "[source_file#chunk_id]" label that phase 2's prompt will also use,
    # so visitors and the LLM see the same reference format.
    return AskResponse(
        answer=answer.text,
        citations=[f"{c.source_file}#{c.chunk_id}" for c in answer.citations],
    )
