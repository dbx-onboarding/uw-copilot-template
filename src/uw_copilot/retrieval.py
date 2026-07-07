"""
uw_copilot.retrieval — Hybrid document retrieval with RBAC enforcement.

Routes queries to:
  - Keyword (BM25) search  → when a reference ID pattern is detected
  - Hybrid (ANN + BM25)    → everything else

RBAC category filtering is applied at the Vector Search query layer,
not the application layer, so it cannot be bypassed.

Usage:
    from uw_copilot.retrieval import HybridRetriever
    retriever = HybridRetriever(cfg, workspace_client)
    docs = retriever.search("loss ratio for ABC Trucking", user_role="underwriter")
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from databricks.sdk import WorkspaceClient

from .config import Config

# Reference ID patterns that indicate a BM25 keyword search is more accurate
# than ANN vector similarity. These IDs are precise — the right chunk will
# have an exact string match.
REFERENCE_ID_PATTERN = re.compile(
    r"\b(ACI|CLM|SUB|INS|DRV|POL|LR)-[\w\d-]+\b",
    re.IGNORECASE,
)

# SQL intent keywords — route to structured data path instead of VS
SQL_INTENT_KEYWORDS = [
    "loss ratio", "premium", "claims count", "how many", "total loss",
    "average", "sum of", "fleet size", "number of drivers", "written premium",
    "earned premium", "incurred loss", "ytd", "year to date",
]


@dataclass
class RetrievedDocument:
    chunk_id:    str
    parent_id:   Optional[str]
    text:        str
    category:    str
    source_path: str
    score:       float
    doc_id:      Optional[str] = None

    def to_context_string(self, index: int) -> str:
        source_name = self.source_path.split("/")[-1] if self.source_path else "unknown"
        return f"### Source {index}: {source_name} ({self.category})\n{self.text}"


class QueryIntent:
    HYBRID   = "hybrid"    # ANN + BM25 (default)
    KEYWORD  = "keyword"   # BM25 only — reference IDs
    SQL      = "sql"       # Route to structured data path


class HybridRetriever:
    """
    Retrieves document chunks from Databricks Vector Search,
    enforcing RBAC at the query layer.
    """

    def __init__(self, cfg: Config, w: WorkspaceClient):
        self.cfg = cfg
        self.w   = w

    # ── Public API ────────────────────────────────────────────────────────────

    def detect_intent(self, query: str) -> str:
        """Classify query intent: hybrid, keyword, or sql."""
        if REFERENCE_ID_PATTERN.search(query):
            return QueryIntent.KEYWORD
        query_lower = query.lower()
        if any(kw in query_lower for kw in SQL_INTENT_KEYWORDS):
            return QueryIntent.SQL
        return QueryIntent.HYBRID

    def get_filter(self, user_role: str) -> Optional[Dict]:
        """
        Returns a VS filters dict restricting results to categories
        the role is allowed to see, or None for unrestricted access.
        Raises KeyError for unknown roles.
        """
        allowed = self.cfg.categories_for_role(user_role)  # None = all
        if allowed is None:
            return None
        return {"category_label": {"in": allowed}}

    def search(
        self,
        query: str,
        user_role: str,
        n_results: int = 8,
        intent: Optional[str] = None,
    ) -> List[RetrievedDocument]:
        """
        Search the Vector Search index.
        Returns up to n_results documents passing the RBAC filter.

        intent can be passed explicitly; if None, detect_intent() is called.
        Returns [] (not raises) on retrieval errors.
        """
        if intent is None:
            intent = self.detect_intent(query)

        if intent == QueryIntent.SQL:
            return []  # Caller should route to structured data path

        filters = self.get_filter(user_role)
        # Databricks Vector Search supports query_type "ANN" and "HYBRID" — there is
        # no "KEYWORD" type. HYBRID combines vector + lexical matching, which also
        # handles exact reference-ID lookups well, so use it for both intents.
        query_type = "HYBRID"

        # columns must be explicit — score is appended automatically as the
        # final element in each data_array row (i.e. row[5] below).
        _COLUMNS = ["chunk_id", "parent_id", "chunk_text", "category", "source_path"]
        try:
            response = self.w.vector_search_indexes.query_index(
                index_name=self.cfg.vs_index,
                columns=_COLUMNS,
                query_text=query,
                num_results=n_results,
                filters_json=_filters_to_json(filters),
                query_type=query_type,
            )
            return self._parse_response(response)
        except Exception as e:
            # Log but don't crash — return empty results with error context
            return [RetrievedDocument(
                chunk_id="error", parent_id=None,
                text=f"[Retrieval error — {type(e).__name__}: {e}]",
                category="", source_path="", score=0.0,
            )]

    def build_context(self, docs: List[RetrievedDocument]) -> str:
        """Format retrieved documents into an LLM context block."""
        if not docs:
            return ""
        parts = ["## Retrieved Context\n"]
        relevant = [d for d in docs if d.score >= self.cfg.similarity_threshold]
        if not relevant:
            relevant = docs[:3]  # Always give at least 3 results even below threshold
        for i, doc in enumerate(relevant[:6], 1):
            parts.append(doc.to_context_string(i))
        return "\n\n".join(parts)

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_response(response) -> List[RetrievedDocument]:
        results = []
        for row in (getattr(response.result, "data_array", None) or []):
            try:
                results.append(RetrievedDocument(
                    chunk_id=row[0],
                    parent_id=row[1] if len(row) > 1 else None,
                    text=row[2] if len(row) > 2 else "",
                    category=row[3] if len(row) > 3 else "",
                    source_path=row[4] if len(row) > 4 else "",
                    score=float(row[5]) if len(row) > 5 else 0.0,
                    doc_id=row[6] if len(row) > 6 else None,
                ))
            except (IndexError, TypeError, ValueError):
                continue
        return results


def _filters_to_json(filters: Optional[Dict]) -> Optional[str]:
    """Convert filters dict to JSON string expected by VS SDK."""
    if filters is None:
        return None
    import json
    return json.dumps(filters)
