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

### The problem, concretely

Phase 3's logs answer "what happened on *this one* request" -- they are
the right tool once you already know which request you care about.
They do not answer "is the service healthy *right now*," or "did p95
latency just get worse after that last deploy." Answering those needs
numbers aggregated across every request, continuously, not text you'd
have to grep and hand-count. That's what metrics are: a small, fixed set
of counters and histograms -- cheap to store, cheap to query, cheap to
put on a dashboard -- that answer "how many," "how fast," "how often
does it fail" at a glance, without caring which individual request
produced any of it.

### Two ideas worth separating

**1. Metrics are usually pulled, not pushed.** The app never sends a
single byte to Prometheus. It just keeps a handful of numbers updated in
memory and exposes them, as plain text, on one HTTP endpoint
(`/metrics`). Prometheus is the one that reaches out, on its own
schedule, and reads that endpoint. This inversion matters operationally:
the app doesn't need to know Prometheus's address, doesn't retry on
network failure, doesn't buffer anything -- it just always answers "here
is what the counters say right now" when asked. If nobody ever scrapes
it, the app behaves identically; it's just wasted potential.

**2. The instrumentation library (OpenTelemetry) and the storage backend
(Prometheus) are two separate, swappable things.** OpenTelemetry defines
a vendor-neutral *API* (`Counter.add(...)`, `Histogram.record(...)`) that
application code calls. A separate *exporter* decides what actually
happens to those numbers -- render them as Prometheus text, ship them to
Azure Monitor, print them to a file, whatever. Swap the exporter,
instrumentation code doesn't change. This is the same API/implementation
split Phase 3 leaned on for `contextvars` vs. plain globals, just at a
different layer of the stack -- and it's why the OTel API is one of only
two things (the other: stdlib `logging`) this codebase's own
architectural rules let deeper layers depend on directly.

### What this looked like, concretely

Real output from `curl localhost:8000/metrics` after asking two
questions, filtered to just this app's own instruments:

```
# TYPE itw_me_questions_total counter
itw_me_questions_total{status="ok"} 2.0

# TYPE itw_me_request_latency_seconds histogram
itw_me_request_latency_seconds_bucket{le="0.005"} 1.0
itw_me_request_latency_seconds_bucket{le="0.01"} 1.0
...
itw_me_request_latency_seconds_bucket{le="+Inf"} 2.0
itw_me_request_latency_seconds_sum 0.000406...

# TYPE itw_me_llm_input_tokens_total counter
itw_me_llm_input_tokens_total 0.0
```

`status="ok"` is a *label* -- Prometheus's way of slicing one metric
name into several time series (`status="ok"` vs `status="error"`),
queryable independently or summed together. The histogram isn't one
number, it's a set of "how many requests took ≤ this long" counts at
several thresholds (its *buckets*) plus a running sum -- that's what
lets a dashboard later compute "p95 latency" without the raw per-request
numbers ever being stored anywhere.

### A real mistake, caught by actually running it

The first version of this exposed exactly the numbers above, except
every single latency landed in the very first bucket, no matter how the
request was timed. Cause: OpenTelemetry's *default* histogram bucket
boundaries are `0, 5, 10, 25, 50, ... 10000` -- sensible if your value is
in **milliseconds**, actively useless if it's in **seconds** (this
codebase's own convention, hence every instrument being named
`*_seconds`). A histogram with the wrong bucket boundaries doesn't
error, doesn't warn, doesn't look wrong in any code review -- it just
quietly produces numbers with zero useful resolution, forever, until
someone happens to look at real output and notices every request "took
less than 5 seconds," which is true and tells you nothing. The fix is
one constructor argument (`explicit_bucket_boundaries_advisory`, a list
of thresholds that actually spans the latencies you expect), but finding
the problem at all required looking at real numbers, not just at
whether the code ran without exceptions. Worth checking explicitly for
VOLT's own histograms, whatever unit they end up in.

### What this deliberately does not do

- **It's not a replacement for Langfuse's token/cost tracking.** These
  counters (`itw_me_llm_input_tokens_total`, etc.) answer "how many
  tokens, in aggregate, across all traffic" -- a health/capacity
  question. Langfuse answers "what did *this specific* call cost, with
  what prompt" -- a debugging/analysis question. Same underlying numbers,
  different shape of question.
