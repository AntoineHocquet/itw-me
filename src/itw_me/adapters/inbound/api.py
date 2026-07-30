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
    """TODO(antoine): call service.ask_question, map the Answer to
    AskResponse, and translate domain errors (unknown interview id)
    into a 404. Note the pattern: try/except around the service call,
    raise HTTPException in the except. The domain raises ValueError
    or its own exceptions; it never imports HTTPException.
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")
