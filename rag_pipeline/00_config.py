# Databricks notebook source
# MAGIC %md
# MAGIC # 00 — Configuration
# MAGIC
# MAGIC Installs the `uw_copilot` package and loads `company_config.yaml`.
# MAGIC Run `%run ./00_config` at the top of every pipeline notebook for
# MAGIC interactive development, or import directly in production:
# MAGIC
# MAGIC ```python
# MAGIC from uw_copilot.config import Config
# MAGIC cfg = Config()
# MAGIC ```

# COMMAND ----------
# Derive repo root from this notebook's location, then pip install the package.
# Works for any user and any workspace path — no hardcoding required.

import subprocess, sys

_nb_path   = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
# nb_path is like /Users/you@example.com/uw-copilot-template/rag_pipeline/00_config
# Go up two levels: rag_pipeline/ → repo root
_repo_root = "/Workspace/" + "/".join(_nb_path.strip("/").split("/")[:-2])

subprocess.run(
    [sys.executable, "-m", "pip", "install", "-q", "-e", _repo_root],
    check=True,
)

# COMMAND ----------
dbutils.library.restartPython()

# COMMAND ----------
from uw_copilot.config import Config

cfg = Config()
cfg.print_summary()

# COMMAND ----------
# Re-export flat names so older notebooks using `%run ./00_config` keep working.
# New code should use cfg.xxx directly.

COMPANY_NAME     = cfg.company_name
PREFIX           = cfg.prefix
CATALOG          = cfg.catalog
SCHEMA           = cfg.schema
VS_ENDPOINT      = cfg.vs_endpoint
VS_INDEX_NAME    = cfg.vs_index
SERVING_ENDPOINT = cfg.serving_endpoint
APP_NAME         = cfg.app_name
UC_MODEL_NAME    = cfg.uc_model

VOLUME_PATH      = cfg.volume_path
CHAT_MODEL       = cfg.chat_model
EMBEDDING_MODEL  = cfg.embedding_model
WAREHOUSE_ID     = cfg.warehouse_id

PARENT_CHUNK_SIZE      = cfg.parent_chunk_size
CHILD_CHUNK_SIZE       = cfg.child_chunk_size
CHUNK_OVERLAP          = cfg.chunk_overlap
SIMILARITY_THRESHOLD   = cfg.similarity_threshold
SIMILARITY_MAX_RESULTS = cfg.similarity_max_results

DOC_CATEGORIES  = cfg.doc_categories
CATEGORY_LABELS = cfg.category_labels
RBAC_POLICY     = cfg.rbac_policy

# Ensure intake volume exists (CREATE VOLUME IF NOT EXISTS)
cfg.ensure_volume_exists(spark)
# NOTE: spark.conf.set('spark.databricks.delta.schema.autoMerge.enabled', 'true')
# is NOT supported on serverless. Use .option('mergeSchema', 'true') on writes.
