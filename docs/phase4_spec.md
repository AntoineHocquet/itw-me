# Task: Complete the itw-me RAG chatbot (Phase 4) -- OTel metrics & Prometheus endpoint

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

## Phase 4: OpenTelemetry metrics + Prometheus endpoint (VOLT's Step 2, exactly)

1. **Instrumentation module**: create
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
2. **Where to measure**: timing of retrieve and generate happens around the
   port calls. Preferred design to keep vendor code out of the application
   layer: implement decorator adapters (e.g. MeasuredCorpusRetriever wrapping
   any CorpusRetriever) composed in the container, OR instrument inside the
   concrete adapters. Exception allowed if you choose otherwise: the
   application layer may import the opentelemetry API (it is designed as a
   vendor-neutral facade), but nothing else. Pick one approach and state it in
   a comment -- Phase 5 (tracing) will reuse the same choice for spans, so
   staying consistent here saves a decision later.
3. **Expose /metrics**: mount the Prometheus ASGI/WSGI app or endpoint in
   api.py so GET /metrics returns the text exposition format.
4. *(itw-me-only plumbing, no VOLT equivalent)* **Dockerfile** for the app:
   python slim base, install project, run uvicorn on 0.0.0.0:8000.
5. *(itw-me-only plumbing, no VOLT equivalent)* **docker-compose.yml**: add the
   `app` service (build: ., ports 8000:8000, env vars passed through).
   Prometheus target `app:8000` already exists.
6. Update README build-order checkboxes and add a short "Running the stack"
   section: ingest, docker compose up, where to see raw metrics on
   `localhost:9090`.

## Definition of done

- `pytest` green, offline, no keys needed.
- With ITW_ME_FAKE_LLM=1: `docker compose up`, POST a question, watch
  `itw_me_questions_total` increase on `http://localhost:9090`.
- `grep -r "import opentelemetry" src/itw_me/domain src/itw_me/application`
  returns nothing outside the permitted API-facade usage.

Next: [phase5_spec.md](phase5_spec.md) (VOLT Step 3: workflow and dependency
tracing).
