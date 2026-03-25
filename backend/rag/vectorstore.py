"""
AgriBot VectorStore — Gestion de ChromaDB pour le stockage vectoriel
Embeddings locaux via Sentence-Transformers (gratuit, pas de clé API).
Sans dépendance langchain — compatible Python 3.14.
"""
import chromadb
from chromadb.config import Settings

from config import CHROMA_PATH, COLLECTION_NAME, EMBEDDING_MODEL


# Cache global
_chroma_client = None
_collection = None
_embed_fn = None


def _get_embedding_function():
    """Retourne la fonction d'embedding (Sentence-Transformers, local)."""
    global _embed_fn
    if _embed_fn is None:
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
        _embed_fn = SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
    return _embed_fn


def get_collection():
    """Retourne la collection ChromaDB (crée si nécessaire)."""
    global _chroma_client, _collection

    if _collection is None:
        CHROMA_PATH.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_PATH),
            settings=Settings(anonymized_telemetry=False)
        )
        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=_get_embedding_function(),
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


def add_documents(chunks: list[dict]) -> int:
    """Ajoute des chunks à la collection ChromaDB."""
    collection = get_collection()

    ids = [chunk["metadata"]["chunk_id"] for chunk in chunks]
    documents = [chunk["content"] for chunk in chunks]
    metadatas = [
        {k: str(v) for k, v in chunk["metadata"].items()}
        for chunk in chunks
    ]

    # Upsert pour éviter les doublons
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )

    return len(ids)


def search_similar(query: str, top_k: int = 5) -> list[dict]:
    """Recherche sémantique dans ChromaDB."""
    collection = get_collection()

    if collection.count() == 0:
        return []

    results = collection.query(
        query_texts=[query],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    formatted = []
    for i in range(len(results["ids"][0])):
        formatted.append({
            "id": results["ids"][0][i],
            "content": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
            "score": 1.0 - results["distances"][0][i]
        })

    return formatted


def get_all_documents_text() -> list[str]:
    """Retourne tous les textes de la collection pour BM25."""
    collection = get_collection()
    if collection.count() == 0:
        return []

    results = collection.get(include=["documents"])
    return results["documents"]


def get_all_documents_info() -> list[dict]:
    """Retourne les métadonnées de tous les documents."""
    collection = get_collection()
    if collection.count() == 0:
        return []

    results = collection.get(include=["metadatas"])

    sources = {}
    for meta in results["metadatas"]:
        source = meta.get("source", "unknown")
        if source not in sources:
            sources[source] = {
                "filename": source,
                "chunks_count": 0,
                "type": meta.get("type", "unknown"),
                "ingested_at": meta.get("ingested_at", "")
            }
        sources[source]["chunks_count"] += 1

    return list(sources.values())


def delete_by_source(source_name: str) -> int:
    """Supprime tous les chunks d'un document source."""
    collection = get_collection()
    results = collection.get(
        where={"source": source_name},
        include=[]
    )
    if results["ids"]:
        collection.delete(ids=results["ids"])
        return len(results["ids"])
    return 0


def get_collection_stats() -> dict:
    """Retourne les statistiques de la collection."""
    collection = get_collection()
    docs_info = get_all_documents_info()
    return {
        "total_chunks": collection.count(),
        "documents_count": len(docs_info),
        "documents": docs_info
    }
