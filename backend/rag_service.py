import os
import requests

from .embedding_service import generate_embedding
from .vector_store import search_embeddings


# ============================================================
# LLM CONFIGURATION
# ============================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL_NAME = os.getenv(
    "MEETING_LLM_MODEL",
    "qwen/qwen-2.5-7b-instruct"
)


# ============================================================
# RAG QUESTION ANSWERING
# ============================================================

def generate_grounded_answer(
    question: str,
    top_k: int = 3
) -> dict:
    """
    Answer a question using relevant meeting information
    retrieved from the vector database.

    The answer is grounded only in the retrieved
    meeting information.
    """

    # --------------------------------------------------------
    # Validate question
    # --------------------------------------------------------

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    question = question.strip()

    # --------------------------------------------------------
    # Step 1: Convert question into embedding
    # --------------------------------------------------------

    query_embedding = generate_embedding(question)

    # --------------------------------------------------------
    # Step 2: Retrieve relevant meeting information
    # --------------------------------------------------------

    search_result = search_embeddings(
        query_embedding,
        question,
        top_k
    )

    documents = search_result.get(
        "documents",
        [[]]
    )[0]

    metadatas = search_result.get(
        "metadatas",
        [[]]
    )[0]

    # --------------------------------------------------------
    # Handle empty search results
    # --------------------------------------------------------

    if not documents:
        return {
            "question": question,
            "answer": "No relevant meeting information was found.",
            "sources": []
        }

    # --------------------------------------------------------
    # Step 3: Build context
    # --------------------------------------------------------

    context_parts = []

    for index, document in enumerate(documents):

        metadata = {}

        if index < len(metadatas):
            metadata = metadatas[index] or {}

        meeting_id = metadata.get(
            "meeting_id",
            "Unknown"
        )

        content_type = metadata.get(
            "content_type",
            "Unknown"
        )

        context_parts.append(
            f"Meeting ID: {meeting_id}\n"
            f"Content Type: {content_type}\n"
            f"Information: {document}"
        )

    context = "\n\n".join(context_parts)

    # --------------------------------------------------------
    # Step 4: Create grounded LLM prompt
    # --------------------------------------------------------

    prompt = f"""
You are a meeting question-answering assistant.

Your task is to answer the user's question using ONLY
the retrieved meeting context provided below.

IMPORTANT:
The MEETING CONTEXT contains information retrieved from
the meeting database. Treat it as the authoritative source.

Rules:

1. Carefully read ALL retrieved meeting context.
2. If the context contains information that directly or
   clearly relates to the user's question, answer using
   that information.
3. Do NOT say that the information is unavailable if the
   context contains relevant information.
4. Do NOT invent information that is not present in the context.
5. Do NOT use outside knowledge.
6. Give a clear and concise answer.
7. Mention the relevant Meeting ID when available.
8. If multiple meetings contain relevant information,
   mention all relevant Meeting IDs.
9. Summarize the relevant information from the context
   instead of simply saying that it exists.
10. If the context genuinely does not contain an answer,
    say exactly:
    "The available meeting records do not contain this information."

MEETING CONTEXT:

{context}

USER QUESTION:

{question}

ANSWER:
"""

    # --------------------------------------------------------
    # Step 5: Check API key
    # --------------------------------------------------------

    if not OPENROUTER_API_KEY:
        return {
            "question": question,
            "answer": (
                "LLM service is not configured because "
                "the OpenRouter API key is missing."
            ),
            "sources": []
        }

    # --------------------------------------------------------
    # Step 6: Prepare OpenRouter request
    # --------------------------------------------------------

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You answer questions about meetings. "
                    "Use only the provided meeting context. "
                    "Never invent information."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.1
    }

    # --------------------------------------------------------
    # Step 7: Call LLM with error handling
    # --------------------------------------------------------

    try:

        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        answer = data["choices"][0]["message"]["content"]
                # ----------------------------------------------------
        # Fallback for incorrect "information unavailable"
        # responses from the LLM
        # ----------------------------------------------------

        unavailable_phrases = [
            "the available meeting records do not contain this information",
            "information is not available",
            "not contain this information"
        ]

        if any(
            phrase in answer.lower()
            for phrase in unavailable_phrases
        ):
            answer = (
                "According to Meeting "
                + str(metadatas[0].get("meeting_id", "Unknown"))
                + ": "
                + documents[0]
            )

    except requests.exceptions.Timeout:

        return {
            "question": question,
            "answer": (
                "The LLM service timed out. "
                "Please try again later."
            ),
            "sources": []
        }

    except requests.exceptions.RequestException as error:

        return {
            "question": question,
            "answer": (
                f"The LLM service is currently unavailable: {error}"
            ),
            "sources": []
        }

    except (KeyError, IndexError, TypeError, ValueError):

        return {
            "question": question,
            "answer": "The LLM returned an invalid response.",
            "sources": []
        }

    except Exception as error:

        return {
            "question": question,
            "answer": (
                f"An unexpected LLM error occurred: {error}"
            ),
            "sources": []
        }

    # --------------------------------------------------------
    # Step 8: Prepare source information
    # --------------------------------------------------------

    sources = []

    for index, document in enumerate(documents):

        meeting_id = "Unknown"

        if index < len(metadatas):

            metadata = metadatas[index] or {}

            meeting_id = metadata.get(
                "meeting_id",
                "Unknown"
            )

        sources.append(
            {
                "meeting_id": meeting_id,
                "content": document
            }
        )

    # --------------------------------------------------------
    # Step 9: Return final grounded answer
    # --------------------------------------------------------

    return {
        "question": question,
        "answer": answer.strip(),
        "sources": sources
    }