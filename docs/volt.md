# Explaining this to the VOLT team

This document is different from the other files in `docs/`. `phase3_spec.md`
through `phase6_spec.md` are *build specs* for itw-me -- they tell whoever
implements a phase exactly what to change, in itw-me's own code. This file is
the opposite direction: for each phase, once it's built here, a write-up
explaining the underlying technique in general terms, for discussion with the
VOLT team, so the concepts (not itw-me's specific code) transfer to VOLT's own
observability rollout.

Written after implementing each step end-to-end here first -- not a spec to
copy verbatim into VOLT, since VOLT's stack differs in places (Azure
Application Insights, AKS, Langfuse already in place). The mechanism is what
should transfer; the code is itw-me's own illustration of it.

One section per phase, added as each phase is actually built and verified --
this file starts with Phase 3 and grows from there.

## What itw-me actually is

itw-me is a toy: a RAG chatbot that lets a visitor "interview" Antoine.
Ask it a question, it retrieves relevant snippets from a small corpus of
markdown files (his CV, his bio) and asks an LLM to answer *only* from
those snippets, citations included. That's the entire product. It is
small on purpose -- one person can read the whole thing, end to end, in
an afternoon.

The point of it existing is not the chatbot. The point is that it is
shaped like a miniature of VOLT -- an HTTP API in front, a retrieval
step, an LLM call, a persistence step -- so that an observability
technique can be built, broken, fixed, and actually *watched running*
here, cheaply, before the same technique gets built for real against
VOLT's actual traffic, actual Azure infrastructure, and actual users.
Think of it as a workbench, not a demo.

### The repo, annotated

```
itw-me/
├── corpus/                      the "memory" the bot is grounded in
│   ├── cv.md                       -- plain markdown, nothing fancier
│   └── bio.md
├── docs/                         phase specs (build instructions) + this file
│   ├── phase1_spec.md … phase6_spec.md
│   └── volt.md                     ← you are here
├── observability/                config for the tools bolted on per phase
│   ├── prometheus.yml               (Phase 4)
│   └── grafana/                     (Phase 6)
├── scripts/
│   └── ingest.py                 corpus/*.md → chunks → vector store
├── src/itw_me/
│   ├── domain/                   business rules ONLY. no framework, no I/O.
│   │   ├── models.py                Interview, Exchange, Question, Answer, Citation
│   │   └── ports.py                 interfaces: CorpusRetriever, AnswerGenerator, InterviewRepository
│   ├── application/               orchestrates domain + ports; imports only domain + stdlib
│   │   ├── interview_service.py      the one use case: ask_question()
│   │   └── request_context.py        Phase 3: correlation_id / interaction_id / trace_id
│   ├── adapters/
│   │   ├── inbound/api.py         FastAPI: HTTP ⇄ domain translation, + Phase 3's middleware
│   │   └── outbound/               Chroma, OpenAI/Ollama, Langfuse, in-memory repo, offline fakes
│   └── infrastructure/
│       ├── container.py           composition root: the ONE place concrete adapters get chosen
│       └── logging.py              Phase 3: the JSON log formatter
├── tests/                        fast, offline -- fakes stand in for every real dependency
├── docker-compose.yml            prometheus + grafana (+ app once Phase 4 lands)
└── pyproject.toml
```

The directory names are not decoration -- `domain/` really cannot import
FastAPI, Chroma, OpenAI, or anything else "real"; `application/` really
cannot import a database driver or a vendor SDK. That constraint is what
makes the "workbench" property true: swap `adapters/outbound/` for
different technology (a different vector store, a different LLM
provider, Langfuse on or off) and nothing in `domain/` or `application/`
changes or even notices. VOLT presumably already leans this way to some
degree; itw-me just makes the boundary strict enough to be a visible,
checkable rule (`grep -r "import chromadb\|import openai" src/itw_me/domain
src/itw_me/application` is a real command in this repo's test suite, not
a metaphor).

### One request, followed through the machine

This is the shape every phase in this document instruments, one layer
at a time:

