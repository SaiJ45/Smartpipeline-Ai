import time

from pinecone import Pinecone, ServerlessSpec

from config.settings import get_settings


class PineconeManager:
    """Manage Pinecone index operations for RAG chunks."""

    def __init__(self) -> None:
        settings = get_settings()
        api_key = settings.PINECONE_API_KEY
        index_name = settings.PINECONE_INDEX

        pc = Pinecone(api_key=api_key)
        existing_indexes = [index["name"] for index in pc.list_indexes()]

        if index_name not in existing_indexes:
            pc.create_index(
                name=index_name,
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1",
                ),
            )

            while not pc.describe_index(index_name).status["ready"]:
                time.sleep(1)

        self.index = pc.Index(index_name)

    def upsert_chunks(
        self,
        chunks: list,
        embeddings: list,
        namespace: str = "olist",
    ) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")

        vectors = [
            (
                chunk["order_id"],
                embedding,
                chunk["metadata"],
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]

        total_upserted = 0
        for start in range(0, len(vectors), 100):
            batch = vectors[start:start + 100]
            self.index.upsert(vectors=batch, namespace=namespace)
            total_upserted += len(batch)

            if total_upserted % 1000 == 0:
                print(f"Upserted {total_upserted} vectors...")

        return total_upserted

    def query(
        self,
        embedding: list,
        top_k: int = 5,
        namespace: str = "olist",
    ) -> list:
        result = self.index.query(
            vector=embedding,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True,
        )

        return [
            {
                "id": match["id"],
                "score": match["score"],
                "metadata": match.get("metadata", {}),
            }
            for match in result.get("matches", [])
        ]

    def get_stats(self) -> dict:
        return self.index.describe_index_stats().to_dict()
