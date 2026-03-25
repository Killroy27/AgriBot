"""
AgriBot Models — Pydantic schemas pour l'API
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Question de l'utilisateur")
    conversation_id: Optional[str] = Field(None, description="ID de conversation pour le contexte")


class Source(BaseModel):
    document: str
    page: Optional[int] = None
    chunk_id: str
    relevance_score: float
    excerpt: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source] = []
    confidence: float = Field(0.0, ge=0, le=1)
    processing_time: float = 0.0
    model_used: str = ""


class UploadResponse(BaseModel):
    filename: str
    chunks_created: int
    status: str = "success"
    message: str = ""


class DocumentInfo(BaseModel):
    id: str
    filename: str
    chunks_count: int
    upload_date: str
    size_bytes: int = 0


class SystemStatus(BaseModel):
    status: str = "online"
    documents_count: int = 0
    total_chunks: int = 0
    llm_provider: str = ""
    model: str = ""
    vector_store_ready: bool = False
