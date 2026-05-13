import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "pmify-project-rag")

SOURCE_API_BASE_URL = os.getenv(
    "SOURCE_API_BASE_URL",
    "https://accustomed-maryalice-bubbleless.ngrok-free.dev/api",
).rstrip("/")

BACKEND_SERVICE_HEADER = os.getenv("BACKEND_SERVICE_HEADER", "")

GLOBAL_PROJECTS_PATH = os.getenv(
    "GLOBAL_PROJECTS_PATH",
    "/project/all/with-raidd/chatbot",
)

SINGLE_PROJECT_PATH = os.getenv(
    "SINGLE_PROJECT_PATH",
    "/project/with-raidd/chatbot/{id}",
)

SOURCE_API_URL = os.getenv("SOURCE_API_URL")

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4.1-mini"
EMBEDDING_DIMENSION = 1536