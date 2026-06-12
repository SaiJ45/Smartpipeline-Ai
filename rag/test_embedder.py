from rag.embedder import TextEmbedder

embedder = TextEmbedder()
test_texts = ["What is the best selling product?", "Which state had most delays?"]
embeddings = embedder.embed(test_texts)
print(f"Embeddings shape: {len(embeddings)} x {len(embeddings[0])}")
# Should print: 2 x 384