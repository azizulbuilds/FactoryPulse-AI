from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

if __package__:
    from .document_loader import build_knowledge_chunks
else:
    from document_loader import build_knowledge_chunks


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def retrieve_documents(
    query: str,
    top_k: int = 3,
) -> list[dict]:
    """
    Retrieve the most relevant maintenance document chunks
    using TF-IDF and cosine similarity.
    """

    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    # Load the knowledge base.
    chunks = build_knowledge_chunks()

    if not chunks:
        return []

    documents = [chunk["content"] for chunk in chunks]

    # Convert text into TF-IDF feature vectors.
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
    )

    document_vectors = vectorizer.fit_transform(documents)

    query_vector = vectorizer.transform([query])

    # Calculate query-to-document similarity.
    similarity_scores = cosine_similarity(
        query_vector,
        document_vectors,
    ).flatten()

    # Rank chunks from most to least relevant.
    ranked_indices = similarity_scores.argsort()[::-1]

    results = []

    for index in ranked_indices[:top_k]:
        score = float(similarity_scores[index])

        # Ignore chunks with no matching vocabulary.
        if score <= 0:
            continue

        chunk = chunks[index]

        results.append(
            {
                "content": chunk["content"],
                "source": chunk["source"],
                "chunk_index": chunk["chunk_index"],
                "relevance_score": round(score, 4),
            }
        )

    return results


if __name__ == "__main__":
    question = (
        "What should be investigated when "
        "machine temperature becomes abnormal?"
    )

    results = retrieve_documents(question, top_k=3)

    print("=" * 60)
    print("FACTORYPULSE AI — KNOWLEDGE RETRIEVAL")
    print("=" * 60)

    print(f"\nQuestion: {question}")
    print(f"Relevant chunks found: {len(results)}")

    for rank, result in enumerate(results, start=1):
        print(f"\n{'-' * 60}")
        print(f"Result {rank}")
        print(f"Source: {result['source']}")
        print(f"Chunk index: {result['chunk_index']}")
        print(f"Relevance score: {result['relevance_score']}")
        print("\nContent:")
        print(result["content"])

    print(f"\n{'=' * 60}")
    print("RETRIEVAL COMPLETE")