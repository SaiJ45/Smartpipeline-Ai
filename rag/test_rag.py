import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.chain import RAGChain

print("Initializing RAG chain...")
chain = RAGChain()

test_questions = [
    "Which state had the most orders?",
    "What was the most popular product category?",
    "Were there any orders with very negative reviews?"
]

for question in test_questions:
    print(f"\nQ: {question}")
    result = chain.answer(question)
    print(f"A: {result['answer']}")
    print(f"Sources: {len(result['sources'])} chunks retrieved")
    print(f"Time: {result['query_time_ms']:.0f}ms")