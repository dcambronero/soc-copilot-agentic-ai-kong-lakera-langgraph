from pathlib import Path

from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from langchain_core.documents import Document

from src.vector_store import (
    build_vector_store,
    load_vector_store
)

from src.config import (
    DOCUMENTS_PATH
)


class RAGEngine:

    def load_documents(self):

        docs = []

        for file in Path(
            DOCUMENTS_PATH
        ).glob("*.txt"):

            content = file.read_text(
                encoding="utf-8"
            )

            docs.append(
                Document(
                    page_content=content,
                    metadata={
                        "source": file.name
                    }
                )
            )

        return docs

    def build(self):

        docs = self.load_documents()

        splitter = (
            RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=150
            )
        )

        chunks = splitter.split_documents(
            docs
        )

        build_vector_store(
            chunks
        )

        return len(chunks)

    def search(
        self,
        query
    ):

        db = load_vector_store()

        results = (
            db.similarity_search(
                query,
                k=3
            )
        )

        return results