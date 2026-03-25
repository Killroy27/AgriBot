"""
AgriBot Retriever — Recherche hybride BM25 + Sémantique
Utilise Reciprocal Rank Fusion pour combiner les scores.
"""
import re
from rank_bm25 import BM25Okapi

from config import TOP_K_RESULTS, BM25_WEIGHT, SEMANTIC_WEIGHT
from rag.vectorstore import search_similar, get_all_documents_text, get_collection


# Cache BM25
_bm25_index = None
_bm25_corpus = None


def _tokenize(text: str) -> list[str]:
    """Tokenisation simple pour BM25."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return [w for w in text.split() if len(w) > 2]


def _build_bm25_index():
    """Construit l'index BM25 à partir de tous les documents."""
    global _bm25_index, _bm25_corpus

    corpus = get_all_documents_text()
    if not corpus:
        _bm25_index = None
        _bm25_corpus = None
        return

    tokenized = [_tokenize(doc) for doc in corpus]
    _bm25_index = BM25Okapi(tokenized)
    _bm25_corpus = corpus


def refresh_bm25():
    """Force la reconstruction de l'index BM25 (après ingestion)."""
    global _bm25_index, _bm25_corpus
    _bm25_index = None
    _bm25_corpus = None
    _build_bm25_index()


def _bm25_search(query: str, top_k: int = 10) -> list[dict]:
    """Recherche BM25 (lexicale)."""
    global _bm25_index, _bm25_corpus

    if _bm25_index is None:
        _build_bm25_index()

    if _bm25_index is None or _bm25_corpus is None:
        return []

    tokenized_query = _tokenize(query)
    scores = _bm25_index.get_scores(tokenized_query)

    # Trier par score décroissant
    scored_docs = [(i, score) for i, score in enumerate(scores) if score > 0]
    scored_docs.sort(key=lambda x: x[1], reverse=True)

    results = []
    for idx, score in scored_docs[:top_k]:
        results.append({
            "content": _bm25_corpus[idx],
            "bm25_score": float(score),
            "index": idx
        })
    return results


def hybrid_search(query: str, top_k: int = None) -> list[dict]:
    """
    Recherche hybride : combine BM25 (lexical) + ChromaDB (sémantique)
    avec Reciprocal Rank Fusion (RRF).
    """
    if top_k is None:
        top_k = TOP_K_RESULTS

    # 1. Recherche sémantique
    semantic_results = search_similar(query, top_k=top_k * 2)

    # 2. Recherche BM25
    bm25_results = _bm25_search(query, top_k=top_k * 2)

    # 3. Reciprocal Rank Fusion
    k = 60  # constante RRF
    fusion_scores = {}

    # Scores sémantiques
    for rank, result in enumerate(semantic_results):
        doc_id = result["content"][:100]  # clé basée sur le contenu
        rrf_score = SEMANTIC_WEIGHT / (k + rank + 1)
        fusion_scores[doc_id] = fusion_scores.get(doc_id, 0) + rrf_score
        if doc_id not in fusion_scores or not isinstance(fusion_scores.get(f"{doc_id}_data"), dict):
            fusion_scores[f"{doc_id}_data"] = result

    # Scores BM25
    for rank, result in enumerate(bm25_results):
        doc_id = result["content"][:100]
        rrf_score = BM25_WEIGHT / (k + rank + 1)
        fusion_scores[doc_id] = fusion_scores.get(doc_id, 0) + rrf_score
        if f"{doc_id}_data" not in fusion_scores:
            fusion_scores[f"{doc_id}_data"] = {
                "content": result["content"],
                "metadata": {},
                "score": result["bm25_score"],
                "id": f"bm25_{result['index']}"
            }

    # Trier par score fusionné
    scored = []
    for key, value in fusion_scores.items():
        if key.endswith("_data"):
            continue
        data = fusion_scores.get(f"{key}_data", {})
        if data:
            scored.append({
                "content": data.get("content", ""),
                "metadata": data.get("metadata", {}),
                "score": value,
                "id": data.get("id", ""),
                "search_type": "hybrid"
            })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
