"""
AgriBot API — FastAPI Backend
Points d'entrée REST pour le chatbot RAG Limagrain.
"""
import os
import shutil
import uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import API_HOST, API_PORT, CORS_ORIGINS, LLM_PROVIDER, GEMINI_MODEL, OPENAI_MODEL, DOCS_PATH
from models import ChatRequest, ChatResponse, UploadResponse, DocumentInfo, SystemStatus
from rag.ingestion import ingest_file, ingest_directory
from rag.vectorstore import add_documents, get_collection_stats, delete_by_source
from rag.retriever import refresh_bm25
from agents.orchestrator import process_message


# === App ===
app = FastAPI(
    title="🌾 AgriBot API",
    description="Assistant IA RAG interne pour Limagrain",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chemins
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


# === Événements ===
@app.on_event("startup")
async def startup():
    """Au démarrage, indexer les documents de démo s'ils existent."""
    print("🌾 AgriBot démarrage...")
    if DOCS_PATH.exists() and any(DOCS_PATH.iterdir()):
        print(f"📂 Indexation des documents de démo depuis {DOCS_PATH}...")
        try:
            chunks = ingest_directory(str(DOCS_PATH))
            if chunks:
                count = add_documents(chunks)
                refresh_bm25()
                print(f"✅ {count} chunks indexés depuis les documents de démo")
        except Exception as e:
            print(f"⚠️ Erreur indexation démo: {e}")
    print("🚀 AgriBot prêt !")


# === Frontend Routes ===
@app.get("/")
async def serve_index():
    """Serve the frontend index.html"""
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/css/{file_path:path}")
async def serve_css(file_path: str):
    """Serve CSS files"""
    full_path = FRONTEND_DIR / "css" / file_path
    if full_path.exists():
        return FileResponse(str(full_path), media_type="text/css")
    raise HTTPException(status_code=404)


@app.get("/js/{file_path:path}")
async def serve_js(file_path: str):
    """Serve JS files"""
    full_path = FRONTEND_DIR / "js" / file_path
    if full_path.exists():
        return FileResponse(str(full_path), media_type="application/javascript")
    raise HTTPException(status_code=404)


# === API Endpoints ===
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Endpoint principal de chat. Envoie une question, reçoit une réponse RAG."""
    try:
        response = process_message(request.message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du traitement: {str(e)}")


@app.post("/api/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload et indexe un document (PDF, DOCX, MD, TXT)."""
    allowed_extensions = {".pdf", ".docx", ".md", ".txt"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté: {ext}. Formats acceptés: {', '.join(allowed_extensions)}"
        )

    file_path = UPLOAD_DIR / file.filename
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        chunks = ingest_file(str(file_path))
        count = add_documents(chunks)
        refresh_bm25()

        return UploadResponse(
            filename=file.filename,
            chunks_created=count,
            status="success",
            message=f"✅ Document '{file.filename}' indexé avec succès ({count} chunks créés)"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur d'indexation: {str(e)}")
    finally:
        if file_path.exists():
            os.remove(file_path)


@app.get("/api/documents")
async def list_documents():
    """Liste tous les documents indexés."""
    stats = get_collection_stats()
    return {
        "documents": stats["documents"],
        "total_chunks": stats["total_chunks"],
        "documents_count": stats["documents_count"]
    }


@app.delete("/api/documents/{source_name}")
async def delete_document(source_name: str):
    """Supprime un document de l'index."""
    deleted = delete_by_source(source_name)
    if deleted == 0:
        raise HTTPException(status_code=404, detail=f"Document '{source_name}' non trouvé")

    refresh_bm25()
    return {
        "message": f"Document '{source_name}' supprimé ({deleted} chunks)",
        "chunks_deleted": deleted
    }


@app.get("/api/status", response_model=SystemStatus)
async def system_status():
    """Retourne le statut du système."""
    stats = get_collection_stats()
    model = GEMINI_MODEL if LLM_PROVIDER == "gemini" else OPENAI_MODEL
    return SystemStatus(
        status="online",
        documents_count=stats["documents_count"],
        total_chunks=stats["total_chunks"],
        llm_provider=LLM_PROVIDER,
        model=model,
        vector_store_ready=True
    )


# === Lancement ===
if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("🌾  AgriBot — Assistant IA RAG Limagrain")
    print(f"🤖  LLM: {LLM_PROVIDER.upper()}")
    print(f"🌐  http://localhost:{API_PORT}")
    print(f"📖  http://localhost:{API_PORT}/docs")
    print("=" * 50)
    uvicorn.run(app, host=API_HOST, port=API_PORT)