- **It's not tracing.** A histogram can tell you "retrieval got slower
  this week"; it cannot tell you *which* request, or whether the
  slowdown was in retrieval itself or in something it called. That's
  Phase 5.
- **Cardinality is a hard constraint, not a style preference.** Every
  label value becomes its own stored time series. A `status` label with
  two possible values (`ok`/`error`) is two time series, forever. A label
  holding a user id, a question's text, or anything else effectively
  unbounded would mean a new time series *per request*, which is exactly
  the failure mode Prometheus calls "cardinality explosion" -- it degrades
  or falls over, not gracefully, under exactly that pattern. Every label
  used here comes from a small, fixed set on purpose.

### Translating this to VOLT

- VOLT's ticket already names the same six-ish categories of metric
  (request count/latency, retrieval, LLM, tokens); the work is choosing
  label sets for each that stay small and fixed -- `status`, maybe a
  `workflow_step` enum, never anything free-text or per-user.
  the exact right idea; check every histogram it defines against real
  observed latencies before calling it done. Milliseconds vs. seconds
  is the specific bug found here, but the general lesson -- default
  bucket boundaries are a guess, not a fact about your service -- applies
  regardless of unit.
- If VOLT already has *any* metrics pipeline (Azure Monitor's own metrics,
  or an existing OTel setup), the swap-the-exporter property described
  above is the thing to lean on: instrumentation code (counters,
  histograms, what gets measured where) shouldn't need to change based
  on which backend receives it.

## Phase 5 (VOLT's Step 3): distributed tracing

### The problem, concretely

Phase 4's metrics can tell you "p95 latency for `generate` went up this
week." They cannot tell you *why*, for any single request -- was it the
retrieval step or the LLM call? Was it always slow, or slow starting
from one specific deploy? A histogram has already thrown away which
request it came from by the time you're looking at it. Distributed
tracing is the tool that keeps that information: for *one specific
request*, exactly which steps ran, in what order, nested how, and how
long each one took -- a timeline you can actually open and look at,
not a number you have to infer a story from.

### The core idea: spans, and parent-child nesting for free

