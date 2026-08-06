"""Markdown -> Chroma-ready chunk records, shared by ingest and its tests.

This is pure logic (no chromadb import, no I/O): it takes a markdown
string and returns plain dicts. It lives next to chroma_config.py because
the two output conventions it defines -- the local `chunk_id`
(f"{section-slug}#{i}") and the Chroma-internal `id`
(f"{source_file}#{chunk_id}") -- only make sense paired with how
ChromaCorpusRetriever reads that same data back out. Being a pure function
of a string, it's fully unit-testable without ever touching Chroma; see
tests/test_corpus_chunking.py.
"""

from __future__ import annotations

import re

# Matches a markdown ATX header line: 1-6 '#' then whitespace then title.
_HEADER_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")

# Chunks are split further only once a section's estimated token count
# exceeds this. Not a hard requirement anywhere downstream -- it just keeps
# any single embedding/context chunk from getting unwieldy.
DEFAULT_MAX_TOKENS = 500


def _estimate_tokens(text: str) -> int:
    """Rough, model-agnostic token estimate (~4 characters per token).

    This is only used to decide when a chunk is "too big" for embedding/
    context purposes -- never to bill or report usage (real usage numbers
    come from the LLM response, see OpenAIAnswerGenerator). A heuristic
    is actually preferable here: it behaves the same regardless of
    whether the corpus ends up embedded/answered by OpenAI or by a local
    Ollama model, instead of being tied to one vendor's tokenizer.
    """
    return max(1, len(text) // 4)


def _split_into_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown into (header_text, body) pairs at every ATX header.

    Every header line -- H1 through H6 -- starts a new section, however
    deep it is nested. That matches how corpus/*.md is actually written
    (one H1 title, then H2 per topic, H3 per entry): treating every level
    as a boundary gives one chunk per CV/bio entry, which is the
    granularity that's actually useful to retrieve.
    """
    sections: list[tuple[str, str]] = []
    header: str | None = None
    body_lines: list[str] = []

    for line in text.splitlines():
        match = _HEADER_RE.match(line)
        if match:
            if header is not None:
                sections.append((header, "\n".join(body_lines)))
            header = match.group(2)
            body_lines = []
        else:
            body_lines.append(line)

    if header is not None:
        sections.append((header, "\n".join(body_lines)))

    return sections


def _split_oversized(text: str, max_tokens: int) -> list[str]:
    """Greedily pack paragraphs into pieces under `max_tokens` each.

    Splitting on blank-line-separated paragraphs (rather than at an
    arbitrary character offset) avoids cutting a sentence, list item, or
    equation block in half. A single paragraph that alone exceeds
    max_tokens is kept whole rather than mangled -- better one oversized
    chunk than a broken one.
    """
    paragraphs = [p for p in re.split(r"\n\s*\n", text) if p.strip()]

    pieces: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for paragraph in paragraphs:
        paragraph_tokens = _estimate_tokens(paragraph)
        if current and current_tokens + paragraph_tokens > max_tokens:
            pieces.append("\n\n".join(current))
            current, current_tokens = [], 0
        current.append(paragraph)
        current_tokens += paragraph_tokens

    if current:
        pieces.append("\n\n".join(current))

    return pieces


def _slugify(header: str) -> str:
    """Turn a header like "2012-2016 - PhD Candidate" into an id-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", header.lower()).strip("-")
    return slug or "section"


def chunk_file(
    source_file: str, text: str, max_tokens: int = DEFAULT_MAX_TOKENS
) -> list[dict]:
    """Turn one corpus markdown file's contents into ingestable chunks.

    Returns a list of dicts, one per chunk, with keys:
    - id: globally-stable Chroma id, f"{source_file}#{chunk_id}". Re-running
      ingestion produces the exact same ids for unchanged content, so
      `collection.upsert` overwrites in place instead of duplicating.
    - source_file: the corpus filename (e.g. "cv.md").
    - chunk_id: local id within this file, f"{section-slug}#{i}". This is
      the value that ends up on RetrievedChunk.chunk_id / Citation.chunk_id
      -- deliberately WITHOUT the filename prefix, since source_file is
      already a separate field and callers compose "{source_file}#{chunk_id}"
      themselves (see api.py and OpenAIAnswerGenerator's prompt labels).
    - section: the original (unslugified) header text, for humans reading
      Chroma's metadata directly.
    - text: the chunk's text content.

    Sections with no body text (e.g. a header immediately followed by a
    subheader, with nothing in between) are skipped: there is nothing
    there to embed or retrieve.
    """
    records: list[dict] = []

    for header, body in _split_into_sections(text):
        body = body.strip("\n")
        if not body.strip():
            continue

        pieces = (
            [body]
            if _estimate_tokens(body) <= max_tokens
            else _split_oversized(body, max_tokens)
        )
        section_slug = _slugify(header)

        for i, piece in enumerate(pieces):
            chunk_id = f"{section_slug}#{i}"
            records.append(
                {
                    "id": f"{source_file}#{chunk_id}",
                    "source_file": source_file,
                    "chunk_id": chunk_id,
                    "section": header,
                    "text": piece.strip(),
                }
            )

    return records
