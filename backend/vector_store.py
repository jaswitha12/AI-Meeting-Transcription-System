
import chromadb
from pathlib import Path


# ============================================================
# VECTOR DATABASE CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
VECTOR_DB_PATH = BASE_DIR / "vector_database"

client = chromadb.PersistentClient(
    path=str(VECTOR_DB_PATH)
)

collection = client.get_or_create_collection(
    name="meeting_knowledge"
)


# ============================================================
# ADD / UPDATE EMBEDDING
# ============================================================

def add_embedding(
    record_id: str,
    text: str,
    embedding: list,
    meeting_id: int,
    content_type: str
):
    """
    Add or update meeting knowledge in ChromaDB.
    """

    try:
        if not record_id:
            raise ValueError("Record ID cannot be empty.")

        if not text or not text.strip():
            raise ValueError("Document text cannot be empty.")

        if not embedding:
            raise ValueError("Embedding cannot be empty.")

        collection.upsert(
            ids=[record_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[
                {
                    "meeting_id": int(meeting_id),
                    "content_type": str(content_type)
                }
            ]
        )

    except Exception as error:
        raise RuntimeError(
            f"Vector database insertion failed: {error}"
        ) from error


# ============================================================
# HYBRID SEARCH
# ============================================================

def search_embeddings(
    query_embedding: list,
    query_text: str,
    top_k: int = 5
):
    """
    Search meeting records using keyword matching
    and semantic similarity.

    Keyword matches receive higher ranking.
    Semantic similarity is used to find related information
    even when the exact query words are absent.

    Returns a ChromaDB-compatible result structure.
    """

    try:
        # ----------------------------------------------------
        # 1. Validate input
        # ----------------------------------------------------

        if not query_text or not query_text.strip():
            raise ValueError("Search query cannot be empty.")

        if not query_embedding:
            raise ValueError("Query embedding cannot be empty.")

        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer.")

        query = query_text.lower().strip()

        # ----------------------------------------------------
        # 2. Handle an empty vector database
        # ----------------------------------------------------

        collection_count = collection.count()

        if collection_count == 0:
            return {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]]
            }

        # ----------------------------------------------------
        # 3. Retrieve candidate records
        # ----------------------------------------------------

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(collection_count, 50),
            include=[
                "documents",
                "metadatas",
                "distances"
            ]
        )

        documents = results.get("documents", [[]])[0] or []
        metadatas = results.get("metadatas", [[]])[0] or []
        distances = results.get("distances", [[]])[0] or []

        if not documents:
            return {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]]
            }

        # ----------------------------------------------------
        # 4. Prepare meaningful query keywords
        # ----------------------------------------------------

        stop_words = {
            "what", "are", "the", "is", "in", "on", "of",
            "to", "a", "an", "and", "for", "from", "with",
            "were", "was", "discussed", "about", "please",
            "tell", "me", "show", "find", "which", "main",
            "topics", "meetings", "meeting", "give", "explain",
            "summarize", "summary", "made", "does", "did",
            "can", "could", "would", "should", "this", "that"
        }

        query_words = [
            word.strip(".,!?;:()'\"").lower()
            for word in query.split()
            if len(word.strip(".,!?;:()'\"")) >= 3
            and word.strip(".,!?;:()'\"").lower()
            not in stop_words
        ]

        # ----------------------------------------------------
        # 5. Rank documents using keyword and semantic scores
        # ----------------------------------------------------

        selected_results = []

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances
        ):
            if not document:
                continue

            document_lower = document.lower()
            metadata = metadata or {}

            # Count meaningful query words found in the document.
            matching_words = sum(
                1
                for word in query_words
                if word in document_lower
            )

            # Exact phrase match provides additional relevance.
            phrase_match = (
                len(query_words) > 1
                and " ".join(query_words) in document_lower
            )

            # Keep direct keyword matches or close semantic matches.
            if matching_words > 0 or distance <= 0.65:
                selected_results.append(
                    {
                        "document": document,
                        "metadata": metadata,
                        "distance": distance,
                        "matching_words": matching_words,
                        "phrase_match": phrase_match
                    }
                )

        # ----------------------------------------------------
        # 6. Sort by relevance
        # ----------------------------------------------------

        selected_results.sort(
            key=lambda item: (
                -int(item["phrase_match"]),
                -item["matching_words"],
                item["distance"]
            )
        )

        selected_results = selected_results[:top_k]

        # ----------------------------------------------------
        # 7. Prepare response
        # ----------------------------------------------------

        filtered_documents = [
            item["document"]
            for item in selected_results
        ]

        filtered_metadatas = [
            item["metadata"]
            for item in selected_results
        ]

        filtered_distances = [
            item["distance"]
            for item in selected_results
        ]

        return {
            "documents": [filtered_documents],
            "metadatas": [filtered_metadatas],
            "distances": [filtered_distances]
        }

    except Exception as error:
        raise RuntimeError(
            f"Vector database search failed: {error}"
        ) from error
