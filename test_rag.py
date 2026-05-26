from src.rag_engine import RAGEngine

engine = RAGEngine()

results = engine.search(
    "usuario hizo clic en enlace sospechoso de correo"
)

print("\nRESULTADOS RAG\n")

for index, result in enumerate(results, start=1):
    print(f"Resultado {index}")
    print(f"Fuente: {result.metadata.get('source')}")
    print(result.page_content[:500])
    print("-" * 80)