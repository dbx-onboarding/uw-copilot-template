"""
uw_copilot.session — Conversation memory backed by a Delta table.

Sessions are stored in {catalog}.{schema}.conversation_sessions.
The table is created by schema/01_create_tables.

Compresses old sessions when message count exceeds COMPRESSION_THRESHOLD
by summarising the oldest messages into a single system message.

Usage:
    from uw_copilot.session import SessionManager
    sm = SessionManager(cfg, spark)
    history = sm.get_history("session-abc-123")
    sm.append("session-abc-123", role="user", content="What is the loss ratio?")
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from .config import Config

if TYPE_CHECKING:
    from pyspark.sql import SparkSession

MAX_MESSAGES           = 10   # Messages returned to the LLM context window
COMPRESSION_THRESHOLD  = 20   # Compress when stored message count exceeds this


class SessionManager:
    """
    Reads and writes conversation history to the conversation_sessions Delta table.
    Pass the active SparkSession; it is used for Delta writes. Reads use spark.sql.
    """

    def __init__(self, cfg: Config, spark: "SparkSession"):
        self.cfg   = cfg
        self.spark = spark
        self._table = f"{cfg.catalog}.{cfg.schema}.conversation_sessions"

    # ── Public API ────────────────────────────────────────────────────────────

    def get_history(self, session_id: str) -> List[dict]:
        """
        Returns the last MAX_MESSAGES messages for a session,
        in chronological order (oldest first).
        Returns [] if the session doesn't exist.
        """
        try:
            rows = self.spark.sql(f"""
                SELECT role, content
                FROM {self._table}
                WHERE session_id = '{_escape(session_id)}'
                ORDER BY created_at ASC
                LIMIT {MAX_MESSAGES}
            """).collect()
            return [{"role": r.role, "content": r.content} for r in rows]
        except Exception:
            return []

    def append(self, session_id: str, role: str, content: str, user_id: str = "") -> None:
        """Add a single message to the session. Creates the row in Delta."""
        now  = datetime.now(timezone.utc).isoformat()
        safe = _escape(content)
        try:
            self.spark.sql(f"""
                INSERT INTO {self._table}
                (session_id, role, content, user_id, created_at)
                VALUES (
                    '{_escape(session_id)}',
                    '{_escape(role)}',
                    '{safe}',
                    '{_escape(user_id)}',
                    TIMESTAMP '{now}'
                )
            """)
            self._maybe_compress(session_id)
        except Exception:
            pass  # Session writes are best-effort; don't crash the request

    def clear(self, session_id: str) -> None:
        """Delete all messages for a session."""
        self.spark.sql(f"""
            DELETE FROM {self._table}
            WHERE session_id = '{_escape(session_id)}'
        """)

    def message_count(self, session_id: str) -> int:
        try:
            return self.spark.sql(f"""
                SELECT COUNT(*) AS cnt FROM {self._table}
                WHERE session_id = '{_escape(session_id)}'
            """).collect()[0].cnt
        except Exception:
            return 0

    # ── Compression ───────────────────────────────────────────────────────────

    def _maybe_compress(self, session_id: str) -> None:
        """
        When the session exceeds COMPRESSION_THRESHOLD messages, summarise
        the oldest half into a single system message and delete the originals.
        """
        count = self.message_count(session_id)
        if count < COMPRESSION_THRESHOLD:
            return

        half = count // 2
        try:
            old_rows = self.spark.sql(f"""
                SELECT role, content FROM {self._table}
                WHERE session_id = '{_escape(session_id)}'
                ORDER BY created_at ASC
                LIMIT {half}
            """).collect()

            summary = "Earlier conversation summary: " + "; ".join(
                f"[{r.role}] {r.content[:100]}" for r in old_rows
            )

            # Delete the old messages
            cutoff_id = self.spark.sql(f"""
                SELECT created_at FROM {self._table}
                WHERE session_id = '{_escape(session_id)}'
                ORDER BY created_at ASC
                LIMIT {half}
            """).collect()[-1].created_at

            self.spark.sql(f"""
                DELETE FROM {self._table}
                WHERE session_id = '{_escape(session_id)}'
                  AND created_at <= TIMESTAMP '{cutoff_id}'
            """)

            # Replace with a single summary message
            now = datetime.now(timezone.utc).isoformat()
            self.spark.sql(f"""
                INSERT INTO {self._table}
                (session_id, role, content, user_id, created_at)
                VALUES (
                    '{_escape(session_id)}', 'system',
                    '{_escape(summary)}', 'system',
                    TIMESTAMP '{now}'
                )
            """)
        except Exception:
            pass  # Compression is best-effort


def _escape(value: str) -> str:
    """Escape single quotes for SQL string literals."""
    return str(value).replace("'", "''")
