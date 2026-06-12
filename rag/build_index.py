import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.chunker import DataChunker
from rag.embedder import TextEmbedder
from rag.pinecone_client import PineconeManager

def build_index(sample_size=50000):
    print("="*50)
    print("Building Pinecone Index")
    print("="*50)

    # Step 1 - Build chunks
    print(f"\n1. Building {sample_size} chunks from database...")
    chunker = DataChunker()
    chunks = chunker.build_chunks(sample_size=sample_size)
    print(f"   Built {len(chunks)} chunks")

    # Step 2 - Embed chunks
    print(f"\n2. Embedding chunks with BGE-small...")
    embedder = TextEmbedder()
    texts = [c['text'] for c in chunks]

    # Process in batches to show progress
    all_embeddings = []
    batch_size = 500
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        embeddings = embedder.embed(batch)
        all_embeddings.extend(embeddings)
        print(f"   Embedded {min(i+batch_size, len(texts))}/{len(texts)}")

    print(f"   Total embeddings: {len(all_embeddings)}")

    # Step 3 - Upload to Pinecone
    print(f"\n3. Uploading to Pinecone...")
    manager = PineconeManager()
    total = manager.upsert_chunks(chunks, all_embeddings, namespace='olist')
    print(f"   Uploaded {total} vectors")

    # Step 4 - Verify
    print(f"\n4. Verifying index...")
    stats = manager.get_stats()
    print(f"   Index stats: {stats}")

    print("\n✅ Index built successfully!")

if __name__ == "__main__":
    build_index(sample_size=50000)