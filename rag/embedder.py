import numpy as np
from sentence_transformers import SentenceTransformer


class TextEmbedder:
    """Generate text embeddings using BGE-small."""

    def __init__(self) -> None:
        self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        print("BGE-small model loaded")
        print(f"Embedding dimension: {self.model.get_embedding_dimension()}")

    def embed(self, texts: list) -> list:
        embeddings = []

        for start in range(0, len(texts), 64):
            batch = texts[start:start + 64]
            batch_embeddings = self.model.encode(
                batch,
                batch_size=64,
                show_progress_bar=False,
            )
            embeddings.extend(np.asarray(batch_embeddings).tolist())

        return embeddings

    def embed_single(self, text: str) -> list:
        embedding = self.model.encode(
            [text],
            batch_size=64,
            show_progress_bar=False,
        )
        return np.asarray(embedding)[0].tolist()
