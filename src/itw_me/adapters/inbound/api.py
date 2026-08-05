"""Inbound (driving) adapter: HTTP API.

FastAPI's job here is translation only: HTTP in, domain call, HTTP out.
No business logic in this file, ever. If an endpoint function grows
beyond ~10 lines, something is leaking in.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from itw_me.infrastructure.container import build_interview_service

app = FastAPI(title="itw-me")

# Wired once at startup: the composition root decides which adapters
# this service gets. The API doesn't know and doesn't care.
service = build_interview_service()


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
