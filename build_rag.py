from src.rag_engine import RAGEngine

engine = RAGEngine()

count = engine.build()

print()

print(
    f"Embeddings creados: {count}"
)

print()