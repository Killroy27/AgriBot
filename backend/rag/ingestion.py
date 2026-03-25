"""
AgriBot Ingestion — Pipeline d'ingestion de documents PDF et DOCX
Chunking intelligent avec métadonnées enrichies.
Sans dépendance langchain — compatible Python 3.14.
"""
import os
import re
import hashlib
from pathlib import Path
from datetime import datetime

from config import CHUNK_SIZE, CHUNK_OVERLAP


def load_pdf(file_path: str) -> list[dict]:
    """Charge un fichier PDF et retourne des documents."""
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    documents = []
    filename = Path(file_path).name

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            documents.append({
                "content": text,
                "metadata": {
                    "source": filename,
                    "page": i + 1,
                    "total_pages": len(reader.pages),
                    "type": "pdf",
                    "ingested_at": datetime.now().isoformat()
                }
            })
    return documents


def load_docx(file_path: str) -> list[dict]:
    """Charge un fichier DOCX."""
    from docx import Document as DocxDocument

    doc = DocxDocument(file_path)
    filename = Path(file_path).name
    full_text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])

    if full_text.strip():
        return [{
            "content": full_text,
            "metadata": {
                "source": filename,
                "type": "docx",
                "ingested_at": datetime.now().isoformat()
            }
        }]
    return []


def load_markdown(file_path: str) -> list[dict]:
    """Charge un fichier Markdown."""
    filename = Path(file_path).name
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    if content.strip():
        return [{
            "content": content,
            "metadata": {
                "source": filename,
                "type": "markdown",
                "ingested_at": datetime.now().isoformat()
            }
        }]
    return []


def load_text(file_path: str) -> list[dict]:
    """Charge un fichier texte brut."""
    filename = Path(file_path).name
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    if content.strip():
        return [{
            "content": content,
            "metadata": {
                "source": filename,
                "type": "text",
                "ingested_at": datetime.now().isoformat()
            }
        }]
    return []


LOADERS = {
    ".pdf": load_pdf,
    ".docx": load_docx,
    ".md": load_markdown,
    ".txt": load_text,
}


def load_document(file_path: str) -> list[dict]:
    """Charge un document selon son extension."""
    ext = Path(file_path).suffix.lower()
    loader = LOADERS.get(ext)
    if not loader:
        raise ValueError(f"Format non supporté: {ext}. Formats acceptés: {list(LOADERS.keys())}")
    return loader(file_path)


def split_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Découpe un texte en chunks avec overlap.
    Utilise les séparateurs naturels (paragraphes, phrases, espaces).
    """
    separators = ["\n\n", "\n", ". ", " ", ""]

    def _split_recursive(text: str, seps: list[str]) -> list[str]:
        if len(text) <= chunk_size:
            return [text] if text.strip() else []

        sep = seps[0] if seps else ""
        remaining_seps = seps[1:] if len(seps) > 1 else [""]

        if sep:
            parts = text.split(sep)
        else:
            # Dernier recours : couper par caractères
            chunks = []
            for i in range(0, len(text), chunk_size - chunk_overlap):
                chunk = text[i:i + chunk_size]
                if chunk.strip():
                    chunks.append(chunk)
            return chunks

        chunks = []
        current = ""

        for part in parts:
            test = current + (sep if current else "") + part
            if len(test) <= chunk_size:
                current = test
            else:
                if current.strip():
                    chunks.append(current)
                if len(part) > chunk_size:
                    # Récursion avec le séparateur suivant
                    sub_chunks = _split_recursive(part, remaining_seps)
                    chunks.extend(sub_chunks)
                    current = ""
                else:
                    current = part

        if current.strip():
            chunks.append(current)

        # Ajouter l'overlap
        if chunk_overlap > 0 and len(chunks) > 1:
            overlapped = [chunks[0]]
            for i in range(1, len(chunks)):
                prev_end = chunks[i - 1][-chunk_overlap:] if len(chunks[i - 1]) >= chunk_overlap else chunks[i - 1]
                overlapped.append(prev_end + chunks[i])
            return overlapped

        return chunks

    return _split_recursive(text, separators)


def chunk_documents(documents: list[dict]) -> list[dict]:
    """Découpe les documents en chunks avec métadonnées enrichies."""
    chunks = []

    for doc in documents:
        text_chunks = split_text(doc["content"])

        for i, chunk_text in enumerate(text_chunks):
            content_hash = hashlib.md5(chunk_text.encode()).hexdigest()[:8]
            source = doc["metadata"].get("source", "unknown")
            chunk_id = f"{source}_{i}_{content_hash}"

            chunks.append({
                "content": chunk_text,
                "metadata": {
                    **doc["metadata"],
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "total_chunks": len(text_chunks)
                }
            })

    return chunks


def ingest_file(file_path: str) -> list[dict]:
    """Pipeline complet : charge + chunke un fichier."""
    documents = load_document(file_path)
    chunks = chunk_documents(documents)
    return chunks


def ingest_directory(dir_path: str) -> list[dict]:
    """Ingère tous les fichiers supportés d'un répertoire."""
    all_chunks = []
    dir_path = Path(dir_path)

    for ext in LOADERS:
        for file_path in dir_path.glob(f"*{ext}"):
            try:
                chunks = ingest_file(str(file_path))
                all_chunks.extend(chunks)
                print(f"  ✅ {file_path.name}: {len(chunks)} chunks")
            except Exception as e:
                print(f"  ❌ {file_path.name}: {e}")

    return all_chunks
