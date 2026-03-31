# memory/hybrid_recall.py
# ─────────────────────────────────────────────
# Hybrid Memory Recall — BM25 + Vector Search + Reranking
#
# Combines keyword-based (BM25) and semantic (vector) search for optimal recall.
# Uses Reciprocal Rank Fusion (RRF) for merging results.
# Optional cross-encoder reranking for precision.
#
# RULES.md Compliance:
# - Type hints mandatory
# - Docstrings complete
# - Error handling comprehensive
# - Logging contextual
# ─────────────────────────────────────────────

import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

# Try to import rank-bm25, gracefully degrade if not available
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
    logger.info("[hybrid_recall] rank-bm25 available for keyword search")
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("[hybrid_recall] rank-bm25 not installed — falling back to vector-only search")


class HybridMemoryRecall:
    """
    Hybrid memory retrieval combining BM25 (keyword) and vector (semantic) search.
    
    Architecture:
    1. Parallel retrieval: BM25 + vector search
    2. Reciprocal Rank Fusion (RRF) for merging
    3. Maximal Marginal Relevance (MMR) for diversity
    4. Optional: Cross-encoder reranking (not implemented - requires model)
    
    Example:
        recall = HybridMemoryRecall()
        results = recall.query(
            user_id="user-123",
            query="write a Python function",
            top_k=5
        )
    """
    
    def __init__(self, rrf_k: int = 60, diversity_lambda: float = 0.7):
        """
        Initialize hybrid recall system.
        
        Args:
            rrf_k: Reciprocal Rank Fusion constant (default: 60)
                   Higher = more weight to top ranks
            diversity_lambda: MMR diversity parameter (default: 0.7)
                             0 = pure relevance, 1 = pure diversity
        """
        self.rrf_k = rrf_k
        self.diversity_lambda = diversity_lambda
        
        # In-memory BM25 index (per user)
        # In production, this would be persisted/rebuilt on startup
        self._bm25_indices: Dict[str, BM25Okapi] = {}
        self._memory_cache: Dict[str, List[Dict]] = {}  # user_id -> memories
        
        logger.info(
            f"[hybrid_recall] initialized with rrf_k={rrf_k}, diversity_lambda={diversity_lambda}"
        )
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25 indexing.
        
        Args:
            text: Input text to tokenize
        
        Returns:
            List of lowercase tokens
        """
        # Simple tokenization: lowercase, split on non-alphanumeric
        import re
        tokens = re.findall(r'\b[a-z0-9]+\b', text.lower())
        return tokens
    
    def _build_bm25_index(self, memories: List[Dict[str, Any]]) -> Optional[BM25Okapi]:
        """
        Build BM25 index from memory documents.
        
        Args:
            memories: List of memory dicts with 'content' field
        
        Returns:
            BM25Okapi index or None if BM25 unavailable
        """
        if not BM25_AVAILABLE or not memories:
            return None
        
        # Tokenize all documents
        tokenized_docs = [
            self._tokenize(mem.get('content', '') + ' ' + mem.get('improved_content', ''))
            for mem in memories
        ]
        
        # Build index
        index = BM25Okapi(tokenized_docs)
        return index
    
    def _bm25_search(
        self,
        user_id: str,
        query: str,
        top_k: int
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search memories using BM25 keyword matching.
        
        Args:
            user_id: User identifier
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of (memory, score) tuples
        """
        if not BM25_AVAILABLE:
            return []
        
        memories = self._memory_cache.get(user_id, [])
        if not memories:
            # ═══ Lazy Provision (Senior Dev Move) ═══
            # Fetch last 150 memories from Supabase to build the BM25 index
            try:
                from database import get_client
                db = get_client()
                result = db.table("langmem_memories")\
                    .select("id, content, improved_content, domain, quality_score, created_at")\
                    .eq("user_id", user_id)\
                    .order("created_at", desc=True)\
                    .limit(150)\
                    .execute()
                
                if hasattr(result, 'data') and result.data:
                    memories = result.data
                    self._memory_cache[user_id] = memories
                    logger.info(f"[hybrid_recall] provisioned {len(memories)} memories for user {user_id[:8]}...")
                else:
                    logger.debug(f"[hybrid_recall] no memories found in DB for user {user_id[:8]}...")
                    return []
            except Exception as e:
                logger.error(f"[hybrid_recall] failed to provision user cache: {e}")
                return []
        
        # Build index if not cached
        if user_id not in self._bm25_indices:
            self._bm25_indices[user_id] = self._build_bm25_index(memories)
        
        index = self._bm25_indices.get(user_id)
        if not index:
            return []
        
        # Tokenize query
        query_tokens = self._tokenize(query)
        
        # Get BM25 scores
        scores = index.get_scores(query_tokens)
        
        # Pair memories with scores and sort
        scored_memories = [
            (mem, score)
            for mem, score in zip(memories, scores)
            if score > 0  # Filter zero-score results
        ]
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        logger.debug(f"[hybrid_recall] BM25 search returned {len(scored_memories)} results")
        return scored_memories[:top_k]
    
    def _vector_search(
        self,
        user_id: str,
        query: str,
        top_k: int
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search memories using vector similarity (pgvector).
        
        Delegates to existing LangMem implementation.
        
        Args:
            user_id: User identifier
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of (memory, similarity_score) tuples
        """
        from memory.langmem import query_langmem
        
        memories = query_langmem(
            user_id=user_id,
            query=query,
            top_k=top_k * 2,  # Get more for fusion
            surface="web_app",
            use_hybrid=False  # CRITICAL: Fix infinite recursion!
        )
        
        # Convert to (memory, score) format
        scored_memories = [
            (mem, mem.get('similarity_score', 0.0))
            for mem in memories
        ]
        
        logger.debug(f"[hybrid_recall] vector search returned {len(scored_memories)} results")
        return scored_memories
    
    def _reciprocal_rank_fusion(
        self,
        bm25_results: List[Tuple[Dict[str, Any], float]],
        vector_results: List[Tuple[Dict[str, Any], float]],
        top_k: int
    ) -> List[Tuple[Dict[str, Any], float]]:
        """
        Merge BM25 and vector results using Reciprocal Rank Fusion (RRF).
        
        RRF formula: score = sum(1 / (k + rank)) for each ranking
        
        Args:
            bm25_results: BM25 search results
            vector_results: Vector search results
            top_k: Number of final results to return
        
        Returns:
            Fused and ranked results
        """
        # Track cumulative RRF scores
        rrf_scores: Dict[str, float] = defaultdict(float)
        memory_by_id: Dict[str, Dict] = {}
        
        # Add BM25 rankings
        for rank, (mem, _) in enumerate(bm25_results, start=1):
            mem_id = mem.get('id', hashlib.md5(mem.get('content', '').encode()).hexdigest())
            rrf_scores[mem_id] += 1.0 / (self.rrf_k + rank)
            memory_by_id[mem_id] = mem
        
        # Add vector rankings
        for rank, (mem, _) in enumerate(vector_results, start=1):
            mem_id = mem.get('id', hashlib.md5(mem.get('content', '').encode()).hexdigest())
            rrf_scores[mem_id] += 1.0 / (self.rrf_k + rank)
            memory_by_id[mem_id] = mem
        
        # Sort by RRF score
        fused_results = [
            (memory_by_id[mem_id], score)
            for mem_id, score in sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        ]
        
        logger.debug(f"[hybrid_recall] RRF fusion: {len(fused_results)} results")
        return fused_results[:top_k]
    
    def _maximal_margin_reranking(
        self,
        results: List[Tuple[Dict[str, Any], float]],
        query: str,
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Apply Maximal Marginal Relevance (MMR) for diversity.
        
        Balances relevance to query with diversity from already-selected results.
        
        Args:
            results: RRF-ranked results
            query: Original query
            top_k: Number of diverse results to return
        
        Returns:
            Diverse subset of results
        """
        if not results or self.diversity_lambda >= 1.0:
            # No reranking needed
            return [mem for mem, _ in results[:top_k]]
        
        # Simple MMR implementation
        selected = []
        remaining = list(results)
        
        # Pre-compute query similarity (use RRF score as proxy)
        # In production, would use actual embedding similarity
        
        while len(selected) < top_k and remaining:
            # Select next item with best MMR score
            best_score = float('-inf')
            best_idx = 0
            
            for i, (mem, rrf_score) in enumerate(remaining):
                # Relevance component (RRF score)
                relevance = rrf_score
                
                # Diversity component (similarity to already-selected)
                # Simplified: penalize if content overlaps with selected
                diversity_penalty = 0
                for sel_mem in selected:
                    # Simple overlap check
                    sel_content = set(sel_mem.get('content', '').lower().split())
                    mem_content = set(mem.get('content', '').lower().split())
                    overlap = len(sel_content & mem_content) / max(len(sel_content), len(mem_content), 1)
                    diversity_penalty += overlap
                
                # MMR score
                mmr_score = (
                    self.diversity_lambda * relevance -
                    (1 - self.diversity_lambda) * diversity_penalty
                )
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i
            
            # Add best to selected
            selected.append(remaining.pop(best_idx)[0])
        
        logger.debug(f"[hybrid_recall] MMR reranking: {len(selected)} diverse results")
        return selected
    
    def query(
        self,
        user_id: str,
        query: str,
        top_k: int = 5,
        use_hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Query memories using hybrid recall.
        
        Args:
            user_id: User identifier
            query: Search query
            top_k: Number of results to return
            use_hybrid: If False, use vector-only search
        
        Returns:
            List of memory dicts, ranked and diversified
        
        Example:
            results = hybrid.query(
                user_id="user-123",
                query="write async Python function",
                top_k=5
            )
        """
        if not use_hybrid:
            # Vector-only fallback
            vector_results = self._vector_search(user_id, query, top_k)
            return [mem for mem, _ in vector_results]
        
        # Parallel retrieval
        bm25_results = self._bm25_search(user_id, query, top_k=top_k * 2)
        vector_results = self._vector_search(user_id, query, top_k=top_k * 2)
        
        # Handle edge cases
        if not bm25_results and not vector_results:
            logger.debug(f"[hybrid_recall] no results for user={user_id[:8]}... query='{query[:30]}...'")
            return []
        
        if not bm25_results:
            # BM25 unavailable or no results — use vector only
            logger.debug("[hybrid_recall] BM25 unavailable — using vector-only")
            return [mem for mem, _ in vector_results[:top_k]]
        
        if not vector_results:
            # Vector search failed — use BM25 only
            logger.debug("[hybrid_recall] vector search failed — using BM25-only")
            return [mem for mem, _ in bm25_results[:top_k]]
        
        # Reciprocal Rank Fusion
        fused = self._reciprocal_rank_fusion(bm25_results, vector_results, top_k=top_k * 2)
        
        # Maximal Marginal Relevance for diversity
        diverse = self._maximal_margin_reranking(fused, query, top_k=top_k)
        
        logger.info(
            f"[hybrid_recall] query complete: user={user_id[:8]}..., "
            f"bm25={len(bm25_results)}, vector={len(vector_results)}, "
            f"fused={len(fused)}, diverse={len(diverse)}"
        )
        
        return diverse


# Global instance for reuse
hybrid_recall = HybridMemoryRecall()


def query_hybrid_memories(
    user_id: str,
    query: str,
    top_k: int = 5,
    use_hybrid: bool = True
) -> List[Dict[str, Any]]:
    """
    Convenience function for hybrid memory queries.
    
    Args:
        user_id: User identifier
        query: Search query
        top_k: Number of results to return
        use_hybrid: If False, use vector-only search
    
    Returns:
        List of memory dicts
    
    Example:
        memories = query_hybrid_memories(
            user_id="user-123",
            query="Python async function",
            top_k=5
        )
    """
    return hybrid_recall.query(user_id, query, top_k, use_hybrid)


__all__ = [
    "HybridMemoryRecall",
    "hybrid_recall",
    "query_hybrid_memories",
]
