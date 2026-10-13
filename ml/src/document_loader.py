from pathlib import Path
import re
from typing import TypedDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]

KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"

CHUNK_SIZE = 800
CHUNK_OVERLAP = 120


class DocumentChunk(TypedDict):
    content: str
    source: str
    chunk_index: int


def load_markdown_documents() -> list[dict[str, str]]:
    """Load Markdown documents from the knowledge base."""

    if not KNOWLEDGE_BASE_DIR.exists():
        raise FileNotFoundError(
            f"Knowledge base not found: {KNOWLEDGE_BASE_DIR}"
        )

    documents = []

    for path in sorted(KNOWLEDGE_BASE_DIR.rglob("*.md")):
        content = path.read_text(
            encoding="utf-8"
        ).strip()

        if not content:
            continue

        documents.append(
            {
                "source": str(path.relative_to(PROJECT_ROOT)),
                "content": content,
            }
        )

    return documents


def split_long_block(
    text: str,
    chunk_size: int,
) -> list[str]:
    """
    Split an unusually long paragraph into smaller pieces.

    Prefer sentence boundaries and fall back to word
    boundaries when an individual sentence is too long.
    """

    if len(text) <= chunk_size:
        return [text]

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text.strip(),
    )

    pieces = []
    current = ""

    for sentence in sentences:
        if len(sentence) > chunk_size:
            if current:
                pieces.append(current.strip())
                current = ""

            # Fall back to word boundaries for long sentences.
            words = sentence.split()
            word_chunk = ""

            for word in words:
                candidate = (
                    f"{word_chunk} {word}".strip()
                )

                if len(candidate) > chunk_size:
                    if word_chunk:
                        pieces.append(word_chunk)

                    word_chunk = word
                else:
                    word_chunk = candidate

            if word_chunk:
                current = word_chunk

            continue

        candidate = (
            f"{current} {sentence}".strip()
        )

        if len(candidate) > chunk_size:
            if current:
                pieces.append(current.strip())

            current = sentence
        else:
            current = candidate

    if current:
        pieces.append(current.strip())

    return pieces


def split_into_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """
    Split Markdown content using paragraph-aware boundaries.

    Consecutive chunks can overlap by a complete paragraph
    when that paragraph fits within the size constraints.
    """

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be positive."
        )

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be non-negative and smaller than chunk_size."
        )

    text = text.strip()

    if not text:
        return []

    # Preserve paragraph and Markdown section boundaries.
    blocks = re.split(
        r"\n\s*\n",
        text,
    )

    blocks = [
        block.strip()
        for block in blocks
        if block.strip()
    ]

    # Split only blocks that exceed the configured limit.
    paragraphs = []

    for block in blocks:
        paragraphs.extend(
            split_long_block(block, chunk_size)
        )

    chunks = []
    current_blocks = []

    for paragraph in paragraphs:
        candidate_blocks = current_blocks + [paragraph]
        candidate = "\n\n".join(candidate_blocks)

        if len(candidate) <= chunk_size:
            current_blocks.append(paragraph)
            continue

        # Save the completed chunk.
        if current_blocks:
            chunks.append(
                "\n\n".join(current_blocks).strip()
            )

        # Preserve the last complete paragraph as overlap
        # when it fits the constraints.
        overlap_blocks = []

        if current_blocks:
            previous_block = current_blocks[-1]

            if (
                len(previous_block) <= overlap
                and len(previous_block) <= chunk_size // 2
            ):
                overlap_blocks = [previous_block]

        next_blocks = overlap_blocks + [paragraph]

        next_chunk = "\n\n".join(next_blocks)

        # If overlap makes the new chunk too large,
        # start cleanly with the next paragraph.
        if len(next_chunk) > chunk_size:
            next_blocks = [paragraph]

        current_blocks = next_blocks

    if current_blocks:
        chunks.append(
            "\n\n".join(current_blocks).strip()
        )

    return chunks


def build_knowledge_chunks() -> list[DocumentChunk]:
    """Load documents and attach source metadata to every chunk."""

    documents = load_markdown_documents()

    all_chunks: list[DocumentChunk] = []

    for document in documents:
        chunks = split_into_chunks(
            document["content"]
        )

        for index, chunk in enumerate(chunks):
            all_chunks.append(
                {
                    "content": chunk,
                    "source": document["source"],
                    "chunk_index": index,
                }
            )

    return all_chunks


if __name__ == "__main__":
    documents = load_markdown_documents()
    chunks = build_knowledge_chunks()

    print("=" * 55)
    print("FACTORYPULSE AI — DOCUMENT LOADER")
    print("=" * 55)

    print(f"\nDocuments loaded: {len(documents)}")
    print(f"Chunks created: {len(chunks)}")

    print("\nSources:")

    for document in documents:
        print(f"- {document['source']}")

    if chunks:
        print("\nChunk details:")

        for chunk in chunks:
            print(
                f"Chunk {chunk['chunk_index']}: "
                f"{len(chunk['content'])} characters"
            )

        print("\nFirst chunk preview:")
        print(chunks[0]["content"][:300])

        print(
            f"\nFirst chunk source: "
            f"{chunks[0]['source']}"
        )

    print("\nDOCUMENT LOADING COMPLETE")