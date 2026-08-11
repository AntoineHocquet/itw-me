# Task: Complete the itw-me RAG chatbot (Phase 3) -- logging & correlation foundation

## Context

itw-me is a small RAG chatbot: visitors "interview" Antoine by chatting with a bot
grounded in a corpus of markdown documents about him (CV, bio, experience). By the
time this phase starts, Phase 1 (hexagonal skeleton, offline) and Phase 2 (real RAG
against Chroma + OpenAI) are both done -- see [phase1_spec.md](phase1_spec.md) and
[phase2_spec.md](phase2_spec.md).

This phase exists to mirror, exactly, Step 1 ("Logging and Correlation Foundation")
of a real "BACKEND OBSERVABILITY" spike ticket written for VOLT, a different RAG
chatbot Antoine works on professionally and where he will write this same rollout
for real. Earlier drafts of this phase bundled logging together with metrics (VOLT's
Step 2); that has been split back apart so that finishing this phase corresponds to
finishing *exactly* VOLT's Step 1 -- no more, no less -- making it usable as a literal
checklist rather than an approximation. Metrics are [phase4_spec.md](phase4_spec.md)
(VOLT Step 2), tracing is [phase5_spec.md](phase5_spec.md) (VOLT Step 3), and
dashboards/alerting are [phase6_spec.md](phase6_spec.md) (VOLT Step 4). Langfuse is
intentionally not part of this sequence at all -- see
[langfuse_spec.md](langfuse_spec.md) for why.

This is also a training codebase. Code quality, comments explaining non-obvious
decisions, and architectural discipline matter more than feature count. Prefer
clear code over clever code.

## Current state (do not rewrite, extend)

- Phase 1 + Phase 2 done: the API answers real questions against the real corpus,
  with citations, using ChromaCorpusRetriever and OpenAIAnswerGenerator (or the
  canned pair when `ITW_ME_FAKE_LLM=1`).
- [langfuse_spec.md](langfuse_spec.md) done too: `AnswerGenerator` is optionally
  wrapped in `LangfuseTracedAnswerGenerator` when `LANGFUSE_PUBLIC_KEY`/
  `LANGFUSE_SECRET_KEY` are set -- unrelated to this phase's logging work, but
  worth knowing the generator you see wired in `container.py` may already be a
  Langfuse-wrapped one.
- No logging module anywhere in `src/itw_me` (`grep -r "^import logging\|^logger"
  src/itw_me` returns nothing) -- whatever logging exists today is `uvicorn`'s
  own, unstructured, with no request correlation.
- `domain/models.py`'s `Exchange` has no id of its own -- only the parent
  `Interview` has one (`interview.id`). There is nothing today that identifies
  a single question/answer turn independently of its position in the list.
- `observability/prometheus.yml` and `docker-compose.yml` exist, prepared with
  `prometheus` and `grafana` services -- irrelevant to this phase, they matter
  starting Phase 4.

## Architectural rules (hard constraints, violating these fails the task)

1. Inward dependency rule: `domain/` imports only stdlib. `application/` imports
   only domain and stdlib. Vendor libraries never appear in `domain/` or
   `application/`. Nothing in this phase needs a vendor library at all --
   structured logging is stdlib `logging` plus a custom `Formatter`.
2. Environment variables are read only at the composition root
   (`infrastructure/container.py`) or inside adapters, never in domain or
   application code.
3. Existing tests must stay green. Tests must not require network access, API
   keys, or running containers.
4. Naming convention for adapters: Technology + PortName (not exercised by this
   phase specifically, but keep in mind for later phases).

## Phase 3: structured logging & correlation IDs (VOLT's Step 1, exactly)

VOLT's Step 1 is three bullets: standardize structured logging, introduce
correlation IDs, align logging conventions. Here is each, translated to itw-me:

1. **Structured JSON logging**: create `src/itw_me/infrastructure/logging.py`
   with a `configure_logging()` function -- stdlib `logging` plus a small custom
   `Formatter` subclass that emits one JSON object per line. Fields, adapted from
   VOLT's logging standard:
   - `timestamp`, `level`, `service` (`"itw-me"`), `environment` (from
     `ITW_ME_ENV`, default `"dev"`)
   - `correlation_id` (step 2 below), `interaction_id` (step 3 below) -- read
     from contextvars, `None` outside request scope
   - `trace_id` -- reserved in the schema now, always `None` here; no tracer
     exists until Phase 5. Reserving the field now, rather than adding it later,
     means Phase 5 changes zero logging code -- it only has to populate a slot
     that already exists.
   - VOLT also lists `thread_id`; itw-me runs a single asyncio process under
     uvicorn, so there is no meaningful thread model to report -- this field is
     deliberately dropped, not silently renamed to something misleading.
   Call `configure_logging()` once, at the top of `container.py`.
2. **Correlation ID propagation**: a small ASGI middleware in `api.py` that reads
   the incoming `X-Correlation-Id` header, or generates a `uuid4` if absent, sets
   it on a `ContextVar` for the duration of the request, and echoes it back on the
   response. Every log line emitted while handling that request picks it up
   automatically via the formatter in step 1.
3. **Interaction id ("align logging conventions" -- one durable id per turn, not
   just per request)**: add `id: str = field(default_factory=lambda:
   str(uuid.uuid4()))` to `Exchange` in `domain/models.py` -- a per-turn identity
   is a legitimate domain fact (same justification as the existing token-count
   fields on `Answer`), not an observability bolt-on. In
   `InterviewService.ask_question`, set the `interaction_id` contextvar to the
   new exchange's id right after `interview.ask(...)` returns, so retrieve/
   generate/record logs for that turn are all tagged with it.
4. **README**: add a short section on the request lifecycle -- correlation id
   in/out via headers, where JSON logs land (stdout).

## Definition of done

- `pytest` green, offline, no keys or containers needed.
- Every log line emitted while handling one HTTP request is single-line JSON
  and shares one `correlation_id`; the exchange's `interaction_id` appears on
  the retrieve/generate/record log lines for that turn; `trace_id` is present
  in the schema and always `None` (Phase 5 populates it).
- `grep -r "import chromadb\|import openai" src/itw_me/domain
  src/itw_me/application` still returns nothing -- this phase touches no vendor
  boundary at all.

Next: [phase4_spec.md](phase4_spec.md) (VOLT Step 2: OpenTelemetry instrumentation
and core metrics).
