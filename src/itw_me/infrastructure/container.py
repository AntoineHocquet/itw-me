"""Composition root: the ONE place where concrete adapters are chosen
and wired into the application service.

Everywhere else in the codebase depends on ports (abstractions).
Only this file knows the real technology stack.
"""

import os

from itw_me.application.interview_service import InterviewService
from itw_me.domain.ports import AnswerGenerator, CorpusRetriever
from itw_me.adapters.outbound.repo_inmemory import InMemoryInterviewRepository
from itw_me.adapters.outbound.retriever_canned import CannedCorpusRetriever
from itw_me.adapters.outbound.retriever_chroma import ChromaCorpusRetriever
from itw_me.adapters.outbound.generator_canned import CannedAnswerGenerator
from itw_me.adapters.outbound.llm_openai import OpenAIAnswerGenerator


def build_interview_service() -> InterviewService:
    # Environment variables are read here and only here (never inside
    # domain/ or application/): the composition root is where "which
    # real world are we running against" gets decided.
    #
    # Phase 1 (default, no external services needed): ITW_ME_FAKE_LLM
    # defaults to "1", so `uvicorn itw_me.adapters.inbound.api:app`
    # answers with canned text out of the box. Once corpus ingestion
    # (phase 2) and a real API key exist, run with ITW_ME_FAKE_LLM=0
    # to switch to ChromaCorpusRetriever + OpenAIAnswerGenerator --
    # nothing else in the codebase needs to change, because both pairs
    # implement the same ports.
    use_fake_llm = os.getenv("ITW_ME_FAKE_LLM", "1") == "1"

    retriever: CorpusRetriever
    generator: AnswerGenerator
    if use_fake_llm:
        retriever = CannedCorpusRetriever()
        generator = CannedAnswerGenerator()
    else:
        retriever = ChromaCorpusRetriever()
        generator = OpenAIAnswerGenerator(
            model=os.getenv("ITW_ME_MODEL", "gpt-4o-mini")
        )

    return InterviewService(
        retriever=retriever,
        generator=generator,
        repository=InMemoryInterviewRepository(),
    )
