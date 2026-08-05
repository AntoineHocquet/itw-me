# Task: Complete the itw-me RAG chatbot (Phase 2)

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

## Phase 2: real RAG

1. ~~**Corpus**: create `corpus/cv.md` and `corpus/bio.md`~~ -- done.
2. **Shared config**: create a small module
   (`src/itw_me/adapters/outbound/chroma_config.py`) holding the collection
   name and embedding-function choice, imported by BOTH the ingest script and
   the retriever adapter, so they cannot drift apart. Decision: use Chroma's
   built-in default embedding function (a local ONNX sentence-transformer,
   `all-MiniLM-L6-v2`) -- no API key, no network call per query, consistent
   with the offline-first approach used in Phase 1. Revisit only if retrieval
   quality turns out to be the bottleneck.
3. **Ingestion** (`scripts/ingest.py`): walk `corpus/*.md`, chunk by markdown
   headers with a ~500-token fallback split, assign STABLE ids
   (`{filename}#{section}#{i}`), and `upsert` into a Chroma
   PersistentClient(path="./chroma_data") collection with metadata
   (source_file, section). The script must be idempotent: running it twice
   yields no duplicates. Put logic in functions; keep the
   `if __name__ == "__main__"` block to a single main() call. Add a unit test
   for the chunking function (pure function, no Chroma needed). Decision:
   estimate token count with a simple heuristic (e.g. `len(text) // 4`), no
   `tiktoken` dependency -- it's only a splitting ceiling, not billed usage,
   and a heuristic is model-agnostic (works the same whether the corpus ends
   up embedded/answered by OpenAI or Ollama).
4. **ChromaCorpusRetriever**: implement `retrieve`. Build client and collection
   once in `__init__`. Convert Chroma distances to a higher-is-better score
   (score = 1 - distance) at this boundary. Map results to RetrievedChunk.
5. **OpenAIAnswerGenerator**: implement `generate` using the openai client.
   Constructor takes `model` and optional `base_url` so the same adapter works
   against Ollama (OpenAI-compatible). Decision: default `base_url` to a local
   Ollama server (`http://localhost:11434/v1`, model e.g. `llama3.1`) so
   real-RAG development costs nothing; point at the real OpenAI API via env
   vars (`ITW_ME_MODEL`, and an `ITW_ME_LLM_BASE_URL` or similar) once
   production-quality answers are wanted. System prompt: the bot speaks AS
   Antoine in first person, answers ONLY from provided excerpts, and must say
   it does not know when the excerpts do not contain the answer. Replay
   `history` as alternating user/assistant messages. Label each context chunk
   with `[source_file#chunk_id]` in the prompt. Build Citations from the
   chunks actually included in the prompt. Fill input_tokens/output_tokens
   from `response.usage` (Ollama's OpenAI-compatible endpoint fills this too).
   API key comes from the OPENAI_API_KEY env var (Ollama ignores it, but the
   openai client requires the field to be set to *something*); never hardcode
   secrets.
6. ~~**Fake generator for dev**: add a CannedAnswerGenerator adapter and switch
   on env var ITW_ME_FAKE_LLM=1~~ -- done in Phase 1, ahead of schedule.
7. Uncomment/add the needed dependencies in pyproject.toml: `chromadb`,
   `openai`, and `python-dotenv` (composition root calls `load_dotenv()` once,
   so `OPENAI_API_KEY` and friends can live in a local, gitignored `.env`
   instead of exported shell variables).

## Definition of done

- `pytest` green, offline, no keys needed.
- After running ingest, with `ITW_ME_FAKE_LLM=0` and a local Ollama server
  running: answers are grounded in the corpus and include citations -- no
  OpenAI key required for this.
- Swapping `ITW_ME_LLM_BASE_URL`/`ITW_ME_MODEL` (or unsetting them) to point
  at the real OpenAI API works with the same adapter, unchanged.
- `grep -r "import chromadb\|import openai" src/itw_me/domain
  src/itw_me/application` returns nothing.

Work through 2.2, 2.3, 2.4, 2.5, 2.7 in order, running the test suite after each
step. If a design decision is ambiguous, prefer the option that keeps the domain
ignorant of technology. Next: [phase3_spec.md](phase3_spec.md) (observability),
once this phase is verified end to end.
