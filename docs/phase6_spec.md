# Task: Complete the itw-me RAG chatbot (Phase 6) -- dashboards & alerting

## Context

itw-me is a small RAG chatbot: visitors "interview" Antoine by chatting with a bot
grounded in a corpus of markdown documents about him (CV, bio, experience). By the
time this phase starts, Phase 3 (logging + correlation), Phase 4 (OTel metrics +
Prometheus), and Phase 5 (distributed tracing) are all done -- see
[phase3_spec.md](phase3_spec.md), [phase4_spec.md](phase4_spec.md), and
[phase5_spec.md](phase5_spec.md).

This phase exists to mirror, exactly, Step 4 ("Dashboards and Alerting") of the
VOLT observability spike ticket this sequence is tracking. VOLT's Step 4 is four
bullets: create Grafana dashboards, configure Azure Monitor alerts, define SLO
monitoring, add operational review dashboards. This is the **last** phase in the
sequence, and it is also the phase where itw-me's stack diverges most from VOLT's
-- VOLT has Azure Monitor and Azure Managed Grafana available; itw-me has plain,
self-hosted Grafana. The "Divergences" section below is deliberately placed here,
at the end, since it is the cumulative answer to "what is different across this
whole sequence," not just this one phase.

This is also a training codebase. Code quality, comments explaining non-obvious
decisions, and architectural discipline matter more than feature count. Prefer
clear code over clever code.

## Current state (do not rewrite, extend)

- Phases 3-5 done: structured JSON logs with `correlation_id`/`interaction_id`/
  populated `trace_id`; Prometheus metrics at `/metrics`; Jaeger traces for every
  request. `docker-compose.yml` has `prometheus`, `grafana`, `app`, and `jaeger`.
- `grafana` service exists but is unprovisioned -- an operator would have to
  click through the UI by hand to add Prometheus as a datasource and build any
  panel. No dashboard JSON, no datasource config, no alert rules exist yet.

## Architectural rules (hard constraints, violating these fails the task)

1. Inward dependency rule: unaffected by this phase -- no new code is added to
   `domain/` or `application/`, only provisioning files under `observability/`.
2. Environment variables (e.g. Grafana admin credentials) are set via
   `docker-compose.yml`, never hardcoded in provisioning files that get committed.
3. Existing tests must stay green -- this phase adds no Python code, so this
   should be automatic, but verify anyway.

## Phase 6: dashboards + alerting (VOLT's Step 4)

1. **Grafana provisioning**: add provisioning files under
   `observability/grafana/` (a datasource pointing at `http://prometheus:9090`,
   plus one dashboard JSON) and mount them in the `grafana` service so the
   dashboard exists the moment `docker compose up` finishes -- no manual
   click-through. Dashboard panels: request rate, error rate, p95 end-to-end
   latency, p95 retrieval and LLM latency, tokens per minute. This is VOLT's
   "create Grafana dashboards" and "add operational review dashboards" bullets.
2. **Alerting (VOLT's Azure Monitor alerts / SLO monitoring, translated)**: VOLT
   would configure Azure Monitor alert rules and action groups; itw-me has no
   Azure Monitor, so the closest self-hosted equivalent is Grafana's own
   alerting engine, querying Prometheus directly -- same signal, different
   product. Define at least one alert rule (e.g. error rate over a threshold
   over a rolling window) provisioned the same way as the dashboard, not
   clicked through the UI. When translating this phase back to VOLT: this step
   becomes literally "configure Azure Monitor alerts + define SLOs" using
   Azure's own tooling, not Grafana's -- the *what* (alert on error rate / p95
   latency breaching a threshold) carries over, the *how* does not.
3. **README**: finish the "Running the stack" section -- `docker compose up`,
   where to see logs (stdout), metrics (`:9090`), traces (`:16686`), and
   dashboards/alerts (`:3000`).

## Divergences from the VOLT ticket (deliberate, across the whole Phase 3-6 sequence)

- **No Azure Application Insights / Azure Monitor / Azure Managed Grafana.**
  itw-me runs on `docker-compose`, not AKS. Jaeger (Phase 5) and
  Prometheus/Grafana (Phases 4/6) are the direct self-hosted equivalents; there
  is no Azure-native tooling to integrate with. Every place this sequence says
  "Grafana" or "Jaeger," VOLT's real implementation reaches for the Azure-native
  or already-existing tool instead.
- **No AKS / Kubernetes.** Out of scope for a portfolio training repo;
  `docker-compose` plays the same "deployment platform" role at this scale.
- **No feedback metrics or conversation-usage metrics** (VOLT: positive/negative
  feedback rate, turns per conversation, conversation age, revisits). VOLT's
  ticket assumes a feedback-capture feature already backed by PostgreSQL; itw-me
  has no feedback feature at all, and building one is a product decision, not an
  observability one. Not covered by any phase here, same spirit as VOLT's own
  "Cost Metrics (Future Candidate)".
- **Langfuse is a separate, optional addition**, not part of Phases 3-6 at all --
  see [langfuse_spec.md](langfuse_spec.md). VOLT already has it; it maps to
  nothing left in VOLT's rollout.

## Definition of done

- `pytest` green, offline, no keys needed (unaffected by this phase).
- With `docker compose up` and some traffic sent through: the Grafana dashboard
  at `localhost:3000` shows live panels with no manual setup.
- The alert rule fires under a manufactured failure (e.g. stop the `app`
  container, or force a burst of 404s) and clears once traffic is healthy again.

This is the last phase in the sequence: once Phases 3-6 are done, itw-me's
observability corresponds to VOLT's Steps 1-4, module for module, modulo the
divergences listed above.
