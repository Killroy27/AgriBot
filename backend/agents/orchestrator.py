"""
AgriBot Agent Orchestrator — Routage intelligent des requêtes
Décide si la question nécessite RAG, réponse directe, ou clarification.
"""
from rag.chain import query_rag
from rag.vectorstore import get_collection_stats
from models import ChatResponse


# Patterns pour détection de type de requête
GREETING_PATTERNS = [
    "bonjour", "salut", "hello", "hi", "hey", "bonsoir",
    "coucou", "yo", "bonne journée"
]

HELP_PATTERNS = [
    "aide", "help", "comment ça marche", "que peux-tu faire",
    "fonctionnalités", "capabilities", "quoi faire"
]

STATUS_PATTERNS = [
    "status", "statut", "état", "combien de documents",
    "stats", "statistiques"
]


def classify_query(message: str) -> str:
    """Classifie le type de requête."""
    msg_lower = message.lower().strip()

    if any(p in msg_lower for p in GREETING_PATTERNS) and len(msg_lower.split()) <= 3:
        return "greeting"
    if any(p in msg_lower for p in HELP_PATTERNS):
        return "help"
    if any(p in msg_lower for p in STATUS_PATTERNS):
        return "status"
    return "rag"


def handle_greeting() -> ChatResponse:
    return ChatResponse(
        answer="""Bonjour ! 👋 Je suis **AgriBot** 🌾, votre assistant IA interne Limagrain.

Je peux vous aider en répondant à vos questions à partir de la documentation interne de l'entreprise. 

Posez-moi une question sur :
- 📋 Les procédures et processus internes
- 📊 Les données métier et rapports
- 🌱 Les études et publications agronomiques
- 🏢 L'organisation et la stratégie Limagrain

Comment puis-je vous aider aujourd'hui ?""",
        sources=[],
        confidence=1.0,
        processing_time=0.0,
        model_used="orchestrator"
    )


def handle_help() -> ChatResponse:
    return ChatResponse(
        answer="""🤖 **Guide d'utilisation AgriBot**

**Ce que je peux faire :**
- 🔍 **Rechercher** dans la base documentaire interne
- 📝 **Résumer** des documents complexes
- ❓ **Répondre** à vos questions métier
- 📊 **Analyser** des données issues des rapports

**Comment m'utiliser :**
1. Tapez votre question en langage naturel
2. Je cherche dans les documents indexés
3. Je vous réponds avec les sources citées

**Conseils pour de meilleurs résultats :**
- Soyez précis dans vos questions
- Mentionnez le contexte si pertinent (département, sujet, période)
- N'hésitez pas à reformuler si la réponse n'est pas satisfaisante

**Besoin d'indexer de nouveaux documents ?**
Utilisez le panneau d'upload pour ajouter des PDF, DOCX ou fichiers texte.""",
        sources=[],
        confidence=1.0,
        processing_time=0.0,
        model_used="orchestrator"
    )


def handle_status() -> ChatResponse:
    stats = get_collection_stats()
    return ChatResponse(
        answer=f"""📊 **Statut du système AgriBot**

- 📄 **Documents indexés** : {stats['documents_count']}
- 🧩 **Chunks totaux** : {stats['total_chunks']}
- ✅ **Statut** : Opérationnel

**Documents en base :**
""" + "\n".join(
            [f"  - `{d['filename']}` ({d['chunks_count']} chunks)"
             for d in stats.get('documents', [])]
        ) if stats['documents'] else "  Aucun document indexé.",
        sources=[],
        confidence=1.0,
        processing_time=0.0,
        model_used="orchestrator"
    )


def process_message(message: str) -> ChatResponse:
    """
    Point d'entrée principal de l'agent.
    Route la requête vers le bon handler.
    """
    query_type = classify_query(message)

    if query_type == "greeting":
        return handle_greeting()
    elif query_type == "help":
        return handle_help()
    elif query_type == "status":
        return handle_status()
    else:
        # RAG pipeline
        return query_rag(message)
