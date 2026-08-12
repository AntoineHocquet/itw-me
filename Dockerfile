# Phase 4 -- itw-me-only plumbing, no VOLT equivalent (VOLT already runs
# on AKS; this exists purely so docker-compose has something to scrape
# on :8000, see docker-compose.yml and observability/prometheus.yml).
FROM python:3.12-slim

WORKDIR /app

# Copy just the dependency manifest first so Docker's layer cache can
# skip reinstalling dependencies on every code change -- only a
# pyproject.toml edit invalidates this layer, not editing application
# code, which is the entire reason this is two COPY steps instead of one.
COPY pyproject.toml ./
COPY src ./src

# No [dev] extra here (no pytest/httpx in the image) and no [langfuse]
# extra either -- this is the runtime image, not the test environment.
# `pip install .` (not `-e`) because there's no local dev loop inside a
# container: the code is copied in once, not edited in place.
RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "itw_me.adapters.inbound.api:app", "--host", "0.0.0.0", "--port", "8000"]
