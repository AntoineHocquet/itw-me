# Task: Complete the itw-me RAG chatbot (Phase 5) -- workflow & dependency tracing -- done

## Context

itw-me is a small RAG chatbot: visitors "interview" Antoine by chatting with a bot
grounded in a corpus of markdown documents about him (CV, bio, experience). By the
time this phase starts, Phase 3 (logging + correlation --
[phase3_spec.md](phase3_spec.md)) and Phase 4 (OTel metrics + Prometheus --
[phase4_spec.md](phase4_spec.md)) are both done.

This phase exists to mirror, exactly, Step 3 ("Workflow Visibility") of the VOLT
observability spike ticket this sequence is tracking. VOLT's Step 3 is two bullets:
add tracing for the agent workflow steps (`plan`/`retrieve`/`reflect`/`generate`),
and add dependency tracing (Azure OpenAI, Azure AI Search, PostgreSQL, Blob
Storage). Both are covered below, translated to itw-me's actual architecture --
which is a plain retrieve-then-generate RAG, not an agentic workflow, and has only
two real external dependencies (an LLM and a vector store), not four. These are
architecture differences, not scope cut -- see the note under step 2.

Langfuse is deliberately **not** part of this phase, even though VOLT's Step 3 is
the closest thematic fit ("workflow visibility"). VOLT's ticket lists Langfuse
under "Current State" -- it already exists there -- not under "Proposed Rollout".
Nothing in VOLT's remaining rollout requires building it. It is documented
separately, as a fully optional addition, in [langfuse_spec.md](langfuse_spec.md),
specifically so it does not get counted as part of "what remains" when this phase
is used as a checklist for VOLT's actual Step 3.

This is also a training codebase. Code quality, comments explaining non-obvious
decisions, and architectural discipline matter more than feature count. Prefer
clear code over clever code.

## Current state (do not rewrite, extend)

- Phase 3 + 4 done: structured JSON logs with `correlation_id`/`interaction_id`,
  `trace_id` reserved as `None` in every log line; Prometheus metrics exposed at
  `/metrics`, `docker-compose.yml` has `prometheus`, `grafana`, and `app`.
- [langfuse_spec.md](langfuse_spec.md) done too: `AnswerGenerator` may already
  be wrapped in `LangfuseTracedAnswerGenerator`, and Phase 4 will have added its
  own metrics decorator around the same port. By the time this phase adds a
  third wrapper for spans, `container.py` is composing up to three decorators
  around one `AnswerGenerator` -- be deliberate about the order (innermost
  wraps closest to the vendor call) and say so in a comment, since it decides
  whether each layer's latency/timing includes the layers around it.
- No OpenTelemetry *tracing* SDK configured (Phase 4 only set up the *metrics*
  SDK) -- `grep -r "TracerProvider" src/itw_me` returns nothing.
- No tracing backend container exists.
- `InterviewRepository` is `InMemoryInterviewRepository` -- there is no real
  database dependency to trace yet, unlike VOLT's PostgreSQL.

## Architectural rules (hard constraints, violating these fails the task)

1. Inward dependency rule: `domain/` imports only stdlib. `application/` imports
   only domain and stdlib. Vendor libraries never appear in `domain/` or
   `application/`, with ONE exception: the application layer MAY import the
   `opentelemetry` API, because it is designed as a vendor-neutral facade.
2. Concrete adapters/exporters are instantiated only in
   `infrastructure/container.py` (and in tests). Environment variables are read
   only at the composition root or inside adapters, never in domain or
   application code.
3. Existing tests must stay green. Tests must not require network access, API
   keys, or running containers -- the tracing backend must be optional and
   absent by default at test time.
4. Naming convention for adapters: Technology + PortName (e.g.
   `TracedCorpusRetriever`).

## Phase 5: distributed tracing (VOLT's Step 3, exactly) -- done

Four things came up during implementation that weren't obvious from this
spec's original wording:

- **`trace_id_var` (Phase 3's reserved ContextVar) got deleted, not
  populated.** The plan was "read it from the logging formatter, write
  to it wherever spans get created." It turned out unnecessary:
  `opentelemetry.trace.get_current_span()` already tracks the active
  span via the exact same ContextVar mechanism internally -- a hand-
  rolled second copy would have been redundant the moment a real tracer
  existed. See `infrastructure/logging.py`'s module docstring.
- **The tracing decorators (`TracedCorpusRetriever`,
  `TracedAnswerGenerator`) take a `Tracer` via constructor, not a bare
  module-level `trace.get_tracer(...)` call** -- unlike `logger` in
  Phase 3, which IS a bare module-level global. Reason: OTel's trace API
  only honors the FIRST `set_tracer_provider()` call in a whole process;
  there is no way for a test to install its own `TracerProvider` after
  `container.py`'s `configure_tracing()` (or any other test that
  triggered it first) already claimed that one global slot. Constructor
  injection sidesteps the problem instead of fighting it -- see
  `infrastructure/tracing.py`'s docstring and
  `tests/test_retriever_traced.py`.
