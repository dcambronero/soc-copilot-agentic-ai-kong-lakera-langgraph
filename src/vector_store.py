from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from src.config import (
    OPENAI_API_KEY,
    VECTOR_DB_PATH
)


def build_vector_store(documents):

    embeddings = OpenAIEmbeddings(
        api_key=OPENAI_API_KEY
    )

    db = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=VECTOR_DB_PATH
    )

    return db


def load_vector_store():

    embeddings = OpenAIEmbeddings(
        api_key=OPENAI_API_KEY
    )

    return Chroma(
        persist_directory=VECTOR_DB_PATH,
        embedding_function=embeddings
    )