```
   caller (browser / curl / VOLT's own frontend, for the analogy)
     │
     │  POST /interviews/42/questions
     │  X-Correlation-Id: demo-1     (caller's own id, or none at all)
     ▼
 ╔══════════════════════════════════════════════════════════╗
 ║ adapters/inbound/api.py                                   ║
 ║   correlation_id = "demo-1"  (reused)  or a fresh uuid4    ║   ← Phase 3
 ╚═══════════════════════════╤════════════════════════════════╝
                              ▼
 ╔══════════════════════════════════════════════════════════╗
 ║ application/interview_service.py :: ask_question()        ║
 ║                                                              ║
 ║   1. load the Interview  ─────────────────── (repository)   ║
 ║   2. ask()  → a new Exchange is born, with its own .id       ║
 ║        interaction_id = exchange.id                          ║   ← Phase 3
 ║   3. retrieve()  ───────────────────────── (CorpusRetriever) ║   ← Phase 5 (spans)
 ║   4. generate()  ────────────────────────── (AnswerGenerator)║   ← Phase 4 (metrics), 5 (spans)
 ║   5. record_answer()  (domain invariant enforced here)        ║
 ║   6. save()  ──────────────────────────────── (repository)   ║
 ╚═══════════════════════════╤════════════════════════════════╝
                              ▼
     stdout, one JSON object per line, e.g.:
     {"correlation_id":"demo-1","interaction_id":"c5cd8848-…","trace_id":null, "message":"generating answer", …}
     {"correlation_id":"demo-1","interaction_id":"c5cd8848-…","trace_id":null, "message":"recorded answer", …}
```

Two ids are already flowing through that diagram (`correlation_id`,
`interaction_id`); a third (`trace_id`) is drawn as `null` because it's
reserved but not populated until Phase 5. That's exactly what the next
section is about.

---

## Phase 3 (VOLT's Step 1): structured logging & correlation IDs

### The problem, concretely

Someone reports: "I asked a question and got a weird answer." You now have to
find that one request. Your service does several things per request --
retrieve, call an LLM, persist a record -- and under load, dozens of these are
interleaved on the same process at the same time. Three tools you might reach
for, and why each one alone falls short:

- **grep the logs for the question text.** Works until the question contains
  nothing distinctive, or the user paraphrases it in the bug report.
- **Look at the timestamp.** Works until two users hit the service in the same
  second -- which, at any real traffic volume, happens constantly.
- **Look at Langfuse.** Tells you what happened *inside* the LLM call -- the
  prompt, the tokens, the cost -- but not what happened *around* it: which
  retrieval query ran, whether the DB write that followed it succeeded, what
  the HTTP layer saw.

What's actually missing is a shared **key** that appears on every line of
evidence for one request, across every system that touched it. That's the
whole idea. Everything below is different ways of making that key exist,
propagate itself without manual effort, and show up in a format you can
actually query.

### Three ideas, not one

**1. Give every request an ID, and echo it back.**
On the way in, read a header (say `X-Correlation-Id`); if the caller didn't
send one, generate one. Attach it to every log line the request produces.
Put it back on the response. Now a bug report that includes "the response
had `X-Correlation-Id: 7f2a...`" is a complete, unambiguous pointer into your
logs -- no timestamp guessing, no grepping for fuzzy text.

**2. Give the *thing inside* the request its own, narrower ID.**
A correlation ID scopes to "one HTTP request." That's often not granular
enough. In a chat/RAG system, "one turn of the conversation" is usually the
more useful unit -- you want to filter logs down to *this specific
question-and-answer*, not just *this specific HTTP call*, especially once a
request can trigger several turns, or a turn can span a retry. Call this
second, narrower id whatever fits your domain (we used `interaction_id`, for
one Q&A turn). The pattern is the same: mint it once, close to where that unit
of work is created, and stop caring about it once that unit of work ends.

**3. Make your logs a format a machine can query, not just a human can read.**
`2026-08-12 10:13:27 INFO retrieving chunks` is fine for a human tailing a
terminal. It is useless for a log aggregator (Loki, Elasticsearch, Azure Log
Analytics, whatever) trying to answer "show me every log line where
`interaction_id = X` and `level = ERROR`." One JSON object per line, with a
handful of fixed fields (`timestamp`, `level`, `service`, `environment`, plus
the two ids above) turns every log line into a queryable record instead of a
string you hope to regex correctly.

None of this requires a new backend, a new vendor, or a network call. It's
pure application code. That's what makes it a sensible *first* step before
metrics or tracing: it's cheap, and everything after it benefits from it
already being there.

### What this looked like, concretely

Two real log lines, captured by actually running the service and asking it
two questions with different correlation ids:

```json
{"timestamp": "2026-08-12T10:13:27.123903Z", "level": "INFO", "service": "itw-me", "environment": "dev", "logger": "itw_me.application.interview_service", "message": "generating answer", "correlation_id": "d44228bc-...", "interaction_id": "c5cd8848-...", "trace_id": null, "retrieved_chunk_count": 0}
{"timestamp": "2026-08-12T10:13:27.131403Z", "level": "INFO", "service": "itw-me", "environment": "dev", "logger": "itw_me.application.interview_service", "message": "generating answer", "correlation_id": "demo-for-the-team", "interaction_id": "4ae081df-...", "trace_id": null, "retrieved_chunk_count": 0}
```

Same message, same code path, two different requests -- trivially
distinguishable by `correlation_id`, and each internally consistent across
every log line for that request. The second one's `correlation_id` is
literally the string a caller sent in -- `X-Correlation-Id: demo-for-the-team`
-- proving the round-trip actually works, not just "an id exists."

