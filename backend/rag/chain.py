"""
AgriBot RAG Chain — Chaîne de génération augmentée par la recherche
Supporte Groq (ultra-rapide), Gemini et OpenAI.
Compatible Python 3.14.
"""
import time
from config import (
    LLM_PROVIDER, GROQ_API_KEY, GOOGLE_API_KEY, OPENAI_API_KEY,
    GROQ_MODEL, GEMINI_MODEL, OPENAI_MODEL
)
from rag.retriever import hybrid_search
from models import ChatResponse, Source


SYSTEM_PROMPT = """Tu es AgriBot 🌾, l'assistant IA interne de Limagrain, un groupe semencier et agroalimentaire mondial.

Tu réponds aux questions des collaborateurs en te basant EXCLUSIVEMENT sur les documents internes fournis comme contexte.

Règles :
1. Réponds en français, de manière claire et professionnelle.
2. Base tes réponses UNIQUEMENT sur le contexte fourni. Si l'information n'est pas disponible, dis-le clairement.
3. Cite les sources en mentionnant le document d'origine.
4. Structure tes réponses avec des puces ou des paragraphes clairs.
5. Si la question porte sur des données chiffrées, sois précis et mentionne les dates/périodes.
6. Adopte un ton professionnel mais accessible, fidèle aux valeurs Limagrain : Audace, Coopération, Progrès, Persévérance.

Si le contexte ne contient pas d'information pertinente, réponds :
"Je n'ai pas trouvé d'information sur ce sujet dans la base documentaire. Veuillez reformuler votre question ou contacter le service concerné."
"""


def call_groq(prompt: str) -> str:
    """Appelle Groq API (ultra-rapide, LPU inference)."""
    from groq import Groq

    client = Groq(api_key=GROQ_API_KEY)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=2048,
    )
    return response.choices[0].message.content


def call_gemini(prompt: str) -> str:
    """Appelle Google Gemini via le SDK officiel."""
    import google.generativeai as genai

    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=SYSTEM_PROMPT,
        generation_config=genai.GenerationConfig(
            temperature=0.3,
            max_output_tokens=2048,
        )
    )
    response = model.generate_content(prompt)
    return response.text


def call_llm(prompt: str) -> str:
    """Appelle le LLM configuré (Groq, Gemini ou OpenAI)."""
    if LLM_PROVIDER == "groq":
        return call_groq(prompt)
    elif LLM_PROVIDER == "gemini":
        return call_gemini(prompt)
    else:
        raise ValueError(f"LLM provider '{LLM_PROVIDER}' non supporté")


def format_context(results: list[dict]) -> str:
    """Formate les résultats de recherche en contexte pour le LLM."""
    if not results:
        return "Aucun document pertinent trouvé."

    context_parts = []
    for i, result in enumerate(results, 1):
        source = result.get("metadata", {}).get("source", "Document inconnu")
        page = result.get("metadata", {}).get("page", "")
        page_str = f" (page {page})" if page else ""
        context_parts.append(
            f"--- Document {i}: {source}{page_str} ---\n{result['content']}"
        )
    return "\n\n".join(context_parts)


def query_rag(question: str) -> ChatResponse:
    """
    Pipeline RAG complet :
    1. Recherche hybride (BM25 + sémantique)
    2. Construction du contexte
    3. Génération de la réponse via LLM
    """
    start_time = time.time()

    # 1. Recherche hybride
    results = hybrid_search(question)

    # 2. Construire le contexte
    context = format_context(results)

    # 3. Construire le prompt
    prompt = f"""Contexte documentaire :
{context}

Question du collaborateur : {question}

Réponds de manière détaillée en citant les sources."""

    # 4. Appeler le LLM
    answer = call_llm(prompt)

    # 5. Calculer la confiance
    avg_score = sum(r.get("score", 0) for r in results) / max(len(results), 1)
    confidence = min(avg_score * 2, 1.0) if results else 0.0

    # 6. Formater les sources
    sources = []
    for r in results:
        meta = r.get("metadata", {})
        page_val = meta.get("page", "")
        sources.append(Source(
            document=meta.get("source", "Unknown"),
            page=int(page_val) if page_val and str(page_val).isdigit() else None,
            chunk_id=r.get("id", ""),
            relevance_score=round(r.get("score", 0), 3),
            excerpt=r.get("content", "")[:200] + "..."
        ))

    elapsed = time.time() - start_time
    model_names = {"groq": GROQ_MODEL, "gemini": GEMINI_MODEL, "openai": OPENAI_MODEL}
    model_name = model_names.get(LLM_PROVIDER, LLM_PROVIDER)

    return ChatResponse(
        answer=answer,
        sources=sources,
        confidence=round(confidence, 2),
        processing_time=round(elapsed, 2),
        model_used=model_name
    )
