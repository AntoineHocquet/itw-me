"""Unit tests for ChromaCorpusRetriever's translation logic.

We patch chroma_config.get_chroma_client/get_collection rather than
touching a real Chroma collection: the real DefaultEmbeddingFunction
downloads an ~80MB model on first use, which would make this test
depend on network access (forbidden by the test rules in
docs/phase2_spec.md). What's actually worth testing here isn't Chroma
itself -- it's this adapter's translation from Chroma's result shape
into RetrievedChunk (metadata -> fields, distance -> score).
"""

from unittest.mock import MagicMock, patch

from itw_me.adapters.outbound.retriever_chroma import ChromaCorpusRetriever
from itw_me.domain.models import RetrievedChunk


def _build_retriever(query_result: dict) -> ChromaCorpusRetriever:
    fake_collection = MagicMock()
    fake_collection.query.return_value = query_result

    with (
        patch(
            "itw_me.adapters.outbound.retriever_chroma.get_chroma_client",
            return_value=MagicMock(),
        ),
        patch(
            "itw_me.adapters.outbound.retriever_chroma.get_collection",
            return_value=fake_collection,
        ),
    ):
        return ChromaCorpusRetriever()


def test_retrieve_maps_chroma_results_to_retrieved_chunks():
    query_result = {
        "documents": [["Antoine did a PhD on the LLG equation."]],
        "metadatas": [[{"source_file": "cv.md", "chunk_id": "education#1"}]],
        "distances": [[0.2]],
    }
    retriever = _build_retriever(query_result)

    chunks = retriever.retrieve("What did Antoine study?", k=4)

    assert chunks == [
        RetrievedChunk(
            chunk_id="education#1",
            source_file="cv.md",
            text="Antoine did a PhD on the LLG equation.",
            score=0.8,
        )
    ]


def test_retrieve_passes_query_and_k_through():
    fake_collection = MagicMock()
    fake_collection.query.return_value = {
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }

    with (
        patch(
            "itw_me.adapters.outbound.retriever_chroma.get_chroma_client",
            return_value=MagicMock(),
        ),
        patch(
            "itw_me.adapters.outbound.retriever_chroma.get_collection",
            return_value=fake_collection,
        ),
    ):
        retriever = ChromaCorpusRetriever()
        result = retriever.retrieve("some question", k=2)

    fake_collection.query.assert_called_once_with(
        query_texts=["some question"], n_results=2
    )
    assert result == []


def test_retrieve_opens_a_dependency_span_with_collection_name_and_k():
    """Phase 5: patching this module's own `_tracer` (a module-level
    OTel handle, not injected -- see this file's Phase 5 comment) is the
    same trick used for the chroma client/collection above, applied to
    the tracer instead. Real OTel objects aren't needed to prove this
    adapter names its span correctly and tags it with non-PII attributes.
    """
    fake_collection = MagicMock()
    fake_collection.query.return_value = {
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }
    fake_span_cm = MagicMock()
    fake_span_cm.__exit__.return_value = False

    with (
        patch(
            "itw_me.adapters.outbound.retriever_chroma.get_chroma_client",
            return_value=MagicMock(),
        ),
        patch(
            "itw_me.adapters.outbound.retriever_chroma.get_collection",
            return_value=fake_collection,
        ),
        patch("itw_me.adapters.outbound.retriever_chroma._tracer") as fake_tracer,
    ):
        fake_tracer.start_as_current_span.return_value = fake_span_cm
        retriever = ChromaCorpusRetriever()
        retriever.retrieve("some question", k=3)

    fake_tracer.start_as_current_span.assert_called_once_with(
        "chroma.query",
        attributes={"chroma.collection_name": "itw_me_corpus", "chroma.n_results": 3},
    )
