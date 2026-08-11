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

Phase 3 (observability):
- [ ] OTel instrumentation: counter for questions, histograms for
      end-to-end / retrieval / LLM latency, token counters
- [ ] /metrics endpoint via the Prometheus exporter
- [ ] docker-compose up: watch Prometheus scrape, build one Grafana
      dashboard (request rate, p95 latency, tokens per answer)

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

## Optional: Langfuse tracing

Set `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` (see .env.example)
to trace every `generate()` call -- prompt, retrieved context, tokens,
latency -- to a Langfuse project. Unset (the default): no Langfuse code
runs at all, `pip install -e ".[dev]"` alone is enough. See
[docs/langfuse_spec.md](docs/langfuse_spec.md) for why this lives
outside the observability phase sequence below.
