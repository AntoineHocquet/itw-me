"""Composition root: the ONE place where concrete adapters are chosen
and wired into the application service.

Everywhere else in the codebase depends on ports (abstractions).
Only this file knows the real technology stack.
"""

import os

from dotenv import load_dotenv

from itw_me.application.interview_service import InterviewService
from itw_me.domain.ports import AnswerGenerator, CorpusRetriever
from itw_me.adapters.outbound.repo_inmemory import InMemoryInterviewRepository
from itw_me.adapters.outbound.retriever_canned import CannedCorpusRetriever
from itw_me.adapters.outbound.retriever_chroma import ChromaCorpusRetriever
from itw_me.adapters.outbound.generator_canned import CannedAnswerGenerator
from itw_me.adapters.outbound.llm_openai import OpenAIAnswerGenerator

# Load a local .env file (if any) into os.environ before anything below
# reads it. A no-op when no .env exists (e.g. in CI or a container that
# sets real environment variables directly) -- this is purely a local-dev
# convenience, never a required step.
load_dotenv()


def build_interview_service() -> InterviewService:
    # Environment variables are read here and only here (never inside
    # domain/ or application/): the composition root is where "which
    # real world are we running against" gets decided.
    #
    # Phase 1 (default, no external services needed): ITW_ME_FAKE_LLM
    # defaults to "1", so `uvicorn itw_me.adapters.inbound.api:app`
    # answers with canned text out of the box.
    use_fake_llm = os.getenv("ITW_ME_FAKE_LLM", "1") == "1"

    retriever: CorpusRetriever
    generator: AnswerGenerator
    if use_fake_llm:
        retriever = CannedCorpusRetriever()
        generator = CannedAnswerGenerator()
    else:
        # Phase 2 (real RAG): retrieval always goes against the corpus
        # ingested by scripts/ingest.py. The LLM side defaults to a local
        # Ollama server -- zero cost while developing/testing this phase,
        # since OpenAIAnswerGenerator only needs an OpenAI-*compatible*
        # endpoint, and Ollama exposes exactly that. Point ITW_ME_LLM_BASE_URL
        # and ITW_ME_MODEL at the real OpenAI API (plus a real
        # OPENAI_API_KEY) for production-quality answers -- no code changes,
        # only configuration.
        retriever = ChromaCorpusRetriever()
        generator = OpenAIAnswerGenerator(
            model=os.getenv("ITW_ME_MODEL", "llama3.1"),
            base_url=os.getenv("ITW_ME_LLM_BASE_URL", "http://localhost:11434/v1"),
            # Ollama ignores this value entirely, but the openai client
            # requires api_key to be set to *something*.
            api_key=os.getenv("OPENAI_API_KEY", "ollama"),
        )

    return InterviewService(
        retriever=retriever,
        generator=generator,
        repository=InMemoryInterviewRepository(),
    )
