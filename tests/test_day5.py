from pathlib import Path
import sys
import types

from fastapi.testclient import TestClient
import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from api.main import app
from rag.chunker import DataChunker
from rag.embedder import TextEmbedder
import rag.embedder as embedder_module

class FakeSentenceTransformer:
    def __init__(self, model_name=None, *args, **kwargs):
        pass
    
    def encode(self, texts, batch_size=64, show_progress_bar=False, **kwargs):
        if isinstance(texts, str):
            return [[0.1] * 384]
        return [[0.1] * 384 for _ in texts]
    
    def get_embedding_dimension(self):
        return 384
    
    def get_sentence_embedding_dimension(self):
        return 384


def test_chunker_builds_chunks():
    chunks = DataChunker().build_chunks(sample_size=10)

    assert len(chunks) == 10
    assert all("order_id" in chunk for chunk in chunks)
    assert all("text" in chunk for chunk in chunks)
    assert all("metadata" in chunk for chunk in chunks)


def test_chunk_text_is_not_empty():
    chunks = DataChunker().build_chunks(sample_size=10)

    assert all(isinstance(chunk["text"], str) for chunk in chunks)
    assert all(chunk["text"].strip() for chunk in chunks)


def test_embedder_returns_correct_dimension(monkeypatch):
    monkeypatch.setattr(embedder_module, "SentenceTransformer", FakeSentenceTransformer)
    embedder = TextEmbedder()
    result = embedder.embed(["This is a test sentence."])

    assert len(result[0]) == 384


def test_embedder_batch(monkeypatch):
    monkeypatch.setattr(embedder_module, "SentenceTransformer", FakeSentenceTransformer)
    embedder = TextEmbedder()
    result = embedder.embed(
        [
            "First text",
            "Second text",
            "Third text",
            "Fourth text",
            "Fifth text",
        ]
    )

    assert len(result) == 5


def test_ask_endpoint_with_rag(monkeypatch):
    class FakeRAGChain:
        def answer(self, question: str, dataset: str = "olist"):
            return {
                "answer": "SP had the most orders in the indexed sample.",
                "sources": [{"state": "SP"}],
                "query_time_ms": 12.5,
            }

    fake_chain_module = types.SimpleNamespace(RAGChain=FakeRAGChain)
    monkeypatch.setitem(sys.modules, "rag.chain", fake_chain_module)

    client = TestClient(app)
    response = client.post("/ask", json={"question": "What state had most orders?"})
    response_json = response.json()

    assert response.status_code == 200
    assert "answer" in response_json
    assert response_json["answer"].strip() != ""
