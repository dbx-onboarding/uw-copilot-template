"""
uw_copilot.config — Single source of truth for all resource names.

Usage:
    from uw_copilot.config import Config
    cfg = Config()                        # auto-discovers company_config.yaml
    cfg = Config("/path/to/config.yaml")  # explicit path

All resource names are derived properties. Never set them manually.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml


class Config:
    """
    Loads company_config.yaml and derives every resource name used
    across the pipeline, the app, and the agent.

    Discovery order for config file:
      1. Explicit path passed to __init__
      2. UWCOPILOT_CONFIG env variable
      3. Walk up from this file's location: look for config/company_config.yaml
         at ../../../ (repo root relative to src/uw_copilot/)
    """

    def __init__(self, config_path: Optional[str] = None):
        resolved = config_path or os.environ.get("UWCOPILOT_CONFIG") or self._discover()
        with open(resolved) as f:
            self._raw: dict = yaml.safe_load(f)
        self._config_path = resolved
        self._derive()

    # ── Discovery ─────────────────────────────────────────────────────────────

    def _discover(self) -> str:
        """Walk up from this file to find config/company_config.yaml."""
        here = Path(__file__).resolve().parent
        for ancestor in [here, here.parent, here.parent.parent, here.parent.parent.parent]:
            candidate = ancestor / "config" / "company_config.yaml"
            if candidate.exists():
                return str(candidate)
        raise FileNotFoundError(
            "company_config.yaml not found. "
            "Set UWCOPILOT_CONFIG env variable or pass an explicit path to Config()."
        )

    # ── Derivation ────────────────────────────────────────────────────────────

    def _derive(self) -> None:
        raw = self._raw

        # Company identity
        self.company_name: str = raw["company"]["name"]
        self.short_name: str   = raw["company"]["short_name"]
        self.domain: str       = raw["company"]["domain"]
        self.prefix: str       = f"{self.short_name}_{self.domain}"

        # ── Resource names — derived, never set manually ──────────────────────
        self.catalog:           str = raw["catalog"]
        self.schema:            str = f"{self.prefix}_rag"
        self.vs_endpoint:       str = f"{self.prefix}_vs_endpoint"
        self.vs_index:          str = f"{self.catalog}.{self.schema}.document_chunks_index"
        self.serving_endpoint:  str = f"{self.prefix}_rag_endpoint"
        self.app_name:          str = f"{self.prefix}_uw_copilot_app"
        self.uc_model:          str = f"{self.catalog}.{self.schema}.uw_copilot_rag_model"
        self.uc_model_alias:    str = "champion"

        # ── Intake ────────────────────────────────────────────────────────────
        self.volume_name:     str  = raw["intake"]["volume_name"]
        _override:            Optional[str] = raw["intake"].get("volume_path")
        self._volume_path_overridden: bool  = bool(_override)
        self.volume_path:     str  = _override or f"/Volumes/{self.catalog}/{self.schema}/{self.volume_name}"
        self.intake_schedule: str  = raw["intake"]["schedule"]

        # ── Models ────────────────────────────────────────────────────────────
        self.chat_model:      str = raw["models"]["chat"]
        self.embedding_model: str = raw["models"]["embedding"]

        # ── SQL Warehouse (for app queries and NL-to-SQL) ─────────────────────
        self.warehouse_id: str = raw.get("warehouse_id", "")

        # ── Chunking ──────────────────────────────────────────────────────────
        self.parent_chunk_size: int = raw["chunking"]["parent_size"]
        self.child_chunk_size:  int = raw["chunking"]["child_size"]
        self.chunk_overlap:     int = raw["chunking"]["overlap"]

        # ── Similarity search ─────────────────────────────────────────────────
        self.similarity_threshold:   float = raw["similarity"]["threshold"]
        self.similarity_max_results: int   = raw["similarity"]["max_results"]

        # ── Document categories ───────────────────────────────────────────────
        self.doc_categories: List[Dict]  = raw["doc_categories"]
        self.category_labels: List[str]  = [c["label"] for c in self.doc_categories]

        # ── RBAC ──────────────────────────────────────────────────────────────
        self.rbac_policy: Dict[str, List[str]] = raw["rbac"]

    # ── RBAC helpers ──────────────────────────────────────────────────────────

    def categories_for_role(self, role: str) -> Optional[List[str]]:
        """
        Returns the list of category labels accessible to a role,
        or None if the role has access to all categories.
        Raises KeyError if the role is not in the policy.
        """
        allowed = self.rbac_policy.get(role)
        if allowed is None:
            raise KeyError(f"Role '{role}' is not defined in rbac_policy")
        if allowed == ["all"] or "all" in allowed:
            return None  # None = no filter = all categories
        return allowed

    def validate_role(self, role: str) -> bool:
        return role in self.rbac_policy

    # ── Summary ───────────────────────────────────────────────────────────────

    def print_summary(self) -> None:
        w = 66
        line = "═" * w
        print(f"╔{line}╗")
        print(f"║  UW CoPilot — Configuration{'':>{w - 28}}║")
        print(f"╠{line}╣")
        rows = [
            ("Company",        self.company_name),
            ("Prefix",         self.prefix),
            ("Catalog",        self.catalog),
            ("Schema",         self.schema),
            ("VS Endpoint",    self.vs_endpoint),
            ("Serving EP",     self.serving_endpoint),
            ("App",            self.app_name),
            ("Chat Model",     self.chat_model),
            ("Volume Path",    self.volume_path),
            ("Warehouse ID",   self.warehouse_id or "(not set)"),
            ("Categories",     str(len(self.doc_categories))),
        ]
        for label, value in rows:
            print(f"║  {label:<16}{value:<{w - 18}}║")
        print(f"╚{line}╝")

    def ensure_volume_exists(self, spark) -> str:
        """
        Creates the intake UC Volume if it does not already exist.
        Also ensures the parent catalog and schema exist.
        Returns the volume path so it can be used immediately.

        If ``intake.volume_path`` is explicitly set in company_config.yaml
        (i.e. pointing to a pre-existing volume in another schema), this is
        a no-op — no CREATE statements are issued.

        Call this in every notebook that reads from or writes to the volume,
        before the first read_files() or cloudFiles .load():

            vol = cfg.ensure_volume_exists(spark)
        """
        if self._volume_path_overridden:
            print(f"[ensure_volume_exists] Using existing volume: {self.volume_path}")
            return self.volume_path
        spark.sql(f"CREATE CATALOG IF NOT EXISTS {self.catalog}")
        spark.sql(f"CREATE SCHEMA IF NOT EXISTS {self.catalog}.{self.schema}")
        spark.sql(
            f"CREATE VOLUME IF NOT EXISTS "
            f"{self.catalog}.{self.schema}.{self.volume_name}"
        )
        return self.volume_path

    def __repr__(self) -> str:
        return f"Config(prefix={self.prefix!r}, catalog={self.catalog!r})"
