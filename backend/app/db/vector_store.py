import re
import math
import hashlib
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from app.config import settings
from app.models.schemas import Chunk

logger = logging.getLogger(__name__)

class LocalFastEmbeddingFunction(EmbeddingFunction):
    """
    A fast, deterministic, 128-dimensional local embedding fallback.
    No network requests, zero download risk, fully local and instant.
    Uses n-gram subword frequency hashing with L2-normalization for cosine similarity.
    Note: Keyword/lexical-hash based, does not perform deep semantic vector mapping.
    """
    def __init__(self, dim: int = 128):
        self.dim = dim

    def name(self) -> str:
        return "proofmind_fast_local_embedding"

    def get_config(self) -> Dict[str, Any]:
        return {"dim": self.dim}

    def _embed_text(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        clean = re.sub(r"[^\w\s]", " ", text.lower())
        tokens = [t for t in clean.split() if t]
        
        if not tokens:
            return vec

        for t in tokens:
            h_val = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16) % self.dim
            vec[h_val] += 1.0
            
            if len(t) >= 3:
                for i in range(len(t) - 2):
                    ngram = t[i:i+3]
                    ng_val = int(hashlib.md5(ngram.encode("utf-8")).hexdigest(), 16) % self.dim
                    vec[ng_val] += 0.5

        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [round(x / norm, 6) for x in vec]
        return vec

    def __call__(self, input: Documents) -> Embeddings:
        return [self._embed_text(doc) for doc in input]


class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.embedding_fn, self.collection_name = self._init_embedding_function()
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"}
        )

    def _init_embedding_function(self):
        provider = getattr(settings, "EMBEDDING_PROVIDER", "onnx_minilm").lower()
        if provider == "onnx_minilm":
            try:
                import chromadb.utils.embedding_functions as ef
                logger.info("Initializing ONNX all-MiniLM-L6-v2 semantic embedding function")
                fn = ef.ONNXMiniLM_L6_V2()
                return fn, "proofmind_evidence_semantic"
            except Exception as e:
                logger.warning(f"Could not initialize ONNXMiniLM_L6_V2 ({e}), falling back to local fast embedding")
        return LocalFastEmbeddingFunction(dim=128), "proofmind_evidence_fast"

    def add_chunks(self, chunks: List[Chunk]):
        if not chunks:
            return
        
        ids = [c.id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [
            {
                "document_id": c.document_id,
                "filename": c.filename,
                "page_number": c.page_number,
                "chunk_index": c.chunk_index
            }
            for c in chunks
        ]
        
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def query(
        self,
        query_text: str,
        n_results: int = 8,
        document_ids: Optional[List[str]] = None,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        total_items = self.collection.count()
        if total_items == 0:
            return []
            
        limit = min(n_results, total_items)
        where_clause = None
        if document_ids and len(document_ids) > 0:
            if len(document_ids) == 1:
                where_clause = {"document_id": document_ids[0]}
            else:
                where_clause = {"document_id": {"$in": document_ids}}
                
        threshold = min_score if min_score is not None else getattr(settings, "SIMILARITY_THRESHOLD", 0.40)

        results = self.collection.query(
            query_texts=[query_text],
            n_results=limit,
            where=where_clause
        )
        
        extracted = []
        if results and "ids" in results and results["ids"] and len(results["ids"][0]) > 0:
            for idx in range(len(results["ids"][0])):
                chunk_id = results["ids"][0][idx]
                doc_text = results["documents"][0][idx]
                meta = results["metadatas"][0][idx]
                distance = results["distances"][0][idx] if "distances" in results and results["distances"] else 0.5
                similarity = max(0.0, min(1.0, 1.0 - (distance / 2.0)))
                
                # Check threshold
                if similarity >= threshold:
                    extracted.append({
                        "chunk_id": chunk_id,
                        "document_id": meta.get("document_id", ""),
                        "filename": meta.get("filename", ""),
                        "page_number": meta.get("page_number", 1),
                        "chunk_index": meta.get("chunk_index", 0),
                        "text": doc_text,
                        "score": round(similarity, 4)
                    })
        return extracted

    def delete_document_vectors(self, document_id: str):
        try:
            self.collection.delete(where={"document_id": document_id})
        except Exception:
            pass

    def count(self) -> int:
        return self.collection.count()

vector_store = VectorStore()
