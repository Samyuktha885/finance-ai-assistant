"""
Knowledge Agent: retrieves relevant chunks from the finance KB via a local
FAISS index. Returns both the retrieved text (for the Orchestrator to
synthesize an answer) and a retrieval confidence signal (based on cosine
similarity) that feeds the overall confidence check.

Uses FAISS rather than ChromaDB — ChromaDB's dependency chain pulls in
grpc/opentelemetry for optional telemetry, whose native DLL can get blocked by
Windows Smart App Control on some machines. FAISS avoids that entirely and is
explicitly listed as an approved vector DB option in the brief.
"""
import os
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "kb", "faiss_store")
INDEX_PATH = os.path.join(INDEX_DIR, "index.faiss")
METADATA_PATH = os.path.join(INDEX_DIR, "metadata.pkl")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

_model = None
_index = None
_metadata = None


def _load():
    global _model, _index, _metadata
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    if _index is None:
        _index = faiss.read_index(INDEX_PATH)
        with open(METADATA_PATH, "rb") as f:
            _metadata = pickle.load(f)
    return _model, _index, _metadata


def retrieve(query: str, top_k: int = 3) -> dict:
    """
    Returns:
        {
            "chunks": [{"text": ..., "source": ..., "similarity": ...}, ...],
            "retrieval_confidence": float in [0, 1],  # higher = more relevant match found
        }
    Uses cosine similarity (via normalized embeddings + inner-product search),
    which is naturally in a sane range and clipped to [0, 1] for readability.
    """
    try:
        model, index, metadata = _load()
    except Exception as e:
        # KB not ingested yet — surface this clearly rather than crashing silently
        return {"chunks": [], "retrieval_confidence": 0.0, "error": str(e)}

    query_embedding = model.encode([query], normalize_embeddings=True)
    query_embedding = np.array(query_embedding, dtype="float32")

    scores, indices = index.search(query_embedding, top_k)

    chunks = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        similarity = max(0.0, min(1.0, float(score)))  # cosine similarity, clipped to [0,1]
        chunks.append(
            {
                "text": metadata["texts"][idx],
                "source": metadata["metadatas"][idx]["source"],
                "similarity": similarity,
            }
        )

    retrieval_confidence = max((c["similarity"] for c in chunks), default=0.0)

    return {"chunks": chunks, "retrieval_confidence": retrieval_confidence}