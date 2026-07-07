"""
tests/test_retrieval.py — HybridRetriever intent routing and RBAC filter logic.

These tests do NOT call the Databricks API — they test the routing and
filter-construction logic in isolation using a Config fixture.

Run with: pytest tests/test_retrieval.py -v
"""

import pytest
import yaml
from unittest.mock import MagicMock, patch

from uw_copilot.config import Config
from uw_copilot.retrieval import HybridRetriever, QueryIntent, RetrievedDocument


# ── Fixtures ──────────────────────────────────────────────────────────────────

BASE_CONFIG = {
    "company": {"name": "Test Co", "short_name": "test", "domain": "casualty"},
    "catalog": "tc",
    "intake":  {"volume_name": "raw_documents", "schedule": "*/15 * * * *"},
    "models":  {"chat": "chat-model", "embedding": "embed-model"},
    "chunking":    {"parent_size": 2500, "child_size": 600, "overlap": 100},
    "similarity":  {"threshold": 0.70, "max_results": 10},
    "doc_categories": [
        {"id": "01", "label": "Underwriting Guidelines"},
        {"id": "02", "label": "Claims Procedures"},
        {"id": "03", "label": "Loss Runs"},
    ],
    "rbac": {
        "underwriter":     ["all"],
        "claims_adjuster": ["Claims Procedures", "Loss Runs"],
        "broker":          ["Underwriting Guidelines"],
    },
}


@pytest.fixture
def cfg(tmp_path):
    path = tmp_path / "config" / "company_config.yaml"
    path.parent.mkdir()
    path.write_text(yaml.dump(BASE_CONFIG))
    return Config(str(path))


@pytest.fixture
def mock_w():
    return MagicMock()


@pytest.fixture
def retriever(cfg, mock_w):
    return HybridRetriever(cfg, mock_w)


# ── Intent detection ──────────────────────────────────────────────────────────

class TestIntentDetection:
    def test_reference_id_routes_to_keyword(self, retriever):
        assert retriever.detect_intent("What is ACI-2024-001?") == QueryIntent.KEYWORD

    def test_claim_id_routes_to_keyword(self, retriever):
        assert retriever.detect_intent("Show details for CLM-5523") == QueryIntent.KEYWORD

    def test_submission_id_routes_to_keyword(self, retriever):
        assert retriever.detect_intent("Review submission SUB-9901") == QueryIntent.KEYWORD

    def test_insured_id_routes_to_keyword(self, retriever):
        assert retriever.detect_intent("Insured INS-1042 loss history") == QueryIntent.KEYWORD

    def test_driver_id_routes_to_keyword(self, retriever):
        assert retriever.detect_intent("Driver DRV-443 MVR status") == QueryIntent.KEYWORD

    def test_loss_ratio_question_routes_to_sql(self, retriever):
        assert retriever.detect_intent("What is the loss ratio for ABC Trucking?") == QueryIntent.SQL

    def test_premium_question_routes_to_sql(self, retriever):
        assert retriever.detect_intent("How much premium did we write in 2024?") == QueryIntent.SQL

    def test_count_question_routes_to_sql(self, retriever):
        assert retriever.detect_intent("How many claims did we have last quarter?") == QueryIntent.SQL

    def test_general_question_routes_to_hybrid(self, retriever):
        assert retriever.detect_intent("What are the HAZMAT referral triggers?") == QueryIntent.HYBRID

    def test_guideline_question_routes_to_hybrid(self, retriever):
        assert retriever.detect_intent("Minimum driver experience for flatbed fleets?") == QueryIntent.HYBRID

    def test_intent_is_case_insensitive(self, retriever):
        assert retriever.detect_intent("what is the LOSS RATIO trend?") == QueryIntent.SQL


# ── RBAC filter construction ──────────────────────────────────────────────────

class TestRBACFilter:
    def test_underwriter_gets_no_filter(self, retriever):
        """underwriter has ["all"] — should return None (no filter)."""
        assert retriever.get_filter("underwriter") is None

    def test_restricted_role_gets_category_filter(self, retriever):
        f = retriever.get_filter("claims_adjuster")
        assert f is not None
        assert set(f["category_label"]["in"]) == {"Claims Procedures", "Loss Runs"}

    def test_broker_filtered_to_one_category(self, retriever):
        f = retriever.get_filter("broker")
        assert f["category_label"]["in"] == ["Underwriting Guidelines"]

    def test_unknown_role_raises_key_error(self, retriever):
        with pytest.raises(KeyError, match="unknown_role"):
            retriever.get_filter("unknown_role")


# ── Context assembly ──────────────────────────────────────────────────────────

class TestContextAssembly:
    def _make_doc(self, text, score=0.85, category="Guidelines", path="doc.pdf"):
        return RetrievedDocument(
            chunk_id="c1", parent_id=None, text=text,
            category=category, source_path=path, score=score,
        )

    def test_empty_docs_returns_empty_string(self, retriever):
        assert retriever.build_context([]) == ""

    def test_context_includes_source_header(self, retriever):
        docs = [self._make_doc("Referral trigger: loss ratio > 75%")]
        ctx = retriever.build_context(docs)
        assert "Source 1" in ctx

    def test_context_includes_document_text(self, retriever):
        docs = [self._make_doc("Loss ratio limit is 75%.")]
        ctx = retriever.build_context(docs)
        assert "Loss ratio limit is 75%." in ctx

    def test_low_score_docs_still_included_up_to_3(self, retriever):
        """Even below threshold, at least 3 docs must be returned."""
        docs = [self._make_doc("text", score=0.1) for _ in range(5)]
        ctx = retriever.build_context(docs)
        assert "Source 1" in ctx
        assert "Source 2" in ctx
        assert "Source 3" in ctx

    def test_max_6_sources_in_context(self, retriever):
        docs = [self._make_doc(f"text {i}", score=0.9) for i in range(10)]
        ctx = retriever.build_context(docs)
        assert "Source 6" in ctx
        assert "Source 7" not in ctx
