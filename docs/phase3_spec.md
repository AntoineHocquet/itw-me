# Task: Complete the itw-me RAG chatbot (Phase 3)

## Context

itw-me is a small RAG chatbot: visitors "interview" Antoine by chatting with a bot
grounded in a corpus of markdown documents about him (CV, bio, experience). By the
time this phase starts, Phase 1 (hexagonal skeleton, offline) and Phase 2 (real RAG
against Chroma + OpenAI) are both done -- see [phase1_spec.md](phase1_spec.md) and
[phase2_spec.md](phase2_spec.md).

This is also a training codebase. Code quality, comments explaining non-obvious
decisions, and architectural discipline matter more than feature count. Prefer
clear code over clever code.

## Current state (do not rewrite, extend)

- Phase 1 + Phase 2 done: the API answers real questions against the real corpus,
  with citations, using ChromaCorpusRetriever and OpenAIAnswerGenerator (or the
  canned pair when `ITW_ME_FAKE_LLM=1`).
- `observability/prometheus.yml` and `docker-compose.yml`: prepared with
  `prometheus` and `grafana` services; scrape target `app:8000` already
  configured; no `app` service yet.
- No OpenTelemetry instrumentation anywhere in the codebase yet.

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
   (e.g. ChromaCorpusRetriever).

## Phase 3: observability (metrics only; no traces/logs backends yet)

Stack decision: instrument with OpenTelemetry metrics API, export via the
Prometheus exporter, scrape with Prometheus, display in Grafana.

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
   a comment.
3. **Expose /metrics**: mount the Prometheus ASGI/WSGI app or endpoint in
   api.py so GET /metrics returns the text exposition format.
4. **Dockerfile** for the app: python slim base, install project, run uvicorn
   on 0.0.0.0:8000.
5. **docker-compose.yml**: add the `app` service (build: ., ports 8000:8000,
   env vars passed through). Prometheus target `app:8000` already exists.
6. **Grafana provisioning**: add provisioning files under
   `observability/grafana/` (datasource pointing at http://prometheus:9090
   plus one dashboard JSON) and mount them in the grafana service. Dashboard
   panels: request rate, error rate, p95 end-to-end latency, p95 retrieval and
   LLM latency, tokens per minute.
7. Update README build-order checkboxes and add a short "Running the stack"
   section: ingest, docker compose up, where to click.

## Definition of done

- `pytest` green, offline, no keys needed.
- With ITW_ME_FAKE_LLM=1: `docker compose up`, POST a question, watch
  itw_me_questions_total increase on http://localhost:9090, see the dashboard
  populate on http://localhost:3000.

Work through 3.1 to 3.7 in order, running the test suite after each step. If a
design decision is ambiguous, prefer the option that keeps the domain ignorant
of technology.
