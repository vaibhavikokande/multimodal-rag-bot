"""
Embedding Pipeline — FREE local embeddings via sentence-transformers
No API key required. Model downloads once (~90MB) and runs on CPU.
"""
import asyncio
from typing import List, Dict, Optional
from loguru import logger
from app.core.config import settings

# Lazy-loaded model (downloads once on first use)
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading local embedding model: all-MiniLM-L6-v2 ...")
            _model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Embedding model loaded.")
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            raise
    return _model


class EmbeddingPipeline:
    """Free local embeddings — no API key, no cost, runs on CPU."""

    def __init__(self):
        self.dimensions = 384   # all-MiniLM-L6-v2 output size
        self.batch_size = 64

    async def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self.dimensions
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._encode_single, text)

    def _encode_single(self, text: str) -> List[float]:
        model = get_embedding_model()
        vec = model.encode(text[:512], normalize_embeddings=True)
        return vec.tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._encode_batch, texts)

    def _encode_batch(self, texts: List[str]) -> List[List[float]]:
        model = get_embedding_model()
        clean = [t[:512] if t else " " for t in texts]
        vecs = model.encode(clean, batch_size=self.batch_size, normalize_embeddings=True, show_progress_bar=False)
        return [v.tolist() for v in vecs]

    async def embed_chunks(self, chunks: List[Dict]) -> List[Dict]:
        texts = [chunk["content"] for chunk in chunks]
        embeddings = await self.embed_batch(texts)
        for chunk, emb in zip(chunks, embeddings):
            chunk["embedding"] = emb
        return chunks

    async def embed_query(self, query: str) -> List[float]:
        return await self.embed_text(query)


class VectorStore:
    """Vector database — ChromaDB persistent local store (free)."""

    def __init__(self):
        self._client = None

    def get_client(self):
        if self._client is None:
            import chromadb
            self._client = chromadb.PersistentClient(path="./chroma_data")
            logger.info("ChromaDB persistent client ready.")
        return self._client

    async def upsert_chunks(self, workspace_id: int, document_id: int, chunks: List[Dict]) -> List[str]:
        client = self.get_client()
        collection = client.get_or_create_collection(
            name=f"workspace_{workspace_id}",
            metadata={"hnsw:space": "cosine"},
        )
        ids, embeddings, documents, metadatas = [], [], [], []
        for chunk in chunks:
            chunk_id = f"doc_{document_id}_chunk_{chunk['index']}"
            ids.append(chunk_id)
            embeddings.append(chunk["embedding"])
            documents.append(chunk["content"])
            metadatas.append({
                "document_id": str(document_id),
                "chunk_index": str(chunk["index"]),
                "chunk_type": chunk["metadata"].get("chunk_type", "text"),
                "page_number": str(chunk["metadata"].get("page_number", "")),
            })
        if ids:
            collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
        logger.info(f"Stored {len(ids)} chunks in ChromaDB for doc {document_id}")
        return ids

    async def similarity_search(self, workspace_id: int, query_embedding: List[float],
                                 top_k: int = 10, filter_doc_ids: Optional[List[int]] = None) -> List[Dict]:
        client = self.get_client()
        try:
            collection = client.get_collection(f"workspace_{workspace_id}")
        except Exception:
            return []

        where = None
        if filter_doc_ids:
            where = {"document_id": {"$in": [str(d) for d in filter_doc_ids]}}

        count = collection.count()
        if count == 0:
            return []

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, count),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        chunks = []
        if results["documents"] and results["documents"][0]:
            for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
                chunks.append({
                    "content": doc,
                    "metadata": meta,
                    "score": 1 - dist,
                    "document_id": int(meta.get("document_id", 0)),
                    "chunk_index": int(meta.get("chunk_index", 0)),
                })
        return chunks

    async def delete_document(self, workspace_id: int, document_id: int) -> bool:
        try:
            client = self.get_client()
            col = client.get_collection(f"workspace_{workspace_id}")
            col.delete(where={"document_id": str(document_id)})
            return True
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
