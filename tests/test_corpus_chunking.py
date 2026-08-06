"""Unit tests for the pure chunking function used by scripts/ingest.py.

No chromadb import here on purpose: chunk_file() is plain string
processing, so it's tested the same way as any other pure function --
fast, no I/O, no network.
"""

from itw_me.adapters.outbound.corpus_chunking import chunk_file


def test_one_chunk_per_header():
    text = (
        "# Title\n"
        "\n"
        "Intro paragraph.\n"
        "\n"
        "## Section One\n"
        "\n"
        "Body one.\n"
        "\n"
        "## Section Two\n"
        "\n"
        "Body two.\n"
    )

    chunks = chunk_file("cv.md", text)

    assert [c["section"] for c in chunks] == ["Title", "Section One", "Section Two"]
    assert [c["text"] for c in chunks] == ["Intro paragraph.", "Body one.", "Body two."]


def test_ids_are_stable_and_source_file_prefixed():
    text = "## Education\n\nSome details."

    chunks = chunk_file("cv.md", text)

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk["chunk_id"] == "education#0"
    assert chunk["id"] == "cv.md#education#0"
    assert chunk["source_file"] == "cv.md"

    # Re-chunking identical input must produce identical ids -- this is
    # what makes scripts/ingest.py's collection.upsert idempotent.
    assert chunk_file("cv.md", text) == chunks


def test_headers_with_no_body_are_skipped():
    text = "## Empty Container\n## Actual Content\n\nHas text.\n"

    chunks = chunk_file("cv.md", text)

    assert len(chunks) == 1
    assert chunks[0]["section"] == "Actual Content"


def test_slugify_handles_punctuation_and_case():
    text = "## 2012–2016 – PhD Candidate & Teaching Assistant\n\nBody.\n"

    chunks = chunk_file("cv.md", text)

    assert chunks[0]["chunk_id"] == "2012-2016-phd-candidate-teaching-assistant#0"


def test_oversized_section_splits_into_multiple_chunks():
    # Two paragraphs, each ~40 "tokens" (160 chars / 4) under the heuristic.
    # With max_tokens=50 they must land in separate pieces.
    paragraph_a = "word " * 160
    paragraph_b = "term " * 160
    text = f"## Long Section\n\n{paragraph_a.strip()}\n\n{paragraph_b.strip()}\n"

    chunks = chunk_file("cv.md", text, max_tokens=50)

    assert len(chunks) == 2
    assert [c["chunk_id"] for c in chunks] == ["long-section#0", "long-section#1"]
    assert chunks[0]["text"] == paragraph_a.strip()
    assert chunks[1]["text"] == paragraph_b.strip()


def test_multiple_files_do_not_collide_on_id():
    text = "## Education\n\nSame header text, different file."

    cv_chunks = chunk_file("cv.md", text)
    bio_chunks = chunk_file("bio.md", text)

    assert cv_chunks[0]["id"] != bio_chunks[0]["id"]
    assert cv_chunks[0]["chunk_id"] == bio_chunks[0]["chunk_id"]
