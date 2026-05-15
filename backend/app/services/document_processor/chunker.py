"""
Intelligent Document Chunking Strategy
Supports semantic chunking, sliding window, recursive splitting
"""
from typing import List, Dict, Optional
from app.core.config import settings
from loguru import logger


def _get_recursive_splitter(chunk_size, chunk_overlap):
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", "? ", "! ", ", ", " ", ""],
            length_function=len,
        )
    except ImportError:
        # Fallback simple splitter
        class SimpleSplitter:
            def __init__(self, size, overlap):
                self.size = size
                self.overlap = overlap
            def split_text(self, text):
                chunks, i = [], 0
                while i < len(text):
                    chunks.append(text[i:i+self.size])
                    i += self.size - self.overlap
                return chunks
        return SimpleSplitter(chunk_size, chunk_overlap)


class DocumentChunker:
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        strategy: str = "recursive"
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.strategy = strategy

    def chunk(self, text: str, doc_type: str = "text", metadata: Dict = None) -> List[Dict]:
        """Split text into chunks with metadata"""
        if not text or not text.strip():
            return []

        splitter = self._get_splitter(doc_type)
        raw_chunks = splitter.split_text(text)

        # Filter empty chunks and limit count
        raw_chunks = [c for c in raw_chunks if c.strip()][:settings.MAX_CHUNKS_PER_DOC]

        chunks = []
        for i, chunk_text in enumerate(raw_chunks):
            chunk_meta = {
                "chunk_index": i,
                "chunk_type": "text",
                "token_count": self._estimate_tokens(chunk_text),
                **(metadata or {}),
            }
            chunks.append({
                "content": chunk_text.strip(),
                "metadata": chunk_meta,
                "index": i,
            })

        logger.info(f"Created {len(chunks)} chunks from {len(text)} chars")
        return chunks

    def chunk_with_pages(self, pages: List[Dict]) -> List[Dict]:
        """Chunk page-aware content (PDFs)"""
        all_chunks = []
        chunk_index = 0

        for page_data in pages:
            page_num = page_data.get("page_number", 0)
            text = page_data.get("text", "")

            splitter = self._get_splitter("text")
            page_chunks = splitter.split_text(text)

            for chunk_text in page_chunks:
                if chunk_text.strip():
                    all_chunks.append({
                        "content": chunk_text.strip(),
                        "metadata": {
                            "chunk_index": chunk_index,
                            "page_number": page_num,
                            "chunk_type": "text",
                            "token_count": self._estimate_tokens(chunk_text),
                        },
                        "index": chunk_index,
                    })
                    chunk_index += 1

        return all_chunks[:settings.MAX_CHUNKS_PER_DOC]

    def chunk_table(self, table_text: str, page_number: int = None) -> List[Dict]:
        """Handle table content as a single chunk (preserve structure)"""
        if not table_text.strip():
            return []

        return [{
            "content": table_text.strip(),
            "metadata": {
                "chunk_index": 0,
                "chunk_type": "table",
                "page_number": page_number,
                "token_count": self._estimate_tokens(table_text),
            },
            "index": 0,
        }]

    def chunk_transcript(self, transcript: str) -> List[Dict]:
        """Chunk audio/video transcripts with temporal awareness"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size * 2,  # Larger for transcripts
            chunk_overlap=self.chunk_overlap * 2,
            separators=["\n\n", "\n", ". ", "? ", "! ", " "],
        )
        raw_chunks = splitter.split_text(transcript)

        return [
            {
                "content": chunk.strip(),
                "metadata": {
                    "chunk_index": i,
                    "chunk_type": "transcript",
                    "token_count": self._estimate_tokens(chunk),
                },
                "index": i,
            }
            for i, chunk in enumerate(raw_chunks)
            if chunk.strip()
        ]

    def _get_splitter(self, doc_type: str):
        return _get_recursive_splitter(self.chunk_size, self.chunk_overlap)

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate (4 chars ~ 1 token)"""
        return len(text) // 4
