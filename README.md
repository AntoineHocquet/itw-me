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

## Build order

Phase 1 (works offline, no keys):
- [x] Implement InterviewService.ask_question
- [x] Un-skip the second test, make it pass
- [x] Implement the /questions endpoint against a fake generator
- [x] `pip install -e ".[dev]" && pytest` green,
      `uvicorn itw_me.adapters.inbound.api:app` answering canned text

Phase 2 (real RAG):
- [ ] Write corpus/cv.md and corpus/bio.md
- [ ] scripts/ingest.py -> Chroma
- [ ] ChromaCorpusRetriever, OpenAIAnswerGenerator
- [ ] Citations returned by the API

Phase 3 (observability):
- [ ] OTel instrumentation: counter for questions, histograms for
      end-to-end / retrieval / LLM latency, token counters
- [ ] /metrics endpoint via the Prometheus exporter
- [ ] docker-compose up: watch Prometheus scrape, build one Grafana
      dashboard (request rate, p95 latency, tokens per answer)
