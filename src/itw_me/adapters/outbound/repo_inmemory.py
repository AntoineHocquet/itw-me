"""Outbound adapters: implementations of the driven ports.

This file contains the in-memory repository, fully implemented as a
worked example. It doubles as the test double for the whole suite:
you can run the entire application without any database.
"""

from itw_me.domain.models import Interview
from itw_me.domain.ports import InterviewRepository


class InMemoryInterviewRepository(InterviewRepository):
    def __init__(self) -> None:
        self._store: dict[str, Interview] = {}

    def get(self, interview_id: str) -> Interview | None:
        return self._store.get(interview_id)

    def save(self, interview: Interview) -> None:
        self._store[interview.id] = interview
