"""
AgriBot Configuration — Paramètres centralisés
"""
from pathlib import Path
from dotenv import load_dotenv
import os

# Charger le .env
load_dotenv(Path(__file__).parent / ".env")

# === Chemins ===
BASE_DIR = Path(__file__).parent
CHROMA_PATH = BASE_DIR / "chroma_db"
DOCS_PATH = BASE_DIR / "demo_docs"

# === LLM Provider ===
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")  # "groq", "gemini" ou "openai"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Modèles
GROQ_MODEL = "llama-3.3-70b-versatile"  # Ultra rapide sur Groq LPU
GEMINI_MODEL = "gemini-2.0-flash"
OPENAI_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Sentence-Transformers (local, gratuit)

# === RAG Parameters ===
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
RELEVANCE_THRESHOLD = 4
TOP_K_RESULTS = 5
BM25_WEIGHT = 0.4
SEMANTIC_WEIGHT = 0.6

# === API ===
API_HOST = "0.0.0.0"
API_PORT = 8000
CORS_ORIGINS = ["*"]

# === Collection ChromaDB ===
COLLECTION_NAME = "agribot_docs"
