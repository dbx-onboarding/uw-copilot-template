"""
uw_copilot.feedback — User feedback loop backed by Delta table.

Records thumbs-up/down feedback, tracks quality metrics, and promotes
negative feedback into the MLflow evaluation dataset for continuous improvement.

Table: {catalog}.{schema}.copilot_feedback
(Created by schema/01_create_tables)

Usage (from app or serving endpoint):
    from uw_copilot.feedback import FeedbackManager
    fm = FeedbackManager(cfg, workspace_client)
    fm.record(user_id="james@co.com", query="...", response="...", rating="thumbs_down")
    stats = fm.get_feedback_stats()
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from databricks.sdk import WorkspaceClient

from .config import Config


class FeedbackManager:
    """
    Records and manages user feedback for the UW CoPilot.
    Uses Statement Execution API (works from app, serving endpoint, or notebook).
    Negative feedback is promoted into the eval dataset for continuous improvement.
    """

    def __init__(self, cfg: Config, w: WorkspaceClient):
        self.cfg = cfg
        self.w = w
        self.table = f"{cfg.catalog}.{cfg.schema}.copilot_feedback"

    def _execute(self, sql: str) -> Optional[dict]:
        """Execute SQL via Statement Execution API. Returns {columns, rows} or None."""
        if not self.cfg.warehouse_id:
            return None
        try:
            result = self.w.statement_execution.execute_statement(
                warehouse_id=self.cfg.warehouse_id,
                statement=sql,
                wait_timeout="30s",
            )
            # Surface server-side SQL failures as exceptions so callers can handle them
            if result.status and result.status.state and result.status.state.value == "FAILED":
                err = result.status.error
                raise RuntimeError(f"SQL FAILED: {getattr(err, 'message', err)}")
            if result.manifest and result.manifest.schema and result.manifest.schema.columns:
                columns = [col.name for col in result.manifest.schema.columns]
                rows = result.result.data_array or []
                return {"columns": columns, "rows": rows}
            return {"columns": [], "rows": []}
        except Exception:
            return None

    # ── Record Feedback ────────────────────────────────────────────────────────────

    def record(
        self,
        user_id: str,
        query: str,
        response: str,
        rating: str,
        comment: Optional[str] = None,
        session_id: Optional[str] = None,
        user_role: Optional[str] = None,
        intent_classification: Optional[str] = None,
        retrieved_documents: Optional[List[dict]] = None,
        sql_generated: Optional[str] = None,
        guardrails_triggered: Optional[List[str]] = None,
        response_latency_ms: Optional[int] = None,
        model_version: Optional[str] = None,
    ) -> Optional[str]:
        """
        Record a feedback entry. Returns feedback_id or None on failure.

        rating: "thumbs_up" or "thumbs_down"
        """
        feedback_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        def esc(s: Optional[str]) -> str:
            """Escape single quotes for SQL string literals."""
            return s.replace("'", "''") if s else ""

        def val(s: Optional[str]) -> str:
            """Format optional string as SQL NULL or quoted literal."""
            return f"'{esc(s)}'" if s is not None else "NULL"

        docs_json = json.dumps(retrieved_documents) if retrieved_documents else None
        guards_json = json.dumps(guardrails_triggered) if guardrails_triggered else None

        # Map string rating to int (table schema: rating INT, 1=up, -1=down)
        rating_int = 1 if rating == "thumbs_up" else -1

        # session_id is NOT NULL in the table — coerce a missing one rather than
        # emit a NULL that silently fails the insert.
        sid = session_id or "no-session"
        sql = f"""
            INSERT INTO {self.table}
            (feedback_id, session_id, user_id, question, answer, rating, comment,
             intent_classification, promoted_to_eval, created_at)
            VALUES (
                '{feedback_id}',
                '{esc(sid)}',
                '{esc(user_id)}',
                '{esc(query)}',
                '{esc(response)}',
                {rating_int},
                {val(comment)},
                {val(intent_classification)},
                false,
                TIMESTAMP '{now}'
            )
        """
        result = self._execute(sql)
        return feedback_id if result is not None else None

    # ── Statistics ───────────────────────────────────────────────────────────────

    def get_feedback_stats(self) -> Dict:
        """Get summary statistics on collected feedback."""
        sql = f"""
            SELECT
                COUNT(*) as total_feedback,
                SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as thumbs_up,
                SUM(CASE WHEN rating = -1 THEN 1 ELSE 0 END) as thumbs_down,
                ROUND(SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) * 100.0
                      / NULLIF(COUNT(*), 0), 1) as satisfaction_pct,
                SUM(CASE WHEN promoted_to_eval THEN 1 ELSE 0 END) as promoted_count
            FROM {self.table}
        """
        result = self._execute(sql)
        if not result or not result["rows"]:
            return {"total_feedback": 0, "thumbs_up": 0, "thumbs_down": 0,
                    "satisfaction_pct": 0, "promoted_count": 0}
        row = result["rows"][0]
        cols = result["columns"]
        return {cols[i]: row[i] for i in range(len(cols))}

    # ── Negative Feedback Review ────────────────────────────────────────────────

    def get_negative_feedback(self, limit: int = 20) -> List[Dict]:
        """Get recent negative feedback for review."""
        sql = f"""
            SELECT feedback_id, created_at AS timestamp, user_id, question AS query,
                   LEFT(answer, 200) as response_preview,
                   comment, intent_classification
            FROM {self.table}
            WHERE rating = -1
              AND (promoted_to_eval IS NULL OR promoted_to_eval = false)
            ORDER BY created_at DESC
            LIMIT {limit}
        """
        result = self._execute(sql)
        if not result or not result["rows"]:
            return []
        cols = result["columns"]
        return [{cols[i]: row[i] for i in range(len(cols))} for row in result["rows"]]

    # ── Export to Eval Dataset ──────────────────────────────────────────────────

    def export_to_eval_dataset(self, min_feedback: int = 5) -> Dict:
        """
        Promote negative feedback into eval dataset entries.
        Negative feedback becomes expected_facts for the eval pipeline.
        Returns count of newly promoted entries.
        """
        # Get un-promoted negatives
        negatives = self.get_negative_feedback(limit=100)

        if len(negatives) < min_feedback:
            return {
                "promoted": 0,
                "reason": f"Need at least {min_feedback} negatives (have {len(negatives)})",
            }

        # Build eval entries
        eval_entries = []
        feedback_ids = []
        for row in negatives:
            entry = {
                "query": row.get("query", ""),
                "source": "user_feedback",
                "feedback_id": row.get("feedback_id", ""),
                "expected_facts": row.get("comment")
                    or f"Previous response was rated negatively: {(row.get('response_preview') or '')[:100]}",
            }
            eval_entries.append(entry)
            feedback_ids.append(row["feedback_id"])

        # Mark as promoted
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        ids_str = "','" .join(feedback_ids)
        update_sql = f"""
            UPDATE {self.table}
            SET promoted_to_eval = true,
                promoted_at = timestamp '{now}'
            WHERE feedback_id IN ('{ids_str}')
        """
        self._execute(update_sql)

        return {
            "promoted": len(eval_entries),
            "entries": eval_entries,
            "message": f"Promoted {len(eval_entries)} negative feedback entries to eval dataset",
        }

    # ── Quality Trends ───────────────────────────────────────────────────────────

    def get_quality_trends(self) -> List[Dict]:
        """Analyze feedback trends by intent type and date."""
        sql = f"""
            SELECT
                intent_classification,
                DATE(created_at) as feedback_date,
                COUNT(*) as total,
                SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as positive,
                ROUND(SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) * 100.0
                      / NULLIF(COUNT(*), 0), 1) as satisfaction_pct
            FROM {self.table}
            GROUP BY intent_classification, DATE(created_at)
            ORDER BY feedback_date DESC, intent_classification
        """
        result = self._execute(sql)
        if not result or not result["rows"]:
            return []
        cols = result["columns"]
        return [{cols[i]: row[i] for i in range(len(cols))} for row in result["rows"]]
