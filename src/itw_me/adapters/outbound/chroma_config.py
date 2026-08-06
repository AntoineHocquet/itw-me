"""Chroma configuration shared by scripts/ingest.py and ChromaCorpusRetriever.

Why this module exists: the ingest script WRITES to a Chroma collection and
the retriever adapter READS from it. If each picked its own collection name,
persistence path, or embedding function, they could silently drift apart
(ingest writing to one place, the retriever reading from another) with no
error -- just empty or wrong search results. Centralizing the three things
that must match in one module makes that drift impossible: both sides import
from here instead of hardcoding their own copy.

Embedding function: Chroma's local, built-in DefaultEmbeddingFunction (an
ONNX-exported sentence-transformer, all-MiniLM-L6-v2). It runs on CPU, needs
no API key, and makes no network call per query -- consistent with the
offline-first approach already used for Phase 1. It downloads its ~80MB
model file on first use only (cached under ~/.cache/chroma/ afterwards),
which is why tests must never exercise this function directly (see the
mocking approach in the ChromaCorpusRetriever and ingest tests).
"""

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions

COLLECTION_NAME = "itw_me_corpus"

# Where the PersistentClient stores its on-disk index. Relative to the
# current working directory, matching the `python scripts/ingest.py` /
# `uvicorn ...` invocations documented in the README (both expect to be
# run from the repo root).
PERSIST_DIR = "./chroma_data"


def get_embedding_function() -> embedding_functions.DefaultEmbeddingFunction:
    return embedding_functions.DefaultEmbeddingFunction()


def get_chroma_client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=PERSIST_DIR)


def get_collection(client: chromadb.ClientAPI) -> Collection:
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )
