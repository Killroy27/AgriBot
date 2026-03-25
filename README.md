# 🌾 AgriBot — Assistant IA RAG pour Limagrain

**Assistant IA interne** utilisant la technologie RAG (Retrieval-Augmented Generation) pour répondre aux questions des collaborateurs Limagrain à partir de la documentation interne.

## ✨ Fonctionnalités

- 🤖 **Chat IA** — Posez vos questions en langage naturel
- 📄 **Upload de documents** — PDF, DOCX, Markdown, TXT
- 🔍 **Recherche hybride** — BM25 (lexical) + sémantique (embeddings)
- 📊 **Scoring de confiance** — Évaluation de la pertinence des réponses
- 📎 **Citations des sources** — Traçabilité complète des réponses
- 🌙 **Dark mode** — Interface adaptative
- 📱 **Responsive** — Fonctionne sur mobile et desktop

## 🏗️ Architecture

```
Frontend (HTML/CSS/JS)  →  FastAPI Backend  →  RAG Pipeline
                                              ├── ChromaDB (sémantique)
                                              ├── BM25 (lexical)
                                              └── Gemini LLM (génération)
```

## 🚀 Lancement rapide

### 1. Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### 2. Frontend
Ouvrir `frontend/index.html` dans votre navigateur.

### 3. Utilisation
- Le backend démarre sur `http://localhost:8000`
- Les documents de démo sont auto-indexés au démarrage
- Posez vos questions dans le chat !

## 🛠️ Stack technique

| Composant | Technologie |
|-----------|-------------|
| Backend | FastAPI (Python) |
| LLM | Google Gemini 2.0 Flash |
| Embeddings | Sentence-Transformers (local) |
| Vector Store | ChromaDB |
| Recherche | Hybrid (BM25 + Sémantique + RRF) |
| Frontend | HTML5 / CSS3 / Vanilla JS |

## 📁 Structure

```
sfzo/
├── backend/
│   ├── app.py              # API FastAPI
│   ├── config.py            # Configuration
│   ├── models.py            # Pydantic models
│   ├── rag/
│   │   ├── ingestion.py     # Pipeline d'ingestion
│   │   ├── vectorstore.py   # ChromaDB
│   │   ├── retriever.py     # Recherche hybride
│   │   └── chain.py         # RAG chain
│   ├── agents/
│   │   └── orchestrator.py  # Routage intelligent
│   └── demo_docs/           # Documents de démo
├── frontend/
│   ├── index.html
│   ├── css/styles.css
│   └── js/
│       ├── app.js
│       ├── chat.js
│       ├── upload.js
│       └── api.js
└── README.md
```

## 👤 Auteur

Projet réalisé dans le cadre d'une candidature alternance — **Assistant(e) Ingénieur en Data Science & AI** chez Limagrain.