Note `trace_id: null` in both. That field is *reserved*, not yet populated --
more on that below.

### The mechanism: how the id gets from "set once" to "on every log line," with no extra function arguments

This is the part that looks like magic if you haven't seen it before, and
it's worth spending real meeting time on, because it's the reusable idea:

- Python's stdlib gives you `contextvars.ContextVar` -- a value that's global
  in scope but *isolated per logical task* (in an async server, that's
  isolated per request). You `.set()` it once, early (in HTTP middleware, for
  the correlation id; deeper in the code, for the interaction id).
- Every log line's formatter reads it back with `.get()`, at format time, not
  at call time. So a function three layers deep in the call stack -- one that
  has *never seen* the correlation id passed as an argument -- still gets it
  stamped onto its log lines, automatically.
- Crucially: this is *not* the same as a plain global variable. A plain
  global would be shared across every concurrent request on the same process
  and would leak request A's id into request B's log lines the moment they
  overlap in time (which, under real traffic, is constantly). `ContextVar`
  specifically solves "isolated per request, shared within it" -- that's the
  entire reason it exists as a distinct primitive from a global.
- You always pair `.set()` with `.reset()` in a `finally` block, so the
  binding cleanly ends when the unit of work ends, rather than leaking into
  whatever code happens to run next on that same worker.

Every mainstream stack has an equivalent of this exact mechanism, because
every mainstream stack has this exact problem: .NET has `Activity`/
`ILogger` scopes, Java has MDC (Mapped Diagnostic Context) in
Log4j/Logback, Node has `AsyncLocalStorage`. If VOLT's backend is Python,
this maps directly. If it's something else, the concept -- "a value bound
for the lifetime of one logical operation, invisible to function
signatures, safe under concurrency" -- is what to look for by name in
that ecosystem.

### One deliberate design wrinkle worth flagging

The framework you're using probably already runs its own logger with its own
formatting (in our case: uvicorn prints its own access log line by default).
Getting to "literally every line is JSON" required explicitly re-pointing
that framework logger at the same formatter -- otherwise you get JSON for
your own application code and plain text for the framework's, side by side,
which defeats the point for anyone trying to query the whole log stream
uniformly. Worth checking for the equivalent gotcha in whatever's serving
VOLT's HTTP traffic.

### What this deliberately does *not* do

- **It is not distributed tracing.** There's no span, no parent/child
  relationship between operations, no visualization of where time went. The
  `trace_id` field being present-but-`null` is a placeholder for exactly
  that -- reserved now, on purpose, so that adding real tracing later is a
  pure *write* to a field that already exists everywhere it needs to, with
  zero changes to any logging code. That's the next step, not this one.
- **It doesn't replace Langfuse**, or whatever LLM-specific observability
  tool is already in place. Langfuse still owns "what did the model see and
  say, what did it cost." Correlation/interaction ids own "which log lines,
  across every part of the system, belong to the same unit of work." They're
  complementary, not competing -- you'd actually want the interaction id to
  end up as metadata *inside* the Langfuse trace too, so the two are
  cross-referenceable.
- **It's not metrics.** A counter of "how many requests failed" is a
  different, aggregate question from "show me everything about *this*
  request." Both matter; this step only buys the second one.

### Translating this to VOLT

VOLT's own version of this step should end up answering the same question --
"given one correlation id, can I pull every log line for that request,
regardless of which part of the pipeline produced it" -- using whatever's
already true about VOLT's stack:

- If logs already flow into Azure Application Insights: App Insights has its
  own operation-correlation concept (`operation_Id`) that Azure's SDKs
  populate automatically inside a request -- check whether that's already
  doing part of this job before building a parallel mechanism. The gap to
  close is likely "is our OWN structured field (an interaction/turn id, not
  just Azure's operation-level one) actually attached to every log line," not
  "does correlation exist at all."
- The "reserve a `trace_id` field now, populate it for real later" trick is
  worth keeping regardless of backend -- it's what makes the later tracing
  step additive rather than a logging rewrite.
- Whatever the wire format ends up being, the test for "did this actually
  work" is the same one used here: run it, send two overlapping requests, and
  check by hand that their log lines don't cross-contaminate. That's a
  five-minute check that catches the single most common way this kind of
  change quietly fails.

---

## Phase 4 (VOLT's Step 2): OpenTelemetry metrics + Prometheus

*Not written yet -- add once [phase4_spec.md](phase4_spec.md) is built.*

## Phase 5 (VOLT's Step 3): distributed tracing

*Not written yet -- add once [phase5_spec.md](phase5_spec.md) is built.*

## Phase 6 (VOLT's Step 4): dashboards & alerting

*Not written yet -- add once [phase6_spec.md](phase6_spec.md) is built.*
