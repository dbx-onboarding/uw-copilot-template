"""
tests/test_config.py — Config loading and resource name derivation.

Run with: pytest tests/test_config.py -v
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from uw_copilot.config import Config

# ── Fixtures ──────────────────────────────────────────────────────────────────

MINIMAL_CONFIG = {
    "company": {"name": "Test Co", "short_name": "test", "domain": "casualty"},
    "catalog": "test_catalog",
    "intake":  {"volume_name": "raw_documents", "schedule": "*/30 * * * *"},
    "models":  {"chat": "test-chat-model", "embedding": "test-embed-model"},
    "chunking": {"parent_size": 2500, "child_size": 600, "overlap": 100},
    "similarity": {"threshold": 0.75, "max_results": 10},
    "doc_categories": [
        {"id": "01_guidelines", "label": "Underwriting Guidelines"},
        {"id": "02_submissions", "label": "Submissions"},
    ],
    "rbac": {
        "underwriter": ["all"],
        "broker": ["Underwriting Guidelines"],
    },
}


@pytest.fixture
def config_file(tmp_path):
    cfg_dir = tmp_path / "config"
    cfg_dir.mkdir()
    path = cfg_dir / "company_config.yaml"
    path.write_text(yaml.dump(MINIMAL_CONFIG))
    return str(path)


@pytest.fixture
def cfg(config_file):
    return Config(config_file)


# ── Naming convention ─────────────────────────────────────────────────────────

class TestNamingConvention:
    def test_prefix_derivation(self, cfg):
        assert cfg.prefix == "test_casualty"

    def test_schema_follows_prefix(self, cfg):
        assert cfg.schema == "test_casualty_rag"

    def test_vs_endpoint_follows_prefix(self, cfg):
        assert cfg.vs_endpoint == "test_casualty_vs_endpoint"

    def test_serving_endpoint_follows_prefix(self, cfg):
        assert cfg.serving_endpoint == "test_casualty_rag_endpoint"

    def test_app_name_follows_prefix(self, cfg):
        assert cfg.app_name == "test_casualty_uw_copilot_app"

    def test_uc_model_is_fully_qualified(self, cfg):
        assert cfg.uc_model == "test_catalog.test_casualty_rag.uw_copilot_rag_model"

    def test_vs_index_is_fully_qualified(self, cfg):
        assert cfg.vs_index == "test_catalog.test_casualty_rag.document_chunks_index"

    def test_short_name_and_domain_are_stored(self, cfg):
        assert cfg.short_name == "test"
        assert cfg.domain == "casualty"


# ── Config fields ─────────────────────────────────────────────────────────────

class TestConfigFields:
    def test_catalog(self, cfg):
        assert cfg.catalog == "test_catalog"

    def test_volume_path_derived(self, cfg):
        assert cfg.volume_name == "raw_documents"
        assert cfg.volume_path == "/Volumes/test_catalog/test_casualty_rag/raw_documents"
        assert cfg._volume_path_overridden is False

    def test_volume_path_override(self, tmp_path):
        raw = {
            **MINIMAL_CONFIG,
            "intake": {
                "volume_name": "raw_documents",
                "volume_path": "/Volumes/other_cat/other_schema/raw_documents",
                "schedule": "*/15 * * * *",
            },
        }
        path = tmp_path / "config" / "company_config.yaml"
        path.parent.mkdir()
        path.write_text(yaml.dump(raw))
        c = Config(str(path))
        assert c.volume_path == "/Volumes/other_cat/other_schema/raw_documents"
        assert c._volume_path_overridden is True

    def test_models(self, cfg):
        assert cfg.chat_model == "test-chat-model"
        assert cfg.embedding_model == "test-embed-model"

    def test_chunking(self, cfg):
        assert cfg.parent_chunk_size == 2500
        assert cfg.child_chunk_size  == 600
        assert cfg.chunk_overlap     == 100

    def test_similarity(self, cfg):
        assert cfg.similarity_threshold   == 0.75
        assert cfg.similarity_max_results == 10

    def test_category_labels(self, cfg):
        assert cfg.category_labels == ["Underwriting Guidelines", "Submissions"]

    def test_warehouse_id_defaults_empty(self, cfg):
        assert cfg.warehouse_id == ""

    def test_warehouse_id_set_when_present(self, tmp_path):
        raw = {**MINIMAL_CONFIG, "warehouse_id": "abc123"}
        path = tmp_path / "config" / "company_config.yaml"
        path.parent.mkdir()
        path.write_text(yaml.dump(raw))
        c = Config(str(path))
        assert c.warehouse_id == "abc123"


# ── RBAC helpers ──────────────────────────────────────────────────────────────

class TestRBAC:
    def test_all_role_returns_none(self, cfg):
        assert cfg.categories_for_role("underwriter") is None

    def test_restricted_role_returns_list(self, cfg):
        assert cfg.categories_for_role("broker") == ["Underwriting Guidelines"]

    def test_unknown_role_raises_key_error(self, cfg):
        with pytest.raises(KeyError, match="claims_adjuster"):
            cfg.categories_for_role("claims_adjuster")

    def test_validate_role_known(self, cfg):
        assert cfg.validate_role("underwriter") is True

    def test_validate_role_unknown(self, cfg):
        assert cfg.validate_role("hacker") is False


# ── Discovery ─────────────────────────────────────────────────────────────────

class TestDiscovery:
    def test_explicit_path_wins(self, config_file):
        c = Config(config_file)
        assert c.company_name == "Test Co"

    def test_env_var_used_when_set(self, config_file, monkeypatch):
        monkeypatch.setenv("UWCOPILOT_CONFIG", config_file)
        c = Config()  # no explicit path — should use env var
        assert c.company_name == "Test Co"

    def test_env_var_takes_priority_over_discovery(self, config_file, monkeypatch):
        monkeypatch.setenv("UWCOPILOT_CONFIG", config_file)
        # Even if _discover() would find the Atlas config, env var should win
        c = Config()
        assert c.company_name == "Test Co"

    def test_missing_config_raises_file_not_found(self, tmp_path, monkeypatch):
        """_discover() raises FileNotFoundError when no config can be found."""
        monkeypatch.delenv("UWCOPILOT_CONFIG", raising=False)
        # Patch _discover so it raises rather than finding the real Atlas config
        with patch.object(Config, "_discover", side_effect=FileNotFoundError("company_config.yaml not found")):
            with pytest.raises(FileNotFoundError, match="company_config.yaml"):
                Config()

    def test_repr(self, cfg):
        assert "test_casualty" in repr(cfg)
