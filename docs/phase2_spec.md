# Task: Complete the itw-me RAG chatbot (Phase 2) -- done

## Context

itw-me is a small RAG chatbot: visitors "interview" Antoine by chatting with a bot
grounded in a corpus of markdown documents about him (CV, bio, experience). The
repository already contains a working Phase 1: a hexagonal skeleton where the full
use case runs end to end (HTTP -> application -> domain -> ports) against offline
"canned" adapters, with passing tests. See [phase1_spec.md](phase1_spec.md) for
what that phase built and why.

This is also a training codebase. Code quality, comments explaining non-obvious
decisions, and architectural discipline matter more than feature count. Prefer
clear code over clever code.

## Current state (do not rewrite, extend)

- `src/itw_me/domain/models.py`: frozen dataclasses (Citation, Question, Answer,
  RetrievedChunk) and the Interview aggregate root with its invariant in
  `record_answer`. Answer carries `input_tokens` / `output_tokens`.
- `src/itw_me/domain/ports.py`: three ABCs: CorpusRetriever, AnswerGenerator,
  InterviewRepository.
- `src/itw_me/application/interview_service.py`: InterviewService with
  `start_interview` and a fully implemented `ask_question` (load, ask, retrieve,
  generate, record, save, return).
- `src/itw_me/adapters/outbound/repo_inmemory.py`: working in-memory repository.
- `src/itw_me/adapters/outbound/retriever_canned.py` and `generator_canned.py`:
  working offline adapters, wired in by default (`ITW_ME_FAKE_LLM=1`).
- `src/itw_me/adapters/outbound/retriever_chroma.py` and `llm_openai.py`: stubs
  raising NotImplementedError. Their docstrings contain implementation guidance;
  follow it.
- `src/itw_me/adapters/inbound/api.py`: FastAPI app, both endpoints implemented,
  DTOs separate from domain models.
- `src/itw_me/infrastructure/container.py`: composition root, already switches
  between the canned pair and the Chroma/OpenAI pair via `ITW_ME_FAKE_LLM`.
- `tests/test_interview_service.py`: two green tests against fakes.
- `corpus/cv.md` and `corpus/bio.md`: done (real content, not placeholders).
- `scripts/ingest.py`: stub.

## Architectural rules (hard constraints, violating these fails the task)

1. Inward dependency rule: `domain/` imports only stdlib. `application/` imports
   only domain and stdlib. Vendor libraries (chromadb, openai, opentelemetry,
   fastapi, pydantic) never appear in `domain/` or `application/`, with ONE
   exception defined in Phase 3.
2. Concrete adapters are instantiated only in `infrastructure/container.py`
   (and in tests). Environment variables are read only at the composition root
   or inside adapters, never in domain or application code.
3. Adapters translate at the boundary: no vendor data structure (Chroma result
   dicts, OpenAI response objects) may leak past an adapter's public methods.
   Ports return domain objects.
4. Existing tests must stay green. Every new adapter gets its own tests. Tests
   must not require network access, API keys, or running containers; use fakes
   for external services.
5. Naming convention for adapters: Technology + PortName
   (e.g. ChromaCorpusRetriever).

## Phase 2: real RAG (all done)

1. ~~**Corpus**: create `corpus/cv.md` and `corpus/bio.md`~~ -- done.
2. ~~**Shared config**~~ -- done:
   `src/itw_me/adapters/outbound/chroma_config.py` holds `COLLECTION_NAME`,
   `PERSIST_DIR`, and `get_embedding_function()`/`get_chroma_client()`/
   `get_collection()`, imported by both `scripts/ingest.py` and
   `ChromaCorpusRetriever`. Uses Chroma's built-in default embedding function
   (local ONNX `all-MiniLM-L6-v2`) -- no API key, no network call per query.
   Note: it downloads its ~80MB model file on first use (cached afterwards),
   which is why tests mock the Chroma boundary rather than exercising it.
3. ~~**Ingestion**~~ -- done: the pure chunking logic lives in
   `src/itw_me/adapters/outbound/corpus_chunking.py` (`chunk_file`), unit
   tested in `tests/test_corpus_chunking.py` with no Chroma import.
   `scripts/ingest.py` walks `corpus/*.md`, chunks, and `upsert`s into Chroma
   with stable ids (`{filename}#{section-slug}#{i}`); verified idempotent by
   running it twice (95 chunks both times, no duplicates). Token estimate is
   the heuristic `len(text) // 4`, no `tiktoken` dependency.
4. ~~**ChromaCorpusRetriever**~~ -- done: builds the client/collection once in
   `__init__`, converts distance to `score = 1 - distance`. Tested by mocking
   `chroma_config.get_chroma_client`/`get_collection` (no real embedding calls
   in tests); verified for real against the ingested corpus too.
5. ~~**OpenAIAnswerGenerator**~~ -- done: first-person system prompt grounded
   only in retrieved excerpts, `[source_file#chunk_id]` labels, history
   replayed as alternating user/assistant messages, citations built from the
   chunks actually placed in the prompt, tokens filled from `response.usage`.
   Defaults to a local Ollama server (`http://localhost:11434/v1`,
   `llama3.1`); override `ITW_ME_LLM_BASE_URL`/`ITW_ME_MODEL`/
   `OPENAI_API_KEY` for the real OpenAI API. Tested by patching the `OpenAI`
   class (no network).
6. ~~**Fake generator for dev**~~ -- done in Phase 1, ahead of schedule.
7. ~~Dependencies~~ -- done: `chromadb`, `openai`, `python-dotenv` added to
   `pyproject.toml`; `container.py` calls `load_dotenv()`; `.env.example`
   documents the variables; `chroma_data/` gitignored.

## Definition of done

- [x] `pytest` green, offline, no keys needed (14 tests).
- [x] `grep -r "import chromadb\|import openai" src/itw_me/domain
      src/itw_me/application` returns nothing.
- [x] Real ingest + real retrieval verified end to end (no mocks) against
      the actual corpus: 95 chunks ingested, idempotent re-run, sensible
      `RetrievedChunk`s back for real queries.
- [x] Real end-to-end generation against Ollama -- verified with zero
      environment overrides (just `ITW_ME_FAKE_LLM=0`): Ollama installed
      via `brew install ollama`, running as a persistent service
      (`brew services start ollama`), `llama3.1` pulled. Asked "What
      programming languages do you know?" through the running API and
      got back the correct list (Python 4.7, SQL 4.0, C++ 3.5, Rust 3.0,
      R 2.5) with citations into `cv.md`. A follow-up question reusing
      conversation history was also answered correctly, confirming
      history replay works, not just single-turn retrieval.

Next: [phase3_spec.md](phase3_spec.md) (observability).
