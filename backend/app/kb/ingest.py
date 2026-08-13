"""
Loads all markdown files in app/kb/docs/ into a local FAISS index for semantic
search. Run with: python -m app.kb.ingest

Uses sentence-transformers (all-MiniLM-L6-v2) for embeddings — runs locally, no
API key needed. FAISS is used instead of ChromaDB specifically because
ChromaDB's dependency chain pulls in grpc/opentelemetry, whose native DLL gets
blocked by Windows Smart App Control on some machines. FAISS has no such
dependency and is explicitly listed as an approved vector DB option in the
brief's recommended tech stack.
"""
import os
import glob
import json
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

KB_DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
INDEX_DIR = os.path.join(os.path.dirname(__file__), "faiss_store")
INDEX_PATH = os.path.join(INDEX_DIR, "index.faiss")
METADATA_PATH = os.path.join(INDEX_DIR, "metadata.pkl")

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def chunk_text(text: str, chunk_size: int = 500) -> list[str]:
    """Simple paragraph-aware chunking — splits on blank lines first, then
    merges to roughly chunk_size characters."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, current = [], ""
    for para in paragraphs:
        if len(current) + len(para) < chunk_size:
            current += ("\n\n" if current else "") + para
        else:
            if current:
                chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    return chunks


def ingest():
    os.makedirs(INDEX_DIR, exist_ok=True)

    doc_paths = sorted(glob.glob(os.path.join(KB_DOCS_DIR, "*.md")))
    if not doc_paths:
        print(f"No .md files found in {KB_DOCS_DIR} — add your KB docs there first.")
        return

    texts, metadatas = [], []
    for path in doc_paths:
        doc_id = os.path.splitext(os.path.basename(path))[0]
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        for chunk in chunk_text(content):
            texts.append(chunk)
            metadatas.append({"source": doc_id})

    print(f"Loading embedding model ({EMBEDDING_MODEL})...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"Embedding {len(texts)} chunks...")
    embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype="float32")

    # IndexFlatIP on normalized embeddings = cosine similarity search
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)
    with open(METADATA_PATH, "wb") as f:
        pickle.dump({"texts": texts, "metadatas": metadatas}, f)

    print(f"Ingested {len(doc_paths)} docs into {len(texts)} chunks -> FAISS index at {INDEX_PATH}")


if __name__ == "__main__":
    ingest()