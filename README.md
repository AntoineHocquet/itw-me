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
- [x] OTel instrumentation: counter for questions, histograms for
      end-to-end / retrieval / LLM latency, token counters
- [x] /metrics endpoint via the Prometheus exporter
- [x] Dockerfile + docker-compose `app` service so Prometheus has
      something to scrape

Phase 5 (distributed tracing):
- [x] OTel spans for retrieve/generate, and for the vendor calls behind
      them (Chroma, the LLM)
- [x] Jaeger, so those spans are visible somewhere
- [x] `trace_id` (reserved above, in Phase 3) populated for real

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

## Running phase 4 (OpenTelemetry metrics + Prometheus)

```bash
uvicorn itw_me.adapters.inbound.api:app
```

```bash
curl -s -X POST http://localhost:8000/interviews
curl -s -X POST http://localhost:8000/interviews/<id>/questions \
  -H 'Content-Type: application/json' -d '{"text": "Where do you work?"}'
curl -s http://localhost:8000/metrics | grep itw_me_
```

That last line is the whole point: `itw_me_questions_total`,
`itw_me_request_latency_seconds`, `itw_me_retrieval_latency_seconds`,
`itw_me_llm_latency_seconds`, `itw_me_llm_input_tokens_total`, and
`itw_me_llm_output_tokens_total`, all in the Prometheus text exposition
format, with no Docker required to see them locally.

With Docker (this is what actually gets scraped -- Prometheus can't
reach a bare `uvicorn` process on your host from inside its own
container):

```bash
docker compose up --build
# then, in another terminal:
curl -s -X POST http://localhost:8000/interviews
curl -s -X POST http://localhost:8000/interviews/<id>/questions \
  -H 'Content-Type: application/json' -d '{"text": "Where do you work?"}'
```

Then open `http://localhost:9090`, and query `itw_me_questions_total` --
Prometheus's own UI plots it. `http://localhost:3000` (Grafana,
admin/admin) is running too, but has nothing provisioned on it yet --
that's Phase 6.

## Running phase 5 (distributed tracing)

Without Docker, the app still opens real spans -- there's just nowhere
for them to land, so a scraper being unreachable is expected and
harmless (see infrastructure/tracing.py's docstring):

```bash
uvicorn itw_me.adapters.inbound.api:app
curl -s -X POST http://localhost:8000/interviews
curl -s -X POST http://localhost:8000/interviews/<id>/questions \
  -H 'Content-Type: application/json' -d '{"text": "Where do you work?"}'
```

The `trace_id` on the three log lines from "Running phase 3" above is no
longer `null` -- it's now a real 32-character hex id, the same one on
all three lines for one question, because they all ran inside the same
span tree.

With Docker, that id becomes something you can actually click through:

```bash
docker compose up --build
# then, in another terminal, same two curls as above
```

Open `http://localhost:16686` (Jaeger), find the `itw-me` service, and
open the most recent trace: `ask_question` (root) contains `retrieve`
and `generate` (one span each per question), and each of those contains
one more span for the actual vendor call (`chroma.query`,
`llm.chat.completions`) -- four spans total per question, nested exactly
the way the code calls them, no manual wiring required to get that
nesting right.

## Optional: Langfuse tracing

Set `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` (see .env.example)
to trace every `generate()` call -- prompt, retrieved context, tokens,
latency -- to a Langfuse project. Unset (the default): no Langfuse code
runs at all, `pip install -e ".[dev]"` alone is enough. See
[docs/langfuse_spec.md](docs/langfuse_spec.md) for why this lives
outside the observability phase sequence below.
