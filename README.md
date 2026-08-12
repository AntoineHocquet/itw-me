# itw-me

A RAG chatbot that lets visitors "interview" Antoine: the corpus is
his CV, biography and experience; the bot answers in his place, with
citations.

Training goals: DDD / hexagonal architecture, RAG, and observability
(OpenTelemetry, Prometheus, Grafana).

## Layout (hexagonal)

```
src/itw_me/
  domain/          # models.py (entities, value objects), ports.py
  application/     # use cases orchestrating domain + ports
  adapters/
    inbound/       # FastAPI (driving side)
    outbound/      # Chroma, LLM, repository (driven side)
  infrastructure/  # container.py: the composition root
corpus/            # markdown source documents (cv.md, bio.md, ...)
scripts/           # ingest.py: corpus -> vector store
observability/     # prometheus.yml, grafana provisioning
tests/             # fast tests against fakes, no I/O
```

The dependency rule: imports only point inward. domain imports
nothing from the project; application imports domain; adapters import
domain (ports); only infrastructure/container.py imports adapters.

## Task runner

This project uses [Task](https://taskfiles.dev) (`brew install go-task`).
`task` with no arguments lists everything; the two commonly used ones:

```bash
task test          # pytest, offline
task run           # uvicorn, offline/canned mode (ITW_ME_FAKE_LLM=1)
task run:llama     # uvicorn against a local Ollama server (ITW_ME_FAKE_LLM=0)
task ingest        # chunk corpus/*.md, embed, upsert into ./chroma_data
```

Every task creates/refreshes `.venv` on its own first (see `Taskfile.yml`).
The raw commands behind each task are still shown below and in "Running
phase 2", since seeing what's actually being run is the point of a
training repo -- `task` is a shortcut, not a black box.

## Build order

Phase 1 (works offline, no keys):
- [x] Implement InterviewService.ask_question
- [x] Un-skip the second test, make it pass
- [x] Implement the /questions endpoint against a fake generator
- [x] `pip install -e ".[dev]" && pytest` green,
      `uvicorn itw_me.adapters.inbound.api:app` answering canned text

Phase 2 (real RAG):
- [x] Write corpus/cv.md and corpus/bio.md
- [x] scripts/ingest.py -> Chroma
- [x] ChromaCorpusRetriever, OpenAIAnswerGenerator
- [x] Citations returned by the API

Observability is split into four phases -- docs/phase3_spec.md through
docs/phase6_spec.md -- deliberately mapped 1:1 onto the four steps of a
real observability rollout ticket for a different, professional project
(see any of those docs' Context section for why that split matters).

Phase 3 (structured logging & correlation IDs):
- [x] `infrastructure/logging.py`: one JSON object per log line, on stdout
- [x] `X-Correlation-Id` middleware: reused from the caller, or minted,
      always echoed back on the response
- [x] `interaction_id`: one per interview turn (`Exchange.id`), bound
      while retrieving/generating/recording so those log lines can be
      grep'd/filtered down to a single turn
- [x] `trace_id`: reserved in every log line, always `null` until Phase 5

Phase 4 (OpenTelemetry metrics + Prometheus endpoint):
- [ ] OTel instrumentation: counter for questions, histograms for
      end-to-end / retrieval / LLM latency, token counters
- [ ] /metrics endpoint via the Prometheus exporter
- [ ] Dockerfile + docker-compose `app` service so Prometheus has
      something to scrape

Phase 5 (distributed tracing):
- [ ] OTel spans for retrieve/generate, and for the vendor calls behind
      them (Chroma, the LLM)
- [ ] Jaeger, so those spans are visible somewhere
- [ ] `trace_id` (reserved above, in Phase 3) populated for real

Phase 6 (dashboards & alerting):
- [ ] Grafana dashboard, provisioned rather than clicked through
- [ ] one alert rule, provisioned the same way

## Running phase 2 (real RAG)

```bash
pip install -e ".[dev]"
python scripts/ingest.py          # chunk corpus/*.md, embed, upsert into ./chroma_data

export ITW_ME_FAKE_LLM=0          # or put it in a local .env (see .env.example)
uvicorn itw_me.adapters.inbound.api:app
```

By default (`ITW_ME_FAKE_LLM=0`) the LLM side targets a local Ollama
server (`http://localhost:11434/v1`, model `llama3.1`) so this costs
nothing while developing -- `ollama pull llama3.1 && ollama serve`
first. To use the real OpenAI API instead, set `ITW_ME_LLM_BASE_URL`,
`ITW_ME_MODEL`, and `OPENAI_API_KEY` (see .env.example). Retrieval
(ChromaCorpusRetriever) is always real and needs no key either way --
embeddings run locally via Chroma's built-in model.

## Running phase 3 (structured logging & correlation IDs)

No new setup versus Phase 1/2 -- run the app exactly as above (canned or
real RAG, doesn't matter) and watch stdout:

```bash
uvicorn itw_me.adapters.inbound.api:app
```

```bash
curl -s -X POST http://localhost:8000/interviews          # note the interview_id
curl -si -X POST http://localhost:8000/interviews/<id>/questions \
  -H 'Content-Type: application/json' -d '{"text": "Where do you work?"}'
```

Every line on stdout, including uvicorn's own startup/access lines, is
now one JSON object -- pipe through `| jq .` for a readable view. The
response has an `X-Correlation-Id` header; pass your own
(`-H 'X-Correlation-Id: demo-1'`) and it comes straight back instead of
a generated one. The three `itw_me.application.interview_service` log
lines per question (`retrieving corpus chunks` / `generating answer` /
`recorded answer`) share that request's `correlation_id` and carry a
per-turn `interaction_id`; `trace_id` is present but always `null` until
Phase 5.

## Optional: Langfuse tracing

Set `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` (see .env.example)
to trace every `generate()` call -- prompt, retrieved context, tokens,
latency -- to a Langfuse project. Unset (the default): no Langfuse code
runs at all, `pip install -e ".[dev]"` alone is enough. See
[docs/langfuse_spec.md](docs/langfuse_spec.md) for why this lives
outside the observability phase sequence below.
