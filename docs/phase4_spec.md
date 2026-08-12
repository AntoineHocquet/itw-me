# Task: Complete the itw-me RAG chatbot (Phase 4) -- OTel metrics & Prometheus endpoint -- done

## Context

itw-me is a small RAG chatbot: visitors "interview" Antoine by chatting with a bot
grounded in a corpus of markdown documents about him (CV, bio, experience). By the
time this phase starts, Phase 1 (hexagonal skeleton), Phase 2 (real RAG), and
Phase 3 (structured logging + correlation IDs -- see
[phase3_spec.md](phase3_spec.md)) are all done.

This phase exists to mirror, exactly, Step 2 ("OpenTelemetry Instrumentation and
Core Metrics") of the VOLT observability spike ticket this whole sequence is
tracking -- see [phase3_spec.md](phase3_spec.md)'s Context for the full background. VOLT's
Step 2 is three bullets: add OpenTelemetry instrumentation, expose a Prometheus
metrics endpoint, implement core service/workflow metrics. All three are covered
below. One thing in this phase has *no* VOLT equivalent and is called out
separately: VOLT already has AKS deployment (see its ticket's "Current State"), so
it never needs to stand up a container to scrape -- itw-me does, since nothing has
built the app's Docker image yet. Steps 4-5 below are that itw-me-only plumbing;
skip them when using this phase as a checklist for VOLT's own Step 2.

Grafana dashboards are deliberately **not** part of this phase, even though
`docker-compose.yml` already has a `grafana` service -- VOLT's own ticket puts
dashboards in Step 4, not Step 2, and this sequence follows that split exactly. See
[phase6_spec.md](phase6_spec.md).

This is also a training codebase. Code quality, comments explaining non-obvious
decisions, and architectural discipline matter more than feature count. Prefer
clear code over clever code.

## Current state (do not rewrite, extend)

- Phase 3 done: `infrastructure/logging.py` emits structured JSON logs with
  `correlation_id` and `interaction_id` populated, `trace_id` reserved as `None`.
  `domain/models.py`'s `Exchange` has an `id`.
- [langfuse_spec.md](langfuse_spec.md) done too (built right after Phase 2,
  before this sequence started): `AnswerGenerator` may already be wrapped in
  `LangfuseTracedAnswerGenerator`. Unrelated to this phase's metrics work --
  the decorator adapter you add here for metrics wraps whatever `generator`
  `container.py` already has at that point, Langfuse-wrapped or not.
- `observability/prometheus.yml` and `docker-compose.yml`: prepared with
  `prometheus` and `grafana` services; scrape target `app:8000` already
  configured; no `app` service yet.
- No OpenTelemetry dependency installed; `pyproject.toml` lists the packages
  commented out.

## Architectural rules (hard constraints, violating these fails the task)

1. Inward dependency rule: `domain/` imports only stdlib. `application/` imports
   only domain and stdlib. Vendor libraries (chromadb, openai, opentelemetry,
   fastapi, pydantic) never appear in `domain/` or `application/`, with ONE
   exception: the application layer MAY import the opentelemetry API (see below),
   because it is designed as a vendor-neutral facade.
2. Concrete adapters/exporters are instantiated only in
   `infrastructure/container.py` (and in tests). Environment variables are read
   only at the composition root or inside adapters, never in domain or
   application code.
3. Existing tests must stay green. Tests must not require network access, API
   keys, or running containers.
4. Naming convention for adapters: Technology + PortName
   (e.g. ChromaCorpusRetriever, MeasuredCorpusRetriever).

## Phase 4: OpenTelemetry metrics + Prometheus endpoint (VOLT's Step 2, exactly) -- done

Three things came up during implementation that weren't obvious from this
spec's original wording:

- **All six instruments ended up defined in `telemetry.py` after all**,
  not four-there-plus-two-in-`InterviewService` as a first draft of this
  note said. `InterviewService.__init__` still can't import
  `infrastructure/telemetry.py` (the inward-dependency rule), so it
  re-creates its own two (`itw_me_questions_total`,
  `itw_me_request_latency_seconds`) via the bare OTel API as a fallback
  -- but `container.py` now always passes in the real ones from
  `telemetry.py`'s `Instruments`, so that fallback only ever fires in
  tests that construct `InterviewService` standalone. Net effect: one
  canonical definition per instrument name, `container.py` wires all six
  explicitly (matching how it already wires the retriever/generator/
  repository), and the fallback is a documented, deliberate duplication,
  not a second source of truth.
- **OTel's default histogram bucket boundaries are wrong for this
  codebase's units.** They're shaped for milliseconds (`0, 5, 10, 25,
  50, ... 10000`); every instrument here is named `*_seconds`. Caught by
  actually running the app and reading `/metrics` -- every latency
  landed in the first bucket. Fixed via
  `explicit_bucket_boundaries_advisory` on each histogram. See
  `telemetry.py`'s `_LATENCY_BUCKET_BOUNDARIES_SECONDS`.
- **Decorator order, now that two wrap `AnswerGenerator`:**
  `MeasuredAnswerGenerator` goes innermost (closest to the real vendor
  call), `LangfuseTracedAnswerGenerator` outermost -- so
  `itw_me_llm_latency_seconds` times only the actual LLM call, never
  Langfuse's own overhead. See `container.py`'s comment at that wrapping
  point. Phase 5's tracing decorator should follow the same rule.
- The spec's own DoD grep pattern, `grep -r "import opentelemetry"`, only
  matches `import opentelemetry` statements -- this codebase's actual
  style is `from opentelemetry import metrics`, which that pattern
  doesn't match at all. `grep -r "opentelemetry" src/itw_me/domain
  src/itw_me/application` is the check that actually verifies anything;
  run that way, it confirms every reference is inside
  `interview_service.py`'s permitted API-facade usage, and `domain/` has
  none at all.

1. ~~**Instrumentation module**~~ -- done: create
   `src/itw_me/infrastructure/telemetry.py` that sets up the OTel MeterProvider
   with a Prometheus exporter and defines these instruments:
   - `itw_me_questions_total` (counter, label: status = ok|error)
   - `itw_me_request_latency_seconds` (histogram, end-to-end ask_question)
   - `itw_me_retrieval_latency_seconds` (histogram)
   - `itw_me_llm_latency_seconds` (histogram)
   - `itw_me_llm_input_tokens_total` and `itw_me_llm_output_tokens_total`
     (counters)
   Cardinality rule: label values must come from small fixed sets. Never use
   interview_id, question text, or any unbounded value as a label.
2. ~~**Where to measure**~~ -- done: decorator adapters
   (`MeasuredCorpusRetriever`, `MeasuredAnswerGenerator` in
   `adapters/outbound/`), composed in `container.py`, wrapping any
   `CorpusRetriever`/`AnswerGenerator` -- Chroma or canned, doesn't matter.
   `InterviewService`'s own two instruments (see the notes above) use the
   explicitly permitted application-layer exception instead, since they
   time the whole use case, not one port call.
3. ~~**Expose /metrics**~~ -- done: `GET /metrics` in `api.py` calls
   `prometheus_client.generate_latest(REGISTRY)` directly -- no ASGI/WSGI
   bridging needed, since the exposition format is just text this route
   returns like any other response.
4. ~~*(itw-me-only plumbing, no VOLT equivalent)* **Dockerfile**~~ -- done.
5. ~~*(itw-me-only plumbing, no VOLT equivalent)* **docker-compose.yml**~~
   -- done: `app` service added, `prometheus` now `depends_on: [app]`.
6. ~~Update README~~ -- done: build-order checkboxes updated, "Running
   phase 4" section added.

## Definition of done

- [x] `pytest` green, offline, no keys needed (37 tests total, 11 new).
- [x] With ITW_ME_FAKE_LLM=1: ran `uvicorn` directly (Docker daemon wasn't
      available in the environment this was built in) and POSTed two
      questions; `curl localhost:8000/metrics` showed all six instruments
      with real values (`itw_me_questions_total{status="ok"} 2.0`, etc.).
      `docker compose up` itself was verified indirectly: `pip install .`
      (non-editable, matching the Dockerfile's own install step) into a
      throwaway venv succeeded and the app imported and started cleanly.
      Actually running `docker compose up` end-to-end is still worth doing
      once Docker is available, as a final check.
- [x] `grep -r "opentelemetry" src/itw_me/domain src/itw_me/application`
      (broader than this line originally specified -- see the note above)
      returns nothing in `domain/`, and only the permitted API-facade
      usage in `application/interview_service.py`.

Next: [phase5_spec.md](phase5_spec.md) (VOLT Step 3: workflow and dependency
tracing).