A **span** is "one named operation, with a start time and an end time."
A **trace** is a tree of spans that all happened as part of one logical
request. The thing worth understanding, because it looks like magic
otherwise: nothing in this codebase explicitly says "`generate` is a
child of `ask_question`." The nesting is entirely a side effect of *when
each span is open*: `ask_question`'s span opens first; while it's still
open, code inside it opens `generate`'s span; while THAT is still open,
code inside IT opens the actual LLM-call span. Whichever span is
"currently open" when a new one starts automatically becomes its parent.
Same underlying mechanism (Python's `contextvars`) Phase 3 used for
`correlation_id`, just OTel's own built-in version of it, applied to a
tree instead of a single flat value.

### What this looked like, concretely

A real trace, from the actual span tree this phase produces for one
question (captured via the JSON logs' shared `trace_id` -- see below --
rather than a screenshot, but the shape is exactly what Jaeger renders):

```
ask_question                          (root -- the whole use case)
├── retrieve                          (workflow span: the retrieval step)
│   └── chroma.query                  (dependency span: the actual vector-store call)
└── generate                          (workflow span: the generation step)
    └── llm.chat.completions          (dependency span: the actual LLM call)
```

And the log-correlation payoff, from actually running the app and
asking one question -- all three application log lines below carry the
SAME `trace_id`, which previously (Phases 3-4) was always `null`:

```json
{"message": "retrieving corpus chunks", "trace_id": "cda1d0a5e77b70a4a326f91db4b7e7fb", "correlation_id": "e5d1c89b-...", ...}
{"message": "generating answer",        "trace_id": "cda1d0a5e77b70a4a326f91db4b7e7fb", "correlation_id": "e5d1c89b-...", ...}
{"message": "recorded answer",          "trace_id": "cda1d0a5e77b70a4a326f91db4b7e7fb", "correlation_id": "e5d1c89b-...", ...}
```

That `trace_id` is the same 32-hex-digit id Jaeger's UI would show for
this request's trace -- click it in either place and you land on the
same thing. That's VOLT's ticket's "correlate logs, metrics, traces"
objective, made concrete: one id, generated once, threading through
every signal without any of them needing to know about each other.

### Two real gotchas, both found only by actually running this

**1. There is exactly one "slot" for a tracer configuration per
process, ever.** Unlike logging (where reconfiguring the root logger's
handlers is always allowed, last call wins) and unlike metrics
(where instruments transparently "upgrade" once a real backend is
configured, regardless of call order), OTel's tracing API accepts
`set_tracer_provider()` exactly once -- every later call is silently
ignored. This has a real, practical consequence for testing: you cannot
spin up a fresh, isolated tracer configuration per test the way you
might expect. The fix used here was to make every tracing-aware
component accept a `Tracer` as a constructor argument (defaulting to the
real global one), so tests can hand it a fake without ever touching
global state. Worth knowing before writing VOLT's own tracing tests,
not after.

**2. A "push" exporter with no collector listening doesn't just fail
quietly -- it can make your test suite hang, and print something
alarming afterward.** Same "pull vs. push" distinction as Phase 4's
Prometheus section, except tracing IS push-based (spans get sent to
Jaeger, nothing scrapes them). Left at OTel's default retry/backoff
settings, a missing collector added 6+ seconds to every test run in
this codebase, and could print a stray `ValueError: I/O operation on
closed file` traceback at process exit -- cosmetic (exit code stayed 0,
every test still passed), but exactly the kind of thing that makes
someone new to a repo think something is broken when nothing is. Fixed
with short, explicit timeouts on the exporter, plus one test fixture
that shuts the tracer down cleanly before the interpreter starts tearing
itself down. If VOLT's own test suite ever adds tracing, budget time to
hit this same issue and fix it the same way -- it is not specific to
this codebase, it is inherent to push-based exporters with no listener.

### What this deliberately does not do

- **It doesn't replace Langfuse.** Langfuse's own tracing is purpose-
  built for LLM calls specifically -- prompts, token-by-token cost,
  model comparisons. The `llm.chat.completions` span here records that a
  call happened and how long it took; it is not trying to be a second
  Langfuse.
- **It isn't automatic.** Every span in this phase was opened by hand,
  at a specific line of code someone chose. Auto-instrumentation
  packages exist (they patch libraries like `requests`/`httpx` to open
  spans for you) and are worth knowing about, but this phase deliberately
  used manual instrumentation throughout, to make every "why does this
  span exist and what does it measure" question answerable by reading
  the code that opens it.
- **Two spans, not four**, for the workflow steps
  (`retrieve`/`generate`, not `plan`/`retrieve`/`reflect`/`generate`) --
  purely because itw-me has no planning or reflection step, not a
  coverage gap. VOLT's own agentic workflow should get all four.

### Translating this to VOLT

- VOLT's Step 3 names two things: workflow spans and dependency spans.
  Both patterns transfer directly -- workflow spans wrap whichever unit
  of orchestration corresponds to itw-me's `retrieve`/`generate` (for
  VOLT: `plan`/`retrieve`/`reflect`/`generate`), and dependency spans
  wrap each of the four vendor calls VOLT's ticket names (Azure OpenAI,
  Azure AI Search, PostgreSQL, Blob Storage) with vendor-specific
  attributes, the same way `chroma.query`/`llm.chat.completions` do here.
- Both gotchas above are worth checking for explicitly, early, rather
  than discovering them the way this build did (by noticing a slow test
  suite and an alarming traceback). They are properties of the
  OpenTelemetry SDK itself, not of this specific codebase.
- Azure Monitor (VOLT's likely tracing backend, given its ticket's
  "Current State") speaks OTLP too -- the exporter swap this phase's
  Phase 4 section already described applies here as well: instrumentation
  code (where spans open, what they're named, what they're tagged with)
  shouldn't need to change based on whether it's Jaeger or Azure Monitor
  receiving them.

## Phase 6 (VOLT's Step 4): dashboards & alerting

*Not written yet -- add once [phase6_spec.md](phase6_spec.md) is built.*
