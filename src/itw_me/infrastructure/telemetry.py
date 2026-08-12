"""OpenTelemetry metrics instrumentation (Phase 4 -- VOLT's Step 2,
"OpenTelemetry Instrumentation and Core Metrics," exactly).

THE SIX INSTRUMENTS, AND ONE WRINKLE WORTH FLAGGING
------------------------------------------------------
docs/phase4_spec.md asks for six named instruments; all six are defined
right here, in `Instruments`, as the one canonical place their names and
descriptions live. `container.py` builds one `Instruments` bundle at
startup and hands the relevant pieces to whoever needs them:

  - itw_me_retrieval_latency_seconds    -> MeasuredCorpusRetriever
  - itw_me_llm_latency_seconds,
    itw_me_llm_input_tokens_total,
    itw_me_llm_output_tokens_total      -> MeasuredAnswerGenerator
  - itw_me_questions_total,
    itw_me_request_latency_seconds      -> InterviewService

The wrinkle: InterviewService (application/) can never IMPORT this
module (infrastructure/) -- that's the inward-dependency rule. So the
last two instruments are ALSO, separately, re-created inside
InterviewService's own `__init__`, via the bare `opentelemetry.metrics`
API (an explicitly permitted exception -- Counter/Histogram are
interface types, not a concrete infrastructure choice), under the exact
same names as here. In production, container.py passes THIS module's
real objects in and that fallback code never runs; it exists purely so
tests can construct InterviewService standalone (as every test in
tests/test_interview_service.py does) without wiring up telemetry at
all. Two definitions of the same two instrument names, in two files, is
a real, deliberate duplication -- the alternative would be application/
importing infrastructure/, which is the one thing this rule exists to
prevent. See interview_service.py's own comment on this for the other
half of the story.
"""

from __future__ import annotations

from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.metrics import Counter, Histogram, Meter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource

# A GOTCHA WORTH KNOWING ABOUT: OTel's default histogram bucket
# boundaries are [0, 5, 10, 25, 50, 75, 100, 250, 500, 750, 1000, 2500,
# 5000, 7500, 10000] -- sensible for a value reported in MILLISECONDS,
# useless for one reported in SECONDS (this codebase's convention,
# hence the "_seconds" suffix on every latency instrument here). Left
# at the default, a 2-second LLM call and a 4-millisecond one land in
# the exact same "<=5" bucket -- every request would look "fast," and
# the histogram would carry no usable signal at all. This was caught by
# actually running the app and reading real output on /metrics, not by
# reading OTel's docs -- the numbers alone don't look wrong until you
# see every single bucket boundary above your real latencies.
_LATENCY_BUCKET_BOUNDARIES_SECONDS = [
    0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30,
]


class Instruments:
    """All six instruments this phase adds, bundled into one object so
    container.py has exactly one thing to build and pass around instead
    of six positional arguments whose order is easy to mix up.
    """

    def __init__(self, meter: Meter) -> None:
        self.questions_total: Counter = meter.create_counter(
            "itw_me_questions_total",
            description="Total questions answered, labeled by outcome.",
        )
        self.request_latency_seconds: Histogram = meter.create_histogram(
            "itw_me_request_latency_seconds",
            unit="s",
            description="End-to-end ask_question latency.",
            explicit_bucket_boundaries_advisory=_LATENCY_BUCKET_BOUNDARIES_SECONDS,
        )
        self.retrieval_latency_seconds: Histogram = meter.create_histogram(
            "itw_me_retrieval_latency_seconds",
            unit="s",
            description="Corpus retrieval latency.",
            explicit_bucket_boundaries_advisory=_LATENCY_BUCKET_BOUNDARIES_SECONDS,
        )
        self.llm_latency_seconds: Histogram = meter.create_histogram(
            "itw_me_llm_latency_seconds",
            unit="s",
            description="LLM answer-generation latency.",
            explicit_bucket_boundaries_advisory=_LATENCY_BUCKET_BOUNDARIES_SECONDS,
        )
        self.llm_input_tokens_total: Counter = meter.create_counter(
            "itw_me_llm_input_tokens_total",
            description="Total LLM input (prompt) tokens consumed.",
        )
        self.llm_output_tokens_total: Counter = meter.create_counter(
            "itw_me_llm_output_tokens_total",
            description="Total LLM output (completion) tokens generated.",
        )


def configure_metrics() -> Instruments:
    """Call once, at composition-root startup (see container.py) -- and
    call it BEFORE InterviewService is ever constructed, so its two
    instruments never fall back to a no-op meter in production (see this
    module's docstring, and interview_service.py's, for why that
    fallback exists and why it's safe).

    PrometheusMetricReader (from opentelemetry-exporter-prometheus) is a
    "pull" reader: it doesn't push data anywhere on its own -- it just
    registers itself with prometheus_client's global registry, and sits
    there until something scrapes it. That "something" is the /metrics
    endpoint mounted in adapters/inbound/api.py, which calls
    prometheus_client.generate_latest() to render whatever's currently
    in that registry as the Prometheus text exposition format, on
    demand, per request. No background thread, no timer, no network
    call happens inside this process until a scraper (Prometheus itself,
    or a plain `curl localhost:8000/metrics`) asks for it.
    """
    # Resource: metadata describing WHAT is producing these metrics, as
    # opposed to the metrics themselves. Without this, the Prometheus
    # exporter labels everything "unknown_service" -- harmless for one
    # single-service demo, but the first thing that matters the moment
    # more than one service's metrics land in the same Prometheus.
    resource = Resource.create({"service.name": "itw-me"})

    reader = PrometheusMetricReader()
    provider = MeterProvider(metric_readers=[reader], resource=resource)

    # Global, process-wide, by design: `opentelemetry.metrics` is meant
    # to be configured exactly once, then have every other part of the
    # codebase call metrics.get_meter(...) and simply find it already
    # there -- the same "configure once at the root, use everywhere"
    # shape as infrastructure/logging.py's configure_logging().
    metrics.set_meter_provider(provider)

    meter = metrics.get_meter("itw_me")
    return Instruments(meter)
