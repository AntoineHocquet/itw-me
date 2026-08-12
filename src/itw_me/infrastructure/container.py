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
from itw_me.adapters.outbound.retriever_measured import MeasuredCorpusRetriever
from itw_me.adapters.outbound.retriever_traced import TracedCorpusRetriever
from itw_me.adapters.outbound.generator_canned import CannedAnswerGenerator
from itw_me.adapters.outbound.generator_measured import MeasuredAnswerGenerator
from itw_me.adapters.outbound.generator_traced import TracedAnswerGenerator
from itw_me.adapters.outbound.llm_openai import OpenAIAnswerGenerator
from itw_me.infrastructure.logging import configure_logging
from itw_me.infrastructure.telemetry import configure_metrics
from itw_me.infrastructure.tracing import configure_tracing

# Load a local .env file (if any) into os.environ before anything below
# reads it. A no-op when no .env exists (e.g. in CI or a container that
# sets real environment variables directly) -- this is purely a local-dev
# convenience, never a required step.
load_dotenv()

# Phase 3: configure structured JSON logging once, at import time of the
# composition root -- the same "do it once, here, not scattered
# elsewhere" reasoning as load_dotenv() above. This has to run AFTER
# load_dotenv() (so a local .env's ITW_ME_ENV is visible) and BEFORE
# build_interview_service() is ever called (so nothing logs before the
# formatter is installed). Module-level placement guarantees both: this
# file's top-level statements only run once, the first time anything
# imports itw_me.infrastructure.container, and Python runs them in the
# order they're written.
#
# Reading ITW_ME_ENV here, not inside infrastructure/logging.py, is
# deliberate: this file is THE composition root, the one place this
# codebase's architectural rules say environment variables get read (see
# docs/phase3_spec.md, rule 2) -- configure_logging() itself only
# accepts an already-resolved `environment` string, which is also what
# keeps it trivially unit-testable (see tests/test_logging.py).
configure_logging(environment=os.getenv("ITW_ME_ENV", "dev"))

# Phase 4: same "once, here, before anything else" placement as
# configure_logging() just above -- and for the same reason. This MUST
# run before build_interview_service() constructs an InterviewService,
# so its two self-created instruments (see interview_service.py) bind to
# the real Prometheus-backed MeterProvider from the very first call,
# never to the no-op fallback tests rely on. `_instruments` is module
# state, not a parameter threaded through every function below, purely
# because build_interview_service() is the only function that needs it
# and it's simpler to close over it than to pass it as an argument
# nothing else uses.
_instruments = configure_metrics()

# Phase 5: same placement, same reason -- and see
# infrastructure/tracing.py's docstring for why this one especially must
# run exactly once, here, before anything calls trace.get_tracer(...):
# the OTel trace API only honors the FIRST set_tracer_provider() call in
# the whole process, unlike logging's root-logger handlers (which can be
# reassigned repeatedly) or metrics' meter provider (whose instruments
# proxy-upgrade regardless of call order).
#
# Read OTEL_EXPORTER_OTLP_TRACES_ENDPOINT here, not inside tracing.py,
# for the same "env vars only at the composition root" reason as every
# other configure_*() call in this file. Default is the OTel spec's own
# convention for "an OTLP/HTTP collector on this same machine" -- exactly
# right for `uvicorn` run directly against a standalone Jaeger container
# (`docker run -p 4318:4318 -p 16686:16686 jaegertracing/all-in-one`).
# Inside `docker compose up`, this app can't reach the jaeger CONTAINER
# via "localhost" (that means "this container," not "the compose
# network") -- docker-compose.yml's `app` service overrides this same
# env var to `http://jaeger:4318/v1/traces`, Jaeger's service name being
# the hostname Docker's internal DNS resolves for it. Same pattern
# ITW_ME_LLM_BASE_URL already uses there for Ollama.
configure_tracing(
    otlp_traces_endpoint=os.getenv(
        "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://localhost:4318/v1/traces"
    )
)


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
    model_name: str | None = None
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
        model_name = os.getenv("ITW_ME_MODEL", "llama3.1")
        generator = OpenAIAnswerGenerator(
            model=model_name,
            base_url=os.getenv("ITW_ME_LLM_BASE_URL", "http://localhost:11434/v1"),
            # Ollama ignores this value entirely, but the openai client
            # requires api_key to be set to *something*.
            api_key=os.getenv("OPENAI_API_KEY", "ollama"),
        )

    # Phase 5: wrap BOTH ports in their tracing decorator FIRST -- i.e.
    # innermost of everything that follows. A span's duration is just a
    # timestamp pair; it costs nothing measurable for Measured*'s
    # histograms to sit outside it, and putting tracing closest to the
    # real vendor call means the "retrieve"/"generate" spans reflect the
    # actual port call as purely as possible, before any other
    # decorator's own bookkeeping has a chance to run inside them.
    retriever = TracedCorpusRetriever(wrapped=retriever)
    generator = TracedAnswerGenerator(wrapped=generator)

    # Phase 4: wrap BOTH ports in their OTel metrics decorator next --
    # metrics apply the same way whether the underlying adapter is canned
    # or real, same as Phase 3's logging. This happens BEFORE the
    # Langfuse wrapping below, on purpose: see the comment there for why
    # wrapping order matters once more than one decorator stacks up.
    retriever = MeasuredCorpusRetriever(
        wrapped=retriever,
        retrieval_latency_seconds=_instruments.retrieval_latency_seconds,
    )
    generator = MeasuredAnswerGenerator(
        wrapped=generator,
        llm_latency_seconds=_instruments.llm_latency_seconds,
        llm_input_tokens_total=_instruments.llm_input_tokens_total,
        llm_output_tokens_total=_instruments.llm_output_tokens_total,
    )

    # Optional Langfuse tracing (see docs/langfuse_spec.md): wraps whichever
    # generator was chosen above. Only imported here, inside the branch that
    # actually needs it -- with the env vars unset (the default), `langfuse`
    # is never imported at all, so it stays a true no-op without the
    # optional dependency installed.
    #
    # Wrapping order, now that there are THREE decorators around
    # `generator`: TracedAnswerGenerator innermost, then
    # MeasuredAnswerGenerator, then LangfuseTracedAnswerGenerator
    # outermost (built here). That means itw_me_llm_latency_seconds times
    # only the raw LLM call, never Langfuse's own bookkeeping overhead --
    # if the order were reversed, every request would look slightly
    # slower to Prometheus the moment Langfuse tracing was turned on, for
    # a reason that has nothing to do with the LLM itself. The "generate"
    # SPAN's duration is subject to the same reasoning, even though a
    # span isn't a stored aggregate the way a histogram is: a trace
    # showing "generate: 2.3s" should mean "the LLM call took 2.3s," not
    # "the LLM call plus whatever Langfuse's SDK needed to do on this
    # thread also took 2.3s."
    langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    if langfuse_public_key and langfuse_secret_key:
        from itw_me.adapters.outbound.generator_langfuse import (
            LangfuseTracedAnswerGenerator,
        )

        generator = LangfuseTracedAnswerGenerator(
            wrapped=generator,
            public_key=langfuse_public_key,
            secret_key=langfuse_secret_key,
            host=os.getenv("LANGFUSE_HOST"),
            model=model_name,
        )

    return InterviewService(
        retriever=retriever,
        generator=generator,
        repository=InMemoryInterviewRepository(),
        questions_total=_instruments.questions_total,
        request_latency_seconds=_instruments.request_latency_seconds,
    )
