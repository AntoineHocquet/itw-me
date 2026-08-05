# Phase 1: hexagonal skeleton (done)

## Context

This is a training codebase: the goal of itw-me is not just "build a RAG
chatbot" but "learn Domain-Driven Design and hexagonal architecture by
building one". This document is a retrospective of Phase 1 -- what was
built, in what order, and *why* each piece is shaped the way it is. Keep it
around as a reference for the concepts, even after Phases 2 and 3 land.

Phase 1's goal: get the full use case (start an interview, ask a question,
get an answer, persist the exchange) working end to end, entirely offline,
with fakes standing in for every piece of real infrastructure. No database,
no LLM, no vector store -- and yet the HTTP API actually answers questions.
That is the payoff hexagonal architecture promises, and Phase 1 is where you
get to see it deliver.

## What was already in place before this phase's work

The domain and the ports were scaffolded first (not part of this phase's
work, but foundational to it):

- `src/itw_me/domain/models.py`: frozen dataclasses (`Citation`, `Question`,
  `Answer`, `RetrievedChunk`) plus the `Interview` aggregate root.
- `src/itw_me/domain/ports.py`: three abstract base classes --
  `CorpusRetriever`, `AnswerGenerator`, `InterviewRepository` -- named after
  what the domain *needs*, not after any technology.
- `src/itw_me/adapters/outbound/repo_inmemory.py`: a fully working
  in-memory `InterviewRepository`.
- Stub adapters (`retriever_chroma.py`, `llm_openai.py`) and a stub
  `scripts/ingest.py`, all raising `NotImplementedError` -- deliberately
  left for Phase 2.

## Concepts this phase demonstrates

**The aggregate root owns its invariants.** `Interview.ask()` appends a
pending `Exchange`; `Interview.record_answer()` refuses to attach an answer
if there is no pending question. The application layer never manipulates
`interview.exchanges` directly -- it only calls these two methods. That is
what makes `Interview` an aggregate and not just a list holder.

**The application layer orchestrates; it does not decide.** Look at
`InterviewService.ask_question` (`src/itw_me/application/interview_service.py`):
it is a straight-line sequence of port calls (load, ask, retrieve, generate,
record, save, return) with zero business rules and zero vendor imports. All
the "what does not-found mean", "what does answered-twice mean" logic lives
in the domain, not here.

**Ports are named after intent, adapters after technology.** The service
depends on `CorpusRetriever` and `AnswerGenerator` (abstract), never on
`ChromaCorpusRetriever` or `OpenAIAnswerGenerator` (concrete). Phase 1 proves
this by wiring in *two entirely different* adapter pairs --
`CannedCorpusRetriever`/`CannedAnswerGenerator` for offline dev, versus the
real Chroma/OpenAI stubs that will be finished in Phase 2 -- without
`InterviewService` changing by a single line.

**The composition root is the only place that knows the real world.**
`src/itw_me/infrastructure/container.py` reads the `ITW_ME_FAKE_LLM`
environment variable and decides which adapters to build. Domain and
application code never read environment variables or `os.getenv` directly --
if they did, you could no longer test them without setting up that
environment.

**Inbound adapters translate; they do not decide.** `src/itw_me/adapters/inbound/api.py`
maps HTTP concepts (`AskRequest`, `AskResponse`, `HTTPException`) onto domain
calls and back. The one interesting line is the `except ValueError` around
`service.ask_question` -- the domain raises a plain `ValueError` for "no such
interview" (a domain-level fact), and it is the *adapter's* job to know that
the HTTP vocabulary for that is `404`, not the domain's.

**Tests exercise the whole use case, with fakes, in milliseconds.**
`tests/test_interview_service.py` defines `FakeRetriever` and
`FakeGenerator` locally and wires them into a real `InterviewService` --
no network, no database. This is the same trick as the `Canned*` adapters
used for local dev; a "fake for tests" and "a stand-in adapter you can run
the app with" are the same idea, aimed at two different callers (pytest vs.
uvicorn).

## What was implemented in this phase

1. `InterviewService.ask_question` -- the full load / ask / retrieve /
   generate / record / save flow, with history snapshotted *before* the
   current question is appended (the generator receives the new question
   separately, so `history` means "everything already answered so far").
2. The `/interviews/{id}/questions` endpoint in `api.py` -- calls the
   service, maps `ValueError` to `404`, maps `Answer` to the `AskResponse`
   DTO, and renders each `Citation` as `f"{source_file}#{chunk_id}"` (the
   same label format Phase 2's prompt will reuse).
3. Two new outbound adapters, `CannedCorpusRetriever` and
   `CannedAnswerGenerator` (`src/itw_me/adapters/outbound/*_canned.py`) --
   legitimate adapters, not test scaffolding, that let the real HTTP server
   run with zero external dependencies.
4. `container.py` updated to switch between the canned pair and the real
   Chroma/OpenAI pair via `ITW_ME_FAKE_LLM` (defaults to `"1"`, i.e. offline
   by default).
5. The previously-skipped `test_ask_question_records_exchange` test,
   un-skipped and passing.

## Definition of done (met)

- `pytest` green, two tests, no network or database.
- `uvicorn itw_me.adapters.inbound.api:app` starts with no environment
  configuration and answers `POST /interviews` and
  `POST /interviews/{id}/questions` with canned text.
- An unknown `interview_id` returns HTTP 404, not a 500 or a raw traceback.
- `grep -r "import chromadb\|import openai" src/itw_me/domain src/itw_me/application`
  returns nothing -- confirmed the inward-dependency rule held even while
  wiring in two adapter pairs.

Next: [phase2_spec.md](phase2_spec.md) (real RAG), then
[phase3_spec.md](phase3_spec.md) (observability).
