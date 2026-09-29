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
    Add or update a meeting knowledge embedding
    in the ChromaDB vector database.
    """

    try:
        collection.upsert(
            ids=[record_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[
                {
                    "meeting_id": meeting_id,
                    "content_type": content_type
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
    Hybrid meeting search.

    For multi-word queries:
    - First checks meaningful phrase matches.
    - Uses semantic similarity only as a fallback.

    For single-word queries:
    - Uses semantic similarity and keyword matching.
    """

    try:
        # ----------------------------------------------------
        # Get a large candidate set
        # ----------------------------------------------------

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(collection.count(), 50),
            include=[
                "documents",
                "metadatas",
                "distances"
            ]
        )

        # ----------------------------------------------------
        # Handle empty database
        # ----------------------------------------------------

        if (
            not results.get("documents")
            or not results["documents"][0]
        ):
            return {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]]
            }

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        query = query_text.lower().strip()

        # ----------------------------------------------------
        # Clean query words
        # ----------------------------------------------------

        query_words = [
            word.strip(".,!?;:")
            for word in query.split()
            if len(word.strip(".,!?;:")) >= 3
        ]

        # ----------------------------------------------------
        # Build meaningful phrases
        # ----------------------------------------------------

        phrases = []

        if len(query_words) >= 2:

            # Full query
            phrases.append(
                " ".join(query_words)
            )

            # Last two words
            phrases.append(
                " ".join(query_words[-2:])
            )

            # First two words
            phrases.append(
                " ".join(query_words[:2])
            )

        # Remove duplicate phrases
        phrases = list(dict.fromkeys(phrases))

        # ----------------------------------------------------
        # Store phrase matches separately
        # ----------------------------------------------------

        phrase_results = []

        semantic_results = []

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances
        ):

            document_lower = document.lower()

            # ------------------------------------------------
            # Check meaningful phrase match
            # ------------------------------------------------

            phrase_match = any(
                phrase in document_lower
                for phrase in phrases
            )

            if phrase_match:
                phrase_results.append(
                    (
                        document,
                        metadata,
                        distance
                    )
                )

            # ------------------------------------------------
            # Store strong semantic results
            # ------------------------------------------------

            if distance <= 0.80:
                semantic_results.append(
                    (
                        document,
                        metadata,
                        distance
                    )
                )

        # ----------------------------------------------------
        # For multi-word queries:
        # prefer actual phrase matches
        # ----------------------------------------------------

        if len(query_words) >= 2:

            selected_results = phrase_results

            # If there are no phrase matches,
            # use only very strong semantic matches.
            if not selected_results:
                selected_results = semantic_results

        else:

            # ------------------------------------------------
            # Single-word query
            # ------------------------------------------------

            selected_results = []

            for document, metadata, distance in zip(
                documents,
                metadatas,
                distances
            ):

                document_lower = document.lower()

                if (
                    query in document_lower
                    or distance <= 0.80
                ):
                    selected_results.append(
                        (
                            document,
                            metadata,
                            distance
                        )
                    )

        # ----------------------------------------------------
        # Limit final results
        # ----------------------------------------------------

        selected_results = selected_results[:top_k]

        # ----------------------------------------------------
        # Prepare response
        # ----------------------------------------------------

        filtered_documents = []
        filtered_metadatas = []
        filtered_distances = []

        for document, metadata, distance in selected_results:

            filtered_documents.append(
                document
            )

            filtered_metadatas.append(
                metadata
            )

            filtered_distances.append(
                distance
            )

        return {
            "documents": [filtered_documents],
            "metadatas": [filtered_metadatas],
            "distances": [filtered_distances]
        }

    except Exception as error:

        raise RuntimeError(
            f"Vector database search failed: {error}"
        ) from error