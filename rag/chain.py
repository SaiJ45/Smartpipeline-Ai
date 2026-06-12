import time

from langchain_groq import ChatGroq

from config.settings import get_settings
from rag.embedder import TextEmbedder
from rag.pinecone_client import PineconeManager


class RAGChain:
    """Question-answering chain backed by Pinecone retrieval and Groq."""

    def __init__(self) -> None:
        settings = get_settings()
        self.embedder = TextEmbedder()
        self.pinecone = PineconeManager()
        self.llm = ChatGroq(
            model_name="llama-3.3-70b-versatile",
            temperature=0.1,
            api_key=settings.GROQ_API_KEY,
        )

    def answer(self, question: str, dataset: str = "olist") -> dict:
        start = time.time()

        question_embedding = self.embedder.embed_single(question)
        results = self.pinecone.query(
            question_embedding,
            top_k=5,
            namespace=dataset,
        )

        if not results:
            return {
                "answer": "I need more data to answer this accurately",
                "sources": [],
                "query_time_ms": (time.time() - start) * 1000,
            }

        context = "\n".join(str(result.get("metadata", {})) for result in results)
        prompt = (
            "You are a senior business analyst. Answer using ONLY the provided context. "
            "Be specific with numbers, dates, locations. If context is insufficient say "
            "I need more data. "
            f"Context: {context} "
            f"Question: {question}"
        )

        response = self.llm.invoke(prompt)

        return {
            "answer": response.content,
            "sources": [result.get("metadata", {}) for result in results],
            "query_time_ms": (time.time() - start) * 1000,
        }
