"""TODO(antoine): ChromaDB implementation of CorpusRetriever.

Suggested approach:
- chromadb.PersistentClient(path="./chroma_data")
- One collection, e.g. "itw_me_corpus".
- retrieve(): embed the query (Chroma can do this with a default
  embedding function to start; swap for a better model later),
  query the collection, map results to RetrievedChunk.

Keep every chromadb import inside this file. If chromadb leaks into
domain/ or application/, the hexagon is broken.
"""

from itw_me.domain.models import RetrievedChunk
from itw_me.domain.ports import CorpusRetriever


class ChromaCorpusRetriever(CorpusRetriever):
    def retrieve(self, query: str, k: int = 4) -> list[RetrievedChunk]:
        raise NotImplementedError
