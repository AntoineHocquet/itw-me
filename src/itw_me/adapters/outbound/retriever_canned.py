"""Phase 1 stand-in for CorpusRetriever: no corpus, no vector store yet.

This is a legitimate adapter, not test scaffolding: the composition
root (infrastructure/container.py) wires it in by default so the API
runs end to end -- HTTP in, domain call, HTTP out -- before ChromaDB
or an ingestion/embedding pipeline exist anywhere in the stack. It
implements the CorpusRetriever port exactly like ChromaCorpusRetriever
will in phase 2; only the technology behind the port changes.
"""

from itw_me.domain.models import RetrievedChunk
from itw_me.domain.ports import CorpusRetriever


class CannedCorpusRetriever(CorpusRetriever):
    """Always returns no context.

    Pairs with CannedAnswerGenerator, which does not need retrieved
    chunks to produce its placeholder answer. Once the corpus is
    ingested into Chroma (phase 2), swap this for ChromaCorpusRetriever
    via the ITW_ME_FAKE_LLM switch in the container -- the application
    layer and the port stay exactly the same.
    """

    def retrieve(self, query: str, k: int = 4) -> list[RetrievedChunk]:
        return []
