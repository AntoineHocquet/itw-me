"""ChromaDB implementation of CorpusRetriever.

Collection name, persistence path, and embedding function all come from
chroma_config.py -- the single source of truth also used by
scripts/ingest.py, so the two can never disagree about where the data
lives or how it's embedded.

Every chromadb import stays in this file (and in chroma_config.py). If
chromadb leaks into domain/ or application/, the hexagon is broken.

Phase 5 note: this file gets a SPAN, not a decorator, unlike the
workflow-level "retrieve" span (TracedCorpusRetriever). Deliberate
difference: "retrieve" wraps ANY CorpusRetriever and knows nothing
vendor-specific; the span below is named and tagged with attributes
(`chroma.collection_name`) that only make sense for Chroma specifically
-- knowledge a generic decorator has no business having. It ends up
nested INSIDE "retrieve" in the trace tree purely because that's the
call order: TracedCorpusRetriever's span is already open by the time
this method runs, so OTel's context propagation nests them automatically
-- nothing here has to know that or arrange it.
"""

from opentelemetry import trace

from itw_me.adapters.outbound.chroma_config import (
    COLLECTION_NAME,
    get_chroma_client,
    get_collection,
)
from itw_me.domain.models import RetrievedChunk
from itw_me.domain.ports import CorpusRetriever

_tracer = trace.get_tracer("itw_me")


class ChromaCorpusRetriever(CorpusRetriever):
    def __init__(self) -> None:
        # Built once per adapter instance -- the composition root
        # constructs this adapter exactly once at startup, not per
        # request, so this is not a hot path.
        client = get_chroma_client()
        self._collection = get_collection(client)

    def retrieve(self, query: str, k: int = 4) -> list[RetrievedChunk]:
        # Attributes: collection name and k, never the query text --
        # same cardinality/PII discipline Phase 4's metric labels
        # already follow. A span attribute isn't stored as a Prometheus
        # time series, so the concern here isn't cardinality explosion;
        # it's simply that a visitor's question has no business sitting
        # in a tracing backend indefinitely either.
        with _tracer.start_as_current_span(
            "chroma.query",
            attributes={"chroma.collection_name": COLLECTION_NAME, "chroma.n_results": k},
        ):
            # query_texts takes a batch; we always send exactly one query,
            # so every result list below has exactly one element -- hence
            # indexing [0] throughout instead of a nested loop.
            results = self._collection.query(query_texts=[query], n_results=k)

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        return [
            RetrievedChunk(
                # chunk_id/source_file come from OUR metadata, not from
                # Chroma's internal id (which additionally embeds the
                # filename -- see corpus_chunking.py). Reading them back
                # from metadata means this adapter never has to parse or
                # assume anything about Chroma's id format.
                chunk_id=metadata["chunk_id"],
                source_file=metadata["source_file"],
                text=document,
                # Chroma reports a distance (lower = more similar); the
                # domain wants a score where higher = better. Translating
                # that convention at this boundary is the whole point of
                # an adapter: RetrievedChunk.score never means "Chroma
                # distance" to any caller. Note this is a simple, useful-
                # for-ranking transform, not a calibrated probability.
                score=1.0 - distance,
            )
            for document, metadata, distance in zip(documents, metadatas, distances)
        ]