- **A real, timed gotcha, not a hypothetical one:** left at OTel's
  defaults, `BatchSpanProcessor`'s background thread adds 6+ seconds to
  every test run when no collector is listening (measured, not
  guessed) -- and can print a confusing `ValueError: I/O operation on
  closed file` traceback at interpreter shutdown even after all tests
  pass. Fixed two ways: short `timeout`/`export_timeout_millis` on the
  exporter/processor (see `infrastructure/tracing.py`), plus
  `tests/conftest.py` explicitly shutting the provider down at session
  end, before Python's own teardown can race it.
- **Dependency spans are NOT decorators**, unlike the workflow spans --
  `chroma.query` and `llm.chat.completions` are hardcoded directly
  inside `retriever_chroma.py`/`llm_openai.py`, because their attributes
  (collection name, model name) are vendor-specific knowledge a generic
  decorator has no business having. They still nest correctly under
  `retrieve`/`generate` in the trace tree purely because of call order --
  nothing had to be wired for that to work.

1. ~~**Tracer setup**~~ -- done: `src/itw_me/infrastructure/tracing.py`,
   a `TracerProvider` exporting spans via OTLP/HTTP, plus a `jaeger`
   service in `docker-compose.yml` (`jaegertracing/all-in-one`, OTLP
   receiver enabled, UI on `:16686`). One addition versus the original
   plan: explicit short timeouts on the exporter/processor -- see the
   implementation notes above.
2. ~~**Workflow spans**~~ -- done: decorator adapters
   (`TracedCorpusRetriever`, `TracedAnswerGenerator`), matching Phase 4's
   choice for metrics, wrapping `retrieve`/`generate` respectively; a
   root `ask_question` span wraps the whole use case in
   `InterviewService`, via the same application-layer OTel-API exception
   Phase 4 established for its own instruments.
   Divergence note: VOLT's ticket lists `plan`/`retrieve`/`reflect`/`generate`
   because their backend is an agentic workflow; itw-me has no planning or
   reflection step. Two spans instead of four is a simplification of itw-me's
   actual architecture, not a coverage gap -- when translating this phase back
   to VOLT, plan/reflect need their own spans there, matching VOLT's own list.
3. ~~**Dependency spans**~~ -- done: inside `ChromaCorpusRetriever.retrieve` and
   `OpenAIAnswerGenerator.generate`, wrapping the actual vendor call in its own span
   (`chroma.query`, `llm.chat.completions`) with attributes such as model name or
   collection name -- never raw question text, same cardinality/PII discipline as
   Phase 4's metric labels.
   Divergence note: VOLT traces four dependencies (Azure OpenAI, Azure AI
   Search, PostgreSQL, Blob Storage); itw-me only has two real ones today (an
   LLM and a vector store) because `InterviewRepository` is in-memory, not a
   real database. If/when itw-me gains a real persistence adapter, it gets a
   `repository.save` span the same way -- but that is not required for this
   phase's definition of done.
4. ~~**Log/trace correlation**~~ -- done, and it really was the only
   change to `infrastructure/logging.py`: read
   `opentelemetry.trace.get_current_span().get_span_context()`; if
   `.is_valid`, populate `trace_id` as 32 lowercase hex digits. This is
   the concrete implementation of VOLT's "correlate logs, metrics,
   traces" objective -- log lines emitted inside a span now automatically
   carry that span's trace id. The field itself needed no change; only
   what feeds it did.
5. ~~**README**~~ -- done: "Running phase 5" section added.

## Definition of done

- [x] `pytest` green, offline, no keys or network needed -- Jaeger is
      optional at test time and absent by default (48 tests total, 11
      new: `test_retriever_traced.py`, `test_generator_traced.py`, plus
      additions to `test_retriever_chroma.py`, `test_llm_openai.py`,
      `test_interview_service.py`, `test_logging.py`, and a new
      `conftest.py` for clean test-session teardown).
- [x] Verified live (Docker daemon wasn't available in this environment,
      same caveat as Phase 4): ran `uvicorn` directly and confirmed, via
      the actual JSON log lines, that all three
      `itw_me.application.interview_service` log lines for one question
      share a real, non-null, 32-hex-digit `trace_id` -- previously
      always `None`. `docker compose up` with the new `jaeger` service,
      end to end through the actual Jaeger UI, is still worth doing once
      Docker is available, same outstanding item as Phase 4.
- [x] `grep -r "opentelemetry" src/itw_me/domain src/itw_me/application`
      (the corrected, broader pattern -- see Phase 4's own note on this)
      returns nothing in `domain/`, and only the permitted API-facade
      usage in `application/interview_service.py` (plus one docstring
      mention in `request_context.py`).

Next: [phase6_spec.md](phase6_spec.md) (VOLT Step 4: dashboards and alerting).
