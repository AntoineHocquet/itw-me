"""Composition root: the ONE place where concrete adapters are chosen
and wired into the application service.

Everywhere else in the codebase depends on ports (abstractions).
Only this file knows the real technology stack.
"""

import os

from itw_me.application.interview_service import InterviewService
from itw_me.adapters.outbound.repo_inmemory import InMemoryInterviewRepository
from itw_me.adapters.outbound.retriever_chroma import ChromaCorpusRetriever
from itw_me.adapters.outbound.llm_openai import OpenAIAnswerGenerator


def build_interview_service() -> InterviewService:
    # TODO(antoine): later, switch on env vars, e.g.
    # ITW_ME_FAKE_LLM=1 -> a canned-answer generator for local dev
    # so you can develop the API without burning tokens.
    return InterviewService(
        retriever=ChromaCorpusRetriever(),
        generator=OpenAIAnswerGenerator(
            model=os.getenv("ITW_ME_MODEL", "gpt-4o-mini")
        ),
        repository=InMemoryInterviewRepository(),
    )
