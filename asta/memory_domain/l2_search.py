from pathlib import Path
from typing import List, Dict, Any
from loguru import logger
import numpy as np
import asyncio
from rank_bm25 import BM25Okapi
from fastembed import TextEmbedding
from asta.core_engine.event_bus import Event


class L2SearchEngine:
    """
    Zero-VRAM Hybrid Search Engine (BM25 + Semantic Vector)
    Indexes and retrieves L3 Obsidian Markdown files.
    """

    def __init__(self, vault_path: str = "~/.asta/vault", event_bus: Any = None) -> None:
        self.vault_path = Path(vault_path).expanduser()

        logger.info("Initializing FastEmbed (L2 Search)...")
        # BGE-Small is extremely fast, lightweight, and runs well locally on CPU
        self.embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

        self.documents: List[str] = []
        self.doc_metadata: List[Dict[str, str]] = []
        self.bm25: Any = None
        self.document_embeddings: Any = None

        self._build_index()

        if event_bus:
            # Subscribe to memory eviction events to dynamically update the index
            event_bus.subscribe("MEMORY_ARCHIVED", self._handle_memory_archived)

    async def _handle_memory_archived(self, event: Event) -> None:
        """Triggered via EventBus when L1 pages memory to L3."""
        logger.debug("L2 Search Engine detected memory archive event. Re-indexing...")
        # In a production setting, this would be an incremental index update.
        # For MVP, we run a full background re-index.
        await asyncio.to_thread(self._build_index)

    def _build_index(self) -> None:
        """Scan the vault and build the lexical and semantic indexes."""
        self.documents = []
        self.doc_metadata = []

        if not self.vault_path.exists():
            return

        for filepath in self.vault_path.glob("*.md"):
            content = filepath.read_text(encoding="utf-8")

            # Simple chunking: chunk by markdown headers or paragraphs
            # For this MVP, we chunk by paragraphs (double newline)
            chunks = [chunk.strip() for chunk in content.split("\n\n") if chunk.strip()]

            # If the file is too small and only has one block (e.g. # Title \n Content)
            # combine them for better context if there are 2 chunks and the first is just a header
            if len(chunks) == 2 and chunks[0].startswith("#"):
                chunks = [f"{chunks[0]}\n{chunks[1]}"]

            for chunk in chunks:
                self.documents.append(chunk)
                self.doc_metadata.append({"file": filepath.name})

        if not self.documents:
            logger.debug("No documents found to index.")
            return

        # Build BM25 Index
        tokenized_corpus = [doc.lower().split(" ") for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized_corpus)

        # Build Vector Embeddings
        logger.debug(f"Computing embeddings for {len(self.documents)} chunks...")
        embeddings_generator = self.embedding_model.embed(self.documents)
        self.document_embeddings = np.array(list(embeddings_generator))

        logger.info(f"L2 Search Index built successfully ({len(self.documents)} chunks).")

    def search(self, query: str, top_k: int = 3, semantic_weight: float = 0.7) -> List[Dict[str, Any]]:
        """
        Hybrid search combining BM25 and Semantic Cosine Similarity.
        """
        if not self.documents or self.bm25 is None or self.document_embeddings is None:
            return []

        # 1. Lexical Score (BM25)
        tokenized_query = query.lower().split(" ")
        bm25_scores = self.bm25.get_scores(tokenized_query)

        # Normalize BM25 scores (0 to 1)
        if np.max(bm25_scores) > 0:
            bm25_scores = bm25_scores / np.max(bm25_scores)

        # 2. Semantic Score (FastEmbed)
        query_embedding_list = list(self.embedding_model.embed([query]))
        query_embedding = np.array(query_embedding_list[0])

        # Calculate Cosine Similarity using pure numpy
        norm_q = np.linalg.norm(query_embedding)
        norm_docs = np.linalg.norm(self.document_embeddings, axis=1)

        # Prevent division by zero
        valid_docs_mask = norm_docs != 0
        semantic_scores = np.zeros(len(self.documents))
        if norm_q != 0:
            semantic_scores[valid_docs_mask] = np.dot(self.document_embeddings[valid_docs_mask], query_embedding) / (norm_docs[valid_docs_mask] * norm_q)

        # 3. Hybrid Scoring
        hybrid_scores = (semantic_weight * semantic_scores) + ((1.0 - semantic_weight) * bm25_scores)

        # Get top K indices
        top_indices = np.argsort(hybrid_scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            # Only return results that have at least some relevance
            if hybrid_scores[idx] > 0.1:
                results.append({
                    "score": float(hybrid_scores[idx]),
                    "content": self.documents[idx],
                    "metadata": self.doc_metadata[idx]
                })

        return results
