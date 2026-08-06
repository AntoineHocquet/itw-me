"""Ingestion flow (phase 2): reads corpus/*.md, chunks, embeds, upserts.

This script is deliberately thin: all the logic that's worth unit-testing
(chunking) lives in itw_me.adapters.outbound.corpus_chunking, and all the
Chroma configuration that must match ChromaCorpusRetriever lives in
itw_me.adapters.outbound.chroma_config. This file just wires the two
together and does the actual file-system / Chroma I/O.

Run with: python scripts/ingest.py
"""

from pathlib import Path

from itw_me.adapters.outbound.chroma_config import (
    COLLECTION_NAME,
    get_chroma_client,
    get_collection,
)
from itw_me.adapters.outbound.corpus_chunking import chunk_file

CORPUS_DIR = Path(__file__).resolve().parent.parent / "corpus"


def load_corpus_chunks(corpus_dir: Path) -> list[dict]:
    """Chunk every corpus/*.md file. Pure-ish (only reads from disk)."""
    chunks: list[dict] = []
    for path in sorted(corpus_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        chunks.extend(chunk_file(path.name, text))
    return chunks


def ingest(corpus_dir: Path = CORPUS_DIR) -> int:
    """Chunk the corpus and upsert every chunk into the Chroma collection.

    `upsert` (rather than `add`) with our stable, content-derived ids is
    what makes this idempotent: running the script twice on an unchanged
    corpus re-writes the same ids with the same content -- no duplicates.
    If a corpus file's text changes, the affected chunk ids get their
    content updated in place; ids for entries that disappeared entirely
    are simply never touched (acceptable for a small, hand-curated corpus
    like this one -- pruning stale ids is not implemented).
    """
    chunks = load_corpus_chunks(corpus_dir)
    if not chunks:
        print(f"No corpus/*.md chunks found under {corpus_dir}; nothing to ingest.")
        return 0

    collection = get_collection(get_chroma_client())
    collection.upsert(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[
            {
                "source_file": c["source_file"],
                "chunk_id": c["chunk_id"],
                "section": c["section"],
            }
            for c in chunks
        ],
    )
    print(f"Ingested {len(chunks)} chunk(s) into Chroma collection '{COLLECTION_NAME}'.")
    return len(chunks)


def main() -> None:
    ingest()


if __name__ == "__main__":
    main()
