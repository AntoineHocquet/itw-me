"""TODO(antoine): ingestion flow (phase 2).

Reads corpus/*.md, chunks, embeds, writes to the Chroma collection.

Suggested steps:
1. Walk corpus/ for .md files.
2. Chunk by markdown headers first, then split anything > ~500 tokens.
   (Header-based chunking works well for a CV/bio: sections are
   already semantically coherent.)
3. Give each chunk a stable id: f"{filename}#{section}#{i}" so
   re-ingestion overwrites instead of duplicating.
4. collection.upsert(ids=..., documents=..., metadatas=...)

Run with: python scripts/ingest.py
"""

if __name__ == "__main__":
    raise NotImplementedError
