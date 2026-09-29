from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

_embedding_model = None


def get_embedding_model():
    global _embedding_model

    if _embedding_model is None:
        _embedding_model = SentenceTransformer(MODEL_NAME)

    return _embedding_model


def generate_embedding(text: str):
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    model = get_embedding_model()

    embedding = model.encode(
        text,
        convert_to_numpy=True
    )

    return embedding.tolist()