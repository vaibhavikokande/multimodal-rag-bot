"""
RAG Engine — FREE via Groq API (Llama 3.3 70B)
Groq free tier: https://console.groq.com
No cost, very fast inference.
"""
import json
import time
from typing import AsyncGenerator, Dict, List, Optional
from loguru import logger
from app.core.config import settings
from app.services.embedding_pipeline.embedder import EmbeddingPipeline, VectorStore


SYSTEM_PROMPT = """You are an expert enterprise AI assistant with access to a company knowledge base.
Answer questions accurately based on the provided context. Always cite sources.
Use markdown formatting for clarity. If context is insufficient, say so clearly."""


class RAGEngine:
    def __init__(self):
        self.embedder = EmbeddingPipeline()
        self.vector_store = VectorStore()
        self._groq = None

    def get_groq(self):
        if self._groq is None:
            from groq import Groq
            self._groq = Groq(api_key=settings.GROQ_API_KEY)
        return self._groq

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    async def query(self, question: str, workspace_id: int, model: str = "llama-3.3-70b-versatile",
                    conversation_history: List[Dict] = None, filter_doc_ids: Optional[List[int]] = None,
                    top_k: int = None) -> Dict:
        start = time.time()
        top_k = top_k or settings.TOP_K_RESULTS

        query_embedding = await self.embedder.embed_query(question)
        chunks = await self.vector_store.similarity_search(workspace_id, query_embedding, top_k * 2, filter_doc_ids)
        if chunks:
            chunks = self._hybrid_rerank(question, chunks, top_k)

        context = self._build_context(chunks)
        sources = self._extract_sources(chunks)
        answer = await self._generate(question, context, conversation_history or [], model)

        return {
            "answer": answer,
            "sources": sources,
            "retrieved_chunks": chunks[:settings.RERANK_TOP_K],
            "latency_ms": (time.time() - start) * 1000,
            "model_used": model,
        }

    async def stream_query(self, question: str, workspace_id: int,
                           model: str = "llama-3.3-70b-versatile",
                           conversation_history: List[Dict] = None,
                           filter_doc_ids: Optional[List[int]] = None) -> AsyncGenerator[str, None]:
        query_embedding = await self.embedder.embed_query(question)
        chunks = await self.vector_store.similarity_search(workspace_id, query_embedding,
                                                           settings.TOP_K_RESULTS * 2, filter_doc_ids)
        if chunks:
            chunks = self._hybrid_rerank(question, chunks, settings.TOP_K_RESULTS)

        context = self._build_context(chunks)
        sources = self._extract_sources(chunks)

        yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

        messages = self._build_messages(question, context, conversation_history or [])
        groq_model = self._resolve_model(model)

        try:
            import asyncio
            loop = asyncio.get_event_loop()

            def _stream_sync():
                groq = self.get_groq()
                return groq.chat.completions.create(
                    model=groq_model,
                    messages=messages,
                    stream=True,
                    temperature=0.1,
                    max_tokens=4096,
                )

            stream = await loop.run_in_executor(None, _stream_sync)
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

        except Exception as e:
            logger.error(f"Groq stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'sources': sources})}\n\n"

    async def generate_summary(self, text: str, doc_title: str = "") -> str:
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            def _call():
                groq = self.get_groq()
                r = groq.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "Create a concise 3-5 paragraph document summary for an enterprise knowledge base."},
                        {"role": "user", "content": f"Summarize this document titled '{doc_title}':\n\n{text[:6000]}"},
                    ],
                    max_tokens=600, temperature=0.3,
                )
                return r.choices[0].message.content
            return await loop.run_in_executor(None, _call)
        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
            return ""

    async def generate_auto_tags(self, text: str) -> List[str]:
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            def _call():
                groq = self.get_groq()
                r = groq.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "Extract 5-8 relevant tags from this document. Return only a JSON array of strings. Example: [\"finance\", \"Q3\", \"revenue\"]"},
                        {"role": "user", "content": text[:3000]},
                    ],
                    max_tokens=150, temperature=0,
                )
                raw = r.choices[0].message.content.strip()
                # extract JSON array
                start = raw.find('[')
                end = raw.rfind(']') + 1
                if start >= 0 and end > start:
                    return json.loads(raw[start:end])
                return []
            return await loop.run_in_executor(None, _call)
        except Exception as e:
            logger.warning(f"Auto-tag generation failed: {e}")
            return []

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    async def _generate(self, question: str, context: str, history: List[Dict], model: str) -> str:
        import asyncio
        messages = self._build_messages(question, context, history)
        groq_model = self._resolve_model(model)
        loop = asyncio.get_event_loop()
        def _call():
            groq = self.get_groq()
            r = groq.chat.completions.create(
                model=groq_model, messages=messages,
                temperature=0.1, max_tokens=4096,
            )
            return r.choices[0].message.content
        return await loop.run_in_executor(None, _call)

    def _resolve_model(self, model: str) -> str:
        """Map any model name to a Groq-supported model."""
        mapping = {
            "gpt-4o": "llama-3.3-70b-versatile",
            "gpt-4o-mini": "llama-3.1-8b-instant",
            "claude-3-5-sonnet-20241022": "llama-3.3-70b-versatile",
            "claude-3-5-sonnet": "llama-3.3-70b-versatile",
        }
        # If it's already a groq model name, keep it
        groq_models = {"llama-3.3-70b-versatile", "llama-3.1-8b-instant",
                        "mixtral-8x7b-32768", "gemma2-9b-it"}
        if model in groq_models:
            return model
        return mapping.get(model, "llama-3.3-70b-versatile")

    def _hybrid_rerank(self, query: str, chunks: List[Dict], top_k: int) -> List[Dict]:
        try:
            from rank_bm25 import BM25Okapi
            corpus = [c["content"].lower().split() for c in chunks]
            bm25 = BM25Okapi(corpus)
            scores = bm25.get_scores(query.lower().split())
            max_s = max(scores) or 1
            alpha = settings.HYBRID_SEARCH_ALPHA
            for i, chunk in enumerate(chunks):
                chunk["hybrid_score"] = alpha * chunk.get("score", 0) + (1 - alpha) * (scores[i] / max_s)
            chunks.sort(key=lambda x: x.get("hybrid_score", 0), reverse=True)
        except ImportError:
            chunks.sort(key=lambda x: x.get("score", 0), reverse=True)
        return chunks[:top_k]

    def _build_context(self, chunks: List[Dict]) -> str:
        if not chunks:
            return "No relevant documents found in the knowledge base."
        parts = []
        for i, c in enumerate(chunks[:settings.RERANK_TOP_K], 1):
            page = c.get("metadata", {}).get("page_number", "")
            page_str = f", Page {page}" if page else ""
            parts.append(f"[Source {i} | Doc ID: {c.get('document_id')}{page_str}]\n{c['content']}")
        return "\n\n---\n\n".join(parts)

    def _extract_sources(self, chunks: List[Dict]) -> List[Dict]:
        seen, sources = set(), []
        for c in chunks:
            did = c.get("document_id")
            if did and did not in seen:
                seen.add(did)
                sources.append({
                    "document_id": did,
                    "score": round(c.get("score", 0), 3),
                    "page_number": c.get("metadata", {}).get("page_number"),
                    "content_preview": c["content"][:150] + "...",
                })
        return sources

    def _build_messages(self, question: str, context: str, history: List[Dict]) -> List[Dict]:
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in history[-10:]:
            msgs.append({"role": m["role"], "content": m["content"]})
        msgs.append({
            "role": "user",
            "content": f"Context from knowledge base:\n\n{context}\n\nQuestion: {question}\n\nAnswer with citations:",
        })
        return msgs
