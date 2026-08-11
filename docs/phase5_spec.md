# Task: Complete the itw-me RAG chatbot (Phase 5) -- workflow & dependency tracing

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

## Phase 5: distributed tracing (VOLT's Step 3, exactly)

1. **Tracer setup**: add `src/itw_me/infrastructure/tracing.py` -- a
   `TracerProvider` exporting spans via OTLP. Add a `jaeger` service to
   `docker-compose.yml` (`jaegertracing/all-in-one`, OTLP receiver enabled, UI on
   `:16686`). Jaeger over Tempo/Azure Monitor: one container, a built-in UI, no
   Grafana provisioning needed to see a trace -- the right tradeoff for a
   training repo where the point is to *look at* a trace, not run production
   infra.
2. **Workflow spans**: wrap `InterviewService.ask_question` in a root span
   (`ask_question`), with child spans `retrieve` and `generate` around the two
   port calls. Use the same instrumentation approach Phase 4 picked for metrics
   (decorator adapters, or spans started directly inside the concrete adapters)
   -- state which one in a comment, and stay consistent rather than mixing
   styles.
   Divergence note: VOLT's ticket lists `plan`/`retrieve`/`reflect`/`generate`
   because their backend is an agentic workflow; itw-me has no planning or
   reflection step. Two spans instead of four is a simplification of itw-me's
   actual architecture, not a coverage gap -- when translating this phase back
   to VOLT, plan/reflect need their own spans there, matching VOLT's own list.
3. **Dependency spans**: inside `ChromaCorpusRetriever.retrieve` and
   `OpenAIAnswerGenerator.generate`, wrap the actual vendor call in its own span
   (`chroma.query`, `llm.chat.completions`) with attributes such as model name or
   collection name -- never raw question text, same cardinality/PII discipline as
   Phase 4's metric labels.
   Divergence note: VOLT traces four dependencies (Azure OpenAI, Azure AI
   Search, PostgreSQL, Blob Storage); itw-me only has two real ones today (an
   LLM and a vector store) because `InterviewRepository` is in-memory, not a
   real database. If/when itw-me gains a real persistence adapter, it gets a
   `repository.save` span the same way -- but that is not required for this
   phase's definition of done.
4. **Log/trace correlation**: in the logging formatter from Phase 3, read
   `opentelemetry.trace.get_current_span().get_span_context()`; if a span is
   recording, populate the (already-reserved) `trace_id` field from it. This is
   the concrete implementation of VOLT's "correlate logs, metrics, traces"
   objective -- log lines emitted inside a span now automatically carry that
   span's trace id, and this is the *only* change to the logging code in this
   whole phase.
5. **README**: add a short section on where to see traces (Jaeger UI,
   `localhost:16686`).

## Definition of done

- `pytest` green, offline, no keys or network needed -- Jaeger is optional at
  test time and absent by default.
- With `docker compose up` including the new `jaeger` service: Jaeger's UI
  (`localhost:16686`) shows one trace per question, with `ask_question` >
  `retrieve`/`generate` spans and a dependency span nested under each.
- The `trace_id` on log lines emitted during a request (previously always
  `None`) now matches the trace id Jaeger shows for that request's trace.
- `grep -r "import opentelemetry" src/itw_me/domain src/itw_me/application`
  returns nothing outside the permitted API-facade usage.

Next: [phase6_spec.md](phase6_spec.md) (VOLT Step 4: dashboards and alerting).
