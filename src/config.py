import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-4o-mini"
)

KONG_AI_GATEWAY_URL = os.getenv(
    "KONG_AI_GATEWAY_URL",
    "http://127.0.0.1:8000/openai/v1/chat/completions"
)

LAKERA_API_KEY = os.getenv("LAKERA_API_KEY")

LAKERA_GUARD_URL = os.getenv(
    "LAKERA_GUARD_URL",
    "https://api.lakera.ai/v2/guard"
)

MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "http://127.0.0.1:9000"
)

VECTOR_DB_PATH = "vector_db"

DOCUMENTS_PATH = "data"