from pathlib import Path
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
    """Load Markdown files from the knowledge base."""

    if not KNOWLEDGE_BASE_DIR.exists():
        raise FileNotFoundError(
            f"Knowledge base not found: {KNOWLEDGE_BASE_DIR}"
        )

    documents = []

    for path in sorted(KNOWLEDGE_BASE_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8").strip()

        if not content:
            continue

        documents.append(
            {
                "source": str(path.relative_to(PROJECT_ROOT)),
                "content": content,
            }
        )

    return documents


def split_into_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping character-based chunks."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be non-negative and smaller than chunk_size."
        )

    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Prefer splitting at a nearby word boundary.
        if end < len(text):
            boundary = text.rfind(" ", start, end)

            if boundary > start:
                end = boundary

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        # Advance while retaining the requested overlap.
        start = max(start + 1, end - overlap)

    return chunks


def build_knowledge_chunks() -> list[DocumentChunk]:
    """Load documents and attach source metadata to each chunk."""

    documents = load_markdown_documents()
    all_chunks: list[DocumentChunk] = []

    for document in documents:
        chunks = split_into_chunks(document["content"])

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
        print("\nFirst chunk preview:")
        print(chunks[0]["content"][:300])

        print(f"\nFirst chunk source: {chunks[0]['source']}")

    print("\nDOCUMENT LOADING COMPLETE")