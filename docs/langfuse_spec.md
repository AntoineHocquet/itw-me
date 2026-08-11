# Task: Complete the itw-me RAG chatbot (optional) -- Langfuse LLM tracing -- done

## Context

itw-me is a small RAG chatbot: visitors "interview" Antoine by chatting with a bot
grounded in a corpus of markdown documents about him. This document is deliberately
**not** numbered as a phase in the Phase 3-6 observability sequence
([phase3_spec.md](phase3_spec.md) through [phase6_spec.md](phase6_spec.md)), and
that omission is the point, not an oversight.

Those four phases were built to correspond 1:1 with the four steps of a real
"BACKEND OBSERVABILITY" spike ticket written for VOLT, a different RAG chatbot
Antoine works on professionally -- the goal being that finishing Phase 6 here tells
him exactly what remains to build for VOLT's actual rollout. Langfuse does not fit
that mapping: VOLT's ticket lists Langfuse under **"Current State"** ("Langfuse
tracing for LLM execution and prompt analysis") -- it already exists there. It is
not one of VOLT's four "Proposed Rollout" steps, and nothing in VOLT's remaining
work requires building it. Folding it into Phases 3-6 would have made "finish Phase
N" stop meaning "VOLT Step N is done," which defeats the reason that sequence was
split the way it was.

This document exists anyway because Langfuse (LLM-specific tracing: prompts, token
usage, cost, retrieval context) is a different kind of observability than generic
OTel spans, and itw-me is a training repo -- seeing both side by side has learning
value independent of VOLT parity. Treat this as a standalone, skippable addition,
best done any time after [phase2_spec.md](phase2_spec.md) (it needs a real
`AnswerGenerator`, nothing from Phases 3-6).

## Current state -- done

- ~~No Langfuse dependency or integration anywhere in the codebase.~~ Done:
  `adapters/outbound/generator_langfuse.py` (`LangfuseTracedAnswerGenerator`),
  wired in `container.py` behind `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`,
  tested offline in `tests/test_generator_langfuse.py` by patching the
  `Langfuse` class.
- Built right after Phase 2, before the Phase 3-6 observability sequence --
  the ordering this doc's Context section recommended, since it puts itw-me in
  a state that mirrors VOLT's own "Current State" (real RAG + Langfuse, no
  generic OTel yet) before that sequence begins.

## Architectural rules (hard constraints, violating these fails the task)

1. Inward dependency rule: `domain/` and `application/` never import `langfuse`.
   Unlike the `opentelemetry` API, Langfuse's SDK is vendor-specific end to end
   and gets no facade exception -- it stays entirely inside
   `adapters/outbound/` and `infrastructure/container.py`.
2. Concrete adapters are instantiated only in `infrastructure/container.py` (and
   in tests). Environment variables are read only there.
3. Existing tests must stay green, offline, without Langfuse credentials.
4. Naming convention for adapters: Technology + PortName, e.g.
   `LangfuseTracedAnswerGenerator`.

## Implementation (all done)

1. ~~**Decorator adapter**~~ -- done: `LangfuseTracedAnswerGenerator` in
   `adapters/outbound/generator_langfuse.py`, wrapping any `AnswerGenerator`.
   Around the wrapped call, it captures the question, retrieved chunks,
   output text, and token usage. One correction versus this doc's original
   plan: Langfuse's Python SDK (v3+) was rewritten on top of OpenTelemetry --
   there is no `client.trace()`/`client.generation()` anymore. The current
   equivalent is `client.start_as_current_observation(as_type="generation")`,
   a context manager that creates one observation and ends it on exit; that's
   what the adapter actually uses. Latency and cost are not captured
   explicitly -- Langfuse derives latency from the observation's own
   start/end timestamps, and cost needs pricing metadata this adapter doesn't
   have, so it's left as a future enhancement rather than faked.
2. ~~**Env-gated wiring**~~ -- done: `container.py` wraps the chosen generator
   in `LangfuseTracedAnswerGenerator` only when both `LANGFUSE_PUBLIC_KEY` and
   `LANGFUSE_SECRET_KEY` are set (the import itself is local to that branch,
   confirmed to never fire otherwise).
3. ~~**Dependency**~~ -- done: `langfuse` added under a new
   `[project.optional-dependencies]` group in `pyproject.toml`, and also
   under `dev` -- tests need the package importable (to patch `Langfuse`),
   even though they never reach the network, the same pattern
   `test_llm_openai.py` uses for the `openai` package.
4. ~~**README**~~ -- done: "Optional: Langfuse tracing" section added.

## Definition of done

- [x] `pytest` green, offline, no Langfuse credentials needed (17 tests total,
      3 new: `tests/test_generator_langfuse.py`).
- [x] With `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` unset: behavior
      identical to before, no Langfuse import attempted at runtime -- verified
      by constructing the service with those env vars unset and confirming
      `generator_langfuse` is never imported.
- [x] With them set (verified with fake keys, no real network needed for this
      check): `build_interview_service()` returns a service whose generator is
      `LangfuseTracedAnswerGenerator`. A real project's credentials would show
      the prompt, retrieved context, and token counts in Langfuse's UI.
- [x] `grep -r "import langfuse" src/itw_me/domain src/itw_me/application`
      returns nothing.
