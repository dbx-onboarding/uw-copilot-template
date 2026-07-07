"""
Unit tests for uw_copilot.session.SessionManager

SessionManager uses Spark SQL for Delta writes. We mock the SparkSession
so tests run without a live cluster.
"""
import pytest
from unittest.mock import MagicMock, call


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_config():
    cfg = MagicMock()
    cfg.catalog = "atlas"
    cfg.schema  = "atlas_insurance_rag"
    return cfg


def _make_spark(rows=None):
    """Return a Spark stub. spark.sql() returns a DataFrame stub."""
    spark = MagicMock()
    df    = MagicMock()
    if rows is not None:
        df.collect.return_value = rows
    else:
        df.collect.return_value = []
    spark.sql.return_value = df
    return spark


def _make_sm(**kwargs):
    from uw_copilot.session import SessionManager
    cfg   = _make_config()
    spark = _make_spark(**kwargs)
    return SessionManager(cfg, spark), spark


# ─── Instantiation ────────────────────────────────────────────────────────────

class TestSessionManagerInit:
    def test_instantiates(self):
        sm, _ = _make_sm()
        assert sm is not None

    def test_table_name_is_fully_qualified(self):
        sm, _ = _make_sm()
        assert "atlas" in sm._table
        assert "conversation_sessions" in sm._table


# ─── append() ─────────────────────────────────────────────────────────────────

class TestAppend:
    def _get_sql(self, role="user", content="Hello", session_id="sess-001") -> str:
        sm, spark = _make_sm()
        sm.append(session_id=session_id, role=role, content=content)
        return spark.sql.call_args_list[0][0][0]

    def test_append_targets_conversation_sessions(self):
        sql = self._get_sql()
        assert "conversation_sessions" in sql

    def test_append_includes_role(self):
        sql = self._get_sql(role="assistant")
        assert "assistant" in sql

    def test_single_quote_in_content_is_escaped(self):
        sql = self._get_sql(content="What\'s the loss ratio?")
        # Escaped apostrophe should appear as doubled quotes
        assert "What''" in sql

    def test_session_id_is_in_sql(self):
        sql = self._get_sql(session_id="my-session-xyz")
        assert "my-session-xyz" in sql

    def test_append_does_not_raise_on_spark_failure(self):
        """append() is best-effort — spark errors must be swallowed."""
        from uw_copilot.session import SessionManager
        spark = MagicMock()
        spark.sql.side_effect = RuntimeError("Delta write failed")
        sm = SessionManager(_make_config(), spark)
        # Should not raise
        sm.append(session_id="s", role="user", content="hello")


# ─── get_history() ────────────────────────────────────────────────────────────

class TestGetHistory:
    def test_returns_list_of_dicts(self):
        row1 = MagicMock(); row1.role = "user";      row1.content = "Hello"
        row2 = MagicMock(); row2.role = "assistant"; row2.content = "Hi there"
        sm, spark = _make_sm(rows=[row1, row2])
        hist = sm.get_history("sess-001")
        assert isinstance(hist, list)
        assert hist[0]["role"] == "user"
        assert hist[1]["content"] == "Hi there"

    def test_returns_empty_list_on_spark_failure(self):
        from uw_copilot.session import SessionManager
        spark = MagicMock()
        spark.sql.side_effect = RuntimeError("table not found")
        sm = SessionManager(_make_config(), spark)
        hist = sm.get_history("any-session")
        assert hist == []
